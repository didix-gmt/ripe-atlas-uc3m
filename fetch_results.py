#!/usr/bin/env python3
"""
Re-fetch results from an existing measurement
==============================================
RIPE Atlas keeps measurement results indefinitely, so there is no need
to re-run (and re-pay for) a measurement just to recover its output.
This script downloads the results of a measurement that already ran,
using its ID, and writes them in the same format connectivity_test.py
produces.

Costs zero credits: fetching results is free, only creating measurements
is billed.

Usage:
    python3 fetch_results.py 194568725 194568726

    With one ID  -> raw results dumped as JSON.
    With two IDs -> treated as a ping/sslcert pair and compared, same
                    output format as connectivity_test.py.

Requirements:
    pip install ripe-atlas-cousteau python-dotenv
"""

import sys
import json
import os
from dotenv import load_dotenv
from ripe.atlas.cousteau import AtlasResultsRequest

load_dotenv()
API_KEY = os.getenv("RIPE_API_KEY", "")


def classify_ssl_result(ssl_r):
    """
    Same three-state classification as connectivity_test.py.

    OK          : certificate returned, no alert -> reachable.
    TLS_FAIL    : server answered but handshake failed -> NOT blocking.
    UNREACHABLE : nothing came back -> candidate blocking signal.
    """
    if not ssl_r:
        return "UNREACHABLE"
    if ssl_r.get("cert") and "alert" not in ssl_r:
        return "OK"
    if "alert" in ssl_r:
        return "TLS_FAIL"
    return "UNREACHABLE"


def fetch(msm_id):
    print(f"Fetching measurement {msm_id}...")
    kwargs = {"msm_id": msm_id}
    if API_KEY:
        kwargs["key"] = API_KEY   # only needed for non-public measurements

    ok, results = AtlasResultsRequest(**kwargs).create()
    if not ok:
        raise RuntimeError(f"Failed to fetch {msm_id}: {results}")

    print(f"  {len(results)} result(s) received.")
    return results


def compare(ping_results, ssl_results):
    """Build the per-probe comparison table."""
    ping_by_probe = {r.get("prb_id"): r for r in ping_results}
    ssl_by_probe = {r.get("prb_id"): r for r in ssl_results}

    rows = []
    for pid in sorted(set(ping_by_probe) | set(ssl_by_probe)):
        ping_r = ping_by_probe.get(pid)
        ping_ok = bool(ping_r and ping_r.get("rcvd", 0) > 0)
        rtt = ping_r.get("avg") if ping_r else None
        rtt_clean = (
            round(rtt, 1)
            if isinstance(rtt, (int, float)) and rtt > 0
            else None
        )

        rows.append({
            "probe_id": pid,
            "ping_ok": ping_ok,
            "ping_rtt_ms": rtt_clean,
            "https_state": classify_ssl_result(ssl_by_probe.get(pid)),
        })
    return rows


def main():
    ids = [int(a) for a in sys.argv[1:]]
    if not ids:
        print(__doc__)
        sys.exit(1)

    if len(ids) == 1:
        results = fetch(ids[0])
        out = f"results_{ids[0]}.json"
        with open(out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved as {out}")
        return

    if len(ids) != 2:
        print("Pass one measurement ID, or two for a ping/sslcert pair.")
        sys.exit(1)

    ping_results = fetch(ids[0])
    ssl_results = fetch(ids[1])
    rows = compare(ping_results, ssl_results)

    out = f"connectivity_{ids[0]}_{ids[1]}.json"
    with open(out, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"\nSaved as {out}")

    n = {"OK": 0, "TLS_FAIL": 0, "UNREACHABLE": 0}
    for r in rows:
        n[r["https_state"]] += 1
    print(f"  {len(rows)} probes: {n['OK']} OK, "
          f"{n['TLS_FAIL']} TLS_FAIL, {n['UNREACHABLE']} unreachable")


if __name__ == "__main__":
    main()