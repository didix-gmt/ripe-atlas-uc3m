# State of the Art - Measuring IP/DNS Blocking with RIPE Atlas

*Literature review for the internship project: measuring La Liga-triggered IP blocking by Spanish ISPs.*
*Draft v1 - July 2026*

---

## 1. Scope and method

This review covers the main recent work on (a) measuring anti-piracy IP/DNS blocking and its collateral damage, and (b) using RIPE Atlas as a measurement platform for blocking/censorship research. Papers were selected from the citation trail suggested by the supervisor, complemented with recent (2024-2026) publications found through direct search - including two studies published after the citation trail was compiled, both directly relevant to our topic.

For each work, the following is summarised: objective, methodology, key results, limitations, and what our project can take from it.

---

## 2. Directly relevant work: anti-piracy blocking measurement

### 2.1 OONI - Collateral Damage of IP-Based Blocking During LALIGA Football Streaming in Spain (June 2026)

**The closest existing work to our project - same country, same blocking campaign, published June 30, 2026.**

- **Objective**: quantify the collateral damage of La Liga's court-authorised IP blocking campaign in Spain.
- **Methodology**: OONI network measurements collected from volunteer devices in Spain (January–June 2026), combined with DNS scans covering 9.2 million popular domains. Blocking events are correlated with match broadcast windows, and affected domains are mapped to the blocked IPs they resolve to.
- **Key results**:
  - 554,507 unique domains (~5.8% of the 9.2M tested) blocked at least once during match broadcasts;
  - 7,441 unique IP addresses affected, across 36 infrastructure providers;
  - extreme concentration on shared infrastructure: over 501,000 of the affected domains sat behind just 2,218 blocked Cloudflare IPs;
  - blocking as few as 4–20 IPs during a one-hour match window was enough to disrupt 400,000+ unrelated domains;
  - per-ISP behaviour differs: Vodafone España (AS12430) blocks at irregular intervals, Mas Movil (AS15704) on an almost weekly cadence - each event still fully disrupting 400,000+ domains;
  - beyond blocking, TLS man-in-the-middle interception was detected on one ISP (Digi Mobil, AS57269), affecting 7,334 addresses and 10,759 domains.
- **Limitations (acknowledged by the authors)**: incomplete visibility into all blocked IPs/domains (measurements depend on volunteer probes being active during matches); estimates are described as conservative.
- **What we take from it**: the reference baseline for our measurements. OONI relies on *volunteer* devices running their app - coverage during a specific match is not guaranteed. Our RIPE Atlas approach offers controlled, schedulable vantage points, which addresses precisely this limitation. Their per-ISP breakdown (by ASN) is a template for how to present our own results.
- **Source**: <https://ooni.org/post/2026-laliga-collateral/>

### 2.2 Sommese et al. - "90th Minute": the Italian Piracy Shield (CNSM 2025)

**The methodological reference for our project - same blocking mechanism, applied in Italy.**

- **Objective**: first data-driven investigation of Italy's Piracy Shield platform - its efficacy against piracy and its collateral damage.
- **Methodology**: the blocked-resource list is not public, so the authors *reconstructed* the blocking activity from partial sources (redacted ISP ticket lists, community reports), then actively measured the reconstructed set: checking blocked domains one by one for active websites, and classifying their content. Study window: February 2024 – June 2025 (3,782 blocking tickets).
- **Key results**:
  - as of June 2025: 10,918 IPv4 addresses and 18,849 domains blocked;
  - collateral damage measured on 6,712 fully-blocked and 402 partially-affected domains;
  - 500+ confirmed non-streaming websites blocked, growing into the thousands over time;
  - notable incident: an October 2024 blocking request took Google Drive offline in Italy for several hours (with effects persisting due to DNS caching);
  - effectiveness is limited: pirates evade via IP rotation and IPv6, while static legitimate services stay blocked.
- **Limitations**: no public ground truth for the block list - the reconstruction step introduces uncertainty; no real-time during-match measurements at scale.
- **What we take from it**: (1) the same ground-truth problem exists in Spain (La Liga's lists are not public and there is no appeal mechanism), so their reconstruction approach is directly reusable; (2) their classification pipeline for collateral domains (active site? what content?) is a template; (3) the paper's framing - efficacy *versus* collateral damage - is the right way to present results to a non-technical audience.
- **Sources**: paper DOI <https://doi.org/10.23919/CNSM67658.2025.11297497>; summary on RIPE Labs <https://labs.ripe.net/author/antonio-prado/live-event-blocking-at-scale-effectiveness-vs-collateral-damage-in-italys-piracy-shield/>; APNIC blog <https://blog.apnic.net/2025/10/17/an-italian-case-study-collateral-damage-from-live-event-site-blocking-with-piracy-shield/>

### 2.3 Comparative note: Spain vs Italy

Both campaigns block shared infrastructure IPs under time pressure (Italy: 30-minute legal requirement; Spain: dynamic injunctions updated in real time without per-block judicial review). Both produce the same failure mode: massive overblocking of CDN-hosted legitimate services, while pirates evade through IP rotation ("whack-a-mole"). Spain's campaign has additionally expanded to VPN providers (court orders against NordVPN and Proton VPN, February 2026). A policy analysis explicitly framing Spain as repeating Italy's mistakes: <https://project-disco.org/european-union/repeating-failure-how-spanish-overblocking-ignores-the-lessons-of-italys-broken-piracy-shield/>

---

## 3. Foundations: RIPE Atlas as a censorship/blocking measurement platform

### 3.1 Anderson et al. - Global Network Interference Detection Over the RIPE Atlas Network (USENIX FOCI 2014)

- **Objective**: propose RIPE Atlas as a censorship measurement platform, addressing the poor adoption, insufficient geographic coverage and scalability problems of dedicated censorship platforms.
- **Methodology**: an algorithm for monitoring reachability of vital services balancing timeliness, diversity and cost; applied to real blocking events in Turkey and Russia.
- **Key results**: identified under-examined forms of interference; provided evidence of cooperation between a blogging platform and government authorities for content blocking.
- **What we take from it**: the founding argument for our approach - using an existing, widely-deployed general-purpose platform instead of a dedicated censorship-measurement network. The probe-selection algorithm (balancing timeliness/diversity/cost) anticipates our credit-budget constraints.
- **Source**: <https://www.usenix.org/conference/foci14/workshop-program/presentation/anderson> (open access)

### 3.2 Bajpai et al. - Lessons Learned From Using the RIPE Atlas Platform (ACM SIGCOMM CCR 2015)

- **Objective**: reflect on practical experience using RIPE Atlas for measurement research.
- **Key findings relevant to us**:
  - the AS-based distribution of probes is heavily skewed - this limits measurements sourced from a *specific* origin AS, which matters for us since we want per-ISP measurements (Movistar AS3352, Orange ES AS12479, Vodafone ES AS12430);
  - probe calibration matters: older hardware probe versions showed measurable load-induced latency artefacts (first-hop latencies up to 6 ms when busy);
  - rate limits and credit controls shape what campaigns are feasible.
- **A follow-up (2017) additionally showed** that 91% of probes are located in the RIPE and ARIN regions - relevant when we select non-European vantage points for the "is the block Spain-only?" comparison.
- **What we take from it**: before designing the final campaign, check *how many probes actually exist in each Spanish ISP's AS* - the skew means some ISPs may have very few. This is a concrete pre-study to run (via the probe API, filters `country_code=ES&asn_v4=...`).
- **Source**: <https://dl.acm.org/doi/10.1145/2805789.2805796>; author PDF: <https://vaibhavbajpai.com/documents/papers/proceedings/ripeatlas-ccr-2015.pdf>

### 3.3 Holterbach et al. - Quantifying Interference between Measurements on RIPE Atlas (IMC 2015)

- **Objective**: measure whether concurrent measurements on the same probe distort results.
- **Key results**: concurrent measurements on one probe can add milliseconds of delay; measurements on different probes can desynchronise even when launched together.
- **What we take from it**: a methodological caution for our latency-sensitive measurements - probes are shared, and a busy probe can bias RTTs. For blocking detection (binary reachable/not-reachable) this matters less, but for any latency-based analysis we should account for it.
- **Source**: <https://dl.acm.org/doi/10.1145/2815675.2815710>

### 3.4 "Day in the Life of RIPE Atlas" (2024/2025)

- **Objective**: a current operational picture of the platform - one full day of data: 50,900 measurements, 1.3 billion results.
- **Key facts for us**: probes in 178 countries; strong bias towards Europe and North America (Germany + US alone host 28% of probes/anchors; 32 countries have a single probe); platform limits: max 100 concurrent measurements, 1,000 probes per measurement, 1M credits/day, with special requests to exceed quotas handled case by case.
- **What we take from it**: the up-to-date reference for platform capabilities and constraints when designing the final campaign; also documents that quota-extension requests for research are a normal, supported path.
- **Source**: <https://arxiv.org/abs/2511.22474>

---

## 4. Context: surveys of censorship measurement

Two recent surveys give the broader landscape and are useful for the report's related-work section:

- **A Survey of Internet Censorship and its Measurement** (Wendzel et al., 2025, arXiv:2502.14945) - the most up-to-date methodological overview, covering 2025 publications and novel trends including regional censorship. Useful for positioning: IP blocking on shared infrastructure and the resulting overblocking are explicitly discussed as an open problem. <https://arxiv.org/abs/2502.14945>
- **A review of internet censorship: Modern measurement and circumvention techniques** (2026, ScienceDirect) - synthesises 146 measurement/circumvention studies (2015-2025), classified by protocol, country, duration, method. Useful as a citation index. <https://www.sciencedirect.com/science/article/pii/S1574013726001103>

---

## 5. The gap our project addresses

Putting the above together:

1. **OONI measures Spain, but from uncontrolled volunteer devices** - coverage during a *specific* match window is not guaranteed, and the authors acknowledge their numbers are conservative for this reason.
2. **The Italian study reconstructs blocking after the fact** - it does not measure in real time during matches.
3. **RIPE Atlas offers controlled, schedulable vantage points** inside Spanish ISPs *and* abroad - but no published work has yet applied it systematically to the La Liga campaign.

Our project's contribution is therefore: **real-time, match-synchronised measurements of La Liga blocking, from controlled RIPE Atlas vantage points inside multiple Spanish ISPs, with simultaneous out-of-country baselines** - combining the geographic comparison capability (is the block Spain-only?) with temporal precision (exactly when do blocks start and stop relative to the match?) that neither existing study provides.

Known constraints to design around (from sections 3.2 and 3.4): probe availability per Spanish ISP AS must be verified first; credit budget and the 100-concurrent-measurement quota shape the campaign size; a quota-extension request to atlas@ripe.net is a documented option for research projects.

---

## 6. Reading list (priority order)

| # | Work | Year | Why |
|---|------|------|-----|
| 1 | OONI - LALIGA Collateral Damage | 2026 | Same topic, same country, published last week |
| 2 | Sommese et al. - 90th Minute (Piracy Shield) | 2025 | Methodological template, Italian twin case |
| 3 | Anderson et al. - FOCI 2014 | 2014 | Founding paper for RIPE Atlas censorship measurement |
| 4 | Bajpai et al. - Lessons Learned (CCR) | 2015 | Platform biases and pitfalls |
| 5 | Day in the Life of RIPE Atlas | 2025 | Current platform capabilities and quotas |
| 6 | Holterbach et al. - Measurement interference | 2015 | Caution for latency-based analysis |
| 7 | Wendzel et al. - Censorship survey | 2025 | Broader related-work positioning |

---

*All claims in this document are sourced inline. Numbers were taken from the cited primary sources or their official summaries (RIPE Labs, APNIC blog, OONI report page) - not from secondary press coverage, except where the primary source is paywalled and the figure was cross-checked across at least two independent outlets.*
