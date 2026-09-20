---
layout: default
title: "Pitfalls in blocking detection"
nav_order: 9
---

# 8. Pitfalls in blocking detection

Everything on this page comes from mistakes we actually made while building the measurement scripts. They are worth reading before designing any campaign, because each one silently produces **false positives** - measurements that look like blocking but aren't.

One of them, added last, produces the opposite and more dangerous failure: a **false negative**, a block that the measurement simply cannot see.

---

## Pitfall 1: treating "failure" as a boolean

The most important lesson. A measurement can fail in several ways, and they do not mean the same thing at all.

For an HTTPS/TLS check (`sslcert` measurement type), there are three meaningfully different outcomes:

| Outcome | What actually happened | Blocking signal? |
|---|---|---|
| **Certificate returned** | TCP connect + TLS handshake both succeeded | No - service reachable |
| **TLS alert (e.g. `handshake_failure`, alert 40)** | TCP connect **succeeded**, server answered, only the crypto negotiation failed | **No** - packets got through |
| **No response at all** (no certificate, no alert) | Nothing came back | **Yes** - worth investigating |

The middle row is the trap. A `handshake_failure` means the server was reached and replied - it is evidence *against* blocking, not for it. Counting it as a failure inflates the blocking rate enormously.

Our scripts therefore classify HTTPS results into three states (`OK` / `TLS_FAIL` / `UNREACHABLE`) rather than a boolean, and only `UNREACHABLE` is treated as a candidate blocking signal.

> **Two implementations, one small difference.** `connectivity_test.py` keys off the presence of `cert` and `alert` only, so any result with neither is `UNREACHABLE`. `fetch_results.py` refines that last bucket: it reads the result's `err` string and splits transport failures (`connect: timeout`, `connection refused`, `no route`) as `UNREACHABLE` from TLS-layer errors as `TLS_FAIL`. The refinement follows the logic of the table above rather than departing from it, but the two scripts can label the same borderline result differently. If you compare their outputs side by side, that is why.

---

## Pitfall 2: the default probe ordering selects the worst possible sample

When you query the probes API without specifying an order:

```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1
```

results come back with the **lowest probe IDs first**. Since RIPE Atlas assigns IDs sequentially, low IDs mean the oldest probes still connected - first-generation hardware from the early 2010s.

This matters because old probes ship an outdated TLS client that cannot negotiate with modern servers. Selecting them produces handshake failures that have nothing to do with the network path.

**What we observed.** Running the same HTTPS check against `uc3m.es` twice, with different probe selections:

| Run | Probe IDs used | HTTPS result |
|---|---|---|
| 1 (default API ordering) | 28 → 3739 | 12/12 handshake failures |
| 1 (same run, higher IDs) | 6349 → 6602 | 5/5 OK |
| 2 (highest IDs per country) | 6548 → 1016320 | 18/18 OK |

The split follows probe age, not geography: Spain, Germany and Japan appear on both sides depending on which probe was picked. In the second run, selecting recent probes only, **every single one succeeded** - including all three Spanish probes.

> The apparent threshold around probe ID ~6000 is an **empirical observation across ~35 probes in our own two runs**, not a documented RIPE specification. Treat it as a rule of thumb for sampling, not as a hard technical boundary. The RIPE Atlas mailing list confirms the general phenomenon (sslcert failures caused by cipher/TLS-version limitations rather than connectivity), but does not publish a cut-off ID.

**The fix**: fetch a wide pool of probes per country (`page_size=100`), then keep the highest IDs, instead of taking whatever the API returns first. See `campaigns/` in this repository.

---

## Pitfall 3: assuming ICMP silence means the service is down

A target that does not answer ping is not necessarily blocked or offline - many servers simply drop ICMP as a matter of policy.

`uc3m.es` is a clean example: **0/18 probes got a ping reply, while 18/18 completed a TLS handshake on port 443**. Ping alone would have reported the service as completely unreachable worldwide, which is plainly wrong.

This is why our connectivity script runs **ping and sslcert in the same API call**: they then share the same probes and the same start/stop time, which makes the comparison meaningful. A mismatch between the two is informative in both directions:

- ping fails, HTTPS works → ICMP filtered somewhere, service fine (the `uc3m.es` case);
- ping works, HTTPS fails → possible port-specific filtering, worth investigating;
- both fail from one country but work elsewhere → strongest blocking candidate.

### We wrote this rule down, then broke it

Worth recording honestly, because it is the most instructive mistake on this page.

The rule above was written early, and the checklist at the bottom of this page has asked "are ping and HTTPS launched in the same request?" ever since. `connectivity_test.py` follows it. But `campaign_match.py` - the script that would actually run the real campaign, the one this whole project exists to run - **launched ping only**, for its entire development. Nobody noticed until the scripts were audited at handover.

Two things made it easy to miss. The script was written first as a scheduling problem (probes, windows, credits) with the measurement type almost an afterthought; and a ping-only campaign runs perfectly, costs less, and produces plausible-looking output. There is no error to trip over.

The consequence would not have been noisy either. Spanish ISPs implementing a block at TCP/443 rather than by null-route would leave ICMP untouched, so **the campaign would have returned "no blocking detected" while the blocking was happening**. A false positive announces itself when you check it; a false negative just looks like a quiet result. And it would have been checked against a ground truth - `188.114.97.5` - that OONI established with TLS measurements, not ping, so the validation step might well have "failed" for reasons nobody could explain.

The general lesson: a rule written in the documentation is not a rule applied in the code. When a checklist item matters, check it against every script that should obey it, not against the one it was written while thinking about.

---

## Pitfall 4: not knowing which measurement types can target what

RIPE Atlas offers six measurement types (ping, traceroute, DNS, NTP, TLS/SSL, HTTP), but **the HTTP type is restricted to targeting RIPE Atlas anchors only** - it cannot be pointed at an arbitrary domain.

So "test whether this website answers over HTTPS" cannot be done with the HTTP measurement type. The practical substitute is `sslcert`, which performs a TCP connect plus TLS handshake on port 443 against any target and reports the certificate or the failure. It answers "is this service reachable on 443?", which is what blocking detection actually needs.

---

## Pitfall 5: leaving measurements public by default

Measurements created through the web interface are always public. Through the API, they are public unless you pass `is_public=False`.

For test campaigns this is fine and even desirable. For the real blocking campaign it is not: a public measurement reveals **which IPs we suspect of being blocked**, before we have published anything. Set `is_public=False` on the real runs.

---

## Pitfall 6: a cost estimate that only counts one measurement type

Directly downstream of pitfall 3, and it bites at the worst possible moment.

`estimate_cost()` in `campaign_match.py` multiplied the result count by the ping unit cost, which was correct as long as the script only created pings. The moment TLS was added, the same function understated the true bill **by a factor of 4.3** - ping costs 3 credits per result, TLS costs 10, so running both costs 13 rather than 3.

Getting this wrong is worse than the original omission. A dry run that says "118,000 credits" for a campaign that will actually spend 513,000 does not just mislead; it invites you to launch something you cannot afford, and measurements stop mid-campaign when the balance runs out - taking the second half of the match with them.

The fix is structural rather than arithmetic: cost is now computed per measurement type from a single table of unit costs, and the dry run prints the breakdown line by line instead of one total. If you add a measurement type, the estimate follows automatically and you can see it did.

---

## Checklist before running a real campaign

- [ ] Does the target answer ICMP at all? (`ping` it yourself first - otherwise every result will be a false negative)
- [ ] Are we selecting recent probes, or whatever the API returned first?
- [ ] Are failures classified by *mode* (no response vs. protocol-level error), not just counted?
- [ ] Are ping and HTTPS launched in the same request, so they share probes and timing? **Check this in the script you are about to run, not in the one you remember writing.**
- [ ] Does the cost estimate count *every* measurement type the script creates?
- [ ] Are out-of-country probes included as a control group?
- [ ] Is `is_public` set appropriately?
- [ ] Does the credit budget cover the planned number of results? (see [page 3](03-credit-system.md))

---

## Sources

- *User-defined Measurements* (measurement types, HTTP restricted to anchors, public/non-public) - <https://atlas.ripe.net/docs/getting-started/user-defined-measurements/>
- *Day in the Life of RIPE Atlas* (2025) - confirms the six measurement types and the anchor-only restriction on HTTP - <https://arxiv.org/abs/2511.22474>
- *TLS error when the certificate is expired?* - RIPE Atlas mailing list thread where a RIPE NCC developer explains that sslcert failures typically come from server-side cipher restrictions rather than connectivity - <https://mailman.ripe.net/archives/list/ripe-atlas@ripe.net/message/OPP65MZQP6H3XGPQAK4B7IAPNENAZC2F/>
- *TLS Certificate probes fail ("handshake failure")* - another mailing list thread documenting the same failure mode against modern servers - <https://mailman.ripe.net/archives/list/ripe-atlas@ripe.net/thread/K5MWPMYFKGUNGJP47DTKW54MEXQSN2IY/>
- *Listing probes* (API filter parameters) - <https://atlas.ripe.net/docs/apis/rest-api-manual/probes/listing-probes/>
- Our own measurements (`194436847`/`194436848` and `194568725`/`194568726` on atlas.ripe.net) - source for the probe-age observation, which is empirical and not officially documented
- Unit costs per measurement type - [page 3](03-credit-system.md), from the official RIPE Atlas credits documentation