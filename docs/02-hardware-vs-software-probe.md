# 2. Hardware vs software probe

Both probe types provide **the same service** and run the same measurements. The difference is in how you obtain, install and control them.

## Hardware probe

A small box sent for free by the RIPE NCC after a request is approved.

- **Getting one**: apply online; the RIPE NCC evaluates the request based on location (they check whether the network would benefit from a probe there). If approved, it's mailed to you, free of charge.
- **Installation**: plug it into the router/switch via Ethernet + USB power. On most networks it gets an IP via DHCP and connects on its own.
- **Important limit**: a regular user is in principle only entitled to **one** hardware probe, unless a specific justification is provided in the application form.
- **Lead time**: depends on shipping and approval — not immediate.

## Software probe

The official RIPE Atlas software installed on your own machine.

- **Getting it**: immediate, you download the package. No waiting for shipping.
- **Officially supported platforms**: binary packages for Debian 11/12/13 and Raspberry Pi OS 12/13 (arm64), Enterprise Linux 8/9/10 (amd64), and a build is possible for OpenWrt 22.03.
- **Control**: you choose the machine, the network, the physical location.
- **Important limit**: there is **no benefit** to running multiple software probes on the same network (they consume resources for nothing), and the RIPE NCC deliberately limits their number per account/network to prevent "credit farming".

## For our case (Raspberry Pi at the lab)

The supervisors mentioned a **Raspberry Pi**, so we go with a **software probe**. Advantages for the project:
- immediate start (no waiting for mail);
- full control over location and timing of measurements;
- the available Pi 3B is more than powerful enough (see [page 5](05-raspberry-pi-installation.md)).

⚠️ **Reminder**: whatever the type, **nothing** gets connected to the UC3M network without the authorisation requested by Pablo from the UC3M team.

## Note on "several probes here and there"

The initially mentioned idea of installing several Raspberry Pis at different locations is valid **for control**, but should be weighed against two facts:
1. we can already use the **public data** of existing probes in Spain without installing anything (see [page 4](04-existing-data.md));
2. multiplying software probes on **the same network** brings nothing and is discouraged by RIPE.

The right trade-off (to settle with the supervisors): use the existing fleet for broad coverage, and deploy our own probes **only where we need fine-grained control** (specific ISP, specific city, measurement launched exactly during a match).

## Sources

- *Become a Probe Host* — <https://atlas.ripe.net/docs/getting-started/become-a-host/>
- *Probes, Hosts, Anchors & Sponsors* (FAQ) — <https://atlas.ripe.net/docs/faq/probes-hosts-anchors-sponsors/>
- *ripe-atlas-software-probe* (supported platforms) — <https://github.com/RIPE-NCC/ripe-atlas-software-probe>
