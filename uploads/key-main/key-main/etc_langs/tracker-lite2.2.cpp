#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <string>
#include <vector>
#include <array>
#include <unordered_set>
#include <chrono>
#include <ctime>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <algorithm>
#include <optional>

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <errno.h>

static const std::string LOG_FILE  = "/data/log.txt";
static const std::string HTML_FILE = "/data/log.html";

static std::ofstream log_fp(LOG_FILE, std::ios::app);
static std::ofstream html_fp(HTML_FILE, std::ios::app);

static double latest_lat   = 0.0;
static double latest_lon   = 0.0;
static int    latest_speed = 0;

static const std::unordered_set<uint8_t> MSG_WITH_GPS_BLOCK{
    0x10, 0x11, 0x12, 0x22, 0x31, 0x32, 0x37, 0x16,
    0x26, 0x27, 0x1A, 0x1E, 0xA0, 0xA2, 0x17, 0x2D, 0x34
};

static constexpr uint8_t MSG_ADDRESS_REQUEST  = 0x2A;
static constexpr uint8_t MSG_ADDRESS_RESPONSE = 0x97;
static constexpr uint8_t MSG_TIME_REQUEST     = 0x8A;

static std::string timestamp()
{
    auto now  = std::chrono::system_clock::now();
    auto tt   = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
    localtime_r(&tt, &tm);
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

static void log(const std::string &msg)
{
    std::string ts = timestamp();
    std::string line = ts + "  " + msg;
    log_fp << line << '\n';
    log_fp.flush();
    std::cout << line << std::endl;
}

static void append_uri(const std::string &uri,
                       int speed,
                       const std::string &dt_str)
{
    std::string ts = timestamp();
    html_fp << "<p><a href=\"" << uri << "\">"
            << dt_str << " Open map</a></p>\n";
    html_fp << "<p>Speed: " << speed << " km/h</p>\n";
    html_fp << "<p>DateTime: " << ts << "</p>\n";
    html_fp.flush();
}

static uint8_t reflect_byte(uint8_t b)
{
    uint8_t res = 0;
    for (int i = 0; i < 8; ++i) {
        res = (res << 1) | (b & 1);
        b >>= 1;
    }
    return res;
}

static uint16_t crc16_x25(const std::vector<uint8_t> &data)
{
    uint16_t crc = 0xFFFF;
    for (uint8_t byte : data) {
        uint8_t b = reflect_byte(byte);
        crc ^= static_cast<uint16_t>(b) << 8;
        for (int i = 0; i < 8; ++i) {
            if (crc & 0x8000) {
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF;
            } else {
                crc = (crc << 1) & 0xFFFF;
            }
        }
    }
    uint8_t crch = reflect_byte((crc >> 8) & 0xFF);
    uint8_t crcl = reflect_byte(crc & 0xFF);
    crc = (static_cast<uint16_t>(crcl) << 8) | crch;
    return crc ^ 0xFFFF;
}

static std::vector<uint8_t> build_response(bool basic,
                                           uint8_t msg_type,
                                           uint16_t index,
                                           const std::vector<uint8_t> &content = {})
{
    std::vector<uint8_t> pkt;
    if (basic) {
        pkt.push_back(0x78);
        pkt.push_back(0x78);
    } else {
        pkt.push_back(0x79);
        pkt.push_back(0x79);
    }
    uint16_t length = 5 + static_cast<uint16_t>(content.size());
    std::vector<uint8_t> length_bytes;
    if (basic) {
        length_bytes.push_back(static_cast<uint8_t>(length));
    } else {
        length_bytes.push_back(static_cast<uint8_t>(length >> 8));
        length_bytes.push_back(static_cast<uint8_t>(length & 0xFF));
    }
    pkt.insert(pkt.end(), length_bytes.begin(), length_bytes.end());
    pkt.push_back(msg_type);
    pkt.insert(pkt.end(), content.begin(), content.end());
    pkt.push_back(static_cast<uint8_t>(index >> 8));
    pkt.push_back(static_cast<uint8_t>(index & 0xFF));
    std::vector<uint8_t> crc_input;
    crc_input.insert(crc_input.end(), length_bytes.begin(), length_bytes.end());
    crc_input.push_back(msg_type);
    crc_input.insert(crc_input.end(), content.begin(), content.end());
    crc_input.push_back(static_cast<uint8_t>(index >> 8));
    crc_input.push_back(static_cast<uint8_t>(index & 0xFF));
    uint16_t crc = crc16_x25(crc_input);
    pkt.push_back(static_cast<uint8_t>(crc >> 8));
    pkt.push_back(static_cast<uint8_t>(crc & 0xFF));
    pkt.push_back('\r');
    pkt.push_back('\n');
    return pkt;
}

static std::optional<std::vector<uint8_t>> extract_frame(std::vector<uint8_t> &buf)
{
    auto it = std::search(buf.begin(), buf.end(),
                          std::begin("\x0D\x0A"),
                          std::begin("\x0D\x0A") + 2);
    if (it == buf.end())
        return std::nullopt;
    size_t idx = std::distance(buf.begin(), it);
    std::vector<uint8_t> pkt(buf.begin(), buf.begin() + idx + 2);
    buf.erase(buf.begin(), buf.begin() + idx + 2);
    return pkt;
}

struct GPSData {
    double latitude;
    double longitude;
    int speed;
    std::string datetime;
};

static std::optional<GPSData> decode_gps_block(const std::vector<uint8_t> &payload)
{
    if (payload.size() < 16)
        return std::nullopt;
    try {
        uint8_t yy = payload[0];
        uint8_t mm = payload[1];
        uint8_t dd = payload[2];
        uint8_t hh = payload[3];
        uint8_t mi = payload[4];
        uint8_t ss = payload[5];
        int year = 2000 + yy;
        std::tm tm_time{};
        tm_time.tm_year = year - 1900;
        tm_time.tm_mon  = mm - 1;
        tm_time.tm_mday = dd;
        tm_time.tm_hour = hh;
        tm_time.tm_min  = mi;
        tm_time.tm_sec  = ss;
        std::ostringstream dt_oss;
        dt_oss << std::put_time(&tm_time, "%Y-%m-%d %H:%M:%S");
        std::string dt_str = dt_oss.str();
        uint8_t sats = payload[6] & 0x0F;
        int pos = 7;
        int32_t lat_raw = static_cast<int32_t>(
            (payload[pos] << 24) | (payload[pos+1] << 16) |
            (payload[pos+2] << 8)  | payload[pos+3]);
        pos += 4;
        int32_t lon_raw = static_cast<int32_t>(
            (payload[pos] << 24) | (payload[pos+1] << 16) |
            (payload[pos+2] << 8)  | payload[pos+3]);
        pos += 4;
        int speed = static_cast<int>(payload[pos]);
        pos += 1;
        uint16_t flags = (payload[pos] << 8) | payload[pos+1];
        double lat = lat_raw / 60.0 / 30000.0;
        double lon = lon_raw / 60.0 / 30000.0;
        if (!(flags & (1 << 10))) lat = -lat;
        if (flags & (1 << 11)) lon = -lon;
        bool valid = (flags >> 12) & 1;
        if (!valid) return std::nullopt;
        GPSData data{lat, lon, speed, dt_str};
        return data;
    } catch (...) {
        return std::nullopt;
    }
}

static void send_response(int fd, const std::vector<uint8_t> &data) {
    send(fd, data.data(), data.size(), 0);
}

static void tcp_server(const std::string &host = "0.0.0.0", int port = 9016)
{
    int listenfd = socket(AF_INET, SOCK_STREAM, 0);
    if (listenfd < 0) throw std::runtime_error("socket() failed");
    int opt = 1;
    setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR,
               reinterpret_cast<char *>(&opt), sizeof(opt));
    struct sockaddr_in serv_addr{};
    serv_addr.sin_family      = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(host.c_str());
    serv_addr.sin_port        = htons(port);
    if (bind(listenfd, reinterpret_cast<struct sockaddr *>(&serv_addr),
             sizeof(serv_addr)) < 0) {
        close(listenfd);
        throw std::runtime_error("bind() failed");
    }
    if (listen(listenfd, 1) < 0) {
        close(listenfd);
        throw std::runtime_error("listen() failed");
    }
    log("[TCP] Listening on " + host + ":" + std::to_string(port));
    while (true) {
        struct sockaddr_in cli_addr{};
        socklen_t cli_len = sizeof(cli_addr);
        int connfd = accept(listenfd,
                            reinterpret_cast<struct sockaddr *>(&cli_addr),
                            &cli_len);
        if (connfd < 0) {
            log("[TCP] accept() error: " + std::string(strerror(errno)));
            continue;
        }
        char cli_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(cli_addr.sin_addr), cli_ip, INET_ADDRSTRLEN);
        log("[TCP] Connected by " + std::string(cli_ip) +
            ":" + std::to_string(ntohs(cli_addr.sin_port)));
        std::vector<uint8_t> buf;
        while (true) {
            uint8_t tmp[1024];
            ssize_t recvd = recv(connfd, tmp, sizeof(tmp), 0);
            if (recvd <= 0) {
                log("[TCP] Connection closed by peer");
                break;
            }
            buf.insert(buf.end(), tmp, tmp + recvd);
            while (true) {
                auto opt_pkt = extract_frame(buf);
                if (!opt_pkt) break;
                std::vector<uint8_t> pkt = std::move(*opt_pkt);
                if (pkt.size() < 7) {
                    std::ostringstream oss;
                    oss << "[RECV] Too short: " << std::hex;
                    for (auto b : pkt) oss << std::setw(2) << std::setfill('0') << (int)b;
                    log(oss.str());
                    continue;
                }
                bool basic = false;
                uint8_t msg_type = 0;
                uint16_t index = 0;
                uint16_t crc_recv = 0;
                uint16_t crc_calc = 0;
                std::vector<uint8_t> payload;
                std::vector<uint8_t> header(pkt.begin(), pkt.begin() + 2);
                if (header[0] == 0x78 && header[1] == 0x78) {
                    basic = true;
                    msg_type = pkt[3];
                    index   = (pkt[pkt.size() - 6] << 8) | pkt[pkt.size() - 5];
                    crc_recv = (pkt[pkt.size() - 4] << 8) | pkt[pkt.size() - 3];
                    crc_calc = crc16_x25(std::vector<uint8_t>(pkt.begin() + 2,
                                                               pkt.end() - 4));
                    payload.assign(pkt.begin() + 4, pkt.end() - 6);
                } else if (header[0] == 0x79 && header[1] == 0x79) {
                    basic = false;
                    msg_type = pkt[4];
                    index   = (pkt[pkt.size() - 6] << 8) | pkt[pkt.size() - 5];
                    crc_recv = (pkt[pkt.size() - 4] << 8) | pkt[pkt.size() - 3];
                    crc_calc = crc16_x25(std::vector<uint8_t>(pkt.begin() + 2,
                                                               pkt.end() - 4));
                    payload.assign(pkt.begin() + 5, pkt.end() - 6);
                } else {
                    std::ostringstream oss;
                    oss << "[RECV] Bad header: " << std::hex;
                    for (auto b : header) oss << std::setw(2) << std::setfill('0') << (int)b;
                    log(oss.str());
                    continue;
                }
                if (crc_calc != crc_recv) {
                    std::ostringstream oss;
                    oss << "[WARN] CRC mismatch: calc=" << std::hex << std::setw(4) << std::setfill('0') << crc_calc
                        << " recv=" << crc_recv << " (processing anyway)";
                    log(oss.str());
                }
                std::ostringstream oss;
                oss << "[RECV] type=0x" << std::hex << std::setw(2) << std::setfill('0')
                    << (int)msg_type << " idx=" << index << " len=" << pkt.size();
                log(oss.str());
                if (MSG_WITH_GPS_BLOCK.count(msg_type)) {
                    auto gps_opt = decode_gps_block(payload);
                    if (gps_opt) {
                        latest_lat   = gps_opt->latitude;
                        latest_lon   = gps_opt->longitude;
                        latest_speed = gps_opt->speed;
                        log("[GPS] lat=" + std::to_string(latest_lat) +
                            ", lon=" + std::to_string(latest_lon) +
                            ", speed=" + std::to_string(latest_speed) + " km/h, datetime=" + gps_opt->datetime);
                        std::ostringstream uri;
                        uri << "geo:" << std::fixed << std::setprecision(6)
                            << latest_lat << "," << latest_lon << ";u=35";
                        append_uri(uri.str(), latest_speed, gps_opt->datetime);
                    }
                } else if (msg_type == MSG_ADDRESS_REQUEST) {
                    std::vector<uint8_t> resp_content = {'N','A','&','&','N','A','&','&','0','#','#'};
                    auto resp = build_response(false, MSG_ADDRESS_RESPONSE, 0, resp_content);
                    send_response(connfd, resp);
                    log("[RESP] Address response");
                } else if (msg_type == MSG_TIME_REQUEST) {
                    auto now = std::chrono::system_clock::now();
                    std::time_t tt = std::chrono::system_clock::to_time_t(now);
                    std::tm utc_tm{};
                    gmtime_r(&tt, &utc_tm);
                    std::vector<uint8_t> time_bytes = {
                        static_cast<uint8_t>(utc_tm.tm_year - 100),
                        static_cast<uint8_t>(utc_tm.tm_mon + 1),
                        static_cast<uint8_t>(utc_tm.tm_mday),
                        static_cast<uint8_t>(utc_tm.tm_hour),
                        static_cast<uint8_t>(utc_tm.tm_min),
                        static_cast<uint8_t>(utc_tm.tm_sec)
                    };
                    auto resp = build_response(true, MSG_TIME_REQUEST, 0, time_bytes);
                    send_response(connfd, resp);
                    log("[RESP] Time response");
                } else if (msg_type != 0x80 && msg_type != 0x81 && msg_type != 0x82) {
                    auto ack = build_response(basic, msg_type, index);
                    send_response(connfd, ack);
                    std::ostringstream ack_msg;
                    ack_msg << "[ACK] 0x" << std::hex << std::setw(2) << std::setfill('0') << (int)msg_type;
                    log(ack_msg.str());
                }
            }
        }
        close(connfd);
    }
    close(listenfd);
}

int main()
{
    try {
        tcp_server();
    } catch (const std::exception &e) {
        log("[ERROR] " + std::string(e.what()));
        return 1;
    }
    return 0;
}