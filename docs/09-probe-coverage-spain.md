---
layout: default
title: "Probe coverage in Spain"
nav_order: 10
---

# 9. Probe coverage in Spain

Before designing a campaign you need to know what you can actually measure. This page documents how many usable vantage points exist inside each Spanish ISP, and how that shaped the sampling design.

It also documents a methodological dead end we went down first, because the reasoning behind abandoning it is more useful than the result would have been.

---

## Why per-ISP coverage matters

The La Liga injunctions are addressed to ISPs, and blocking is applied inside each operator's network. So the unit of analysis is the **operator**, not the country: a block present on Telefónica may be absent on Vodafone, and that difference is one of the more interesting things we can measure.

That means we need vantage points inside each target AS, and enough of them to say something. Bajpai et al. warned that RIPE Atlas probe distribution across ASes is heavily skewed, so this had to be checked before designing anything.

---

## Coverage, measured

Connected probes in Spain (`country_code=ES&status=1`), 259 at time of writing:

| ISP | AS | Connected probes |
|---|---|---|
| Telefónica / Movistar | 3352 | 72 |
| DIGI Spain | 57269 | 35 |
| Orange Espagne | 12479 | 15 |
| MásMóvil (Xtra Telecom) | 15704 | 15 |
| Vodafone España | 12430 | 9 |
| *All other Spanish ASes* | - | 113 |

The skew Bajpai described is clearly present: the best-covered target operator has eight times more probes than the worst.

> Re-run `probe_profile.py` before any campaign. Probe populations change, and a count from three months ago is not a count from today.

---

## The dead end: trying to identify residential probes

**The initial reasoning.** The injunctions target consumer subscribers, so a probe on a university or corporate line might sit on the wrong side of the filter and produce a false negative. It therefore seemed important to count *residential* probes specifically, not just probes.

**The problem.** RIPE Atlas publishes no system tag for "residential" or "datacentre" - the official system tags cover only protocol capability, connectivity, stability, DNS resolution and probe metadata. So the classification had to be inferred, and we used three signals: anchors (certain infrastructure), host-declared location tags (`home`, `office`, `datacentre` - reliable but voluntary, so absent on most probes), and `system-ipv4-rfc1918`, meaning the probe holds a private address and therefore sits behind NAT.

**Why we dropped it.** The NAT signal does not carry the weight we put on it. Homes NAT, but so do offices, universities and plenty of hosting setups; conversely some home connections hand a public address straight to the device, so a genuine residential probe may not carry the tag at all. It errs in both directions, and 144 of our 189 "residential" probes rested on that signal alone - only ~45 were host-declared.

**And more importantly, the question was the wrong one.** Blocking is applied at the operator's core network, not at the customer's premises. Any probe inside the AS traverses the same filtering infrastructure, whether it sits in a flat or an office. So a precise residential count buys us very little, as long as we exclude probes that might sit behind an *additional* filter of their own.

**What replaced it.** A much simpler rule:

- select by AS;
- exclude anchors and probes explicitly declared as infrastructure (`datacentre`, `academic`, `office`, etc.);
- treat everything else as usable, without pretending to know whether it is a flat or a small business.

### A trap worth recording anyway

Before dropping the approach we hit a genuine bug in it, and the lesson generalises. An early version treated **connection-technology tags** (`fibre`, `ftth`, `dsl`, `cable`, `nat`) as residential markers. They are not: they describe *how* a probe connects, not *where* it sits. An office with fibre is still an office.

The effect was concrete - every probe tagged `fibre` + `office` was recorded as a contradiction rather than correctly classified as infrastructure, and probes tagged `fibre` alone were counted as homes. Fixing it doubled the infrastructure count (19 → 41) and cut unresolvable conflicts from 25 to 2.

The general lesson: when combining tags into a classification, check that they describe the *same dimension*. Mixing "what kind of place" with "what kind of link" produces confident nonsense.

---

## Sampling design: equal n per operator

The natural instinct is to use every probe available - 72 for Telefónica, 9 for Vodafone. That is a mistake for our purpose, because **the headline analysis is a comparison between operators**. With unequal sample sizes, a difference in detected blocking rate could just as easily reflect the difference in sample size as a real difference in behaviour.

So the design is **the same number of probes per operator**, and that number can be small. Within a single operator we do not expect probe-to-probe variation, since all of them sit behind the same filtering infrastructure - assuming no additional firewall in between, which is what excluding declared infrastructure is for.

**n = 6 per operator** is the current setting (`PROBES_PER_ISP` in `campaign_match.py`). Vodafone's connected count fluctuated between 7 and 9 across several checks during this internship - not a fixed number - so n was set below the observed floor rather than at it, to leave margin if a probe drops before a match. Re-check Vodafone's current count before assuming 6 is still safe.

This also keeps the campaign cheap. 6 probes × 5 operators = 30 target probes per round instead of the 146 a proportional sample would need, which is what buys the sampling frequency needed to pin down *when* blocks start and stop.

**What we give up.** We cannot map variation *inside* an operator's network - regional differences within Telefónica, for instance. That is a separate question requiring a different design, and it should be stated as out of scope rather than left ambiguous.

---

## Which ISPs to target

We started with the three obvious consumer ISPs (Movistar, Orange, Vodafone). The coverage data says the list should be **five**.

**DIGI (AS57269)** has the second-best coverage in Spain, and its own dedicated analysis in the OONI report: TLS man-in-the-middle activity affecting 7,334 unique IPs across 14 ASNs and 10,759 domain names, observed on measurements collected from that network.

> ⚠️ **Wording matters here.** OONI observed this **on** DIGI's network; the report explicitly does not attribute responsibility for the interception. Any write-up should say "observed on", never "performed by". We are documenting a measurement, not making an accusation.

**MásMóvil (AS15704)** is in OONI's set of networks showing match-correlated blocking, with coverage equal to Orange.

For reference, OONI observed match-correlated blocking on a broader set: Telefónica (AS3352), MásMóvil (AS15704), Orange Espagne (AS12479), Vodafone España (AS12430), Mas Orange (AS12334), Vodafone ONI (AS6739) and Euskaltel (AS12338), plus dedicated charts for DigiMobil (AS57269) and RedIRIS (AS766).

Cross-referenced with our probe counts:

| AS | Operator | Probes | In OONI's set | In scope? |
|---|---|---|---|---|
| 3352 | Telefónica | 72 | yes | Yes |
| 57269 | DIGI | 35 | yes | Yes |
| 12479 | Orange | 15 | yes | Yes |
| 15704 | MásMóvil | 15 | yes | Yes |
| 12430 | Vodafone | 7-9 (fluctuates) | yes | Yes - sets n for all, with margin |
| 766 | RedIRIS | 5 | yes | No - academic network |
| 12338 | Euskaltel | 3 | yes | No - below n |
| 6739 | Vodafone ONI | 1 | yes | No - below n |
| 12334 | Mas Orange | 1 | yes | No - below n |

The bottom four appear in OONI's data but cannot support an equal-n design. Worth revisiting if their coverage grows.

---

## Control group

Blocking is only meaningful relative to a baseline. Every campaign should include probes **outside Spain** measuring the same targets at the same time - the same design OONI used with a Frankfurt control point.

A target unreachable from Spain *and* from the controls is simply down. A target unreachable from Spain only is a blocking candidate. Without the control, those two cases are indistinguishable.

---

## What the blocking actually hits

The other half of the design question: having chosen where to measure *from*, what should we measure *towards*? OONI publishes the full list of affected addresses, so this is answerable from data rather than guesswork. Computed from their CSV (September 2026, 7,374 addresses across 33 ASNs):

| Provider | AS | Affected addresses | Share |
|---|---|---|---|
| Amazon AWS | 16509 | 4,286 | 58.1% |
| Cloudflare | 13335 | 2,215 | 30.0% |
| Amazon AWS | 14618 | 811 | 11.0% |
| *30 other ASNs* | - | 62 | 0.8% |

Two observations follow, both relevant to target selection.

**Two providers hold 99.2% of every affected address, and by address count Amazon is the larger half**, not Cloudflare.

> ⚠️ This is not a correction of OONI, and must not be written up as one. OONI foregrounds Cloudflare because it counts affected *sites*: one Cloudflare anycast address fronts a very large number of unrelated sites, so blocking it does far more damage than blocking an AWS address serving few. Counting addresses and counting sites answer different questions - say which one you are counting.

**The blocking is overwhelmingly range-level, not address-level.** Grouping the affected addresses by /24, **86% of them sit in a /24 that holds at least eight other affected addresses** — 88.8% of Amazon's and 82.4% of Cloudflare's. Whole ranges are being swept rather than individual addresses picked out, which makes the collateral damage a direct consequence of the mechanism rather than an unlucky side effect of it.

Worth recording what is *absent*, since it was checked: Google (AS15169), Fastly (AS54113) and Akamai's AS16625 contribute no affected addresses at all. Akamai's AS20940 contributes 4 and Microsoft 2 — trace amounts in the tail, not categories of their own.

`select_targets.py` samples across these strata deliberately **non**-proportionally, over-weighting Cloudflare and the small-provider tail. The reasoning, and the alternative, are documented at the top of that script; whichever choice a write-up rests on has to be stated, because per-stratum figures mean different things under each.

```bash
python3 campaigns/campaign-match/select_targets.py --verify
```

---

## A known ground truth for validation

OONI's charts use the Cloudflare IP **188.114.97.5** as a worked example: most Spanish ISPs block it shortly before kick-off and lift the block soon after the match.

That makes it a validation target - a case where we roughly know what the answer should look like, so we can confirm the pipeline produces it before trusting the pipeline on unknown IPs. `select_targets.py` pins it into every sample for that reason.

Note that OONI established this with TLS measurements, not ping. A ping-only campaign might not reproduce it at all — see [page 8](08-pitfalls.md), pitfall 3.

---

## Reproducing this

```bash
python3 campaigns/probe_profile/probe_profile.py
```

Outputs the per-ISP breakdown and a CSV with every probe and its classification. Note that RIPE also publishes an [official coverage page](https://atlas.ripe.net/statistics/coverage) with a world map and top-ASN breakdown - check that first for general "where are the probes" questions. Our script exists for the per-target-ISP breakdown it does not provide.

---

## Sources

- *Probe tags* (system tag categories - confirms no residential/datacentre tag) - <https://atlas.ripe.net/docs/getting-started/probe-tags.html>
- *Listing probes* (API filters used) - <https://atlas.ripe.net/docs/apis/rest-api-manual/probes/listing-probes/>
- *RIPE Atlas coverage statistics* - <https://atlas.ripe.net/statistics/coverage>
- OONI, *Collateral Damage of IP-Based Blocking During LALIGA Football Streaming in Spain* (June 2026) - the ISP list, the TLS MitM observation on AS57269, the control-vantage-point design, and the 188.114.97.5 example - <https://ooni.org/post/2026-laliga-collateral/>
- OONI's published list of affected IP addresses - the source for the provider breakdown and the /24 concentration figures above, both computed by `select_targets.py` - <https://ooni.org/post/2026-laliga-collateral/data/20260629-all-affected-ips.csv>
- CyberInsider coverage of the OONI report (confirms the report does not attribute responsibility for the TLS interception) - <https://cyberinsider.com/ooni-laliga-piracy-blocks-disrupted-over-500000-legitimate-sites/>
- AS ownership cross-checked via RIPE WHOIS and Cloudflare Radar (AS57269 = DIGI Spain Telecom; AS15704 = Xtra Telecom / MásMóvil; AS16509 and AS14618 = Amazon; AS13335 = Cloudflare)
- Bajpai et al., *Lessons Learned From Using the RIPE Atlas Platform for Measurement Research* (SIGCOMM CCR 2015) - the AS-distribution skew - <https://dl.acm.org/doi/10.1145/2805789.2805796>
- Our own probe profiling run (`probe_profile_es.csv`) - the coverage figures are empirical, not published by RIPE