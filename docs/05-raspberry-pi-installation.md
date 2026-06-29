# 5. Installing a software probe on Raspberry Pi

Procedure verified against the official `RIPE-NCC/ripe-atlas-software-probe` repository (release 5120, Oct 2025). Also tested elsewhere on a Raspberry Pi 5 with Raspberry Pi OS Lite 64-bit (source at the bottom); the Pi 3B follows the same procedure.

## Hardware

- Raspberry Pi 3B or newer
- micro SD card
- Ethernet cable
- a PC with an SD card reader (or USB adapter)

## Software probe hardware requirements

The RIPE Atlas measurement software is **very lightweight**. For scale: the old hardware probes ran on 32 MB of RAM (v3), and the current v4 probes on 512 MB. A Pi 3B (1 GB RAM, quad-core CPU) is therefore **vastly oversized** for this role.

## Step 0 - Pick the right OS

In **Raspberry Pi Imager**:
- OS: **Raspberry Pi OS Lite (64-bit)** - no need for a desktop on a headless device.
- The official package for the Pi is **arm64**: you therefore absolutely need the **64-bit** version of the OS. The Pi 3B supports 64-bit.

## Step 1 - Pre-configure before flashing

In Raspberry Pi Imager, before "Write", click the gear ("Edit Settings") and set:
- **hostname** (e.g. `ripe-probe-uc3m`)
- **username + password** (avoid default credentials)
- **enable SSH** (password authentication to start)
- don't configure Wi-Fi (we use Ethernet)

This lets you control the Pi **without a screen or keyboard**.

## Step 2 - Flash and boot

1. "Write" → the OS is written to the card (a few minutes).
2. Card into the Pi.
3. Ethernet cable plugged.
4. Power → the Pi boots.

## Step 3 - Connect to the Pi over SSH

From the PC (PowerShell, or WSL):

```bash
ssh your_user@ripe-probe-uc3m.local
```

(`.local` works on the local network; otherwise, use the Pi's IP address.) The password requested is the one set in step 1.

## Step 4 - Install the probe package (official)

Once connected over SSH on the Pi, update then install. Official commands for **Raspberry Pi OS 12/13**:

```bash
# Preliminary update
sudo apt update && sudo apt upgrade -y

# Download the repo package + verify the checksum
ARCH=$(dpkg --print-architecture)
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
REPO_PKG=ripe-atlas-repo_1.5-5_all.deb
wget https://ftp.ripe.net/ripe/atlas/software-probe/debian/dists/"$CODENAME"/main/binary-"$ARCH"/"$REPO_PKG" \
     https://github.com/RIPE-NCC/ripe-atlas-software-probe/releases/latest/download/CHECKSUMS
grep -q "$(sha256sum "$REPO_PKG")" CHECKSUMS && echo "Success: checksum matches" \
  || ( printf "\n\033[1;31mError: checksum does not match\033[0m\n\n"; rm "$REPO_PKG" )

# Install
sudo dpkg -i "$REPO_PKG" && rm "$REPO_PKG"
sudo apt update
sudo apt-get install ripe-atlas-probe
```

> The repo package version number (`1.5-5`) may change: always check the up-to-date command on the official README (link at the bottom).

## Step 5 - Retrieve the public key

On installation, a key pair is generated. The **public** key is in:

```bash
sudo cat /etc/ripe-atlas/probe_key.pub
```

> **Never share or distribute the _private_ key** (`/etc/ripe-atlas/probe_key`). Only the **public** key is used for registration.

## Step 6 - Register the probe

1. Go to <https://atlas.ripe.net/apply/swprobe/> (signed in to your RIPE NCC Access account).
2. Paste the contents of `probe_key.pub` into the field provided.
3. The "AS Number" and "Notes" fields can be left blank (the AS is filled automatically from the public IP).
4. The probe appears on the dashboard with a **pending** status.

## Step 7 - Check the connection

On <https://atlas.ripe.net/probes/mine>, the status column should turn to **Connected** (green cloud icon). Going from pending to connected can take a few minutes.

## Useful technical notes

- **Internal ports**: the software uses TCP ports **2023** and **8080**. In case of a conflict with another service, you can change them via `/etc/ripe-atlas/config.txt`.
- **Updates**: since release 5080, the package no longer updates automatically. To update: `sudo apt update && sudo apt upgrade`. (You can enable `unattended-upgrades` to automate it.)
- **Backup**: before any major update, back up `/etc/ripe-atlas/probe_key` and the config.

## How long to leave it running?

To earn credits and provide useful data, the probe must stay **connected continuously** (credits accumulate per minute of connection). For our topic, it must at least be active **before, during and after** each observed match, but ideally it's left plugged in permanently (power and bandwidth usage are negligible).

## Sources

- *Official README* (install commands, ports, updates) - <https://github.com/RIPE-NCC/ripe-atlas-software-probe>
- *Setting up a RIPE Atlas software probe*, L. Rodriguez (procedure tested on Pi 5, key/tunnel details) - <https://www.lucasrodriguez.net/posts/ripe-atlas-software-probe-setup/>
- *Software probes* (official docs) - <https://atlas.ripe.net/docs/howtos/software-probes/>
- v3/v4 probe specs (RAM order of magnitude) - <https://atlas.ripe.net/docs/probeinfo/probe-v4/>
