use std::fs::{OpenOptions, File};
use std::io::{BufWriter, Write, Read};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};

/// Simple UTC timestamp formatter – no external crates.
fn now_timestamp() -> String {
    let now = SystemTime::now();
    let duration = now.duration_since(UNIX_EPOCH).unwrap();
    let secs = duration.as_secs();

    let days = secs / 86_400;
    let remaining = secs % 86_400;
    let hour = remaining / 3_600;
    let minute = (remaining % 3_600) / 60;
    let second = remaining % 60;

    // Convert days since 1970‑01‑01 to year‑month‑day.
    let mut year: i32 = 1970;
    let mut d = days;
    loop {
        let days_in_year = if is_leap(year) { 366 } else { 365 };
        if d < days_in_year as u64 {
            break;
        }
        d -= days_in_year as u64;
        year += 1;
    }

    let mut month: u32 = 1;
    loop {
        let dim = month_len(year, month);
        if d < dim as u64 {
            break;
        }
        d -= dim as u64;
        month += 1;
    }

    let day = d + 1;

    format!(
        "{:04}-{:02}-{:02} {:02}:{:02}:{:02}",
        year, month, day, hour, minute, second
    )
}

fn is_leap(year: i32) -> bool {
    (year % 4 == 0) && (year % 100 != 0 || year % 400 == 0)
}

fn month_len(year: i32, month: u32) -> u32 {
    match month {
        1 => 31,
        2 => if is_leap(year) { 29 } else { 28 },
        3 => 31,
        4 => 30,
        5 => 31,
        6 => 30,
        7 => 31,
        8 => 31,
        9 => 30,
        10 => 31,
        11 => 30,
        12 => 31,
        _ => 0,
    }
}

/// Handles logging of plain text and HTML.
struct Logger {
    log: BufWriter<File>,
    html: BufWriter<File>,
}

impl Logger {
    fn new(log_path: &str, html_path: &str) -> std::io::Result<Self> {
        let log_file = OpenOptions::new().append(true).create(true).open(log_path)?;
        let html_file = OpenOptions::new().append(true).create(true).open(html_path)?;
        Ok(Self {
            log: BufWriter::new(log_file),
            html: BufWriter::new(html_file),
        })
    }

    fn log(&mut self, msg: &str) {
        let ts = now_timestamp();
        let line = format!("{}  {}\n", ts, msg);
        let _ = self.log.write_all(line.as_bytes());
        let _ = self.log.flush();
        print!("{}", line);
    }

    fn append_uri(&mut self, uri: &str, speed: u8) {
        let ts = now_timestamp();
        let l1 = format!("<p><a href=\"{}\">{}</a> Open map</p>\n", uri, ts);
        let l2 = format!("<p>Speed: {} km/h</p>\n", speed);
        let _ = self.html.write_all(l1.as_bytes());
        let _ = self.html.write_all(l2.as_bytes());
        let _ = self.html.flush();
    }
}

/// CRC‑16/XMODEM.
fn crc16_xmodem(data: &[u8]) -> u16 {
    let mut crc: u16 = 0;
    for &b in data {
        crc ^= (b as u16) << 8;
        for _ in 0..8 {
            if (crc & 0x8000) != 0 {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc <<= 1;
            }
        }
    }
    crc & 0xFFFF
}

/// Build ACK packet.
fn ack_packet(ack_prot: &[u8; 1], seq: &[u8; 2]) -> Vec<u8> {
    let mut buf = Vec::with_capacity(11);
    buf.extend_from_slice(&[0x78, 0x78, 0x05]);
    buf.extend_from_slice(ack_prot);
    buf.extend_from_slice(seq);
    let crc = crc16_xmodem(&buf[3..]); // over ack_prot + seq
    buf.extend_from_slice(&crc.to_be_bytes());
    buf.extend_from_slice(&[0x0d, 0x0a]); // CRLF
    buf
}

/// Handle one TCP connection.
fn handle_connection(mut stream: TcpStream, logger: Arc<Mutex<Logger>>) {
    let mut buf = Vec::new();
    loop {
        let mut tmp = [0u8; 1024];
        match stream.read(&mut tmp) {
            Ok(0) => {
                logger.lock().unwrap().log("[TCP] Connection closed by peer");
                break;
            }
            Ok(n) => {
                buf.extend_from_slice(&tmp[..n]);
                loop {
                    if let Some(pos) = buf.windows(2).position(|w| w == [0x0d, 0x0a]) {
                        let end = pos + 2;
                        let pkt = buf.drain(..end).collect::<Vec<u8>>();
                        if pkt.len() < 4 || pkt[pkt.len() - 2..] != [0x0d, 0x0a] {
                            logger
                                .lock()
                                .unwrap()
                                .log("[TCP] Ignored malformed packet");
                            continue;
                        }
                        let proto = pkt[3];
                        logger
                            .lock()
                            .unwrap()
                            .log(&format!("[RECV] pkt={:02x?}", pkt));
                        match proto {
                            34 => {
                                if pkt.len() < 20 {
                                    logger
                                        .lock()
                                        .unwrap()
                                        .log("[GPS] Packet too short");
                                    continue;
                                }
                                let lat = i32::from_be_bytes([
                                    pkt[11], pkt[12], pkt[13], pkt[14],
                                ]) as f64
                                    / 1_800_000.0;
                                let lon = i32::from_be_bytes([
                                    pkt[15], pkt[16], pkt[17], pkt[18],
                                ]) as f64
                                    / 1_800_000.0;
                                let speed = if pkt.len() > 19 { pkt[19] } else { 0 };
                                logger.lock().unwrap().log(&format!(
                                    "[GPS] lat={:.6}, lon={:.6}, speed={} km/h",
                                    lat, lon, speed
                                ));
                                let uri = format!("geo:{:.6},{:.6};u=35", lat, lon);
                                logger.lock().unwrap().append_uri(&uri, speed);
                            }
                            1 | 19 => {
                                let seq = if proto == 1 {
                                    if pkt.len() < 18 {
                                        logger
                                            .lock()
                                            .unwrap()
                                            .log("[ACK] Packet too short for seq");
                                        continue;
                                    }
                                    [pkt[16], pkt[17]]
                                } else {
                                    if pkt.len() < 9 {
                                        logger
                                            .lock()
                                            .unwrap()
                                            .log("[ACK] Packet too short for seq");
                                        continue;
                                    }
                                    [pkt[7], pkt[8]]
                                };
                                let ack_prot = if proto == 1 { [0x01] } else { [0x13] };
                                let ack = ack_packet(&ack_prot, &seq);
                                let _ = stream.write_all(&ack);
                                logger
                                    .lock()
                                    .unwrap()
                                    .log(&format!("[ACK] sent for proto {:02x}", proto));
                            }
                            _ => logger
                                .lock()
                                .unwrap()
                                .log(&format!("[TCP] Unknown proto {:02x}", proto)),
                        }
                    } else {
                        break;
                    }
                }
            }
            Err(e) => {
                logger
                    .lock()
                    .unwrap()
                    .log(&format!("[TCP] Read error: {}", e));
                break;
            }
        }
    }
}

/// TCP listener.
fn tcp_server(host: &str, port: u16, logger: Arc<Mutex<Logger>>) {
    let addr = format!("{}:{}", host, port);
    let listener = TcpListener::bind(&addr).expect("Failed to bind address");
    logger
        .lock()
        .unwrap()
        .log(&format!("[TCP] Listening on {}", addr));
    for stream in listener.incoming() {
        match stream {
            Ok(s) => {
                let peer = s.peer_addr().unwrap_or_else(|_| "unknown".parse().unwrap());
                logger
                    .lock()
                    .unwrap()
                    .log(&format!("[TCP] Connected by {}", peer));
                let log_clone = Arc::clone(&logger);
                thread::spawn(move || handle_connection(s, log_clone));
            }
            Err(e) => logger
                .lock()
                .unwrap()
                .log(&format!("[TCP] Connection failed: {}", e)),
        }
    }
}

fn main() {
    let logger = Arc::new(Mutex::new(
        Logger::new("log.txt", "log.html").expect("Could not open log files"),
    ));
    tcp_server("0.0.0.0", 9016, logger);
}