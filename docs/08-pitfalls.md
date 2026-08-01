---
layout: default
title: "Pitfalls in blocking detection"
nav_order: 9
---

# 8. Pitfalls in blocking detection

Everything on this page comes from mistakes we actually made while building the measurement scripts. They are worth reading before designing any campaign, because each one silently produces **false positives** — measurements that look like blocking but aren't.

---

## Pitfall 1: treating "failure" as a boolean

The most important lesson. A measurement can fail in several ways, and they do not mean the same thing at all.

For an HTTPS/TLS check (`sslcert` measurement type), there are three meaningfully different outcomes:

| Outcome | What actually happened | Blocking signal? |
|---|---|---|
| **Certificate returned** | TCP connect + TLS handshake both succeeded | No — service reachable |
| **TLS alert (e.g. `handshake_failure`, alert 40)** | TCP connect **succeeded**, server answered, only the crypto negotiation failed | **No** — packets got through |
| **No response at all** (no certificate, no alert) | Nothing came back | **Yes** — worth investigating |

The middle row is the trap. A `handshake_failure` means the server was reached and replied — it is evidence *against* blocking, not for it. Counting it as a failure inflates the blocking rate enormously.

Our scripts therefore classify HTTPS results into three states (`OK` / `TLS_FAIL` / `UNREACHABLE`) rather than a boolean, and only `UNREACHABLE` is treated as a candidate blocking signal.

---

## Pitfall 2: the default probe ordering selects the worst possible sample

When you query the probes API without specifying an order:

```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1
```

results come back with the **lowest probe IDs first**. Since RIPE Atlas assigns IDs sequentially, low IDs mean the oldest probes still connected — first-generation hardware from the early 2010s.

This matters because old probes ship an outdated TLS client that cannot negotiate with modern servers. Selecting them produces handshake failures that have nothing to do with the network path.

**What we observed.** Running the same HTTPS check against `uc3m.es` twice, with different probe selections:

| Run | Probe IDs used | HTTPS result |
|---|---|---|
| 1 (default API ordering) | 28 → 3739 | 12/12 handshake failures |
| 1 (same run, higher IDs) | 6349 → 6602 | 5/5 OK |
| 2 (highest IDs per country) | 6548 → 1016320 | 18/18 OK |

The split follows probe age, not geography: Spain, Germany and Japan appear on both sides depending on which probe was picked. In the second run, selecting recent probes only, **every single one succeeded** — including all three Spanish probes.

> The apparent threshold around probe ID ~6000 is an **empirical observation across ~35 probes in our own two runs**, not a documented RIPE specification. Treat it as a rule of thumb for sampling, not as a hard technical boundary. The RIPE Atlas mailing list confirms the general phenomenon (sslcert failures caused by cipher/TLS-version limitations rather than connectivity), but does not publish a cut-off ID.

**The fix**: fetch a wide pool of probes per country (`page_size=100`), then keep the highest IDs, instead of taking whatever the API returns first. See `campaigns/` in this repository.

---

## Pitfall 3: assuming ICMP silence means the service is down

A target that does not answer ping is not necessarily blocked or offline — many servers simply drop ICMP as a matter of policy.

`uc3m.es` is a clean example: **0/18 probes got a ping reply, while 18/18 completed a TLS handshake on port 443**. Ping alone would have reported the service as completely unreachable worldwide, which is plainly wrong.

This is why our connectivity script runs **ping and sslcert in the same API call**: they then share the same probes and the same start/stop time, which makes the comparison meaningful. A mismatch between the two is informative in both directions:

- ping fails, HTTPS works → ICMP filtered somewhere, service fine (the `uc3m.es` case);
- ping works, HTTPS fails → possible port-specific filtering, worth investigating;
- both fail from one country but work elsewhere → strongest blocking candidate.

---

## Pitfall 4: not knowing which measurement types can target what

RIPE Atlas offers six measurement types (ping, traceroute, DNS, NTP, TLS/SSL, HTTP), but **the HTTP type is restricted to targeting RIPE Atlas anchors only** — it cannot be pointed at an arbitrary domain.

So "test whether this website answers over HTTPS" cannot be done with the HTTP measurement type. The practical substitute is `sslcert`, which performs a TCP connect plus TLS handshake on port 443 against any target and reports the certificate or the failure. It answers "is this service reachable on 443?", which is what blocking detection actually needs.

---

## Pitfall 5: leaving measurements public by default

Measurements created through the web interface are always public. Through the API, they are public unless you pass `is_public=False`.

For test campaigns this is fine and even desirable. For the real blocking campaign it is not: a public measurement reveals **which IPs we suspect of being blocked**, before we have published anything. Set `is_public=False` on the real runs.

---

## Checklist before running a real campaign

- [ ] Does the target answer ICMP at all? (`ping` it yourself first — otherwise every result will be a false negative)
- [ ] Are we selecting recent probes, or whatever the API returned first?
- [ ] Are failures classified by *mode* (no response vs. protocol-level error), not just counted?
- [ ] Are ping and HTTPS launched in the same request, so they share probes and timing?
- [ ] Are out-of-country probes included as a control group?
- [ ] Is `is_public` set appropriately?
- [ ] Does the credit budget cover the planned number of results? (see [page 3](03-credit-system.md))

---

## Sources

- *User-defined Measurements* (measurement types, HTTP restricted to anchors, public/non-public) — <https://atlas.ripe.net/docs/getting-started/user-defined-measurements/>
- *Day in the Life of RIPE Atlas* (2025) — confirms the six measurement types and the anchor-only restriction on HTTP — <https://arxiv.org/abs/2511.22474>
- *TLS error when the certificate is expired?* — RIPE Atlas mailing list thread where a RIPE NCC developer explains that sslcert failures typically come from server-side cipher restrictions rather than connectivity — <https://mailman.ripe.net/archives/list/ripe-atlas@ripe.net/message/OPP65MZQP6H3XGPQAK4B7IAPNENAZC2F/>
- *TLS Certificate probes fail ("handshake failure")* — another mailing list thread documenting the same failure mode against modern servers — <https://mailman.ripe.net/archives/list/ripe-atlas@ripe.net/thread/K5MWPMYFKGUNGJP47DTKW54MEXQSN2IY/>
- *Listing probes* (API filter parameters) — <https://atlas.ripe.net/docs/apis/rest-api-manual/probes/listing-probes/>
- Our own measurements (`194436847`/`194436848` and `194568725`/`194568726` on atlas.ripe.net) — source for the probe-age observation, which is empirical and not officially documented