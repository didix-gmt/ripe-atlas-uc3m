---
layout: default
title: "Example campaign: latency vs distance"
nav_order: 8
---

# 7. Example campaign: latency vs distance

A complete, working example of a measurement campaign - from probe selection to final plot. Useful as a template for future campaigns. The code lives in [`campaigns/latency-vs-distance/`](../campaigns/latency-vs-distance/) in this repository.

## Objective

Verify that ping RTT from vantage points around the world correlates with geographic distance to the target, as physics predicts (light in fiber travels at ~200,000 km/s, so RTT in ms ≥ distance in km / 100). This validates that our measurement pipeline works end to end, following the approach of "The Internet at the Speed of Light" (Singla et al., HotNets 2014).

## What the script does

1. **Selects probes**: queries the public API for 3 connected probes in each of 14 countries across all continents (filter: `status=1`, tag `system-ipv4-works`).
2. **Launches a one-off ping** (3 packets) from all 42 probes towards the target, as a single measurement.
3. **Polls the measurement status** every 30 s until it reports `Stopped`.
4. **Fetches the results**, saves them as raw JSON.
5. **Computes the great-circle distance** (Haversine formula) between each probe and the target.
6. **Plots RTT vs distance**, with the theoretical speed-of-light lower bound as reference.

## Real-world numbers from our run

- **42 probes**, 14 countries, single one-off ping measurement
- **Cost**: ~250 credits (42 probes × 3 packets × 2 for one-off)
- **Duration**: ~6-7 minutes from creation to completion
- **Result**: clear latency/distance correlation, all points above the physical lower bound - pipeline validated

## Pitfalls we hit (so you don't have to)

- **The target must answer ICMP.** Our first attempt targeted `uc3m.es`, which silently drops pings - 41 results received, all with 100% packet loss. Always `ping` the target from your own machine first. We switched to `telecom-physique.fr`, which responds.
- **One measurement, not one per probe.** 42 probes pinging one target is a *single* measurement (1/100 of the parallel quota), not 42. Quotas count measurements, and the "same target" limit (25) counts concurrent measurements towards one target - see the quota panel on your Atlas dashboard.

## Running it yourself

```bash
cd campaigns/latency-vs-distance
python3 -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
echo "RIPE_API_KEY=your_key_here" > .env
python3 campaign.py
```

## Sources

- *The Internet at the Speed of Light* (Singla et al., HotNets 2014) - <https://doi.org/10.1145/2670518.2673876>
- *User-defined Measurements* (quotas, one-off vs periodic) - <https://atlas.ripe.net/docs/getting-started/user-defined-measurements/>
- *Guidelines For Best Practices* (RIPE Atlas) - <https://atlas.ripe.net/docs/howtos/best-practices.html>