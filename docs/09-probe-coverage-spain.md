---
layout: default
title: "Probe coverage in Spain"
nav_order: 10
---

# 9. Probe coverage in Spain

Before designing a campaign, you need to know what you can actually measure. This page documents how many usable vantage points exist inside each Spanish ISP, how that number was obtained, and what it means for the study design.

The short version: coverage is uneven. Two operators support solid statistical claims, three support weaker ones, and that asymmetry has to be stated in any result we publish rather than hidden behind an average.

---

## Why residential probes specifically

The La Liga injunctions require ISPs to block for their **consumer subscribers**. A probe sitting in a university network, a hosting provider or a corporate line may carry the same AS number as a home connection while sitting on a completely different side of the filter.

Measuring only from such probes risks a **false negative**: concluding "no blocking" when we were simply looking from the wrong place. This is the mirror image of the TLS false-positive problem described on [page 8](08-pitfalls.md), and just as damaging.

---

## The problem: RIPE Atlas has no residential tag

There is no system tag for "residential" or "datacentre". The official system tag categories cover only protocol capability, basic connectivity, stability, DNS resolution, and probe metadata (version, software, anchor, virtual, geolocation).

So classification has to be inferred. We combine three signals, checked strongest first:

| Signal | Source | Reliability |
|---|---|---|
| `is_anchor` / `system-anchor` / `system-virtual` | System | Certain - infrastructure by definition |
| Host location tags (`home`, `office`, `datacentre`, `academic`…) | User, voluntary | Reliable when present, absent for most probes |
| `system-ipv4-rfc1918` (private address → behind NAT) | System | Soft - homes almost always NAT, but so do offices |

### One trap worth knowing about

An earlier version of our script treated **connection-technology tags** (`fibre`, `ftth`, `dsl`, `cable`, `nat`) as residential markers. They are not: they describe *how* a probe connects, not *where* it sits. An office with fibre is still an office.

The consequence was concrete - every probe tagged `fibre` + `office` was flagged as a contradiction instead of being correctly classified as infrastructure, and probes tagged `fibre` alone were counted as homes. Fixing it doubled the infrastructure count (19 → 41) and cut unresolvable conflicts from 25 to 2.

The current script keeps `CONNECTION_TECH` as an explicit, unused set, so that it is obvious those tags were considered and deliberately excluded.

---

## Results

Measured on connected probes in Spain (`country_code=ES&status=1`), 259 probes at time of writing:

| ISP | AS | Declared residential | Inferred (NAT only) | Total residential |
|---|---|---|---|---|
| Telefónica / Movistar | 3352 | 16 | 44 | 60 |
| DIGI Spain | 57269 | 8 | 25 | 33 |
| Orange Espagne | 12479 | 5 | 10 | 15 |
| MásMóvil (Xtra Telecom) | 15704 | 4 | 10 | 14 |
| Vodafone España | 12430 | 3 | 6 | 9 |

**Read this as a range, not a number.** "Declared" is the defensible floor - the host explicitly tagged the probe. "Inferred" rests on the NAT signal alone, which is genuinely soft. Across the five ISPs that gives roughly **36 certain** residential probes and **131 optimistic**.

Nationwide: 189 of 259 probes classified residential (73%), but 144 of those 189 come from the soft NAT inference. Only about 45 are declared. That ratio is worth keeping in mind before quoting the 73% figure anywhere.

One reassuring detail: the declaration rate is fairly consistent across operators (24–33%), which suggests hosts tag their probes similarly everywhere, so the NAT inference is probably not biased toward one ISP. With only 3–4 declared probes on some operators, though, that ratio is too small to be conclusive.

---

## Which ISPs to target

We started with the three obvious consumer ISPs (Movistar, Orange, Vodafone). The coverage data says that list should be **five**.

**DIGI (AS57269)** has the second-best probe coverage in Spain - more residential probes than Orange and Vodafone combined. It also has its own dedicated analysis in the OONI report, including an observation that matters: OONI recorded TLS man-in-the-middle activity affecting 7,334 unique IPs across 14 ASNs, hosting 10,759 domain names, on measurements collected from this network.

> **Wording matters here.** OONI observed this **on** DIGI's network; the report explicitly does not attribute responsibility for the interception. Any write-up should say "observed on", never "performed by". We are documenting a measurement, not making an accusation.

**MásMóvil (AS15704)** is listed by OONI among the networks where blocking correlates with match windows, and has residential coverage comparable to Orange.

For reference, the full set of networks where OONI observed match-correlated blocking is broader than five: Telefónica (AS3352), MásMóvil (AS15704), Orange Espagne (AS12479), Vodafone España (AS12430), Mas Orange (AS12334), Vodafone ONI (AS6739) and Euskaltel (AS12338), plus dedicated charts for DigiMobil (AS57269) and RedIRIS (AS766).

Cross-referencing that list with our probe counts:

| AS | Operator | Residential probes | In OONI's set | Usable for us? |
|---|---|---|---|---|
| 3352 | Telefónica | 60 | yes | Yes - statistical claims |
| 57269 | DIGI | 33 | yes | Yes - statistical claims |
| 12479 | Orange | 15 | yes | Indicative |
| 15704 | MásMóvil | 14 | yes | Indicative |
| 12430 | Vodafone | 9 | yes | Case study only |
| 766 | RedIRIS | 2 | yes | No - academic network anyway |
| 12338 | Euskaltel | 2 | yes | No - too few |
| 6739 | Vodafone ONI | 1 | yes | No - too few |
| 12334 | Mas Orange | 1 | yes | No - too few |

The bottom four are in OONI's set but have too few probes to support anything. Worth revisiting if their coverage grows.

---

## Handling the Vodafone problem

Nine probes, three of them confidently residential. If two disconnect during a match - which happens routinely - the result rests on a handful of vantage points.

We are not adding probes, so the approach is to **calibrate the claims to the coverage**:

- **Telefónica and DIGI** - enough probes for statistical claims about blocking prevalence and timing.
- **Orange and MásMóvil** - indicative; report trends, avoid precise percentages.
- **Vodafone** - treat as a case study. State the limitation explicitly rather than presenting it alongside the others as if equivalent.

Two things partly compensate:

**Trade spatial coverage for temporal resolution.** Fewer probes means fewer results per round, which means each round costs fewer credits, which means we can sample far more frequently. With nine probes at a one-minute interval we can pin down *when* a block starts and stops on Vodafone quite precisely. What we cannot do is map variation *across* Vodafone's network. Separating those two questions explicitly in the write-up resolves most of the problem.

**Cross-check against OONI.** Their Vodafone data comes from volunteer devices - a completely different sampling method with different biases. Agreement between two independent methods is stronger evidence than either alone, and it costs nothing.

---

## A known ground truth for validation

OONI's charts use the IP **188.114.97.5** (Cloudflare) as a worked example: most Spanish ISPs block it shortly before kick-off and lift the block soon after the match.

That makes it a useful validation target - a case where we know roughly what the answer should look like, so we can check the pipeline produces it before trusting the pipeline on unknown IPs.

---

## Reproducing this

```bash
python3 campaigns/probe-profile/probe_profile.py
```

Outputs a per-ISP breakdown and a full CSV with the classification reason for every probe. Re-run it before designing any campaign: probe populations change, and a count from three months ago is not a count from today.

Note that RIPE also publishes an official coverage page with a world map and top-ASN breakdown - worth checking before building anything custom, since it covers the general "where are the probes" question well. Our script exists for the specific question it doesn't answer: residential versus infrastructure, per target ISP, side by side.

---

## Sources

- *Probe tags* (system tag categories - confirms no residential/datacentre tag) - <https://atlas.ripe.net/docs/getting-started/probe-tags.html>
- *Listing probes* (API filters used) - <https://atlas.ripe.net/docs/apis/rest-api-manual/probes/listing-probes/>
- *RIPE Atlas coverage statistics* (official map and ASN breakdown) - <https://atlas.ripe.net/statistics/coverage>
- OONI, *Collateral Damage of IP-Based Blocking During LALIGA Football Streaming in Spain* (June 2026) - source for the ISP list, the TLS MitM observation on AS57269, and the 188.114.97.5 example - <https://ooni.org/post/2026-laliga-collateral/>
- CyberInsider coverage of the OONI report (confirms the report does not attribute responsibility for the TLS interception) - <https://cyberinsider.com/ooni-laliga-piracy-blocks-disrupted-over-500000-legitimate-sites/>
- AS ownership cross-checked via RIPE WHOIS and Cloudflare Radar (AS57269 = DIGI Spain Telecom; AS15704 = Xtra Telecom / MásMóvil)
- Bajpai et al., *Lessons Learned From Using the RIPE Atlas Platform for Measurement Research* (SIGCOMM CCR 2015) - the AS-distribution skew this page quantifies for Spain - <https://dl.acm.org/doi/10.1145/2805789.2805796>
- Our own probe profiling run (`probe_profile_es.csv`) - the coverage figures above are empirical, not published by RIPE