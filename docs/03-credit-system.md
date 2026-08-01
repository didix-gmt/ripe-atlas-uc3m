---
layout: default
title: The credit system
nav_order: 4
---

# 3. The credit system

RIPE Atlas runs on **credits**. You earn them by contributing to the network, and spend them by running your own measurements.

## How you earn credits

| Path | Cost | Credits earned | Relevant for us? |
|---|---|---|---|
| Host 1 hardware probe | €0 - mailed for free by the RIPE NCC | ~21,600 / day | No |
| Host 1 software probe | €0 - but you need your own device | ~21,600 / day | Yes - our case, Pi already provided by the lab |
| RIPE NCC member (LIR) | €2,800 first year, then €1,800/year | 1,000,000 / month | No, disproportionate |
| Transfer from another user | €0 | Variable | If UC3M already has a credited account |
| Existing public data | €0 | No credits needed | Yes to exploit existing data |

**The detail that matters**: a host receives **15 credits per minute** their probe is connected, i.e. **~21,600 credits / 24h** per probe, as long as it stays connected. Accounts are credited once per day, showing up as two separate entries in the credits history: one for uptime ("Probe uptime"), one for the probe's participation in RIPE's *built-in* measurements, the ones running automatically in the background, not the ones we create ourselves ("For results delivered"). **You don't need anyone else to use your probe to earn credits.**

> **In practice the "results delivered" bonus is much larger than the docs suggest.** On our own probe it has consistently been ~10,500-12,000 credits/day on top.

Hosting more than one probe earns credits independently for each - roughly doubling to ~43,200 credits/day with 2 probes. This is capped though: RIPE limits software probes to 2 per IP address (4 per BGP prefix), specifically to prevent this from being used to farm unlimited credits (see [page 2](02-hardware-vs-software-probe.md) for the full table).
## How you spend credits

Each measurement has a **cost per result** that depends on its type. Official unit costs:

| Measurement | Cost per result |
|---|---|
| Ping (3 packets, default) | **3** credits |
| DNS (UDP) | **10** credits |
| DNS (TCP) | **20** credits |
| Traceroute (default) | **30** credits |
| SSLCert | **10** credits |

Important rules:
- the cost depends on the **number of results delivered**, not on frequency or number of probes. A measurement from 1 probe every minute costs the same as from 10 probes every 10 minutes (same total number of results);
- a **one-off** measurement costs **2× more** than a periodic measurement result, due to scheduling overhead;
- billing happens in batches, every 4 to 6 hours.

### Orders of magnitude for our topic

With ~21,600 credits/day from a single probe:

| Type | Cost/result | Possible results / day |
|---|---|---|
| Ping | 3 | ~7,200 |
| DNS (UDP) | 10 | ~2,160 |
| DNS (TCP) | 20 | ~1,080 |
| Traceroute | 30 | ~720 |

**Concrete example.** Testing 1,000 IPs with a single ping: 1,000 × 3 = **3,000 credits** (easy). But repeating that test every 5 min for a 3h match: 1,000 × 36 × 3 = **108,000 credits**, i.e. ~5 days of a single probe's income. → You'll need to **either limit** the frequency/number of IPs, **or accumulate** credits over several days before a match, **or use multiple probes**.

## If you run out of credits

- RIPE periodically computes your consumption rate.
- If fewer than **5 days** of credits remain at the current rate → warning email.
- If the balance goes negative → the most expensive measurement is **stopped automatically**. You keep access to results already obtained, but must **recreate** the measurement once credits are replenished.

## Can you measure without credits?

- **Running your own measurements (UDM)**: no, credits are required.
- **Using already-existing measurements**: yes, for free and without even an account (see [page 4](04-existing-data.md)).

## Sources

- *Credits* (official docs, all figures above) - <https://atlas.ripe.net/docs/getting-started/credits/>
- *Billing, Payment and Fees* (2026 LIR fees) - <https://www.ripe.net/membership/payment/>
- *What Can You Do with One Million RIPE Atlas Credits?* (RIPE Labs) — <https://labs.ripe.net/author/becha/what-can-you-do-with-one-million-ripe-atlas-credits/>
- *RIPE Atlas: Presentations, Tutorials and Videos* (RIPE Labs) — <https://labs.ripe.net/atlas/user-experiences/presentations-tutorials-and-videos>