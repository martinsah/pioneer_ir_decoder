# Pronto Hex Decoder

A Python tool to parse, analyze, and decode Pronto Hex infrared remote signals, with utilities to visualize, "meanify", and convert the timings into binary and hex representations. Suitable for IR protocol analysis, debugging, or reverse engineering remote controls.

"Pronto" hex log file should come from an ESPHOME device setup as an IR Receiver, for example here is a working esphome YAML config. This is using a small "ESP-01M" board.
```yaml
esphome:
  name: espir
  friendly_name: ESPIR1

esp8266:
  board: esp8285

# Enable logging
logger:

# Enable Home Assistant API
api:
  encryption:
    key: "xx="

ota:
  - platform: esphome
    password: "xx"

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

  # Enable fallback hotspot (captive portal) in case wifi connection fails
  ap:
    ssid: "Espir Fallback Hotspot"
    password: "xx"

captive_portal:
    
remote_receiver:
  id: rcvr
  pin:
    number: GPIO14
    inverted: true
  dump: all

remote_transmitter:
  pin: GPIO4
  carrier_duty_percent: 50%

```

        

And here is valid input data:
```text
[11:46:33.217][I][remote.pronto:229]: Received Pronto: data=
[11:46:33.229][I][remote.pronto:237]: 0000 006D 0072 0000 0077 003D 0014 0029 0014 0029 0014 000C 0014 000C 0014 000C 0014 0029 0014 000C 0014 000C 0014 0029 0014 0029 0014 000C 0014 0029 0014 000C 0014 000C 0014 0029 0014 0029 0014 000C 0014 0029 0014 0029 0014 000C 
[11:46:33.250][I][remote.pronto:237]: 0014 000C 0014 0029 0014 000C 0014 000C 0014 0029 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 0029 
[11:46:33.271][I][remote.pronto:237]: 0014 000C 0014 000C 0014 0029 0014 000C 0014 000C 0014 0029 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 0029 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 0029 0014 000C 
[11:46:33.292][I][remote.pronto:237]: 0014 0029 0014 0029 0014 0029 0014 0029 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 
[11:46:33.314][I][remote.pronto:237]: 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 000C 0014 0029 0014 000C 0014 000C 0014 000C 0014 000C 0014 0029 0014 0029 0014 000C 0014 0029 0014 0029 0014 0029 0014 0029 0014 0029 0014 0029 
[11:46:33.321][I][remote.pronto:237]: 0014 0181 
```

---

## Features

- Parse Pronto Hex logs and extract timing sequences and carrier frequency.
- Create timing histograms of signal durations.
- Reduce similar timings to canonical "meanified" values to handle noisy IR signals.
- Convert signal timings to binary and hexadecimal, highlighting differences between sequences.
- Supports start/stop bit offsets and odd/even message splitting.
- Colorized terminal output for better readability (uses `colorama`).

---

## Requirements

- Python 3.6+
- [colorama](https://pypi.org/project/colorama/)

Install dependencies:
```bash
pip install colorama
```

---

## Usage

Typically run via the command line and expects Pronto Hex logs from stdin:

```bash
python test_parse_log.py < my_pronto.log
```

### Command-Line Options

- `--start-bits N` &nbsp; Number of bits to skip at the start of binary messages (default: 0)
- `--stop-bits N` &nbsp; Number of bits to skip at the end of binary messages (default: 0)
- `--show-odd-even True|False` &nbsp; Show odd/even messages separately

Example:
```bash
python test_parse_log.py --start-bits 1 --stop-bits 1 --show-odd-even true < test_log_files/mode_change_logs_espir.txt
```

---

## Example Output

Output shows:
- Extracted hex numbers and statistics
- Decoded timing sequences per message
- Timing histograms and meanified values
- Binary messages, visually highlighting differences between subsequent messages
- Hex byte output with computed checksums for each message

```
Message 0:   1 0 1 0 1 0 ...  Length: 32
...
[0] 8C 12 03 ...  Checksum: AB [1] 8D 12 03 ...  Checksum: AC
```

---

## File Overview

- `decode_pronto_hex.py` – Core parsing, decoding, and conversion utilities
- `test_parse_log.py` – Command-line utility to apply the decoder to Pronto logs (demonstration and example use)

---

## License

MIT License

---

## Acknowledgements

This tool leverages [Colorama](https://pypi.org/project/colorama/) for colored terminal output. Pronto Hex format specification is well documented by various IR hobbyist communities.
