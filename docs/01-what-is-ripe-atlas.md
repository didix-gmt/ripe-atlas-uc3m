---
layout: default
title: What is RIPE Atlas?
nav_order: 2
---

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
- vantage points **inside Spanish ISPs' networks**, to observe whether a block is actually applied to local subscribers;
- vantage points **outside Spain** (Europe, Americas, Asia), to determine whether a block is Spain-specific or global, a page that times out from Madrid but loads fine from Berlin is likely locally blocked, not down;
- the ability to launch targeted tests (ping/DNS/HTTP) towards the IPs suspected of being blocked;
- access to data already collected by others, without installing anything.

> **Key point: you are not limited to your own probe.** RIPE Atlas is a shared network, once you have an account and credits, you can launch measurements from *any* of the thousands of probes hosted by other people around the world, not just your own. Your probe contributes to the network and earns credits; those credits are then spent to task other probes anywhere on the planet. This is what makes distributed, multi-continent measurements possible without owning hardware in every country.

## Sources

- *What is RIPE Atlas?* — <https://atlas.ripe.net/docs/getting-started/what-is-ripe-atlas/>
- *How RIPE Atlas works* (RIPE NCC) — <https://www.ripe.net/analyse/internet-measurements/ripe-atlas/how-ripe-atlas-works/>
- *RIPE Atlas Guide* (community, for measurement types) — <https://ripe-atlas-guide.0x03c0.com/index.php/RIPE_Atlas>
- *RIPE Atlas Probes and Anchors* (Internet Society) — <https://www.internetsociety.org/resources/doc/2016/ripe-atlas-probes-and-anchors/>
- *RIPE Atlas* (official intro video, RIPE NCC YouTube) — <https://www.youtube.com/watch?v=Z3SW2vO8qW0>
- *RIPE Atlas: Presentations, Tutorials and Videos* (RIPE Labs) — <https://labs.ripe.net/atlas/user-experiences/presentations-tutorials-and-videos>