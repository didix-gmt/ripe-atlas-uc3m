#!/usr/bin/env python3
"""
Match-synchronised blocking campaign
=====================================
Schedules a periodic measurement around a football match, from an equal
number of probes inside each target Spanish ISP, plus an out-of-country
control group.

Design decisions and why:

  * PERIODIC, not one-off. One-off results cost twice as much each, and
    we need a time series anyway — the whole point is to see the block
    appear and disappear. Scheduled with explicit start/stop times.

  * EQUAL n PER OPERATOR. The headline analysis is a comparison between
    ISPs. With 72 probes on Telefonica and 9 on Vodafone, a difference
    in detected blocking rate could just be a difference in sample size.
    Equal n removes that confound. n is small on purpose: within one
    operator all probes sit behind the same filtering infrastructure,
    so probe-to-probe variation is not expected. (See guide page 9.)

  * CONTROL GROUP OUTSIDE SPAIN. A target unreachable from Spain *and*
    from the controls is simply down; unreachable from Spain only is a
    blocking candidate. Without controls the two are indistinguishable.
    Same design as OONI's Spain/Frankfurt comparison.

  * RECENT PROBES ONLY. The API returns oldest probe IDs first, and old
    probes have an outdated TLS client that fails handshakes against
    modern servers for reasons unrelated to blocking. (See guide
    page 8.)

  * is_public=False. A public measurement reveals which IPs we suspect
    of being blocked before we have published anything.

  * DRY RUN BY DEFAULT. Creating measurements spends credits and they
    are not refundable. Nothing is launched until --launch is passed,
    and the estimated cost is printed first.

Usage:
    # See what it would do, spend nothing
    python3 campaign_match.py --kickoff "2026-08-15 19:30" --targets targets.txt

    # Actually schedule it
    python3 campaign_match.py --kickoff "2026-08-15 19:30" --targets targets.txt --launch

    targets.txt: one IP address per line, '#' for comments.

Requirements:
    pip install ripe-atlas-cousteau requests python-dotenv
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from ripe.atlas.cousteau import (
    Ping,
    AtlasSource,
    AtlasCreateRequest,
)

load_dotenv()
API_KEY = os.getenv("RIPE_API_KEY", "")

ATLAS_PROBES_URL = "https://atlas.ripe.net/api/v2/probes/"

# ── Campaign configuration ────────────────────────────────────────────────────

# Target ISPs. Five, not three: DIGI and MasMovil have more probes than
# Orange or Vodafone, and both appear in OONI's set of networks with
# match-correlated blocking. See guide page 9.
TARGET_ISPS = {
    3352:  "Telefonica",
    57269: "DIGI",
    12479: "Orange ES",
    15704: "MasMovil",
    12430: "Vodafone ES",
}

# Control countries, outside Spain. Kept small: their job is to answer
# "is this target up at all?", not to map anything.
CONTROL_COUNTRIES = {
    "FR": "France",
    "DE": "Germany",
    "PT": "Portugal",
}

PROBES_PER_ISP = 6        # set by the smallest target ISP (Vodafone)
PROBES_PER_CONTROL = 4
CANDIDATE_POOL = 100      # probes fetched per AS before picking the newest

LEAD_MINUTES = 60         # start measuring this long before kickoff
TRAIL_MINUTES = 60        # keep measuring this long after expected final whistle
MATCH_MINUTES = 115       # 90 + half-time + stoppage, approximate

INTERVAL_SECONDS = 300    # one round every 5 minutes
PING_PACKETS = 3
CREDITS_PER_PING_RESULT = 3

# Tags that mark a probe as sitting behind additional filtering of its
# own, which would confound an ISP-level measurement.
EXCLUDE_TAGS = {
    "system-anchor", "system-virtual",
    "datacentre", "datacenter", "hosting", "colocation", "colo",
    "academic", "university", "school", "office", "corporate",
    "ixp", "core", "backbone", "transit",
}


# ── Probe selection ───────────────────────────────────────────────────────────

def fetch_candidates(params, label):
    """Fetch one page of connected probes matching params."""
    params = dict(params)
    params.update({"status": 1, "page_size": CANDIDATE_POOL,
                   "fields": "id,asn_v4,country_code,tags,is_anchor"})
    try:
        resp = requests.get(ATLAS_PROBES_URL, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        print(f"  ! {label}: {e}")
        return []


def is_usable(probe):
    """
    Reject anchors and probes declared as infrastructure.

    We are deliberately NOT trying to prove a probe is residential —
    that classification turned out not to be reliably derivable from
    the available tags (guide page 9). We only exclude probes likely
    to sit behind an extra firewall of their own, which would confound
    an ISP-level measurement.
    """
    if probe.get("is_anchor"):
        return False
    slugs = {(t.get("slug") or "").lower() for t in (probe.get("tags") or [])}
    return not (slugs & EXCLUDE_TAGS)


def pick_newest(probes, n):
    """
    Keep the n highest probe IDs.

    RIPE assigns IDs sequentially, so a high ID means newer hardware and
    firmware. This matters: the API's default ordering returns the
    OLDEST probes first, whose obsolete TLS clients fail handshakes for
    reasons unrelated to blocking.
    """
    return sorted(probes, key=lambda p: p["id"], reverse=True)[:n]


def select_probes():
    """
    Build the probe set: equal n per target ISP, plus controls.

    Returns (probe_ids, metadata dict, per-group counts).
    """
    probe_ids, meta, counts = [], {}, {}

    print("Selecting probes inside target ISPs...")
    for asn, name in TARGET_ISPS.items():
        raw = fetch_candidates({"country_code": "ES", "asn_v4": asn}, name)
        usable = [p for p in raw if is_usable(p)]
        chosen = pick_newest(usable, PROBES_PER_ISP)

        for p in chosen:
            probe_ids.append(p["id"])
            meta[p["id"]] = {"group": name, "asn": asn, "role": "target"}

        counts[name] = len(chosen)
        flag = "" if len(chosen) == PROBES_PER_ISP else "  <-- SHORT"
        print(f"  {name:14s} (AS{asn:<6}) {len(raw):>3} connected, "
              f"{len(usable):>3} usable, {len(chosen)} selected{flag}")

    print("\nSelecting control probes outside Spain...")
    for cc, name in CONTROL_COUNTRIES.items():
        raw = fetch_candidates({"country_code": cc}, name)
        usable = [p for p in raw if is_usable(p)]
        chosen = pick_newest(usable, PROBES_PER_CONTROL)

        for p in chosen:
            probe_ids.append(p["id"])
            meta[p["id"]] = {"group": name, "asn": p.get("asn_v4"), "role": "control"}

        counts[name] = len(chosen)
        print(f"  {name:14s} ({cc})        {len(chosen)} selected")

    return probe_ids, meta, counts


# ── Targets ───────────────────────────────────────────────────────────────────

def load_targets(path):
    """Read one IP per line, ignoring blanks and # comments."""
    targets = []
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                targets.append(line)
    if not targets:
        raise ValueError(f"{path} contains no targets")
    return targets


# ── Cost ──────────────────────────────────────────────────────────────────────

def estimate_cost(n_targets, n_probes, duration_minutes):
    """
    Credits = targets x probes x rounds x cost-per-result.

    Periodic measurements are billed per result delivered, with no
    one-off surcharge. One measurement is created per target, each
    sourced from the full probe set.
    """
    rounds = int(duration_minutes * 60 / INTERVAL_SECONDS)
    results = n_targets * n_probes * rounds
    return results * CREDITS_PER_PING_RESULT, rounds, results


def check_balance():
    """Fetch the current credit balance, or None if unavailable."""
    try:
        resp = requests.get(
            "https://atlas.ripe.net/api/v2/credits/",
            headers={"Authorization": f"Key {API_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("current_balance")
    except Exception:
        return None


# ── Launch ────────────────────────────────────────────────────────────────────

def launch(targets, probe_ids, start, stop):
    """
    Create one periodic ping measurement per target IP.

    One measurement per target rather than one overall, because RIPE
    measurements have a single target each. All share the same probe
    set and the same window, so the results line up.
    """
    source = AtlasSource(
        type="probes",
        value=",".join(str(p) for p in probe_ids),
        requested=len(probe_ids),
    )

    created = []
    for i, target in enumerate(targets, 1):
        ping = Ping(
            af=4,
            target=target,
            packets=PING_PACKETS,
            interval=INTERVAL_SECONDS,
            description=f"LaLiga blocking campaign - {target}",
        )
        request = AtlasCreateRequest(
            key=API_KEY,
            measurements=[ping],
            sources=[source],
            start_time=start,
            stop_time=stop,
            is_oneoff=False,
            is_public=False,
        )
        ok, response = request.create()
        if not ok:
            print(f"  ! {target}: {response}")
            continue

        msm_id = response["measurements"][0]
        created.append({"target": target, "msm_id": msm_id})
        print(f"  [{i:>3}/{len(targets)}] {target:<18} -> msm {msm_id}")
        time.sleep(0.5)   # be gentle with the API

    return created


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kickoff",
                        help='Kickoff time, "YYYY-MM-DD HH:MM", interpreted as UTC. '
                             'Spain is UTC+2 in August, so a 21:30 local kickoff '
                             'is 19:30 UTC. Not needed with --test.')
    parser.add_argument("--targets", required=True, help="File with one IP per line")
    parser.add_argument("--launch", action="store_true",
                        help="Actually create the measurements (spends credits)")
    parser.add_argument("--test", action="store_true",
                        help="Short validation run: 20-minute window starting in "
                             "5 minutes, ignoring --kickoff. Use this to check the "
                             "pipeline end to end without paying for a full match.")
    parser.add_argument("--duration", type=int, metavar="MIN",
                        help="Override the total window length in minutes")
    args = parser.parse_args()

    if not API_KEY:
        raise SystemExit("RIPE_API_KEY not set — check your .env file.")

    if not args.test and not args.kickoff:
        raise SystemExit("--kickoff is required (or use --test for a short "
                         "validation run).")

    if args.test:
        # Validation mode: a short window starting shortly from now. The
        # point is to confirm measurements get created, run, and can be
        # fetched - not to observe anything. Five minutes of lead time so
        # the scheduler has room to accept the request.
        kickoff = datetime.now(timezone.utc) + timedelta(minutes=5)
        start = kickoff
        stop = kickoff + timedelta(minutes=20)
    else:
        kickoff = datetime.strptime(args.kickoff, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        start = kickoff - timedelta(minutes=LEAD_MINUTES)
        stop = kickoff + timedelta(minutes=MATCH_MINUTES + TRAIL_MINUTES)

    if args.duration:
        stop = start + timedelta(minutes=args.duration)

    duration = (stop - start).total_seconds() / 60

    targets = load_targets(args.targets)
    probe_ids, meta, counts = select_probes()

    if not probe_ids:
        raise SystemExit("No probes selected.")

    cost, rounds, results = estimate_cost(len(targets), len(probe_ids), duration)

    print("\n" + "=" * 70)
    print("CAMPAIGN PLAN" + ("  [TEST RUN]" if args.test else ""))
    print("=" * 70)
    if args.test:
        print("Mode            : validation only, not a real match window")
    print(f"Kickoff (UTC)   : {kickoff:%Y-%m-%d %H:%M}")
    print(f"Window          : {start:%H:%M} -> {stop:%H:%M}  ({duration:.0f} min)")
    print(f"Interval        : {INTERVAL_SECONDS}s  ({rounds} rounds)")
    print(f"Targets         : {len(targets)}")
    print(f"Probes          : {len(probe_ids)} "
          f"({sum(1 for m in meta.values() if m['role']=='target')} target, "
          f"{sum(1 for m in meta.values() if m['role']=='control')} control)")
    print(f"Results         : {results:,}")
    print(f"Estimated cost  : {cost:,} credits")

    balance = check_balance()
    if balance is not None:
        print(f"Current balance : {balance:,} credits")
        if cost > balance:
            print("\n!! Estimated cost exceeds the current balance.")
            print("   Reduce targets, lengthen the interval, or wait for credits.")
        else:
            print(f"Remaining after : {balance - cost:,} credits")

    short = [k for k, v in counts.items() if k in TARGET_ISPS.values() and v < PROBES_PER_ISP]
    if short:
        print(f"\n!! Under-sampled ISPs: {', '.join(short)}")
        print("   Equal-n comparison is compromised — consider lowering")
        print("   PROBES_PER_ISP so every operator matches.")

    if not args.launch:
        print("\nDry run — nothing created. Re-run with --launch to schedule.")
        return

    if start < datetime.now(timezone.utc):
        raise SystemExit("Start time is in the past — check --kickoff.")

    print("\nCreating measurements...")
    created = launch(targets, probe_ids, start, stop)

    out = f"campaign_{kickoff:%Y%m%d_%H%M}.json"
    with open(out, "w") as f:
        json.dump({
            "kickoff_utc": kickoff.isoformat(),
            "start_utc": start.isoformat(),
            "stop_utc": stop.isoformat(),
            "interval_seconds": INTERVAL_SECONDS,
            "probes": meta,
            "measurements": created,
        }, f, indent=2)

    print(f"\n{len(created)}/{len(targets)} measurements scheduled.")
    print(f"Campaign manifest saved as {out}")
    print("Fetch results after the match with fetch_results.py using the IDs above.")


if __name__ == "__main__":
    main()