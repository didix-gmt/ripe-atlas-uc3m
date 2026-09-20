---
layout: default
title: Handover
nav_order: 11
---

# Project Handover - La Liga Blocking Measurement

*Written by Didier Gamiette (intern, June–September 2026), for whoever picks up the project next.*
*Last updated: 20 September 2026.*

---

## TL;DR

- **The project**: measuring La Liga's IP-blocking anti-piracy campaign in Spain, using RIPE Atlas as a distributed measurement platform.
- **What exists**: a full onboarding guide, a literature review, and a complete measurement pipeline for running a match-synchronised campaign.
- **What's missing - this is the one thing that matters**: no real match has ever been measured. The pipeline was validated with a 20-minute dry run against non-match traffic (see below), but it has never been pointed at an actual kickoff. Running it on the next available match is the single highest-value thing the next person can do.
- **One thing to know before you spend any credits**: an audit at handover found that `campaign_match.py` had been launching **ping only**, in violation of the project's own documented rule. It now launches ping + TLS, which is correct but **4.3× more expensive**. That changes what a campaign costs, so read [How to run a campaign](#how-to-run-a-campaign-cheat-sheet) before picking an interval and target count.
- **Start here**: read this whole document once, then go to [Day one checklist](#day-one-checklist) and just run it.

---

## Day one checklist

Do this before anything else in this document.

1. `git pull`, then open `campaigns/campaign-match/` and confirm `campaign_match.py`, `select_targets.py`, `fetch_results.py` and `targets.txt` are all there. (They were nearly lost to an uncommitted local-only state at handover time - see [Open items](#open-items-and-known-risks).)
2. Check the current credit balance at atlas.ripe.net → Credits (see [Accounts & access](#accounts--access) for which account). It has likely not grown since the probe was returned around 24 August - see below.
3. Look up the next La Liga fixture on laliga.com and note its kickoff time in **UTC** (Spain is UTC+2 until late October, UTC+1 after).
4. Re-run the coverage check, since probe populations shift daily:
   ```bash
   python3 campaigns/probe_profile/probe_profile.py
   ```
5. **Dry run first - it creates nothing and costs nothing.** It prints the plan, the per-measurement-type cost breakdown, and the balance:
   ```bash
   python3 campaigns/campaign-match/campaign_match.py \
     --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt
   ```
6. **Decide what you can afford**, using the table in [How to run a campaign](#how-to-run-a-campaign-cheat-sheet). The three levers are the number of targets, `INTERVAL_SECONDS`, and whether to run ping + TLS or TLS alone (`MEASURE_PING` / `MEASURE_TLS` near the top of `campaign_match.py`). Re-run the dry run after each change until the cost fits.
7. Launch:
   ```bash
   python3 campaigns/campaign-match/campaign_match.py \
     --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt --launch
   ```
8. After the match, fetch results (free, no credits spent) and start the analysis - see [Suggested next steps](#suggested-next-steps-in-order).

---

## Where everything lives

| What | Where |
|---|---|
| Onboarding guide (RIPE Atlas concepts, credits, install, pitfalls, coverage) | `docs/` in this repo, published at the GitHub Pages URL - see repo README |
| Literature review (SOTA) | `sota/sota.md` |
| Measurement scripts | `campaigns/*/` - one folder per script, each self-contained |
| This document | repo root, `HANDOVER.md` |

The guide (`docs/`) is written for someone who has never touched RIPE Atlas. This document is written for someone who needs to know what state *this specific project* is in. Read the guide for how things work; read this for where things stand.

---

## Current status (20 September 2026)

- **Probe**: the physical Raspberry Pi was returned to the lab around 24 August 2026. UC3M network authorisation was never obtained during this internship, so as far as is known the probe **is not currently hosted anywhere**, meaning **credit income likely stopped around that date**. Confirm this rather than assuming it - check the credits page directly.
- **Real match data**: **none was collected.** No matchday between mid-August and mid-September was measured with `campaign_match.py --launch` against an actual kickoff.
- **Pipeline validation**: on 22 August 2026 a 20-minute test run was launched successfully. Per its manifest (`campaigns/campaign-match/results/campaign_20260822_1910.json`), it created **one periodic measurement - `msm_id` 203356204 - against `188.114.97.5`**, at a 5-minute interval over 19:10–19:30 UTC, from probes spread across the five target ISPs plus controls. This confirms measurements can be created and run. It ran outside any match window, so it correctly shows no blocking.
- **`fetch_results.py` was validated separately**, on measurements 194568725 / 194568726 (the `uc3m.es` connectivity check). That run is a useful sanity reference: `uc3m.es` came back **0/18 on ping and 18/18 on TLS**, which is the ICMP pitfall from `docs/08` reproduced live. If a future change to the classification logic ever makes that target look "blocked", the logic is wrong, not the target. Note that this does *not* prove the API key can read **non-public** measurements, which is how real campaigns are created - see the credits/permissions item below.
- **A defect was found and fixed at handover.** `campaign_match.py` had been creating **ping measurements only** - no TLS - for its entire development, despite `docs/08` stating the rule and its checklist asking for it. A ping-only campaign is blind to a block applied at TCP/443, so it could have returned "no blocking detected" while blocking was happening, and it would have been validated against a ground truth (`188.114.97.5`) that OONI established with TLS rather than ping. It now creates both, in one request per target so they share probes and timing, and `estimate_cost()` was corrected in the same pass - it had been understating the bill by 4.3× once TLS was added. **Neither change has been exercised against a live launch**, only against a mocked dry run; the first real campaign is also the first test of them.
- **Documentation**: pages 1–9 are complete and published. Page 8 (pitfalls) now records the ping-only mistake and the cost-estimate mistake as pitfalls 3 and 6; page 9 carries the target-composition findings below.
- **Target list**: `campaigns/campaign-match/targets.txt` holds ~26 IPs, built from OONI's published list of confirmed-blocked addresses (`select_targets.py` regenerates it). This has not been validated against a live match, so treat it as a strong starting point, not a proven list.
- **A page 10 covering real match results was planned but could not be written**, because there is no real match data yet to write about.

---

## Accounts & access

**RIPE Atlas account.** Registered under a personal email (`gamiette.c@gmail.com`), not an institutional one - IMDEA/UC3M never set up an institutional account during this internship. Whoever continues the project needs either:
- credentials to that account (ask Didier or Pablo), or
- a credit transfer to a new/institutional account (RIPE Atlas supports this - see guide page 3), or
- a fresh account, starting from zero credits.

**API key.** Generated in that account's key manager (atlas.ripe.net/keys/), with permissions for creating and listing measurements. The credits-read permission was *not* enabled during this internship - `campaign_match.py`'s balance check silently fails without it. Fix this on whichever account continues the work.

**GitHub repo.** Currently under Didier's personal GitHub account. Needs a collaborator invite or a transfer to an institutional/team account for continuity.

---

## Key methodological decisions (and why)

Each links to the guide page with the full reasoning - this is just the summary so you don't have to reconstruct the logic from scratch.

| Decision | Why | Detail |
|---|---|---|
| Software probe on a Raspberry Pi, not hardware | Immediate start, full control, general-purpose Linux box | [Page 2](docs/02-hardware-vs-software-probe.md) |
| Five target ISPs (Telefónica, DIGI, Orange, MásMóvil, Vodafone), not three | DIGI and MásMóvil have more probe coverage than Orange/Vodafone and show distinctive behaviour in OONI's data | [Page 9](docs/09-probe-coverage-spain.md) |
| Equal n probes per operator, currently n = 6 | The headline analysis compares operators; unequal sample sizes confound the comparison. n = 6 sits below Vodafone's observed floor (7–9, fluctuating) to leave margin | [Page 9](docs/09-probe-coverage-spain.md) |
| Dropped residential-vs-infrastructure probe classification | RIPE publishes no reliable tag for it; more importantly, blocking is applied at the operator's core network, so it doesn't matter where inside the AS a probe sits | [Page 9](docs/09-probe-coverage-spain.md) |
| Ping + SSL/TLS check together, not ping alone | Some targets (e.g. uc3m.es) drop ICMP but serve HTTPS fine, and a block applied at TCP/443 only would be invisible to ping. `campaign_match.py` violated this rule for its whole development and was corrected at handover - it is the most expensive decision in the campaign, see the cost section above | [Page 8](docs/08-pitfalls.md), pitfalls 3 and 6 |
| Select recent probes (highest IDs), never the API's default order | Old probes have an outdated TLS client that fails handshakes against modern servers - reads as false-positive blocking otherwise. This was a real bug that inflated the apparent blocking rate before it was caught. | [Page 8](docs/08-pitfalls.md) |
| Target IP list built from OONI's published dataset, not guessed | OONI publishes the actual list of IPs they confirmed blocked - no need to guess at Cloudflare ranges | `campaigns/campaign-match/select_targets.py`, sourced from OONI's report |
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

# 3. Dry run - see the plan and cost estimate, nothing is created
python3 campaigns/campaign-match/campaign_match.py \
  --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt
# (kickoff time is UTC - Spain is UTC+2 in summer/early autumn, UTC+1 in winter)

# 4. If the cost fits the credit balance, launch for real
python3 campaigns/campaign-match/campaign_match.py \
  --kickoff "YYYY-MM-DD HH:MM" --targets campaigns/campaign-match/targets.txt --launch

# 5. After the match, fetch results (free - no credits spent on reading)
python3 campaigns/campaign-match/fetch_results.py <measurement_id>
```

For a quick pipeline sanity check without spending real budget, use `--test` instead of `--kickoff`: a 20-minute validation window starting 5 minutes from now. This is exactly what was done on 22 August - see `campaigns/campaign-match/results/campaign_20260822_1910.json` for a worked example of the output shape.

### What a campaign costs, and the decision you have to make

This is the part that needs a deliberate choice rather than a default, because fixing the ping-only defect made campaigns roughly four times more expensive.

Unit costs are 3 credits per ping result and 10 per TLS result ([page 3](docs/03-credit-system.md), official RIPE figures), so running both costs 13 per probe per round. With the standard setup - 42 probes (5 ISPs × 6 + 3 controls × 4) over a 235-minute window (60 min lead + 115 match + 60 trail):

| Targets | Interval | Rounds | ping only | TLS only | ping + TLS |
|---|---|---|---|---|---|
| 20 | 5 min | 47 | 118,440 | 394,800 | **513,240** |
| 20 | 10 min | 23 | 57,960 | 193,200 | 251,160 |
| 15 | 10 min | 23 | 43,470 | 144,900 | 188,370 |
| 12 | 10 min | 23 | 34,776 | **115,920** | 150,696 |
| 10 | 10 min | 23 | 28,980 | 96,600 | 125,580 |

For scale: one probe earns about 21,600 credits/day ([page 3](docs/03-credit-system.md)), and in practice we observed closer to 33,000 including the results-delivered bonus. So **ping + TLS at the current defaults is roughly three weeks of a single probe's income for one match.** With no probe currently hosted, that is not a rounding error.

Three ways out, all defensible, none free:

- **TLS only, 12 targets, 10-minute interval** (~116k credits) costs about what the old ping-only plan did, while actually measuring what a user experiences. `fetch_results.py` already extracts three states from a TLS result alone, and it matches OONI's own methodology. The cost is resolution: a 10-minute interval blurs exactly *when* a block starts and stops, which is one of the more interesting things to measure.
- **ping + TLS, fewer targets** keeps the fine timing and the ping/TLS mismatch diagnostic, at the price of a narrower target list - which weakens the per-stratum picture from `select_targets.py`.
- **ping + TLS at full scope** is the best dataset and needs a credit top-up or transfer arranged first.

My own reading, for what it's worth: **TLS-only at a 10-minute interval is the right first real campaign.** It fits a realistic budget, it answers the question, and once there is one real dataset to argue from it becomes far easier to justify asking for more credits. But this is Pablo's call as much as anyone's, and it should be stated in the write-up either way.

**Whatever you choose, re-run the dry run and check the live balance first.** Do not trust the numbers in this table as current: they assume the probe counts and window above, and credit accrual almost certainly stopped when the Pi was returned in late August.

---

## Suggested next steps, in order

1. **Run a real campaign on the next available match.** This is not optional or one option among several - it is the one thing that turns two months of tooling into a research result. Nothing else on this list matters until this happens at least once.
2. **Analyse the first real dataset** and write it up as guide page 10: does `188.114.97.5` show the block-before-kickoff, unblock-after-final-whistle pattern OONI described? That's the pipeline's validation against real-world ground truth, not just against idle traffic.
3. **Re-establish credit income** if continuing past the current balance: either get the Pi hosted somewhere (lab, if UC3M authorisation finally comes through, or a new volunteer host), or request a credit transfer/top-up.
4. **Expand and validate the target list** once a first real dataset exists - `targets.txt` is currently built from OONI's historical data and has never been checked against a live match.
5. **Consider the DNS-vs-IP blocking comparison** described in the SOTA (Müller et al.'s EU-sanctions methodology) - comparing ISP resolvers against public resolvers would show whether any part of the La Liga blocking is DNS-based rather than pure IP-blocking, which the current pipeline doesn't test for.
6. **Write up results** for whatever report/deliverable is expected - the doc, SOTA and scripts already contain most of the material needed; what's missing is the actual findings section, because there are no findings yet.

---

## Open items and known risks

- **UC3M network authorisation was never obtained.** Pablo raised it with UC3M admins early on and never heard back. If lab hosting is still desired, this needs chasing.
- **Vodafone has the thinnest, most unstable coverage** of the five target ISPs - observed fluctuating between 7 and 9 connected probes over the course of this internship. Treat any Vodafone-specific finding as a case study, not a statistically robust claim, and re-check its count before every campaign - see guide page 9.
- **Probe populations fluctuate daily.** Always re-run `probe_profile.py` shortly before a campaign rather than trusting a count from days earlier.
- **Quotas**: 100 concurrent measurements, 25 concurrent measurements toward the same target, 1,000 probes per measurement (see guide page 3). None of these were hit during this internship, but a larger target list or more probes per ISP could approach them.
- **The credits-read API permission was never enabled** - fix this so `campaign_match.py`'s balance check actually works instead of silently failing.
- **An open methodological choice in the target sampling.** Measured on OONI's published CSV, the affected addresses break down as **Amazon AWS 5,097 (69.1%), Cloudflare 2,215 (30.0%), and a tail of 62 addresses (0.8%) across 30 small ASNs** - the two big providers hold 99.2% of everything. `select_targets.py` deliberately samples *non*-proportionally (AWS 50%, Cloudflare 40%, tail 10%), over-weighting Cloudflare because each of its anycast addresses fronts far more distinct sites and so carries more of the collateral damage, and over-weighting the tail so its presence can be checked at all. That is defensible, but it is a *choice*: per-stratum figures from this sample are not estimates of what fraction of addresses were blocked. Decide explicitly - impact-weighted or address-proportional - before writing up results, and state which. Worth putting to Pablo. Reasoning and the alternative are documented at the top of `select_targets.py`.
- **Two findings from OONI's data are now in [page 9](docs/09-probe-coverage-spain.md), but the SOTA has not caught up.** First, by *address* count Amazon is the larger half of the blocking (69%), not Cloudflare (30%) - which does not contradict OONI, who count affected *sites*, where Cloudflare's anycast concentration dominates; the two answer different questions and a write-up must say which it is asking. Second, the blocking is overwhelmingly range-level: 86% of affected addresses sit in a /24 holding at least eight others. Both belong in `sota/sota.md` alongside the discussion of OONI's report, and neither is there yet.
- **The DIGI TLS-interception wording.** `docs/09` carries a warning about it that is worth re-reading before writing anything public: OONI observed the interception **on** DIGI's network and explicitly does not attribute responsibility. "Observed on", never "performed by".
- **Two lessons from the handover audit itself**, both worth a moment because they are the kind of thing that recurs:
  - The most important scripts (`campaign_match.py`, `select_targets.py`, `fetch_results.py`, `probe_density.py`) existed only in a local working directory and had never been committed - two months of the most critical work, one disk failure from gone. Two of them had to be rebuilt from scratch at handover because no copy survived anywhere. Commit early, commit often.
  - The ping-only defect sat in the main script for its whole development *while the documentation correctly stated the rule*. Writing a rule down is not the same as applying it. When a checklist item matters, check it against every script that should obey it - not against the one you were thinking about when you wrote it.

---

## People

- **Pablo Serrano Yañez-Mingot** - supervisor, Deputy Director at IMDEA Networks. Primary contact for anything involving direction, UC3M administration, or the account/credit situation.
- **Marco**, **Juan Manuel** - collaborators on the project; Pablo can point you to current contact details.
- **Didier Gamiette** (outgoing intern) - available for questions during the handover period; contact via the email associated with the RIPE Atlas account.

---

*If you're reading this because you've just joined the project: welcome. Start with the guide (`docs/`), then the [Day one checklist](#day-one-checklist) above.*

*The pipeline is built, and every part of it has been exercised - probe selection, target sampling, measurement creation, result fetching and classification - but never all at once against a real kickoff, and the ping + TLS change is newer than the last real launch. Expect to fix one or two things on the first run. That gap, between a pipeline that works in pieces and one real match measured end to end, is the whole distance between what exists here and a finished piece of research. It is not a large distance. It just has to be walked once.*