/************************************************************
 *  File:  tracker-lite.cpp
 *  Purpose:  TCP server that logs GPS packets, creates an HTML
 *            link, and replies with ACK packets.
 *
 *  Build:
 *      g++ -std=c++17 -Wall -O2 -o tracker tracker-lite.cpp
 *
 *  Run:
 *      ./tracker            # listens on 0.0.0.0:9016
 *****************************************************************/

#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <string>
#include <vector>
#include <chrono>
#include <ctime>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <algorithm>          // <-- needed for std::search

/* POSIX socket headers */
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <errno.h>

/* ------------------- Globals ----------------------------------- */
static std::ofstream log_fp("log.txt", std::ios::app);
static std::ofstream html_fp("log.html", std::ios::app);

static double latest_lat  = 0.0;
static double latest_lon  = 0.0;
static int    latest_speed = 0;

/* ------------------- Helpers ----------------------------------- */
static std::string timestamp()
{
    auto now  = std::chrono::system_clock::now();
    auto tt   = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
#if defined(_MSC_VER) || defined(__MINGW32__)
    localtime_s(&tm, &tt);
#else
    localtime_r(&tt, &tm);
#endif
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

static void log(const std::string &msg)
{
    std::string ts = timestamp();
    log_fp << ts << "  " << msg << '\n';
    log_fp.flush();
    std::cout << ts << "  " << msg << std::endl;
}

static void append_uri(const std::string &uri, int speed)
{
    std::string ts = timestamp();
    html_fp << "<p><a href=\"" << uri << "\">" << ts
            << " Open map</a></p>\n";
    html_fp << "<p>Speed: " << speed << " km/h</p>\n";
    html_fp.flush();
}

static uint16_t crc16_xmodem(const std::vector<uint8_t> &data)
{
    uint16_t crc = 0;
    for (uint8_t b : data) {
        crc ^= static_cast<uint16_t>(b) << 8;
        for (int i = 0; i < 8; ++i) {
            crc = (crc & 0x8000) ?
                ((crc << 1) ^ 0x1021) :
                (crc << 1);
        }
    }
    return crc & 0xFFFF;
}

static std::vector<uint8_t> ack_packet(const std::vector<uint8_t> &ack_prot,
                                       const std::vector<uint8_t> &seq)
{
    std::vector<uint8_t> payload;
    payload.insert(payload.end(), ack_prot.begin(), ack_prot.end());
    payload.insert(payload.end(), seq.begin(), seq.end());
    uint16_t crc = crc16_xmodem(payload);
    std::vector<uint8_t> pkt{0x78, 0x78, 0x05};
    pkt.insert(pkt.end(), ack_prot.begin(), ack_prot.end());
    pkt.insert(pkt.end(), seq.begin(), seq.end());
    pkt.push_back(static_cast<uint8_t>(crc >> 8));
    pkt.push_back(static_cast<uint8_t>(crc & 0xFF));
    pkt.push_back(0x0D);
    pkt.push_back(0x0A);
    return pkt;
}

static void sendall(int sock, const std::vector<uint8_t> &data)
{
    size_t total = 0;
    while (total < data.size()) {
        ssize_t sent = send(sock, data.data() + total,
                            data.size() - total, 0);
        if (sent <= 0) {
            throw std::runtime_error("send failed");
        }
        total += static_cast<size_t>(sent);
    }
}

/* ------------------- Server ----------------------------------- */
static void tcp_server(const std::string &host = "0.0.0.0", int port = 9016)
{
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) throw std::runtime_error("socket() failed");

    int opt = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR,
               reinterpret_cast<char *>(&opt), sizeof(opt));

    struct sockaddr_in serv_addr{};
    serv_addr.sin_family      = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(host.c_str());
    serv_addr.sin_port        = htons(port);
    if (bind(sockfd, reinterpret_cast<struct sockaddr *>(&serv_addr),
             sizeof(serv_addr)) < 0) {
        close(sockfd);
        throw std::runtime_error("bind() failed");
    }

    if (listen(sockfd, 1) < 0) {
        close(sockfd);
        throw std::runtime_error("listen() failed");
    }

    log("[TCP] Listening on " + host + ":" + std::to_string(port));

    while (true) {
        struct sockaddr_in cli_addr{};
        socklen_t cli_len = sizeof(cli_addr);
        int connfd = accept(sockfd,
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

            /* Process all complete packets */
            while (true) {
                /* Search for CRLF (0x0D 0x0A) only, not the NUL terminator */
                auto it = std::search(buf.begin(), buf.end(),
                                      std::begin("\x0D\x0A"),
                                      std::begin("\x0D\x0A") + 2);
                if (it == buf.end())
                    break;              // no full packet yet

                size_t end_idx = std::distance(buf.begin(), it);
                std::vector<uint8_t> pkt(buf.begin(), buf.begin() + end_idx + 2);
                buf.erase(buf.begin(), buf.begin() + end_idx + 2);

                if (pkt.size() < 4 || pkt.back() != 0x0A ||
                    *(pkt.rbegin() + 1) != 0x0D) {
                    log("[TCP] Ignored malformed packet");
                    continue;
                }

                uint8_t proto = pkt[3];
                std::ostringstream hex_stream;
                for (auto b : pkt) hex_stream << std::hex << std::setw(2)
                                              << std::setfill('0')
                                              << static_cast<int>(b);
                log("[RECV] pkt=" + hex_stream.str());

                /* GPS packet (proto == 34) */
                if (proto == 34) {
                    try {
                        if (pkt.size() < 20) throw std::runtime_error("short packet");

                        int32_t lat_raw = static_cast<int32_t>(
                            (pkt[11] << 24) | (pkt[12] << 16) |
                            (pkt[13] << 8)  | pkt[14]);
                        int32_t lon_raw = static_cast<int32_t>(
                            (pkt[15] << 24) | (pkt[16] << 16) |
                            (pkt[17] << 8)  | pkt[18]);

                        latest_lat  = static_cast<double>(lat_raw) / 1800000.0;
                        latest_lon  = static_cast<double>(lon_raw) / 1800000.0;
                        latest_speed = static_cast<int>(pkt[19]);

                        log("[GPS] lat=" + std::to_string(latest_lat) +
                            ", lon=" + std::to_string(latest_lon) +
                            ", speed=" + std::to_string(latest_speed) + " km/h");

                        std::ostringstream uri;
                        uri << "geo:" << std::fixed << std::setprecision(6)
                            << latest_lat << "," << latest_lon
                            << ";u=35";
                        append_uri(uri.str(), latest_speed);
                    } catch (const std::exception &e) {
                        log("[GPS] Error parsing packet: " + std::string(e.what()));
                    }
                }
                /* ACK packets (proto == 1 or 19) */
                else if (proto == 1 || proto == 19) {
                    std::vector<uint8_t> seq;
                    if (proto == 1) {
                        if (pkt.size() < 18) continue;
                        seq.insert(seq.end(), pkt.begin() + 16, pkt.begin() + 18);
                        std::vector<uint8_t> ack = ack_packet({0x01}, seq);
                        sendall(connfd, ack);
                    } else { /* proto == 19 */
                        if (pkt.size() < 9) continue;
                        seq.insert(seq.end(), pkt.begin() + 7, pkt.begin() + 9);
                        std::vector<uint8_t> ack = ack_packet({0x13}, seq);
                        sendall(connfd, ack);
                    }
                    log("[ACK] sent for proto " + std::to_string(proto));
                }
            }   // end while (process packets)
        }       // end while (connection)
        close(connfd);
    }           // end while (accept)
    close(sockfd);
}

/* ------------------- Main ------------------------------------ */
int main()
{
    try {
        tcp_server();   // default host and port
    } catch (const std::exception &e) {
        log("[ERROR] " + std::string(e.what()));
        return 1;
    }
    return 0;
}