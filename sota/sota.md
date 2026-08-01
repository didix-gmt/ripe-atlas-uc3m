# State of the Art - Measuring IP/DNS Blocking with RIPE Atlas

*Literature review for the internship project: measuring La Liga-triggered IP blocking by Spanish ISPs.*
*Draft v2 - July 2026*

---

## 1. Scope and method

This review covers recent work on (a) measuring anti-piracy IP/DNS blocking and its collateral damage, and (b) using RIPE Atlas as a measurement platform for blocking and censorship research.

Sources were selected from the citation trail suggested by the supervisor, complemented by direct search for 2024–2026 publications - including two studies that post-date that citation trail and are the closest existing work to our topic.

For each work: objective, methodology, key results, limitations, and what our project takes from it.

> **On sourcing.** Every figure below was taken from the primary source or its official summary. Where a figure appears in press coverage only, it was cross-checked across at least two independent outlets before inclusion. Claims about named companies are worded to match exactly what the source states - see the note in §2.1 on the TLS interception finding.

---

## 2. Directly relevant work: anti-piracy blocking measurement

### 2.1 OONI - Collateral Damage of IP-Based Blocking During LALIGA Football Streaming in Spain (June 2026)

**The closest existing work to this project: same country, same blocking campaign, published June 2026.**

**Objective.** Quantify the collateral damage of La Liga's court-authorised IP blocking campaign in Spain.

**Methodology.** Two data sources combined:
- OONI network measurements collected in Spain, January–June 2026, from volunteer devices running OONI Probe;
- a ZDNS scan against a target list of 9.2 million domain names, assembled from the Cloudflare Radar top 1M, the Tranco top 1M, Citizen Lab test lists, the Majestic Million, and Certificate Transparency logs. The list was resolved four times a day from a vantage point in Spain and from a control vantage point outside Spain (Frankfurt) to allow comparison.

An IP is classified as blocked when it shows a high failure rate from within Spain while responding normally from the control point. Because OONI measurements predate the DNS scanning campaign (which began 4 May 2026), the earliest available scan is used to estimate domain impact for earlier measurements.

**Key results.**

| Finding | Figure |
|---|---|
| Domains affected at least once during broadcasts | 554,507 (≈5.8% of the 9.2M tested) |
| Unique IP addresses affected | 7,441, across 36 ASNs |
| Concentration on Cloudflare (AS13335) | 501,305 domains - 90.4% of the total - sitting on just 2,218 IPs |
| Impact of a single one-hour window | Blocking 4–20 IPs was enough to disrupt over 400,000 unrelated domains |
| Squarespace, as an extreme case | 18,592 domains behind a single address |
| Amazon, opposite pattern | 11,647 domains spread over 4,286 IPs |

Affected organisations span human rights groups, environmental organisations, government institutions, news media, humanitarian organisations and messaging platforms - Amnesty International, Greenpeace, Harvard University and the University of Washington among those named.

**Per-ISP behaviour.** Blocking timing correlates with match broadcasts, beginning shortly before kick-off and lifting shortly after the final whistle, on Telefónica de España (AS3352), MásMóvil / Xtra Telecom (AS15704), Orange Espagne (AS12479), Vodafone España (AS12430), Mas Orange (AS12334), Vodafone ONI (AS6739) and Euskaltel (AS12338). Blocking is largely confined to those windows, with minimal spillover outside broadcast periods.

Telefónica is identified as one of the most consistently compliant operators, showing enforcement on almost every match weekend from January to June 2026, with 144 measurement windows exceeding 400,000 blocked domains.

**A separate finding: TLS interception observed on AS57269.** OONI data collected from Digi Mobil (AS57269) shows 7,334 unique IPs across 14 ASNs, hosting 10,759 domain names, affected by TLS man-in-the-middle activity. The affected IPs are concentrated on AWS, then Cloudflare and Alibaba Cloud.

> ⚠️ **Wording matters.** OONI reports this as observed **on** that network and explicitly does **not** attribute responsibility for the interception. Any write-up must say "observed on", never "performed by". This is a measurement finding, not an attribution.

**Limitations acknowledged by the authors.** Incomplete visibility into all blocked IPs and domains - measurements depend on volunteers being active during a given match. OONI describes its estimates as conservative and likely understating the true scale.

**What we take from it.** This is our reference baseline and the closest prior art. The critical methodological gap: OONI's coverage during any *specific* match window is not guaranteed, because it depends on volunteer devices happening to be running. RIPE Atlas gives controlled, schedulable vantage points - which addresses precisely that limitation. Their per-ASN breakdown is also a good template for presenting our own results, and their control-vantage-point design (Spain vs Frankfurt) is directly reusable.

Source: <https://ooni.org/post/2026-laliga-collateral/>

### 2.2 Sommese et al. - "90th Minute": Italy's Piracy Shield (CNSM 2025)

**The methodological reference: same blocking mechanism, applied in Italy.**

**Objective.** First data-driven investigation of Italy's Piracy Shield platform - both its efficacy against piracy and its collateral damage.

**Methodology.** The blocked-resource list is not public, so the authors *reconstructed* blocking activity from partial sources (redacted ISP ticket lists, community reports), then actively measured the reconstructed set: checking each blocked domain for an active website and classifying its content. Study window: February 2024 – June 2025, covering 3,782 blocking tickets.

**Key results.**
- As of June 2025: 10,918 IPv4 addresses and 18,849 domains blocked.
- Collateral damage measured on 6,712 fully-blocked and 402 partially-affected domains.
- Over 500 confirmed non-streaming websites blocked, growing into the thousands over the study period.
- An October 2024 blocking request took Google Drive offline in Italy for several hours, with effects persisting due to DNS caching.
- Effectiveness is limited: pirates evade via IP rotation and IPv6, while static legitimate services stay blocked.

**Limitations.** No public ground truth for the block list - the reconstruction step introduces uncertainty. No real-time during-match measurement at scale.

**What we take from it.** Three things. First, the same ground-truth problem exists in Spain: La Liga's lists are not public and there is no per-block appeal mechanism, so their reconstruction approach is directly transferable. Second, their classification pipeline for collateral domains (is the site active? what content?) is a usable template. Third, the framing - efficacy *versus* collateral damage - is the right way to present findings to a non-technical audience.

Sources: DOI <https://doi.org/10.23919/CNSM67658.2025.11297497>; RIPE Labs summary <https://labs.ripe.net/author/antonio-prado/live-event-blocking-at-scale-effectiveness-vs-collateral-damage-in-italys-piracy-shield/>; APNIC blog <https://blog.apnic.net/2025/10/17/an-italian-case-study-collateral-damage-from-live-event-site-blocking-with-piracy-shield/>

### 2.3 Comparative note: Spain vs Italy

Both campaigns block shared-infrastructure IPs under time pressure - Italy under a 30-minute legal requirement, Spain under dynamic injunctions updated in real time without per-block judicial review. Both produce the same failure mode: large-scale overblocking of CDN-hosted legitimate services while pirates evade through IP rotation.

Spain's campaign has since extended beyond ISPs: in February 2026, court orders required NordVPN and Proton VPN to block access from Spain to 16 streaming sites.

A policy analysis framing Spain as repeating Italy's mistakes: <https://project-disco.org/european-union/repeating-failure-how-spanish-overblocking-ignores-the-lessons-of-italys-broken-piracy-shield/>

---

## 3. Foundations: RIPE Atlas as a blocking-measurement platform

### 3.1 Anderson et al. - Global Network Interference Detection Over the RIPE Atlas Network (USENIX FOCI 2014)

**Objective.** Propose RIPE Atlas as a censorship measurement platform, addressing the adoption, geographic coverage and scalability problems of dedicated censorship-measurement networks.

**Methodology.** An algorithm for monitoring reachability of vital services, balancing timeliness, diversity and cost; applied to real blocking events in Turkey and Russia.

**Key results.** Identified under-examined forms of interference, and found evidence of cooperation between a blogging platform and government authorities for content blocking.

**What we take from it.** The founding argument for our approach: use an existing, widely deployed general-purpose platform rather than building a dedicated censorship-measurement network. Their probe-selection algorithm - explicitly balancing timeliness against cost - anticipates the credit-budget constraint we face.

Source (open access): <https://www.usenix.org/conference/foci14/workshop-program/presentation/anderson>

### 3.2 Bajpai et al. - Lessons Learned From Using the RIPE Atlas Platform (ACM SIGCOMM CCR 2015)

**Objective.** Reflect on practical experience using RIPE Atlas for measurement research.

**Findings relevant to us.**
- The AS-based distribution of probes is heavily skewed, which constrains measurements sourced from a *specific* origin AS. This matters directly: we want per-ISP measurements inside named Spanish operators.
- Probe calibration matters: older hardware probe versions showed load-induced latency artefacts, with first-hop latencies up to 6 ms when busy.
- Rate limits and credit controls shape what campaigns are feasible.
- A 2017 follow-up found 91% of probes located in the RIPE and ARIN regions - relevant when selecting non-European vantage points for the "is this block Spain-only?" comparison.

**What we take from it.** This paper is the reason we ran a probe-coverage pre-study before designing anything. The results are documented on page 9 of our guide: coverage inside Spanish ISPs ranges from 60 residential probes (Telefónica) down to 9 (Vodafone), which directly determines what can be claimed per operator.

Source: <https://dl.acm.org/doi/10.1145/2805789.2805796>; author PDF: <https://vaibhavbajpai.com/documents/papers/proceedings/ripeatlas-ccr-2015.pdf>

### 3.3 Holterbach et al. - Quantifying Interference between Measurements on RIPE Atlas (IMC 2015)

**Objective.** Determine whether concurrent measurements on the same probe distort results.

**Key results.** Concurrent measurements on one probe can add milliseconds of delay, and measurements on different probes can desynchronise even when launched together.

**What we take from it.** A caution for any latency-based analysis: probes are shared, and a busy probe biases RTT. For binary blocking detection (reachable / not reachable) this matters less, but it constrains what we can conclude from timing data - relevant given that precise block start/stop timing is one of our intended contributions.

Source: <https://dl.acm.org/doi/10.1145/2815675.2815710>

### 3.4 Day in the Life of RIPE Atlas (2025)

**Objective.** An operational snapshot of the platform: one full day of data - 50,900 measurements, 1.3 billion results.

**Facts we rely on.** Probes in 178 countries, with a strong bias toward Europe and North America (Germany and the US alone host 28% of probes and anchors; 32 countries have a single probe). Platform limits: 100 concurrent measurements, 1,000 probes per measurement, 1M credits/day, with quota-extension requests handled case by case. Six measurement types, with HTTP restricted to targeting anchors.

**What we take from it.** The current reference for platform capabilities when sizing the campaign. It also documents that quota extensions for research are a normal, supported path - relevant if the final campaign needs more than 100 concurrent measurements.

Source: <https://arxiv.org/abs/2511.22474>

---

## 4. Context: censorship measurement surveys

Two recent surveys give the broader landscape, useful for the report's related-work section:

- **A Survey of Internet Censorship and its Measurement** (Wendzel et al., 2025) - the most current methodological overview, covering 2025 publications and emerging trends including regional censorship. IP blocking on shared infrastructure and the resulting overblocking are explicitly discussed as an open problem. <https://arxiv.org/abs/2502.14945>
- **A review of internet censorship: modern measurement and circumvention techniques** (2026) - synthesises 146 measurement and circumvention studies from 2015–2025, classified by protocol, country, duration and method. Useful primarily as a citation index. <https://www.sciencedirect.com/science/article/pii/S1574013726001103>

---

## 5. The gap this project addresses

Bringing the above together:

1. **OONI measures Spain, but from uncontrolled volunteer devices.** Coverage during any specific match window is not guaranteed, and the authors state their figures are conservative for this reason.
2. **The Italian study reconstructs blocking after the fact.** It does not measure in real time during matches.
3. **RIPE Atlas offers controlled, schedulable vantage points** inside Spanish ISPs and abroad - but no published work has yet applied it systematically to the La Liga campaign.

**Our contribution**: real-time, match-synchronised measurement of La Liga blocking, from controlled RIPE Atlas vantage points inside multiple Spanish ISPs, with simultaneous out-of-country baselines. This combines the geographic comparison (is the block Spain-specific?) with the temporal precision (exactly when does a block start and stop relative to kick-off?) that neither existing study provides.

**Constraints to design around**, drawn from §3.2 and §3.4 and confirmed empirically:
- Probe availability per Spanish ISP is uneven - verified, see guide page 9.
- Credit budget and the 100-concurrent-measurement quota bound the campaign size.
- A quota-extension request to `atlas@ripe.net` is a documented option for research projects.
- Probe interference (§3.3) limits how far latency data can be pushed.

**A ready-made validation target.** OONI's charts use the Cloudflare IP `188.114.97.5` as a worked example: most Spanish ISPs block it shortly before kick-off and unblock it soon after. Reproducing that specific signal is a concrete way to validate our pipeline before trusting it on unknown IPs.

---

## 6. Reading list, priority order

| # | Work | Year | Why |
|---|------|------|-----|
| 1 | OONI - LALIGA Collateral Damage | 2026 | Same topic, same country, closest prior art |
| 2 | Sommese et al. - 90th Minute (Piracy Shield) | 2025 | Methodological template, Italian twin case |
| 3 | Anderson et al. - FOCI | 2014 | Founding paper for RIPE Atlas censorship measurement |
| 4 | Bajpai et al. - Lessons Learned (CCR) | 2015 | Platform biases; motivated our coverage pre-study |
| 5 | Day in the Life of RIPE Atlas | 2025 | Current platform capabilities and quotas |
| 6 | Holterbach et al. - Measurement interference | 2015 | Constrains latency-based conclusions |
| 7 | Wendzel et al. - Censorship survey | 2025 | Broader related-work positioning |

---

## 7. Open items

- Read the full PDFs of items 1 and 2 rather than the official summaries - the methodology sections in particular.
- Extend this review to blocking outside the sports-piracy context (country-level blocking of news outlets, for instance), per the supervisor's suggestion. The methodology transfers even though the legal basis differs.
- Check whether the Piracy Shield paper's reconstruction method can be adapted to Spain, given La Liga's lists are similarly unpublished.

---

*Figures in this document come from the cited primary sources or their official summaries. Where a figure appears only in press coverage, it was cross-checked across at least two independent outlets. Claims about named companies follow the source's own wording - in particular, the TLS interception finding in §2.1 is reported as observed on a network, not attributed to its operator.*