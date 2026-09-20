---
layout: default
title: Handover
nav_order: 11
---

# Project Handover — La Liga Blocking Measurement

*Written by Didier Gamiette (intern, June–September 2026), for whoever picks up the project next.*
*Last updated: 17 September 2026.*

---

## TL;DR

- **The project**: measuring La Liga's IP-blocking anti-piracy campaign in Spain, using RIPE Atlas as a distributed measurement platform.
- **What exists**: a full onboarding guide, a literature review, and a complete, tested measurement pipeline for running a match-synchronised campaign.
- **What's missing — this is the one thing that matters**: no real match has ever been measured. The pipeline was validated with a 20-minute dry run against non-match traffic (see below), but it has never been pointed at an actual kickoff. Running it on the next available match is the single highest-value thing the next person can do.
- **Start here**: read this whole document once, then go to [Day one checklist](#day-one-checklist) and just run it.

---

## Day one checklist

Do this before anything else in this document.

1. `git pull`, then open `campaigns/campaign-match/` and confirm `campaign_match.py`, `select_targets.py`, `fetch_results.py` and `targets.txt` are all there. (They were nearly lost to an uncommitted local-only state at handover time — see [Open items](#open-items-and-known-risks).)
2. Check the current credit balance at atlas.ripe.net → Credits (see [Accounts & access](#accounts--access) for which account). It has likely not grown since the probe was returned around 24 August — see below.
3. Look up the next La Liga fixture on laliga.com and note its kickoff time in **UTC** (Spain is UTC+2 until late October, UTC+1 after).
4. Re-run the coverage check, since probe populations shift daily:
   ```bash
   python3 campaigns/probe_profile/probe_profile.py
   ```
5. Dry run, then launch:
   ```bash
   python3 campaigns/campaign-match/campaign_match.py \
     --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt
   # if the cost fits the balance:
   python3 campaigns/campaign-match/campaign_match.py \
     --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt --launch
   ```
6. After the match, fetch results (free, no credits spent) and start the analysis — see [Suggested next steps](#suggested-next-steps-in-order).

---

## Where everything lives

| What | Where |
|---|---|
| Onboarding guide (RIPE Atlas concepts, credits, install, pitfalls, coverage) | `docs/` in this repo, published at the GitHub Pages URL — see repo README |
| Literature review (SOTA) | `sota/sota.md` |
| Measurement scripts | `campaigns/*/` — one folder per script, each self-contained |
| This document | repo root, `HANDOVER.md` |

The guide (`docs/`) is written for someone who has never touched RIPE Atlas. This document is written for someone who needs to know what state *this specific project* is in. Read the guide for how things work; read this for where things stand.

---

## Current status (17 September 2026)

- **Probe**: the physical Raspberry Pi was returned to the lab around 24 August 2026. UC3M network authorisation was never obtained during this internship, so as far as is known the probe **is not currently hosted anywhere**, meaning **credit income likely stopped around that date**. Confirm this rather than assuming it — check the credits page directly.
- **Real match data**: **none was collected.** No matchday between mid-August and mid-September was measured with `campaign_match.py --launch` against an actual kickoff.
- **Pipeline validation**: on 22 August 2026, a 20-minute test run (`--test` flag, 3 targets, 42 probes: `188.114.97.5` plus two control resolvers) was launched successfully. The manifest is `campaigns/campaign-match/results/campaign_20260822_1910.json`. This confirms measurements can be created, run, and fetched end to end — but it ran outside any match window, so it shows no blocking (correctly — nothing was expected to be blocked at that time).
- **Documentation**: pages 1–9 are complete and published, including the methodology page (9) covering the equal-n sampling design and the residential-classification dead end.
- **Target list**: `campaigns/campaign-match/targets.txt` holds ~26 IPs, built from OONI's published list of confirmed-blocked addresses (`select_targets.py` regenerates it). This has not been validated against a live match, so treat it as a strong starting point, not a proven list.
- **A page 10 covering real match results was planned but could not be written**, because there is no real match data yet to write about.

---

## Accounts & access

**RIPE Atlas account.** Registered under a personal email (`gamiette.c@gmail.com`), not an institutional one — IMDEA/UC3M never set up an institutional account during this internship. Whoever continues the project needs either:
- credentials to that account (ask Didier or Pablo), or
- a credit transfer to a new/institutional account (RIPE Atlas supports this — see guide page 3), or
- a fresh account, starting from zero credits.

**API key.** Generated in that account's key manager (atlas.ripe.net/keys/), with permissions for creating and listing measurements. The credits-read permission was *not* enabled during this internship — `campaign_match.py`'s balance check silently fails without it. Fix this on whichever account continues the work.

**GitHub repo.** Currently under Didier's personal GitHub account. Needs a collaborator invite or a transfer to an institutional/team account for continuity.

---

## Key methodological decisions (and why)

Each links to the guide page with the full reasoning — this is just the summary so you don't have to reconstruct the logic from scratch.

| Decision | Why | Detail |
|---|---|---|
| Software probe on a Raspberry Pi, not hardware | Immediate start, full control, general-purpose Linux box | [Page 2](docs/02-hardware-vs-software-probe.md) |
| Five target ISPs (Telefónica, DIGI, Orange, MásMóvil, Vodafone), not three | DIGI and MásMóvil have more probe coverage than Orange/Vodafone and show distinctive behaviour in OONI's data | [Page 9](docs/09-probe-coverage-spain.md) |
| Equal n probes per operator, currently n = 6 | The headline analysis compares operators; unequal sample sizes confound the comparison. n = 6 sits below Vodafone's observed floor (7–9, fluctuating) to leave margin | [Page 9](docs/09-probe-coverage-spain.md) |
| Dropped residential-vs-infrastructure probe classification | RIPE publishes no reliable tag for it; more importantly, blocking is applied at the operator's core network, so it doesn't matter where inside the AS a probe sits | [Page 9](docs/09-probe-coverage-spain.md) |
| Ping + SSL/TLS check together, not ping alone | Some targets (e.g. uc3m.es) drop ICMP but serve HTTPS fine — ping alone would misreport them as unreachable | [Page 8](docs/08-pitfalls.md) |
| Select recent probes (highest IDs), never the API's default order | Old probes have an outdated TLS client that fails handshakes against modern servers — reads as false-positive blocking otherwise. This was a real bug that inflated the apparent blocking rate before it was caught. | [Page 8](docs/08-pitfalls.md) |
| Target IP list built from OONI's published dataset, not guessed | OONI publishes the actual list of IPs they confirmed blocked — no need to guess at Cloudflare ranges | `campaigns/campaign-match/select_targets.py`, sourced from OONI's report |
| `is_public=False` on real campaigns | A public measurement reveals which IPs we suspect of being blocked, before anything is published | [Page 6](docs/06-running-measurements.md) |

---

## How to run a campaign (cheat sheet)

Full detail is in the scripts themselves and in `docs/07-example-campaign.md`.

```bash
cd ripe-atlas-uc3m
source venv/bin/activate

# 1. Check current probe coverage per ISP (populations shift day to day)
python3 campaigns/probe_profile/probe_profile.py

# 2. Rebuild the target list from OONI's data if it's gone stale
python3 campaigns/campaign-match/select_targets.py --count 20

# 3. Dry run — see the plan and cost estimate, nothing is created
python3 campaigns/campaign-match/campaign_match.py \
  --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt
# (kickoff time is UTC — Spain is UTC+2 in summer/early autumn, UTC+1 in winter)

# 4. If the cost fits the credit balance, launch for real
python3 campaigns/campaign-match/campaign_match.py \
  --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt --launch

# 5. After the match, fetch results (free — no credits spent on reading)
python3 campaigns/campaign-match/fetch_results.py <measurement_id>
```

For a quick pipeline sanity check without spending real budget, use `--test` instead of `--kickoff`: a 20-minute validation window starting 5 minutes from now. This is exactly what was done on 22 August — see `campaigns/campaign-match/results/campaign_20260822_1910.json` for a worked example of the output shape.

**Cost, order of magnitude only — not a promise.** With 5 ISPs × 6 probes + 12 control probes = 42 probes, ~20 targets, a 5-minute sampling interval, and the standard ±1h match window, a rough back-of-envelope estimate lands somewhere in the low hundreds of thousands of credits per match (the script's `estimate_cost()` function will give you the actual number for whatever target list and interval you use — trust that over any figure written here). At a 10-minute interval, roughly half that. **Always check the actual current credit balance and re-run `estimate_cost()` before committing to an interval** — do not assume any number from this document still applies, since accrual likely stopped when the probe was returned in late August, and credit pricing/bonus behaviour was only ever observed empirically, never confirmed against official documentation (see `docs/03-credit-system.md`'s note on this).

---

## Suggested next steps, in order

1. **Run a real campaign on the next available match.** This is not optional or one option among several — it is the one thing that turns two months of tooling into a research result. Nothing else on this list matters until this happens at least once.
2. **Analyse the first real dataset** and write it up as guide page 10: does `188.114.97.5` show the block-before-kickoff, unblock-after-final-whistle pattern OONI described? That's the pipeline's validation against real-world ground truth, not just against idle traffic.
3. **Re-establish credit income** if continuing past the current balance: either get the Pi hosted somewhere (lab, if UC3M authorisation finally comes through, or a new volunteer host), or request a credit transfer/top-up.
4. **Expand and validate the target list** once a first real dataset exists — `targets.txt` is currently built from OONI's historical data and has never been checked against a live match.
5. **Consider the DNS-vs-IP blocking comparison** described in the SOTA (Müller et al.'s EU-sanctions methodology) — comparing ISP resolvers against public resolvers would show whether any part of the La Liga blocking is DNS-based rather than pure IP-blocking, which the current pipeline doesn't test for.
6. **Write up results** for whatever report/deliverable is expected — the doc, SOTA and scripts already contain most of the material needed; what's missing is the actual findings section, because there are no findings yet.

---

## Open items and known risks

- **UC3M network authorisation was never obtained.** Pablo raised it with UC3M admins early on and never heard back. If lab hosting is still desired, this needs chasing.
- **Vodafone has the thinnest, most unstable coverage** of the five target ISPs — observed fluctuating between 7 and 9 connected probes over the course of this internship. Treat any Vodafone-specific finding as a case study, not a statistically robust claim, and re-check its count before every campaign — see guide page 9.
- **Probe populations fluctuate daily.** Always re-run `probe_profile.py` shortly before a campaign rather than trusting a count from days earlier.
- **Quotas**: 100 concurrent measurements, 25 concurrent measurements toward the same target, 1,000 probes per measurement (see guide page 3). None of these were hit during this internship, but a larger target list or more probes per ISP could approach them.
- **The credits-read API permission was never enabled** — fix this so `campaign_match.py`'s balance check actually works instead of silently failing.
- **A lesson from the handover itself**: at the point this document was written, the two most important scripts (`campaign_match.py`, `select_targets.py`, `fetch_results.py`, and `probe_density.py`) existed only in the local working directory, never committed to git — two months of the most critical work, one disk failure away from being lost. If you're reading this in the repo, it means that got fixed before handover — but it's a good argument for committing early and often rather than batching it all up at the end.

---

## People

- **Pablo Serrano Yañez-Mingot** — supervisor, Deputy Director at IMDEA Networks. Primary contact for anything involving direction, UC3M administration, or the account/credit situation.
- **Marco**, **Juan Manuel** — collaborators on the project; Pablo can point you to current contact details.
- **Didier Gamiette** (outgoing intern) — available for questions during the handover period; contact via the email associated with the RIPE Atlas account.

---

*If you're reading this because you've just joined the project: welcome. Start with the guide (`docs/`), then the [Day one checklist](#day-one-checklist) above — the pipeline is fully built and tested, it just needs to be pointed at a real match. That's the whole gap between what exists and a finished piece of research.*
