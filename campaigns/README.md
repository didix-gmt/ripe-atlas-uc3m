# Campaigns

One folder per measurement script, each self-contained. Shared dependencies are in `requirements.txt` at this level.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r campaigns/requirements.txt
echo "RIPE_API_KEY=your_key_here" > .env    # never commit this
```

Only `campaign-match/campaign_match.py` spends credits, and only when passed `--launch`. Everything else either reads public data or runs a dry run by default.

---

## `campaign-match/` — the real thing

The match-synchronised campaign: ping + TLS against a list of target IPs, from an equal number of probes inside each of the five target Spanish ISPs, plus controls outside Spain. This is the script the project exists to run.

| File | What it does | Costs credits |
|---|---|---|
| `campaign_match.py` | Selects probes, estimates cost, launches the campaign around a kick-off time | only with `--launch` |
| `select_targets.py` | Builds `targets.txt` by stratified sampling of OONI's published affected-IP list | no |
| `fetch_results.py` | Re-fetches and classifies results of measurements that already exist | no |
| `targets.txt` | The current target list | — |
| `targets_test.txt` | Three IPs for `--test` runs | — |
| `results/` | Campaign manifests and fetched results | — |

```bash
# dry run — prints the plan and the cost, creates nothing
python3 campaigns/campaign-match/campaign_match.py \
  --kickoff "2026-09-20 19:00" --targets campaigns/campaign-match/targets.txt

# 20-minute pipeline check against 3 targets, no match needed
python3 campaigns/campaign-match/campaign_match.py --test
```

Kick-off times are **UTC**. Spain is UTC+2 until late October, UTC+1 after.

## `probe_profile/` — who can we measure from

Counts connected probes per target ISP and writes `probe_profile_es.csv`. Probe populations shift daily, so run this shortly before any campaign rather than trusting a count from last week. The reasoning behind the classification (and the dead end it replaced) is in [docs/09](../docs/09-probe-coverage-spain.md).

## `probe-density/` — coverage per capita

Compares probe counts against live World Bank population data, for the "is Spain well covered relative to its neighbours" question. Reads public APIs only.

## `connectivity-check/` — ping + TLS, generic

The three-state HTTPS classification in isolation, against an arbitrary target from a handful of countries. Useful for checking whether a single host behaves oddly before putting it in a target list.

## `latency-vs-distance/` — the validation toy

Pings one target from 42 probes across 14 countries and plots RTT against great-circle distance, with the speed-of-light bound for reference. It exists to prove the pipeline works end to end; it tells you nothing about blocking. Walked through in [docs/07](../docs/07-example-campaign.md).

---

## Before running anything that spends credits

Read [docs/08 — Pitfalls](../docs/08-pitfalls.md). Two of them will bite you otherwise: a TLS handshake failure is not proof of blocking (old probes fail handshakes on their own), and silence on ICMP is not proof of anything at all (plenty of hosts just drop ping).
