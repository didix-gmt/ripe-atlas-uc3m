#!/usr/bin/env python3
"""
Connectivity campaign - Ping vs HTTPS (SSL/TLS handshake)
===========================================================
Objective: compare ICMP reachability (ping) with actual service
reachability (HTTPS / TLS handshake on port 443) for the same target,
from the same set of probes, at the same time.

Why this matters for our project: some targets drop ICMP but still
serve HTTPS (e.g. uc3m.es), and conversely a blocking mechanism might
filter TCP/443 while leaving ICMP untouched. Running both tests
together, from the same probes, lets us tell these cases apart -
which is exactly the diagnostic signature described on doc page 1
(DNS blocking vs IP blocking have different fingerprints).

Note on measurement types: RIPE Atlas's native "HTTP" measurement
type can only target anchors, not arbitrary domains. The practical
substitute for "does this service respond over HTTPS?" on any target
is the "Sslcert" measurement type: it performs a TCP connect + TLS
handshake on port 443 and reports success/failure plus certificate
details.

IMPORTANT - not all failures mean blocking:
    A TLS "handshake_failure" (alert 40) means the TCP connection on
    port 443 SUCCEEDED and the server answered - only the crypto
    negotiation failed afterwards. Old RIPE Atlas probes (v1/v2, low
    probe IDs) ship an outdated TLS client that cannot negotiate with
    modern servers, producing handshake failures that have nothing to
    do with blocking. Reading those as "blocked" would produce massive
    false positives.
    Only a total absence of response (no cert, no alert) indicates the
    packets never got through - that is the signature that matters for
    blocking detection.
    This script therefore classifies HTTPS results in three states
    (OK / TLS_FAIL / UNREACHABLE) rather than a boolean, and only
    counts UNREACHABLE as a suspicious mismatch.

Requirements:
    pip install ripe-atlas-cousteau requests python-dotenv
"""

import time
import json
import os
import requests
from dotenv import load_dotenv
from ripe.atlas.cousteau import (
    Ping,
    Sslcert,
    AtlasSource,
    AtlasCreateRequest,
    AtlasResultsRequest,
)

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

load_dotenv()
API_KEY = os.getenv("RIPE_API_KEY", "")

TARGET = "uc3m.es"   # drops ICMP but should answer HTTPS - good test case

COUNTRIES = {
    "ES": "Spain",
    "DE": "Germany",
    "GB": "UK",
    "US": "USA",
    "BR": "Brazil",
    "JP": "Japan",
}

# Target Spanish ISPs for the real campaign. Five, not three: DIGI and
# MasMovil have more probes than Orange or Vodafone and both show
# distinctive blocking behaviour in the OONI report. See probe_profile.py
# for the coverage figures behind this choice.
SPANISH_ISPS = {
    3352:  "Movistar / Telefonica",
    57269: "DIGI Spain",
    12479: "Orange Espana",
    15704: "MasMovil",
    12430: "Vodafone Espana",
}

N_PER_COUNTRY = 3
CANDIDATE_POOL = 100   # how many probes to fetch per country before filtering
POLL_INTERVAL = 30
MAX_WAIT = 900

# Whether the resulting measurements should be publicly listed on
# atlas.ripe.net. Keep True for this toy test; switch to False for
# the real La Liga campaign (see doc page 6).
IS_PUBLIC = True


# ── STEP 1: Select probes, favouring recent hardware ──────────────────────────

def select_probes():
    """
    Fetch a wide pool of connected probes per country, then keep the
    highest probe IDs.

    RIPE Atlas assigns probe IDs sequentially, so a high ID means more
    recent hardware and firmware. This matters a lot here: the API's
    default ordering returns the LOWEST ids first, i.e. the oldest
    probes (v1/v2 hardware from 2010-2011), whose obsolete TLS client
    fails the handshake against modern servers. Selecting those would
    fill the results with false "failures" unrelated to connectivity.
    """
    probe_ids = []
    probe_meta = {}

    print("Selecting probes (favouring recent hardware)...")
    for cc, label in COUNTRIES.items():
        url = "https://atlas.ripe.net/api/v2/probes/"
        params = {
            "country_code": cc,
            "status": 1,
            "tags": "system-ipv4-works",
            "page_size": CANDIDATE_POOL,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except Exception as e:
            print(f"  [{label}] Could not fetch probes: {e}")
            continue

        candidates = sorted(
            (p for p in results if p.get("id")),
            key=lambda p: p["id"],
            reverse=True,
        )[:N_PER_COUNTRY]

        for p in candidates:
            probe_ids.append(p["id"])
            probe_meta[p["id"]] = {"label": label}

        ids_preview = ", ".join(str(p["id"]) for p in candidates)
        print(f"  {label:10s} ({cc}): {len(candidates)} probe(s) -> {ids_preview}")

    print(f"\nTotal probes selected: {len(probe_ids)}")
    return probe_ids, probe_meta


# ── STEP 2: Launch BOTH ping and sslcert in one request ───────────────────────

def launch_measurement(probe_ids):
    """
    Create ping + sslcert measurements in a single API call, so they
    share the same probes and the same start/stop time - this is
    what makes the comparison meaningful.
    """
    ping = Ping(
        af=4,
        target=TARGET,
        packets=3,
        description=f"Connectivity check (ping) - {TARGET}",
    )
    sslcert = Sslcert(
        af=4,
        target=TARGET,
        port=443,
        description=f"Connectivity check (HTTPS/TLS) - {TARGET}",
    )

    source = AtlasSource(
        type="probes",
        value=",".join(str(pid) for pid in probe_ids),
        requested=len(probe_ids),
    )

    request = AtlasCreateRequest(
        key=API_KEY,
        measurements=[ping, sslcert],
        sources=[source],
        is_oneoff=True,
        is_public=IS_PUBLIC,
    )

    success, response = request.create()
    if not success:
        raise RuntimeError(f"Measurement creation failed: {response}")

    msm_ids = response["measurements"]
    print(f"\nMeasurements created - IDs: {msm_ids}")
    for msm_id in msm_ids:
        print(f"  https://atlas.ripe.net/measurements/{msm_id}/")

    # Ping: 3 packets x 3 credits x 2 (one-off) = 18 credits/probe
    # Sslcert: 1 result x 10 credits x 2 (one-off) = 20 credits/probe
    estimated_cost = len(probe_ids) * (3 * 3 * 2 + 10 * 2)
    print(f"Estimated total cost: ~{estimated_cost} credits")

    return msm_ids


# ── STEP 3: Wait for both measurements ─────────────────────────────────────────

def wait_for_completion(msm_ids):
    print(f"\nWaiting for results (polling every {POLL_INTERVAL}s, max {MAX_WAIT//60} min)...")
    elapsed = 0
    while elapsed < MAX_WAIT:
        statuses = {}
        for msm_id in msm_ids:
            try:
                resp = requests.get(
                    f"https://atlas.ripe.net/api/v2/measurements/{msm_id}/",
                    headers={"Authorization": f"Key {API_KEY}"},
                    timeout=10,
                )
                statuses[msm_id] = resp.json().get("status", {}).get("name", "Unknown")
            except Exception as e:
                statuses[msm_id] = f"(error: {e})"

        print(f"  [{elapsed:4d}s] " + ", ".join(f"{k}={v}" for k, v in statuses.items()))
        if all(v == "Stopped" for v in statuses.values()):
            print("  Both measurements complete.")
            return True

        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    print("  Timeout reached - results may be incomplete.")
    return False


# ── STEP 4: Fetch and compare results ─────────────────────────────────────────

def classify_ssl_result(ssl_r):
    """
    Turn a raw sslcert result into one of three states.

    OK          : certificate returned, no TLS alert -> service reachable.
    TLS_FAIL    : the server answered but the handshake failed (alert).
                  TCP/443 got through, so this is NOT evidence of blocking;
                  on old probes it is almost always a client-side TLS
                  limitation.
    UNREACHABLE : no certificate and no alert -> nothing came back at all.
                  This is the state that actually suggests filtering.
    """
    if not ssl_r:
        return "UNREACHABLE"
    if ssl_r.get("cert") and "alert" not in ssl_r:
        return "OK"
    if "alert" in ssl_r:
        return "TLS_FAIL"
    return "UNREACHABLE"


def fetch_and_compare(msm_ids, probe_meta):
    """
    Fetch results for both measurements and build a per-probe
    comparison: did ping succeed? what state is the TLS handshake in?
    """
    ping_msm, ssl_msm = msm_ids[0], msm_ids[1]

    print(f"\nFetching ping results (measurement {ping_msm})...")
    ping_success, ping_results = AtlasResultsRequest(msm_id=ping_msm, key=API_KEY).create()

    print(f"Fetching HTTPS/TLS results (measurement {ssl_msm})...")
    ssl_success, ssl_results = AtlasResultsRequest(msm_id=ssl_msm, key=API_KEY).create()

    if not ping_success or not ssl_success:
        raise RuntimeError("Failed to fetch one or both result sets")

    ping_by_probe = {r.get("prb_id"): r for r in ping_results}
    ssl_by_probe = {r.get("prb_id"): r for r in ssl_results}

    all_probe_ids = set(ping_by_probe) | set(ssl_by_probe)

    rows = []
    for pid in sorted(all_probe_ids):
        label = probe_meta.get(pid, {}).get("label", "?")

        ping_r = ping_by_probe.get(pid)
        ping_ok = bool(ping_r and ping_r.get("rcvd", 0) > 0)
        ping_rtt = ping_r.get("avg") if ping_r else None
        rtt_clean = (
            round(ping_rtt, 1)
            if isinstance(ping_rtt, (int, float)) and ping_rtt > 0
            else None
        )

        ssl_state = classify_ssl_result(ssl_by_probe.get(pid))

        rows.append({
            "probe_id": pid,
            "country": label,
            "ping_ok": ping_ok,
            "ping_rtt_ms": rtt_clean,
            "https_state": ssl_state,
        })

    return rows


def print_summary(rows):
    print(f"\n{'Probe':>8} {'Country':<10} {'Ping':<8} {'RTT (ms)':<10} {'HTTPS':<13} {'Note'}")
    print("-" * 80)

    n_ok = n_tls_fail = n_unreachable = 0

    for r in rows:
        ping_str = "OK" if r["ping_ok"] else "FAIL"
        rtt_str = str(r["ping_rtt_ms"]) if r["ping_rtt_ms"] is not None else "-"
        state = r["https_state"]

        note = ""
        if state == "OK":
            n_ok += 1
            if not r["ping_ok"]:
                note = "ICMP dropped, service fine"
        elif state == "TLS_FAIL":
            n_tls_fail += 1
            note = "probe-side TLS issue, not blocking"
        else:
            n_unreachable += 1
            note = "no response at all - possible filtering"

        print(f"{r['probe_id']:>8} {r['country']:<10} {ping_str:<8} {rtt_str:<10} {state:<13} {note}")

    print("-" * 80)
    print(f"Total probes: {len(rows)}")
    print(f"  HTTPS OK          : {n_ok}")
    print(f"  TLS handshake fail: {n_tls_fail}  (server answered - NOT evidence of blocking)")
    print(f"  Unreachable       : {n_unreachable}  (nothing came back - worth investigating)")

    if n_unreachable:
        print("\nOnly the 'Unreachable' rows are candidate blocking signals.")
        print("Cross-check them against probes in other countries before")
        print("concluding anything: a target unreachable everywhere is down,")
        print("a target unreachable only from one country is being filtered.")
    else:
        print("\nNo unreachable probes: the service answered on TCP/443 from")
        print("every vantage point, so there is no sign of filtering here.")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    if not API_KEY:
        raise ValueError("RIPE_API_KEY not set - check your .env file.")

    probe_ids, probe_meta = select_probes()
    if not probe_ids:
        raise RuntimeError("No probes selected - check your internet connection.")

    msm_ids = launch_measurement(probe_ids)
    wait_for_completion(msm_ids)

    rows = fetch_and_compare(msm_ids, probe_meta)

    out_file = f"connectivity_{msm_ids[0]}_{msm_ids[1]}.json"
    with open(out_file, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"\nResults saved as {out_file}")

    print_summary(rows)


if __name__ == "__main__":
    main()