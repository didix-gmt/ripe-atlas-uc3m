---
layout: default
title: Hardware vs software probe
nav_order: 3
---

# 2. Hardware vs software probe

Both probe types provide **the same service** and run the same measurements. The difference is in how you obtain, install and control them.

## Hardware probe

A small box sent for free by the RIPE NCC after a request is approved.

- **Getting one**: apply online; the RIPE NCC evaluates the request based on location (they check whether the network would benefit from a probe there). If approved, it's mailed to you, free of charge.
- **Installation**: plug it into the router/switch via Ethernet + USB power. On most networks it gets an IP via DHCP and connects on its own.
- **Important limit**: a regular user is in principle only entitled to **one** hardware probe, unless a specific justification is provided in the application form.
- **Lead time**: depends on shipping and approval - not immediate.

## Software probe

The official RIPE Atlas software installed on your own machine.

- **Getting it**: immediate, you download the package. No waiting for shipping.
- **Officially supported platforms**: binary packages for Debian 11/12/13 and Raspberry Pi OS 12/13 (arm64), Enterprise Linux 8/9/10 (amd64), and a build is possible for OpenWrt 22.03.
- **Control**: you choose the machine, the network, the physical location.
- **Important limit**: running several software probes on the same network brings no real benefit - they all consume resources without adding value - so RIPE Atlas actively limits how many software probes are allowed per account/network, specifically to prevent abuse and what they call "credit farming". *(Source: FAQ, "Probes, Hosts, Anchors & Sponsors", question on software probes.)* The exact thresholds are tiered by network grouping:

  | Grouping level | Limit |
  |---|---|
  | Same IP address | 2 software probes |
  | Same IP prefix | 4 software probes |
  | Same IPv4 / IPv6 prefix, across all hosts | 32 / 64 probes |

  *(Source: official docs, "Managing Your Probe" page, section on controls limiting software probes per network.)* Probes beyond these limits are simply refused connection until another one drops. If multiple probes genuinely add value despite sharing an apparent IP (e.g. they're geographically distributed but exit through the same address), the host can email `atlas@ripe.net` with an explanation to request an exception.

## For our case

We're going with a **software probe** on a Raspberry Pi 3B.

**Why choosing a Pi?**
- immediate start - no waiting for an application to be approved and shipped;
- full control over location and timing of measurements;
- a Raspberry Pi 3B is more than powerful enough for the job (see [page 5](05-raspberry-pi-installation.md));
- it's a general-purpose Linux machine - we can also run our own measurement scripts directly on it, not just RIPE's official measurements;
- we could connect a second software probe on the same network to roughly double the credits earned, up to the 2-per-IP limit shown in the table above (see [page 3](03-credit-system.md) for the exact numbers).

Keep in mind that with a software probe, updates have to be applied manually (`apt update && apt upgrade`), whereas a hardware probe updates its firmware automatically once connected.

## Sources

- *Become a Probe Host* - <https://atlas.ripe.net/docs/getting-started/become-a-host/>
- *Probes, Hosts, Anchors & Sponsors* (FAQ) - <https://atlas.ripe.net/docs/faq/probes-hosts-anchors-sponsors/>
- *ripe-atlas-software-probe* (supported platforms) - <https://github.com/RIPE-NCC/ripe-atlas-software-probe>
- *Managing Your Probe* (firmware auto-update, software probe network limits) — <https://atlas.ripe.net/docs/faq/managing-your-probe/>
- *RIPE Atlas: Presentations, Tutorials and Videos* (RIPE Labs) — <https://labs.ripe.net/atlas/user-experiences/presentations-tutorials-and-videos>