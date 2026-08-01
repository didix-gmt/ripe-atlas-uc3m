---
layout: default
title: Installing a software probe on Raspberry Pi
nav_order: 6
---

# 5. Installing a software probe on Raspberry Pi

Procedure verified against the official `RIPE-NCC/ripe-atlas-software-probe` GitHub repository (latest release: 5120, Oct 2025). The Pi 3B follows the same procedure as newer models.

## Hardware

- Raspberry Pi 3B (or newer)
- micro SD card
- Ethernet cable
- a PC with an SD card reader (or USB adapter)

## Software probe hardware requirements

The RIPE Atlas measurement software is very lightweight. For scale: the older hardware probes (v3) ran on 32 MB of RAM, and the current hardware probes (v4) run on 512 MB. A Pi 3B (1 GB RAM, quad-core CPU) is therefore far more powerful than what the official hardware itself requires.

## Step 0 - Pick the right OS

In **Raspberry Pi Imager**, the option you want is **not** the one shown at the top of the list. The top entry ("Raspberry Pi OS (64-bit)") is the full desktop version - heavier and unnecessary for a headless device.

The Lite version is hidden one level deeper: click **"Raspberry Pi OS (other)"**, then select **"Raspberry Pi OS Lite (64-bit)"**.

## Step 1 - Pre-configure before flashing

In Raspberry Pi Imager, before "Write", click the gear ("Edit Settings") and set:
- **hostname** (e.g. `ripe-probe-uc3m`)
- **username + password**
- **enable SSH** (password authentication to start)
- optionally configure Wi-Fi here if you want the Pi to connect to a hotspot on first boot (see note in Step 3)

This lets you control the Pi without a screen or keyboard.

## Step 2 - Flash and boot

1. "Write" → the OS is written to the card. Wait for the **"Write Successful"** message before removing the card - pulling it out early can corrupt the boot partition.
2. Card into the Pi.
3. Ethernet cable plugged in (see Step 3 for the network setup options).
4. Power → the Pi boots. The green LED will blink actively for the first minute or two while the system initialises.

## Step 3 - Getting the Pi on the network (initial setup)

### Recommended approach: Windows Internet Connection Sharing

The most reliable way to get the Pi online for the initial setup is to use Windows **Internet Connection Sharing** (ICS). This turns your PC's Ethernet port into a mini-router with its own DHCP server, so the Pi gets a proper IP address automatically.

1. Open **Control Panel → Network and Sharing Centre**
2. Click on your active Wi-Fi connection → **Properties** → **Sharing** tab
3. Check **"Allow other network users to connect through this computer's Internet connection"**
4. In the dropdown, select **Ethernet**
5. Click OK - Windows assigns `192.168.137.1` to the Ethernet interface and starts a DHCP server

Once the Pi boots with the Ethernet cable plugged in, it will request an IP from Windows. Find it with:

```powershell
arp -a
```

Look for a new dynamic entry under `Interface: 192.168.137.1` - the Pi will show up with a `192.168.137.x` address and a MAC address starting with `dc:a6:32` (Raspberry Pi Foundation prefix).

### If internet access still doesn't work through ICS (IPv6 issue)

Windows ICS only routes IPv4 traffic. On some setups, `apt` tries IPv6 addresses first and times out before falling back to IPv4. If `apt update` hangs with errors like `Cannot initiate the connection to ...:80 (2a00:...)`, disable IPv6 on the Pi:

```bash
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
```

If this still doesn't resolve the issue, the fallback is to connect the Pi to a **mobile hotspot** instead. Configure the hotspot SSID and password either in Raspberry Pi Imager before flashing (under "Edit Settings" → Wi-Fi), or via SSH once connected through ICS:

```bash
sudo nmcli dev wifi connect "your_hotspot_name" password "your_password"
```

Note: even when using a hotspot for internet access, the Ethernet cable between PC and Pi remains useful - it's how you find the Pi's Wi-Fi IP address in the first place (`ip addr show wlan0`), before switching your SSH session over to the Wi-Fi address.

## Step 4 - Connect to the Pi over SSH

```bash
ssh your_user@192.168.137.x   # via ICS (replace with the IP from arp -a)
# or
ssh your_user@ripe-probe-uc3m.local  # if .local resolution works in your setup
```

## Step 5 - Install the probe package

Official commands for **Debian / Raspberry Pi OS 12/13**, from the "Installation" → "Debian & Raspberry Pi OS" section of the official README:

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

> The repo package version number (`1.5-5`) is current as of the 5120 release (Oct 2025) - always check the up-to-date command on the official README before running it, since this number changes between releases.

## Step 6 - Retrieve the public key

```bash
sudo cat /etc/ripe-atlas/probe_key.pub
```

> Never share or distribute the *private* key (`/etc/ripe-atlas/probe_key`). Only the public key is used for registration.

## Step 7 - Register the probe

1. Go to <https://atlas.ripe.net/apply/swprobe/>, signed in to a RIPE NCC Access account.
2. Paste the contents of `probe_key.pub`.
3. The probe appears on the dashboard with a **pending** status, then turns to **Connected** once it reaches the RIPE infrastructure (checked on <https://atlas.ripe.net/probes/mine>).

### Check the connection

On <https://atlas.ripe.net/probes/mine>, the status column should turn to **Connected** (green cloud icon). Going from pending to connected can take a few minutes.

## Useful technical notes

- **Internal ports**: the software uses TCP ports **2023** and **8080**. In case of a conflict with another service, you can change them via `/etc/ripe-atlas/config.txt`.
- **Updates**: since release 5080, the package no longer updates automatically. To update: `sudo apt update && sudo apt upgrade`. (You can enable `unattended-upgrades` to automate it.)
- **Backup**: before any major update, back up `/etc/ripe-atlas/probe_key` and the config.

## How long to leave it running?

The probe should stay connected continuously, since credits accumulate per minute of connection (see [page 3](03-credit-system.md)). For our topic, it must at minimum be active before, during and after each observed match.

## Sources

- *Official README* (install commands, ports, updates) - <https://github.com/RIPE-NCC/ripe-atlas-software-probe>
- *Setting up a RIPE Atlas software probe*, L. Rodriguez (procedure tested on Pi 5, key/tunnel details) - <https://www.lucasrodriguez.net/posts/ripe-atlas-software-probe-setup/>
- *Software probes* (official docs) - <https://atlas.ripe.net/docs/howtos/software-probes/>
- v3/v4 probe specs (RAM order of magnitude) - <https://atlas.ripe.net/docs/probeinfo/probe-v4/>
- *Probe v3* spec page (companion to the v4 link above) - <https://atlas.ripe.net/docs/probeinfo/probe-v3/>
- *RIPE Atlas: Presentations, Tutorials and Videos* (RIPE Labs) - <https://labs.ripe.net/atlas/user-experiences/presentations-tutorials-and-videos>