# Wi-PWN Agent Guide

## Project overview

Wi-PWN is an ESP8266 firmware that performs deauthentication attacks via a web UI. Three subsystems: Arduino firmware (`arduino/`), Jekyll web UI (`web_server/`), Android WebView wrapper (`android_app/`).

## Critical constraints (violation = broken build)

- **ESP8266 SDK MUST be version 2.0.0** – newer versions remove the `wifi_send_pkt_freedom()` API that deauth packets depend on
- **SDK patching required** before building: add `wifi_send_pkt_freedom` / `wifi_register_send_pkt_freedom_cb` / `wifi_unregister_send_pkt_freedom_cb` to `user_interface.h`, and replace `ESP8266WiFi.cpp`/`.h` with files from `arduino/sdk_fix/`
- **License: CC BY-NC 4.0** – no commercial use, must retain attribution
- **Only master branch exists**, single remote (`origin`)

## Firmware (`arduino/Wi-PWN/`)

### Entrypoint
`Wi-PWN.ino` — Arduino sketch. `setup()` initializes EEPROM, SPIFFS, WiFi AP, web server routes, display (optional). `loop()` handles HTTP, attack engine, deauth detector, serial commands, GPIO button.

### Architecture
- **No PlatformIO / CMake** – Arduino IDE only (`.ino` + `.cpp`/`.h`)
- **Build command** (CI): `arduino --verify --board esp8266:esp8266:nodemcuv2:CpuFrequency=80,FlashSize=4M3M arduino/Wi-PWN/Wi-PWN.ino`
- **Flash settings**: 80MHz CPU, 4M (1M SPIFFS) flash size
- **Serial baud**: 115200

### Key modules
| File | Purpose |
|---|---|
| `Attack.h/.cpp` | Packet generation: deauth, beacon, probe-request frames; 3 attack slots |
| `APScan.h/.cpp` | WiFi AP scanning, selection, results |
| `ClientScan.h/.cpp` | Client (station) discovery via promiscuous mode |
| `Settings.h/.cpp` | EEPROM-backed configuration (manual address mapping, see `#define` blocks in Settings.h) |
| `SSIDList.h/.cpp` | Beacon SSID list management |
| `Mac.h/.cpp` | MAC address abstraction (6-byte array) |
| `MacList.h/.cpp` | List of MAC addresses used by attack engine |
| `NameList.h/.cpp` | User-defined device names |
| `data.h` | Gzip-compressed PROGMEM byte arrays for all web assets – **auto-generated, do not edit by hand** |

### Compile-time flags (`#define`)
- `USE_DISPLAY` – OLED support (SSD1306/SH1106 via I2C)
- `GPIO0_DEAUTH_BUTTON` – Flash button as deauth toggle (long-press = deauth all, short-press = toggle)
- `USE_LED16` – Pocket ESP8266 LED on GPIO16
- `USE_CAPTIVE_PORTAL` – Evil Twin mode with DNS captive portal (patched DNSServer)
- `debug` (`const bool debug = true`) – enables serial debug output
- `resetPin` (GPIO4) – pull low at boot to reset settings

### Settings storage
EEPROM address mapping in `Settings.h` (`ssidLenAdr 1024` through `checkNumAdr 3000`). Settings are manually read/written byte-by-byte — no library. `checkNum` at address 3000 validates EEPROM sanity.

### Attack types
| # | Name | Description |
|---|---|---|
| 0 | Deauth | Disconnect clients from AP |
| 1 | Beacon | Beacon flood with cloned/random SSIDs |
| 2 | Probe-Request | Probe request flood |

### Deauth detector
Integrated from DeauthDetector project. Sniffs for deauth/disassoc frames (0xA0, 0xC0) and sets an alert pin high/low. Configurable channel hopping, scan interval.

## Web UI (`web_server/html/`)

### Development workflow
- **Jekyll-based** static site with multi-language support
- **Serve locally**: `cd web_server/html && jekyll serve` → `http://127.0.0.1:1337`
- **Dependencies**: Ruby + Gem, then `bundler install` in `web_server/html/`
- **Plugins**: `jekyll-tidy`, `jekyll-multiple-languages-plugin`
- **Build output**: `web_server/output/html/`

### Translation
- Files in `web_server/html/_i18n/*.yml`
- 14 languages: chinese, english, german, russian, italian, dutch, portuguese, slovak, polish, estonian, hebrew, czech, turkish, indonesia
- **Default language** = first in list. Currently set to `chinese` via `_config.yml`

### Important: web asset pipeline
HTML/CSS/JS source files are in `web_server/html/` (Jekyll source). After editing, they must be minified and converted to gzip-compressed PROGMEM byte arrays that go into `arduino/Wi-PWN/data.h`. The conversion tool is `web_server/auto_generate.exe` (Windows only). **Never edit `data.h` directly** — edit Jekyll source, then run the conversion pipeline.

### Android app
`android_app/` is a standard Gradle project. It is a WebView wrapper around the ESP8266's web UI at `http://192.168.4.1/scan.html?minimal=true`. The `?minimal=true` param hides nav/footer and replaces them with native controls.

## Testing
- **No unit tests** in the repo
- **CI (legacy)**: `.travis.yml` — Travis CI, verifies compilation only
- **CI (current)**: `.github/workflows/build.yml` — GitHub Actions, applies SDK patches, compiles, uploads `.bin` artifact
- **Manual testing**: Flash to ESP8266 hardware, connect to `Wi-PWN` AP, open `http://192.168.4.1`
- **Debug**: Serial console at 115200 baud

## Common pitfalls
1. Forgetting that web assets in `data.h` are gzip PROGMEM — editing HTML in Jekyll source won't reflect until conversion pipeline runs
2. Using wrong ESP8266 SDK version (must be 2.0.0)
3. Skipping SDK patch (`user_interface.h` + `ESP8266WiFi` replacement) → deauth packets won't send (0 pkts/s)
4. EEPROM address overlap when adding new settings — all addresses are manually assigned in `Settings.h`
5. The `.ino.nodemcu.bin` in the firmware directory is a pre-compiled binary, not source
