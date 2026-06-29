# 1. What is RIPE Atlas?

## In one sentence

RIPE Atlas is a global network of probes that actively measure Internet connectivity and reachability, giving a real-time picture of the state of the Internet.

## Core concepts

**Vantage point.** A place in the network from which you observe the Internet. The value of RIPE Atlas is having thousands of vantage points spread around the world, which lets you see how a given target (an IP, a domain) is reachable — or not — depending on where and from which operator you look. This is exactly what we need: observing a block from inside a Spanish ISP's network.

**Probe.** The small device (or piece of software) that runs the measurements. Two families:
- *hardware probe*: a small box supplied by the RIPE NCC, plugged into your router;
- *software probe*: the same software installed on your own machine (e.g. a Raspberry Pi).

Both provide the same service. (Details and the choice: see [page 2](02-hardware-vs-software-probe.md).)

**Anchor.** A "beefed-up" probe, more powerful, which also serves as a measurement target. Reserved for organisations, with much heavier hardware and network requirements. Out of our scope, but good to know.

**Measurement.** The network test launched from one or more probes towards a target. Two categories:
- *built-in*: launched automatically by the system, continuously;
- *user-defined (UDM)*: the ones you create yourself, in exchange for credits.

Available measurement types are: **ping, traceroute, DNS, NTP, TLS/SSL, and HTTP (restricted)**.

## Why this is relevant to our project

Our topic is to measure IP/DNS blocking applied by Spanish ISPs during football matches. RIPE Atlas gives us:
- vantage points **physically located in Spain**, on real ISPs, hence subject to the same blocks as an ordinary subscriber;
- the ability to launch targeted tests (ping/DNS/HTTP) towards the IPs suspected of being blocked;
- access to data already collected by others, without installing anything.

## Sources

- *What is RIPE Atlas?* — <https://atlas.ripe.net/docs/getting-started/what-is-ripe-atlas/>
- *How RIPE Atlas works* (RIPE NCC) — <https://www.ripe.net/analyse/internet-measurements/ripe-atlas/how-ripe-atlas-works/>
- *RIPE Atlas Guide* (community, for measurement types) — <https://ripe-atlas-guide.0x03c0.com/index.php/RIPE_Atlas>
