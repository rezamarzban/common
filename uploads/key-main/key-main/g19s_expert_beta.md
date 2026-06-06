
# Wanway G19S GPS Tracker – Complete Protocol & Configuration Guide

This document consolidates all information about the Wanway G19S GPS tracker, including:
- TCP protocol structure (Login, Heartbeat, GPS, Alarms, Commands)
- Coordinate decoding and CRC calculation
- SMS configuration commands and troubleshooting
- Traccar compatibility and setup

---

## 1. TCP Protocol Overview

### 1.1 General Packet Format
```
[START] [LEN] [PROTO] [DATA] [CRC] [END]
 78 78    XX     YY      ...    ZZZZ  0D 0A
```

| Field   | Bytes | Description |
|---------|-------|-------------|
| START   | 2     | Fixed `0x78 0x78` |
| LEN     | 1     | Length of PROTO + DATA + CRC (excludes START and END) |
| PROTO   | 1     | Protocol type (`0x01`, `0x13`, `0x22`, `0x26`, `0x27`, `0x80`) |
| DATA    | var   | Payload – structure depends on PROTO |
| CRC     | 2     | CRC16‑XMODEM (polynomial `0x1021`, initial `0x0000`), big‑endian |
| END     | 2     | Fixed `0x0D 0x0A` |

### 1.2 Protocol Types and ACK Responses

| Proto | Type                | ACK Response Format                     | Sequence Bytes Location |
|-------|---------------------|-----------------------------------------|-------------------------|
| `0x01`| Login               | `78 78 05 01 00 SS SS CC CC 0D 0A`      | `pkt[16:18]` (offset from packet start) |
| `0x13`| Heartbeat           | `78 78 05 13 00 SS SS CC CC 0D 0A`      | `pkt[7:9]` |
| `0x22`| GPS Location Data   | ACK required (sequence location varies) | **Not explicitly defined** – check live traffic |
| `0x26`| Alarm Data (Status) | ACK required                            | Typically first two bytes of DATA |
| `0x27`| Alarm Data (Ext.)   | ACK required                            | Typically first two bytes of DATA |
| `0x80`| Command Response    | No ACK needed (it is a response)        | N/A |

**ACK Packet Structure (Universal):**
```
78 78 06 [PROTO] 00 [SEQ_H SEQ_L] [CRC_H CRC_L] 0D 0A
```
*(Note: Document example shows LEN=0x05, but mathematically it should be 0x06. Verify with actual device.)*

---

## 2. Detailed Packet Structures

### 2.1 Login Packet (`0x01`)
```
78 78 0D 01 [IMEI 8 bytes] [INFO...] [SEQ 2 bytes] [CRC 2 bytes] 0D 0A
```
- **LEN:** `0x0D` = 13 (PROTO 1 + DATA 10 + CRC 2)
- **Sequence:** Bytes 16‑17 (from first `78`). Extract and return in ACK.

### 2.2 Heartbeat Packet (`0x13`)
```
78 78 0A 13 [SEQ 2 bytes] [STATUS...] [CRC 2 bytes] 0D 0A
```
- **LEN:** `0x0A` = 10
- **Sequence:** Bytes 7‑8. Extract and return in ACK.

### 2.3 GPS Location Data Packet (`0x22`)
| Offset | Bytes | Field                | Description |
|--------|-------|----------------------|-------------|
| 0‑1    | 2     | START                | `78 78` |
| 2      | 1     | LEN                  | `0x26` = 38 |
| 3      | 1     | PROTO                | `0x22` |
| 4‑9    | 6     | Date / Time          | YY MM DD HH MM SS (each 1 byte) |
| 10     | 1     | GPS Info             | Bits: satellite count, fix status |
| 11‑14  | 4     | **Latitude**         | Signed 32‑bit, big‑endian |
| 15‑18  | 4     | **Longitude**        | Signed 32‑bit, big‑endian |
| 19     | 1     | **Speed**            | km/h, unsigned 8‑bit |
| 20‑…   | var   | Other status         | Heading, altitude, mileage, I/O, etc. |
| last‑4 | 2     | CRC16                | Over PROTO + DATA |
| last‑2 | 2     | END                  | `0D 0A` |

**Coordinate Decoding:**
```python
lat_raw = int.from_bytes(pkt[11:15], 'big', signed=True)
lon_raw = int.from_bytes(pkt[15:19], 'big', signed=True)

latitude  = lat_raw / 1_800_000.0   # degrees
longitude = lon_raw / 1_800_000.0
```

**Speed:**
```python
speed_kmh = pkt[19]   # 0–255 km/h
```

### 2.4 Alarm Packets (`0x26` and `0x27`)
| Protocol | Typical Alarms                           |
|----------|------------------------------------------|
| `0x26`   | SOS, Vibration, Geo‑fence In/Out         |
| `0x27`   | Power Cut, Over‑speed, Moving            |

**Alarm Codes (Byte 4 of DATA):**
| Code | Meaning               | Packet Type |
|------|-----------------------|-------------|
| 0    | Normal                | `0x22`      |
| 1    | SOS Alarm             | `0x26`      |
| 2    | Power Cut Alarm       | `0x27`      |
| 3    | Vibration Alarm       | `0x26`      |
| 4    | Geo‑fence In Alarm    | `0x26`      |
| 5    | Geo‑fence Out Alarm   | `0x26`      |
| 6    | Over‑speed Alarm      | `0x27`      |
| 9    | Moving Alarm          | `0x27`      |

### 2.5 Command Packet (`0x80`) – Server to Device
```
78 78 [LEN] 80 [COMMAND_BYTE] [COMMAND_DATA] [CRC] 0D 0A
```
**Common Commands:**
- Set Update Interval: `[IP],[PORT],[ACC_ON_INTERVAL],[ACC_OFF_INTERVAL]`
- Set APN: `APN[APN_NAME],[USER],[PASSWORD]`
- Restart Device: `RESET`
- Remote Engine Cut: `RELAY,1` (cut) / `RELAY,0` (restore)

### 2.6 Command Response (`0x80`) – Device to Server
```
78 78 [LEN] 80 [RESPONSE_DATA] [CRC] 0D 0A
```
The device acknowledges commands with this packet.

---

## 3. CRC16‑XMODEM Implementation

```python
def crc16_xmodem(data: bytes) -> int:
    crc = 0x0000
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc
```

**Usage for ACK packet:**
```python
ack_data = bytes([proto, 0x00, seq_high, seq_low])
crc = crc16_xmodem(ack_data)
ack_packet = b'\x78\x78\x06' + ack_data + crc.to_bytes(2, 'big') + b'\x0d\x0a'
```

---

## 4. SMS Configuration Commands

### 4.1 Unlock Commands (if device is vendor‑locked)
```
LOCKIP,WWDSS20,UNLOCK#
LOCKAPN,WWDSS20,UNLOCK#
FACTORY#
```
*If these fail, the device is hard‑locked and requires seller assistance.*

### 4.2 Set APN (Access Point Name)
```
APN,<APN_NAME>,<USER>,<PASSWORD>#
```
Example (no user/password):
```
APN,internet,,#
```

### 4.3 Set Server IP / Port
```
SERVER,<Mode>,<IP_or_Domain>,<Port>,<Protocol>#
```
- Mode: `0` = IP address, `1` = domain name
- Protocol: `0` = TCP, `1` = UDP

Example (TCP with domain):
```
SERVER,1,my-tracker-server.com,5023,0#
```

### 4.4 Set GPRS Mode
```
GPRSON,1#      # Enable GPRS (TCP preferred)
GPRSON,0#      # Disable GPRS
```
Alternative syntax:
```
GPRS,1#        # TCP
GPRS,0#        # UDP
```

### 4.5 Other Useful SMS Commands
| Command               | Description                          |
|-----------------------|--------------------------------------|
| `STATUS#`             | Returns device status (GPS, GSM, power) |
| `VERSION#`            | Returns firmware version             |
| `WHERE#`              | Returns current location             |
| `RESET#`              | Reboots the device                   |
| `GMT,E,8,0#`          | Set time zone (e.g., GMT+8)          |

---

## 5. Troubleshooting SMS Non‑Responsiveness

### 5.1 Basic Checks
- **SIM Card:** Active, with credit, and able to send/receive SMS (test in a phone).
- **Power Supply:** Stable 9‑90V DC, both constant and ACC wires connected.
- **GSM Signal:** Ensure the device is in an area with adequate 2G/GSM coverage.
- **SMS Format:** Commands must end with `#` and have no extra spaces.

### 5.2 Device Locked to Another Server
- Symptoms: Replies to `STATUS#` but rejects `SERVER` or `APN` commands with `ERROR: The domain name or IP is locked...`.
- Solution: Send unlock commands listed above. If unsuccessful, contact seller.

### 5.3 Server Commands vs SMS Commands
- **SMS commands** use the cellular text channel – device's phone number.
- **Server commands** use the GPRS data channel – device must be connected to internet.
- A device may stop responding to SMS but still accept server commands if GPRS is active.

### 5.4 Advanced Recovery
- **Full Power Cycle:** Disconnect main power **and** internal backup battery for 5 minutes.
- **Factory Reset:** Try `FACTORY#` (may also require unlock codes).

---

## 6. Traccar Compatibility

### 6.1 Supported Versions
The Wanway G19S uses the **GT06 protocol**, supported since **Traccar 3.1 (2015)**. All later versions (3.x, 4.x, 5.x, 6.x) work flawlessly. **Recommend using the latest stable release (6.x).**

### 6.2 Traccar Configuration (`traccar.xml`)
```xml
<entry key='gt06.port'>5023</entry>
```
Restart Traccar after editing. Ensure firewall forwards **TCP port 5023** to the Traccar server.

### 6.3 Device Configuration for Traccar
Send SMS:
```
SERVER,1,<your-server-domain.com>,5023,0#
```
- Replace `<your-server-domain.com>` with your Traccar server's public IP or domain.
- `5023` must match the `gt06.port` value.
- `0` = TCP mode.

---

## 7. Implementation Checklist

1. **Initial Setup (SMS):**
   - Unlock device (if needed).
   - Set APN.
   - Set server IP/port.
   - Set GPRS mode to TCP.
   - Set time zone (optional).
   - Reboot.

2. **Server Side:**
   - Open TCP port (e.g., 5023).
   - Implement packet parser with START/END detection.
   - Validate CRC16.
   - Handle protocol types `0x01`, `0x13`, `0x22`, `0x26`, `0x27`.
   - Extract sequence and send ACK immediately.
   - Optionally send commands via `0x80`.

3. **Testing:**
   - Monitor logs for incoming connections.
   - Verify latitude/longitude conversion.
   - Trigger alarms (e.g., SOS button) to confirm alarm decoding.

---

## 8. References & Online Resources

- [Wanway G19S User Manual (Manualslib)](https://www.manualslib.com/manual/2030089/Wanway-Tech-G19s.html)
- [Wanway Tech S20 GitHub (Unlock Info)](https://github.com/bohdan-s/WanWay-Tech-S20)
- [GPS‑Trace Configuration Guide](https://gps-trace.com/en/devices/wanway-g18)
- [Traccar Forum – Wanway G19 Thread](https://www.traccar.org/forums/topic/wanway-g19/)
- [Wanway Official Website](http://www.wanwaytech.net)

---

*Document compiled from community knowledge, technical analysis, and manufacturer documentation. Always verify critical parameters with actual device traffic.*