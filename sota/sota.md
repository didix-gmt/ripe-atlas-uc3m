# State of the Art - Measuring IP/DNS Blocking with RIPE Atlas

*Literature review for the internship project: measuring La Liga-triggered IP blocking by Spanish ISPs.*
*Draft v3 - August 2026*

---

## 1. Scope and method

This review covers recent work on (a) measuring anti-piracy IP/DNS blocking and its collateral damage, (b) blocking mandated for reasons other than piracy, as a methodological comparison, and (c) using RIPE Atlas as a measurement platform for blocking and censorship research.

Sources were selected from the citation trail suggested by the supervisor, complemented by direct search for 2024–2026 publications - including two studies that post-date that citation trail and are the closest existing work to our topic.

For each work: objective, methodology, key results, limitations, and what our project takes from it.

> **On sourcing.** Every figure below was taken from the primary source or its official summary. Where a figure appears in press coverage only, it was cross-checked across at least two independent outlets before inclusion. Claims about named companies are worded to match exactly what the source states - see the note in §2.1 on the TLS interception finding.

---

## 2. Anti-piracy blocking measurement

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

## 3. Blocking outside sports piracy: the EU media sanctions

Piracy is not the only mandate that produces ISP-level blocking in Europe. Comparing the two cases is useful because the *legal* basis differs completely while the *technical* mechanism and the measurement problem are nearly identical - which lets us separate what is specific to La Liga from what is generic to mandated blocking.

### 3.1 Müller et al. - Internet Sanctions on Russian Media (FOCI 2024)

**The methodological blueprint closest to what we want to build.** A collaboration between SIDN Labs, the University of Illinois Chicago, OONI, the University of Twente and the University of Amsterdam.

**Context.** From 1 March 2022, the EU sanctioned media outlets under Russian state control - initially Russia Today, its localised versions and Sputnik, with the list extended several times since. Although the wording targets "broadcasting", the sanctions also require ISPs in member states to block access to the associated websites. Crucially, enforcement is delegated to member states, and the Council decisions list *organisations*, not *domain names* - so each state or operator decides for itself which domains to block.

**Methodology.** Multi-source, and worth copying:
- **OONI** volunteer measurements for broad coverage over time;
- **RIPE Atlas** for custom DNS measurements from chosen vantage points, testing whether ISP resolvers return correct answers for sanctioned domains;
- **EduVPN** to observe blocking on university networks;
- **Dataplane.org and NLNOG RING** to observe blocking on data centre networks.

The focus is DNS-level blocking, the most common method in the EU: a resolver may return a landing-page IP instead of the real one, return an error, or return nothing.

On distinguishing real blocking from noise, they make the same point we hit in our own work: unstable connections can look like deliberate blocking. Their answer is to classify against **known block-page fingerprints**, using the public `ooni/blocking-fingerprints` repository plus fingerprints identified manually during the study.

**Key results.**
- Adoption was fast: one month after the sanctions, 54% of OONI vantage points that ever showed blocking of `www.rt.com` were already blocking it; three months later, 77%. Two vantage points in Poland showed blocking *two days before* the sanctions were published.
- Implementation is inconsistent between **and within** member states. `www.rt.com` is blocked at scale nearly everywhere except Sweden. For domains added later the picture fragments: `ntv.ru` is blocked in Croatia and Finland but not in the Netherlands. In Denmark, around 30% of DNS queries still returned a valid answer, indicating that some national ISPs do not block at all.
- Blocking lags domain changes badly. When `sputniknews.com` moved to `sputnikglobe.com` in April 2023, blocking of the new domain was still rarely observed five months later.
- **Mirror sites largely defeat the blocks** - and here Spain stands out: German and Austrian ISPs blocked at least some German-language RT mirrors (`rtd.xyz`, `rtde.tech`), while **Spanish ISPs did not block the Spanish mirrors** `esrt.online` and `esrt.press` at measurement time.
- University networks also block, at widely varying scales. Data centre networks showed little blocking, mostly because their vantage points used public resolvers.
- Transparency varies enormously. German ISPs largely returned NXDOMAIN, leaving users unaware a block existed. Others served block pages of varying detail - and notably, **some reused the block pages built for piracy blocking**, with no reference to sanctions.
- Circumvention is trivial: switching to a public resolver such as Google or Quad9 bypasses DNS-level blocks entirely.

**What we take from it.** More than any other paper in this review:

1. **The multi-vantage-point design is directly reusable.** Comparing ISP resolvers against public resolvers separates DNS-level blocking from IP-level blocking - a distinction we need, since La Liga blocking is IP-based and would survive a resolver change. Running both tells us *which* mechanism is in play.
2. **Block-page fingerprinting** is a concrete technique with a public dataset behind it. Our current pipeline classifies by failure mode (page 8 of the guide); fingerprints would let us go further and identify *who* is blocking and *how*.
3. **The reuse of piracy block pages for sanctions blocking** is direct evidence that the two regimes share technical infrastructure. That strengthens the case for treating them as one measurement problem.
4. **The Spanish ISPs' non-blocking of RT mirrors** is a useful counterpoint: the same operators that block aggressively during matches were lax on sanctions enforcement. Whatever drives La Liga compliance is not general diligence.

Paper (open PDF): <https://www.sidnlabs.nl/downloads/2AI9596Mj7gS5MzicOfOi7/df52d043b674b435868af238e69e58ef/foci_24_author_version_sidn.pdf>
Summary: <https://labs.ripe.net/author/moritz_muller/internet-sanctions-on-russian-media-diverging-actions-and-mixed-effects/>
Fingerprint dataset: <https://github.com/ooni/blocking-fingerprints>

### 3.2 ISD - Auditing the EU's ban of Russian state media, three years on (March 2026)

A follow-up audit by the Institute for Strategic Dialogue, also using RIPE Atlas DNS measurements. It confirms the FOCI findings persist years later: enforcement remains inconsistent across ISPs, with one measurement showing `sputnikglobe.com` blocked by only 1 of 18 ISPs while `rt.com` and `ria.ru` were blocked by 9 and 8 respectively.

The audit also identifies the structural cause: the European Commission sanctions named entities but publishes no list of their domain names, so when RT registers a new mirror it operates freely until someone notices and ISPs manually update their blocklists.

**What we take from it.** The parallel with La Liga is exact - in both cases the blocklist is not public, which is precisely why independent measurement is needed. It also demonstrates that RIPE Atlas DNS measurement is an accepted method for this class of audit, including by non-academic policy organisations.

Source: <https://www.isdglobal.org/digital-dispatch/investigation-holding-the-line-auditing-the-eus-ban-of-russian-state-media-3-years-on/>

### 3.3 What the comparison tells us

| | La Liga (Spain) | EU media sanctions |
|---|---|---|
| Legal basis | Court injunction, private rightsholder | EU Council regulation |
| Blocking method | Mainly IP-level | Mainly DNS-level |
| Duration | Minutes to hours, tied to match windows | Permanent |
| Blocklist public? | No | No (entities listed, domains not) |
| Circumvention | Hard (IP blocking survives resolver change) | Easy (change resolver) |
| Collateral damage | Massive, via shared CDN IPs | Limited, domain-scoped |
| Main enforcement failure | Overblocking | Underblocking, mirrors |

The two cases fail in opposite directions, and the reason is the blocking layer. DNS blocking is domain-scoped, so it under-blocks (mirrors escape) but rarely harms bystanders. IP blocking is address-scoped, so it catches mirrors on the same host but takes down every unrelated service sharing the address.

That contrast is worth making explicitly in the final report: **the collateral damage we measure is not incidental to IP blocking, it is intrinsic to choosing that layer.**

---

## 4. Foundations: RIPE Atlas as a blocking-measurement platform

### 4.1 Anderson et al. - Global Network Interference Detection Over the RIPE Atlas Network (USENIX FOCI 2014)

**Objective.** Propose RIPE Atlas as a censorship measurement platform, addressing the adoption, geographic coverage and scalability problems of dedicated censorship-measurement networks.

**Methodology.** An algorithm for monitoring reachability of vital services, balancing timeliness, diversity and cost; applied to real blocking events in Turkey and Russia.

**Key results.** Identified under-examined forms of interference, and found evidence of cooperation between a blogging platform and government authorities for content blocking.

**What we take from it.** The founding argument for our approach: use an existing, widely deployed general-purpose platform rather than building a dedicated censorship-measurement network. Their probe-selection algorithm - explicitly balancing timeliness against cost - anticipates the credit-budget constraint we face.

Source (open access): <https://www.usenix.org/conference/foci14/workshop-program/presentation/anderson>

### 4.2 Bajpai et al. - Lessons Learned From Using the RIPE Atlas Platform (ACM SIGCOMM CCR 2015)

**Objective.** Reflect on practical experience using RIPE Atlas for measurement research.

**Findings relevant to us.**
- The AS-based distribution of probes is heavily skewed, which constrains measurements sourced from a *specific* origin AS. This matters directly: we want per-ISP measurements inside named Spanish operators.
- Probe calibration matters: older hardware probe versions showed load-induced latency artefacts, with first-hop latencies up to 6 ms when busy.
- Rate limits and credit controls shape what campaigns are feasible.
- A 2017 follow-up found 91% of probes located in the RIPE and ARIN regions - relevant when selecting non-European vantage points for the "is this block Spain-only?" comparison.

**What we take from it.** This paper is the reason we ran a probe-coverage pre-study before designing anything. The results are on page 9 of our guide: coverage inside Spanish ISPs ranges from 72 probes (Telefónica) down to 9 (Vodafone), which directly determines the sampling design.

Source: <https://dl.acm.org/doi/10.1145/2805789.2805796>; author PDF: <https://vaibhavbajpai.com/documents/papers/proceedings/ripeatlas-ccr-2015.pdf>

### 4.3 Holterbach et al. - Quantifying Interference between Measurements on RIPE Atlas (IMC 2015)

**Objective.** Determine whether concurrent measurements on the same probe distort results.

**Key results.** Concurrent measurements on one probe can add milliseconds of delay, and measurements on different probes can desynchronise even when launched together.

**What we take from it.** A caution for any latency-based analysis: probes are shared, and a busy probe biases RTT. For binary blocking detection (reachable / not reachable) this matters less, but it constrains what we can conclude from timing data - relevant given that precise block start/stop timing is one of our intended contributions.

Source: <https://dl.acm.org/doi/10.1145/2815675.2815710>

### 4.4 Day in the Life of RIPE Atlas (2025)

**Objective.** An operational snapshot of the platform: one full day of data - 50,900 measurements, 1.3 billion results.

**Facts we rely on.** Probes in 178 countries, with a strong bias toward Europe and North America (Germany and the US alone host 28% of probes and anchors; 32 countries have a single probe). Platform limits: 100 concurrent measurements, 1,000 probes per measurement, 1M credits/day, with quota-extension requests handled case by case. Six measurement types, with HTTP restricted to targeting anchors.

**What we take from it.** The current reference for platform capabilities when sizing the campaign. It also documents that quota extensions for research are a normal, supported path.

Source: <https://arxiv.org/abs/2511.22474>

---

## 5. Context: censorship measurement surveys

Two recent surveys give the broader landscape, useful for the report's related-work section:

- **A Survey of Internet Censorship and its Measurement** (Wendzel et al., 2025) - the most current methodological overview, covering 2025 publications and emerging trends including regional censorship. IP blocking on shared infrastructure and the resulting overblocking are explicitly discussed as an open problem. <https://arxiv.org/abs/2502.14945>
- **A review of internet censorship: modern measurement and circumvention techniques** (2026) - synthesises 146 measurement and circumvention studies from 2015–2025, classified by protocol, country, duration and method. Useful primarily as a citation index. <https://www.sciencedirect.com/science/article/pii/S1574013726001103>

---

## 6. The gap this project addresses

Bringing the above together:

1. **OONI measures Spain, but from uncontrolled volunteer devices.** Coverage during any specific match window is not guaranteed, and the authors state their figures are conservative for this reason.
2. **The Italian study reconstructs blocking after the fact.** It does not measure in real time during matches.
3. **The sanctions work (§3.1) built exactly the multi-vantage-point RIPE Atlas methodology we need** - but applied it to permanent, DNS-level blocking, not to blocking that appears and disappears within a two-hour window.
4. **No published work has applied controlled, schedulable vantage points to the La Liga campaign.**

**Our contribution**: real-time, match-synchronised measurement of La Liga blocking, from controlled RIPE Atlas vantage points inside multiple Spanish ISPs, with simultaneous out-of-country baselines. This combines the geographic comparison (is the block Spain-specific?) with the temporal precision (exactly when does a block start and stop relative to kick-off?) that no existing study provides.

**Constraints to design around**, drawn from §4.2 and §4.4 and confirmed empirically:
- Probe availability per Spanish ISP is uneven - verified, see guide page 9.
- Credit budget and the 100-concurrent-measurement quota bound the campaign size.
- A quota-extension request to `atlas@ripe.net` is a documented option for research projects.
- Probe interference (§4.3) limits how far latency data can be pushed.

**A ready-made validation target.** OONI's charts use the Cloudflare IP `188.114.97.5` as a worked example: most Spanish ISPs block it shortly before kick-off and unblock it soon after. Reproducing that specific signal is a concrete way to validate our pipeline before trusting it on unknown IPs.

---

## 7. Reading list, priority order

| # | Work | Year | Why |
|---|------|------|-----|
| 1 | OONI - LALIGA Collateral Damage | 2026 | Same topic, same country, closest prior art |
| 2 | Müller et al. - Internet Sanctions on Russian Media (FOCI) | 2024 | The multi-vantage-point RIPE Atlas methodology to copy |
| 3 | Sommese et al. - 90th Minute (Piracy Shield) | 2025 | Methodological template, Italian twin case |
| 4 | Anderson et al. - FOCI | 2014 | Founding paper for RIPE Atlas censorship measurement |
| 5 | Bajpai et al. - Lessons Learned (CCR) | 2015 | Platform biases; motivated our coverage pre-study |
| 6 | Day in the Life of RIPE Atlas | 2025 | Current platform capabilities and quotas |
| 7 | ISD - Auditing the EU ban, 3 years on | 2026 | Recent applied audit using the same tooling |
| 8 | Holterbach et al. - Measurement interference | 2015 | Constrains latency-based conclusions |
| 9 | Wendzel et al. - Censorship survey | 2025 | Broader related-work positioning |

---

## 8. Open items

- Read the full PDFs of items 1–3 rather than the official summaries - the methodology sections in particular.
- Evaluate whether the `ooni/blocking-fingerprints` dataset can be integrated into our classification pipeline (§3.1). This would move us from "did it fail?" to "who blocked it, and how?".
- Add an ISP-resolver vs public-resolver comparison to the campaign design, following §3.1 - this distinguishes DNS-level from IP-level blocking, which matters because La Liga blocking is IP-based and should survive a resolver change.
- Check whether the Piracy Shield reconstruction method (§2.2) can be adapted to Spain, given La Liga's lists are similarly unpublished.

---

*Figures in this document come from the cited primary sources or their official summaries. Where a figure appears only in press coverage, it was cross-checked across at least two independent outlets. Claims about named companies follow the source's own wording - in particular, the TLS interception finding in §2.1 is reported as observed on a network, not attributed to its operator.*