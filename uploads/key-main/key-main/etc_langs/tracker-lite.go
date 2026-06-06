package main

import (
    "bufio"
    "encoding/binary"
    "fmt"
    "net"
    "os"
    "time"
)

var (
    logFile  *os.File
    htmlFile *os.File
)

var (
    latestLat   float64
    latestLon   float64
    latestSpeed int
)

func logMsg(msg string) {
    ts := time.Now().Format("2006-01-02 15:04:05")
    line := fmt.Sprintf("%s  %s\n", ts, msg)

    if logFile != nil {
        _, _ = logFile.WriteString(line)
        _ = logFile.Sync()
    }
    fmt.Print(line)
}

func appendURI(uri string, speed int) {
    ts := time.Now().Format("2006-01-02 15:04:05")
    if htmlFile != nil {
        fmt.Fprintf(htmlFile, `<p><a href="%s">%s Open map</a></p>`+"\n", uri, ts)
        fmt.Fprintf(htmlFile, `<p>Speed: %d km/h</p>`+"\n", speed)
        _ = htmlFile.Sync()
    }
}

func crc16XModem(data []byte) uint16 {
    var crc uint16 = 0
    for _, b := range data {
        crc ^= uint16(b) << 8
        for i := 0; i < 8; i++ {
            if crc&0x8000 != 0 {
                crc = (crc << 1) ^ 0x1021
            } else {
                crc <<= 1
            }
        }
    }
    return crc & 0xFFFF
}

func ackPacket(ackProt, seq []byte) []byte {
    crc := crc16XModem(append(ackProt, seq...))
    res := []byte{0x78, 0x78, 0x05}
    res = append(res, ackProt...)
    res = append(res, seq...)
    res = append(res, byte(crc>>8), byte(crc&0xFF))
    res = append(res, 0x0d, 0x0a)
    return res
}

func tcpServer(host string, port int) {
    var err error
    logFile, err = os.OpenFile("log.txt", os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Println("Error opening log.txt:", err)
        return
    }
    defer logFile.Close()

    htmlFile, err = os.OpenFile("log.html", os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Println("Error opening log.html:", err)
        return
    }
    defer htmlFile.Close()

    addr := fmt.Sprintf("%s:%d", host, port)
    listener, err := net.Listen("tcp", addr)
    if err != nil {
        logMsg(fmt.Sprintf("[TCP] Listen error: %v", err))
        return
    }
    defer listener.Close()
    logMsg(fmt.Sprintf("[TCP] Listening on %s", addr))

    for {
        conn, err := listener.Accept()
        if err != nil {
            logMsg("[TCP] Accept error:" + err.Error())
            continue
        }
        logMsg(fmt.Sprintf("[TCP] Connected by %v", conn.RemoteAddr()))
        go handleConn(conn)
    }
}

func handleConn(conn net.Conn) {
    defer func() {
        _ = conn.Close()
        logMsg("[TCP] Connection closed by peer")
    }()

    reader := bufio.NewReader(conn)
    buf := make([]byte, 0)

    for {
        tmp := make([]byte, 1024)
        n, err := reader.Read(tmp)
        if err != nil {
            logMsg("[TCP] Read error:" + err.Error())
            return
        }
        if n == 0 {
            return
        }
        buf = append(buf, tmp[:n]...)

        for {
            idx := indexOfCRLF(buf)
            if idx < 0 {
                break
            }
            pkt := buf[:idx+2]
            buf = buf[idx+2:]

            if len(pkt) < 4 || !isCRLF(pkt) {
                logMsg("[TCP] Ignored malformed packet")
                continue
            }
            proto := pkt[3]
            logMsg(fmt.Sprintf("[RECV] pkt=%x", pkt))

            switch proto {
            case 34:
                handleGPS(pkt)
            case 1, 19:
                handleAck(pkt, conn, proto)
            }
        }
    }
}

func handleGPS(pkt []byte) {
    if len(pkt) < 20 {
        logMsg("[GPS] Packet too short")
        return
    }
    latRaw := binary.BigEndian.Uint32(pkt[11:15])
    lonRaw := binary.BigEndian.Uint32(pkt[15:19])
    speed := int(pkt[19])

    lat := float64(int32(latRaw)) / 1_800_000.0
    lon := float64(int32(lonRaw)) / 1_800_000.0

    latestLat, latestLon, latestSpeed = lat, lon, speed
    logMsg(fmt.Sprintf("[GPS] lat=%.6f, lon=%.6f, speed=%d km/h", lat, lon, speed))

    uri := fmt.Sprintf("geo:%.6f,%.6f;u=35", lat, lon)
    appendURI(uri, speed)
}

func handleAck(pkt []byte, conn net.Conn, proto byte) {
    var seq []byte
    if proto == 1 {
        seq = pkt[16:18]
    } else {
        seq = pkt[7:9]
    }
    ackProt := []byte{0x01}
    if proto == 19 {
        ackProt = []byte{0x13}
    }
    ack := ackPacket(ackProt, seq)
    _, err := conn.Write(ack)
    if err != nil {
        logMsg("[ACK] Send error:" + err.Error())
        return
    }
    logMsg(fmt.Sprintf("[ACK] sent for proto 0x%02x", proto))
}

func indexOfCRLF(b []byte) int {
    for i := 0; i < len(b)-1; i++ {
        if b[i] == 0x0d && b[i+1] == 0x0a {
            return i
        }
    }
    return -1
}

func isCRLF(b []byte) bool {
    return len(b) >= 2 && b[len(b)-2] == 0x0d && b[len(b)-1] == 0x0a
}

func main() {
    tcpServer("0.0.0.0", 9016)
}