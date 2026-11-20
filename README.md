# CrossPoint Nightly `.bin` Installer (Xteink X3)

A lightweight Python installer that fetches the latest CrossPoint nightly `.bin` firmware for the **Xteink X3** (and X4) from [`brendanlefebvre/crossink-nightlies`](https://github.com/brendanlefebvre/crossink-nightlies/releases) and optionally flashes it over USB using `esptool`.

## Usage

List recent Xteink X3 nightly releases:
```bash
python3 install_x3_nightly.py --list
```

Download the latest nightly `.bin` file:
```bash
python3 install_x3_nightly.py --download-only
```

Download and flash directly to your connected Xteink X3 (requires `esptool`):
```bash
pip install esptool
python3 install_x3_nightly.py --flash --port /dev/ttyACM0
```

You can also flash the downloaded `.bin` file using the web installer at https://crosspointreader.com/install (or https://crosspointreader.com/debug for advanced flash controls).
