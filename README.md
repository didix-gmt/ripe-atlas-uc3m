# Getting Started with RIPE Atlas — Internal Guide

> Written during a research internship at **Universidad Carlos III de Madrid (UC3M)**, as part of a project measuring network blocking (La Liga anti-piracy).
> The goal is for the next student to be able to pick up the topic without starting from scratch.

**Project status: 🚧 waiting for UC3M network authorisation.**
No probe should be connected to the lab network until the UC3M team has given approval (see [Before you start](#before-you-start)).

---

## Who this guide is for

You, if you're joining the project and have never touched RIPE Atlas. It assumes you know basic networking (IP, DNS, ping) but not the RIPE ecosystem. Everything stated here is sourced at the bottom of each page — if a claim has no source, it's still **to be verified**, and that's flagged as such.

## Contents

1. [What is RIPE Atlas?](docs/01-what-is-ripe-atlas.md) — core concepts, vantage points, probes vs anchors
2. [Hardware vs software probe](docs/02-hardware-vs-software-probe.md) — which one to choose for our case
3. [The credit system](docs/03-credit-system.md) — how to earn them, what each measurement costs
4. [Using existing data](docs/04-existing-data.md) — measuring without installing anything
5. [Installing a software probe on Raspberry Pi](docs/05-raspberry-pi-installation.md) — the step-by-step procedure
6. [Running measurements (web UI + Python API)](docs/06-running-measurements.md) — create a measurement and fetch results
7. [Open questions / to validate](docs/07-open-questions.md) — what's still unclear and needs to be settled with the supervisors

---

## Before you start

⚠️ **Supervisor instruction (Pablo):** let the team know before hosting a probe, so that the authorisation request can be made to the UC3M team. Concretely, until authorisation is granted:

- ✅ you can create a RIPE NCC Access account (free, it's just a web account)
- ✅ you can prepare and configure the Raspberry Pi **locally** (direct Pi ↔ PC cable, without connecting it to the UC3M network)
- ✅ you can explore and use the **public data** already collected (no credits or account required)
- ❌ you do **not** connect any probe to the lab network

---

## How to publish this guide as a website (GitHub Pages)

This repository is meant to be published as-is via **GitHub Pages**, which turns Markdown files into a website reachable by a URL.

1. Create a GitHub repository and push these files to it.
2. In the repo: `Settings` → `Pages` → `Source`: pick the branch (`main`) and the root folder.
3. GitHub generates a URL like `https://<your-username>.github.io/<repo-name>/`.
4. Any change pushed to the branch updates the site automatically.

> For a more "site-like" feel (sidebar menu, search), you can enable a Jekyll theme or move to a generator like MkDocs later. Raw Markdown stays readable and copy-pasteable in all cases, which is the main need here.

---

## Main sources

- Official RIPE Atlas documentation — <https://atlas.ripe.net/docs/>
- Official probe software repository — <https://github.com/RIPE-NCC/ripe-atlas-software-probe>

*Last updated: see the repository's Git history.*
