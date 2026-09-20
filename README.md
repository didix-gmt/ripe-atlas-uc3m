---
layout: default
title: Home
nav_order: 1
permalink: /
---

# Getting Started with RIPE Atlas - Guide

> Written as part of a project measuring network blocking (La Liga anti-piracy).
> The goal is to be able to pick up the topic without starting from scratch.

---

## Who this guide is for

You, if you're joining the project and have never touched RIPE Atlas. It assumes you know basic networking (IP, DNS, ping) but not the RIPE ecosystem. Everything stated here is sourced at the bottom of each page.

## Contents

1. [What is RIPE Atlas?](docs/01-what-is-ripe-atlas.md) - core concepts, vantage points, probes vs anchors
2. [Hardware vs software probe](docs/02-hardware-vs-software-probe.md) - which one to choose for our case
3. [The credit system](docs/03-credit-system.md) - how to earn them, what each measurement costs
4. [Using existing data](docs/04-existing-data.md) - measuring without installing anything
5. [Installing a software probe on Raspberry Pi](docs/05-raspberry-pi-installation.md) - the step-by-step procedure
6. [Running measurements (web UI + Python API)](docs/06-running-measurements.md) - create a measurement and fetch results
7. [Example campaign: latency vs distance](docs/07-example-campaign.md) - a complete working measurement, from probe selection to plot
8. [Pitfalls in blocking detection](docs/08-pitfalls.md) - false positives to avoid before running a real campaign
9. [Probe coverage in Spain](docs/09-probe-coverage-spain.md) - how many usable vantage points per ISP, and what that means for the study design

---

## Reprendre le projet

Si vous reprenez ce projet, commencez par **[HANDOVER.md](HANDOVER.md)** - état actuel, ce qui a été fait, ce qui ne l'a pas été, et une checklist de démarrage.

## Main sources

- Official RIPE Atlas documentation - <https://atlas.ripe.net/docs/>
- Official probe software repository - <https://github.com/RIPE-NCC/ripe-atlas-software-probe>
- RIPE Labs' curated collection of RIPE Atlas talks and tutorials - <https://labs.ripe.net/atlas/user-experiences/presentations-tutorials-and-videos>

*Last updated: see the repository's Git history.*