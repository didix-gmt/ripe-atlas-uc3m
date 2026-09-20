#!/usr/bin/env python3
"""
fetch_results.py - re-fetch and classify the results of measurements that
already exist.

Reading results costs nothing. RIPE Atlas bills you when a measurement is
*created*; fetching what it produced is free and can be done as many times as
you like. So if a results file gets deleted, overwritten or lost, you do not
re-run the campaign - you re-fetch it with this script. Re-running would spend
credits a second time and, worse, would produce a different dataset, because
the network has moved on.

What it does
------------
For each measurement ID:
  1. reads the measurement's metadata (type, target, window);
  2. downloads every result;
  3. classifies each one;
  4. optionally groups the outcome by the probe's AS, which is the breakdown
     this project actually cares about - blocking is applied per operator;
  5. writes the raw results plus the classification to a JSON file.

Classification
--------------
HTTPS (sslcert) results get three states, never a boolean:

  OK           a certificate came back - the host answered TLS normally.
  TLS_FAIL     something spoke TLS and refused: an alert, or a handshake
               error. The TCP connection worked.
  UNREACHABLE  the connection never got far enough to speak TLS: timeout,
               refused, no route.

The distinction matters. Collapsing TLS_FAIL and UNREACHABLE into "failed"
hides which mechanism is at work, and the two have completely different
causes. See docs/08-pitfalls.md.

  !! TLS_FAIL IS NOT PROOF OF BLOCKING. Old probes carry an outdated TLS
     client that fails handshakes against modern servers all on its own. That
     bug once inflated our apparent blocking rate badly before it was caught.
     If you see TLS_FAIL, check the probe's age before concluding anything -
     campaign_match.py selects recent probes specifically to avoid this.

ICMP (ping) results get two:

  OK           at least one reply came back.
  NO_REPLY     none did.

  !! NO_REPLY IS NOT PROOF OF BLOCKING EITHER. Plenty of hosts drop ICMP as a
     matter of policy and serve HTTPS perfectly well - uc3m.es is one. This is
     exactly why the campaign pairs a ping with an sslcert against every
     target instead of trusting either alone.

Usage
-----
    python3 fetch_results.py 194568725
    python3 fetch_results.py 194568725 194568726 --probes
    python3 fetch_results.py 194568725 --out results_run1.json
    python3 fetch_results.py 194568725 --start "2026-08-22 19:10"

An API key is only needed for measurements created with is_public=False -
which is how real campaigns are created, so in practice you will want one.
It is read from RIPE_API_KEY in the environment or in a .env file.
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; the env var alone works fine

API = "https://atlas.ripe.net/api/v2"
API_KEY = os.getenv("RIPE_API_KEY", "")

# Standard TLS alert descriptions (RFC 5246 / RFC 8446), for readable output.
TLS_ALERTS = {
    0: "close_notify",
    10: "unexpected_message",
    20: "bad_record_mac",
    40: "handshake_failure",
    42: "bad_certificate",
    43: "unsupported_certificate",
    44: "certificate_revoked",
    45: "certificate_expired",
    46: "certificate_unknown",
    47: "illegal_parameter",
    48: "unknown_ca",
    49: "access_denied",
    50: "decode_error",
    51: "decrypt_error",
    70: "protocol_version",
    71: "insufficient_security",
    80: "internal_error",
    86: "inappropriate_fallback",
    90: "user_canceled",
    112: "unrecognized_name",
    113: "bad_certificate_status_response",
    120: "no_application_protocol",
}

# Error substrings that mean "never reached the TLS layer at all".
TRANSPORT_ERRORS = (
    "timeout", "timed out", "unreachable", "refused", "no route",
    "network is down", "connect:", "connection reset",
)


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------


def classify_ssl_result(res):
    """-> (state, detail). States: OK / TLS_FAIL / UNREACHABLE / UNKNOWN."""
    if res.get("cert"):
        rt = res.get("rt")
        ver = res.get("ver", "?")
        return "OK", f"TLS {ver}" + (f", {rt:.0f} ms" if isinstance(rt, (int, float)) else "")

    alert = res.get("alert")
    if isinstance(alert, dict):
        desc = alert.get("description")
        name = TLS_ALERTS.get(desc, "unknown alert")
        return "TLS_FAIL", f"alert {desc} ({name})"

    err = res.get("err")
    if err:
        low = str(err).lower()
        if any(k in low for k in TRANSPORT_ERRORS):
            return "UNREACHABLE", str(err)
        return "TLS_FAIL", str(err)

    return "UNKNOWN", "no cert, no alert, no error field"


def classify_ping_result(res):
    """-> (state, detail). States: OK / NO_REPLY."""
    sent = res.get("sent", 0)
    rcvd = res.get("rcvd", 0)
    if rcvd:
        avg = res.get("avg")
        detail = f"{rcvd}/{sent} replies"
        if isinstance(avg, (int, float)) and avg >= 0:
            detail += f", avg {avg:.1f} ms"
        return "OK", detail
    return "NO_REPLY", f"0/{sent} replies"


def classify(res, msm_type):
    if msm_type == "sslcert":
        return classify_ssl_result(res)
    if msm_type == "ping":
        return classify_ping_result(res)
    return "UNSUPPORTED", f"no classifier for measurement type '{msm_type}'"


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------


def headers():
    return {"Authorization": f"Key {API_KEY}"} if API_KEY else {}


def get_measurement(msm_id, timeout=30):
    r = requests.get(f"{API}/measurements/{msm_id}/", headers=headers(), timeout=timeout)
    if r.status_code in (401, 403):
        raise PermissionError(
            f"measurement {msm_id}: access denied. It is probably non-public - "
            "set RIPE_API_KEY to a key that can read it."
        )
    if r.status_code == 404:
        raise LookupError(f"measurement {msm_id}: not found")
    r.raise_for_status()
    return r.json()


def get_results(msm_id, start=None, stop=None, timeout=120):
    params = {}
    if start:
        params["start"] = start
    if stop:
        params["stop"] = stop
    r = requests.get(
        f"{API}/measurements/{msm_id}/results/",
        headers=headers(), params=params, timeout=timeout,
    )
    if r.status_code in (401, 403):
        raise PermissionError(
            f"measurement {msm_id}: results are not readable with this key."
        )
    r.raise_for_status()
    return r.json()


def get_probe_asns(probe_ids, timeout=60):
    """{probe_id: {'asn':..,'country':..}} from the public probes API (no key)."""
    out = {}
    ids = sorted(set(probe_ids))
    for i in range(0, len(ids), 100):  # keep the URL a sane length
        chunk = ids[i:i + 100]
        try:
            r = requests.get(
                f"{API}/probes/",
                params={"id__in": ",".join(str(p) for p in chunk), "page_size": 100},
                timeout=timeout,
            )
            r.raise_for_status()
            for p in r.json().get("results", []):
                out[p["id"]] = {
                    "asn": p.get("asn_v4") or p.get("asn_v6"),
                    "country": p.get("country_code"),
                }
        except requests.RequestException as exc:
            print(f"  ! probe metadata lookup failed for one chunk: {exc}",
                  file=sys.stderr)
    return out


def parse_time(text):
    """'2026-08-22 19:10' (UTC) -> unix timestamp."""
    if text is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            continue
    raise ValueError(f"cannot parse time '{text}' - use 'YYYY-MM-DD HH:MM' (UTC)")


# --------------------------------------------------------------------------


def process(msm_id, start=None, stop=None, want_probes=False):
    meta = get_measurement(msm_id)
    msm_type = meta.get("type")
    target = meta.get("target") or meta.get("target_ip") or "?"
    print(f"\n  Measurement {msm_id}  [{msm_type}]  -> {target}")
    print(f"    {meta.get('description', '(no description)')}")

    results = get_results(msm_id, start=start, stop=stop)
    print(f"    {len(results)} results")

    probe_meta = {}
    if want_probes and results:
        probe_meta = get_probe_asns([r.get("prb_id") for r in results if r.get("prb_id")])

    classified, states = [], Counter()
    per_asn = defaultdict(Counter)

    for res in results:
        state, detail = classify(res, msm_type)
        states[state] += 1
        prb = res.get("prb_id")
        info = probe_meta.get(prb, {})
        classified.append({
            "probe_id": prb,
            "probe_asn": info.get("asn"),
            "probe_country": info.get("country"),
            "timestamp": res.get("timestamp"),
            "state": state,
            "detail": detail,
        })
        if info.get("asn"):
            per_asn[info["asn"]][state] += 1

    total = sum(states.values()) or 1
    print(f"    {'state':<14}{'n':>6}{'share':>9}")
    for state, n in states.most_common():
        print(f"    {state:<14}{n:>6}{n / total:>8.0%}")

    if per_asn:
        print(f"\n    Per AS (blocking is applied per operator):")
        for asn in sorted(per_asn, key=lambda a: -sum(per_asn[a].values())):
            counts = per_asn[asn]
            n = sum(counts.values())
            summary = "  ".join(f"{s}={c}" for s, c in counts.most_common())
            print(f"      AS{asn:<8} n={n:<4} {summary}")

    return {
        "measurement_id": msm_id,
        "type": msm_type,
        "target": target,
        "description": meta.get("description"),
        "start_time": meta.get("start_time"),
        "stop_time": meta.get("stop_time"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(results),
        "state_counts": dict(states),
        "per_asn": {str(a): dict(c) for a, c in per_asn.items()},
        "classified": classified,
        "raw": results,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Re-fetch and classify results of existing measurements (free)."
    )
    ap.add_argument("ids", nargs="+", type=int, help="measurement ID(s)")
    ap.add_argument("--out", default=None,
                    help="output JSON file (default: results_<ids>.json)")
    ap.add_argument("--probes", action="store_true",
                    help="look up each probe's AS and break results down by operator")
    ap.add_argument("--start", default=None,
                    help="only results at/after this UTC time, 'YYYY-MM-DD HH:MM'")
    ap.add_argument("--stop", default=None,
                    help="only results at/before this UTC time")
    args = ap.parse_args()

    try:
        start = parse_time(args.start)
        stop = parse_time(args.stop)
    except ValueError as exc:
        print(f"  ! {exc}", file=sys.stderr)
        return 1

    if not API_KEY:
        print("  Note: no RIPE_API_KEY set - only public measurements are readable.")

    payload = []
    for msm_id in args.ids:
        try:
            payload.append(process(msm_id, start, stop, args.probes))
        except (PermissionError, LookupError) as exc:
            print(f"  ! {exc}", file=sys.stderr)
        except requests.RequestException as exc:
            print(f"  ! measurement {msm_id}: request failed: {exc}", file=sys.stderr)

    if not payload:
        print("\n  Nothing fetched.", file=sys.stderr)
        return 1

    out = args.out or "results_" + "_".join(str(i) for i in args.ids) + ".json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"\n  Wrote {out}  ({len(payload)} measurement(s))")
    print("  No credits were spent: reading results is free.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
