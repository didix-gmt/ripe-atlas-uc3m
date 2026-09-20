#!/usr/bin/env python3
"""
select_targets.py - build a stratified sample of target IPs for a match campaign.

Source data
-----------
OONI's published list of IP addresses affected by LALIGA IP-blocking in Spain:

    https://ooni.org/post/2026-laliga-collateral/data/20260629-all-affected-ips.csv

The file has exactly two columns, `ip` and `ip_asn`. No provider names, no
per-IP impact figures. Everything else this script does - provider grouping,
concentration, quotas - is derived from those two columns and nothing else.

Why sample at all
-----------------
The published list holds roughly 7,400 addresses. A campaign measures every
target from every probe at every interval, so cost scales linearly with the
number of targets: measuring all of them is not affordable. What we want is a
few dozen addresses that between them represent the *shape* of the blocking,
rather than a random handful that all turn out to be Cloudflare edge IPs.

Stratification
--------------
Five strata, all computed from the CSV itself:

  cloudflare_dense    AS13335, sitting in a /24 that holds many other affected
                      IPs. Range-level sweeps - the bulk of the collateral
                      damage OONI documented.
  cloudflare_sparse   AS13335, in a /24 with few affected IPs. Individually
                      caught Cloudflare addresses rather than swept ranges.
  major_cdn           AWS / Akamai / Fastly / Google / Microsoft. Shared
                      hosting outside Cloudflare.
  high_concentration  Any other AS among the top contributors by affected-IP
                      count - smaller hosts that took a disproportionate hit.
  long_tail           Everything else: one-off addresses at small providers.

`--verify` prints the resulting split without writing anything, so the two
tunables below (DENSE_24_THRESHOLD, TOP_ASN_COUNT) can be sanity-checked
against the real data before committing to a target list.

PROVENANCE - read this before assuming reproducibility
------------------------------------------------------
The original version of this script was lost before it was ever committed
(see HANDOVER.md). This is a rebuild against the same source CSV. The strata
are a reasonable reconstruction of the original intent, not a byte-identical
recovery of it, so re-running this will NOT reproduce the committed
`targets.txt`. That file is kept as-is precisely because it is the list the
original script produced, and it is the list any already-planned campaign
should use. Use this script to extend or refresh the list, not to regenerate
a past one.

Usage
-----
    python3 select_targets.py --verify
    python3 select_targets.py --count 20
    python3 select_targets.py --count 20 --out targets.txt
    python3 select_targets.py --csv ./local-copy.csv --count 30

Costs nothing: this only reads a published file, it creates no measurements.
"""

import argparse
import csv
import io
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import requests

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

OONI_CSV_URL = (
    "https://ooni.org/post/2026-laliga-collateral/"
    "data/20260629-all-affected-ips.csv"
)

# OONI's own worked example: most Spanish ISPs block this address shortly
# before kick-off and lift the block soon after the match. It is our one piece
# of external ground truth, so it is always in the sample regardless of how
# the dice land. See docs/09-probe-coverage-spain.md.
VALIDATION_IP = "188.114.97.5"

CLOUDFLARE_ASN = 13335

# Only ASNs cross-checked against RIPE WHOIS / bgp.he.net are named here. The
# map is deliberately short: every other AS is categorised from the data, by
# how many affected IPs it contributes, so an unnamed AS is never mislabelled.
# Look any unfamiliar ASN up on bgp.he.net before quoting a name in a write-up.
MAJOR_CDN_ASNS = {
    16509: "Amazon AWS",
    14618: "Amazon AWS",
    20940: "Akamai",
    16625: "Akamai",
    54113: "Fastly",
    15169: "Google",
    8075: "Microsoft",
}

# A /24 holding at least this many affected IPs counts as a swept range rather
# than an individually caught address. Tunable - run --verify after changing.
DENSE_24_THRESHOLD = 8

# How many non-CDN ASNs (by affected-IP count) count as "high concentration".
TOP_ASN_COUNT = 10

# Share of the sample given to each stratum. Must sum to 1.0.
QUOTAS = [
    ("cloudflare_dense", 0.30),
    ("cloudflare_sparse", 0.25),
    ("major_cdn", 0.15),
    ("high_concentration", 0.15),
    ("long_tail", 0.15),
]

# Fixed so the same --count gives the same list on every run of THIS version.
SEED = 42

STRATUM_NOTES = {
    "cloudflare_dense": "Cloudflare, swept /24 range",
    "cloudflare_sparse": "Cloudflare, isolated address",
    "major_cdn": "major CDN / cloud host",
    "high_concentration": "high-impact non-CDN AS",
    "long_tail": "small provider, one-off",
}


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_rows(csv_path=None, url=OONI_CSV_URL, timeout=30):
    """Return [(ip, asn), ...] from a local CSV or the published OONI file."""
    if csv_path:
        with open(csv_path, "r", encoding="utf-8") as fh:
            text = fh.read()
        origin = csv_path
    else:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
        origin = url

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError(f"{origin}: file is empty")

    fields = [f.strip().lower() for f in reader.fieldnames]
    if "ip" not in fields:
        raise ValueError(
            f"{origin}: expected an 'ip' column, found {reader.fieldnames}. "
            "OONI may have changed the file format - check the report page."
        )
    asn_field = "ip_asn" if "ip_asn" in fields else None

    rows = []
    for raw in reader:
        clean = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        ip = clean.get("ip", "")
        if not ip:
            continue
        asn_text = clean.get(asn_field, "") if asn_field else ""
        try:
            asn = int(asn_text)
        except ValueError:
            asn = 0  # unknown / unparseable - falls into long_tail
        rows.append((ip, asn))

    if not rows:
        raise ValueError(f"{origin}: no usable rows found")
    return rows, origin


# --------------------------------------------------------------------------
# Stratification
# --------------------------------------------------------------------------


def slash24(ip):
    """'104.26.9.44' -> '104.26.9.'  (string prefix, no ipaddress needed)."""
    parts = ip.split(".")
    return ".".join(parts[:3]) + "." if len(parts) == 4 else ip


def build_strata(rows):
    """Split rows into the five strata. Returns (buckets, stats)."""
    per_24 = Counter(slash24(ip) for ip, _ in rows)
    per_asn = Counter(asn for _, asn in rows)

    # Top non-CDN ASNs by affected-IP count.
    excluded = set(MAJOR_CDN_ASNS) | {CLOUDFLARE_ASN, 0}
    ranked = [(asn, n) for asn, n in per_asn.most_common() if asn not in excluded]
    high_conc_asns = {asn for asn, _ in ranked[:TOP_ASN_COUNT]}

    buckets = defaultdict(list)
    for ip, asn in rows:
        if asn == CLOUDFLARE_ASN:
            dense = per_24[slash24(ip)] >= DENSE_24_THRESHOLD
            buckets["cloudflare_dense" if dense else "cloudflare_sparse"].append((ip, asn))
        elif asn in MAJOR_CDN_ASNS:
            buckets["major_cdn"].append((ip, asn))
        elif asn in high_conc_asns:
            buckets["high_concentration"].append((ip, asn))
        else:
            buckets["long_tail"].append((ip, asn))

    stats = {
        "total": len(rows),
        "distinct_asns": len(per_asn),
        "high_conc_asns": ranked[:TOP_ASN_COUNT],
    }
    return buckets, stats


def allocate(count, buckets):
    """Turn the quota shares into integer per-stratum counts."""
    alloc = {}
    for name, share in QUOTAS:
        alloc[name] = min(int(count * share), len(buckets.get(name, [])))

    # Hand out whatever rounding left over, largest stratum first, never
    # asking a stratum for more IPs than it actually holds.
    leftover = count - sum(alloc.values())
    order = sorted(QUOTAS, key=lambda q: q[1], reverse=True)
    while leftover > 0:
        progressed = False
        for name, _ in order:
            if leftover == 0:
                break
            if alloc[name] < len(buckets.get(name, [])):
                alloc[name] += 1
                leftover -= 1
                progressed = True
        if not progressed:
            break  # every stratum exhausted; sample will be short of `count`
    return alloc


def sample_targets(buckets, count, seed=SEED):
    rng = random.Random(seed)
    alloc = allocate(count, buckets)

    chosen = []
    for name, _ in QUOTAS:
        pool = sorted(buckets.get(name, []))  # sort first: dict order is not a guarantee
        take = alloc[name]
        if take:
            chosen.extend((ip, asn, name) for ip, asn in rng.sample(pool, take))

    # Force the validation IP in, replacing a same-stratum pick if needed.
    if not any(ip == VALIDATION_IP for ip, _, _ in chosen):
        home = next(
            (name for name, entries in buckets.items()
             if any(ip == VALIDATION_IP for ip, _ in entries)),
            None,
        )
        if home:
            for i, (_, _, name) in enumerate(chosen):
                if name == home:
                    chosen[i] = (VALIDATION_IP, CLOUDFLARE_ASN, home)
                    break
            else:
                chosen.append((VALIDATION_IP, CLOUDFLARE_ASN, home))
        else:
            print(
                f"  ! {VALIDATION_IP} is not in this CSV - skipping the pin. "
                "Check whether OONI republished the file.",
                file=sys.stderr,
            )

    order = {name: i for i, (name, _) in enumerate(QUOTAS)}
    chosen.sort(key=lambda t: (order[t[2]], t[0]))
    return chosen, alloc


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def write_targets(path, chosen, origin, stats):
    """Write targets.txt.

    Annotations are full-line comments above each block rather than inline,
    so the file parses under any reasonable reader - including one that only
    strips lines starting with '#'.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Target IPs for a LALIGA match campaign.",
        f"# Generated {now} by select_targets.py",
        f"# Source: {origin}",
        f"# Sampled {len(chosen)} of {stats['total']} affected IPs "
        f"across {stats['distinct_asns']} ASNs.",
        "#",
        "# One IP per line. Lines starting with '#' are comments.",
        "",
    ]

    current = None
    for ip, asn, stratum in chosen:
        if stratum != current:
            current = stratum
            n = sum(1 for _, _, s in chosen if s == stratum)
            lines.append(f"# --- {stratum} ({n}) - {STRATUM_NOTES[stratum]}")
        name = MAJOR_CDN_ASNS.get(asn) or ("Cloudflare" if asn == CLOUDFLARE_ASN else None)
        label = f"AS{asn}" + (f" {name}" if name else "")
        if ip == VALIDATION_IP:
            label += "  <- OONI worked example, validation ground truth"
        lines.append(f"{ip}  # {label}")
    lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def print_report(buckets, stats, alloc=None):
    print(f"  Affected IPs in source : {stats['total']:,}")
    print(f"  Distinct ASNs          : {stats['distinct_asns']:,}")
    print()
    print(f"  {'stratum':<20} {'available':>10} {'sampled':>9}")
    print(f"  {'-' * 20} {'-' * 10} {'-' * 9}")
    for name, _ in QUOTAS:
        got = alloc.get(name, 0) if alloc else 0
        print(f"  {name:<20} {len(buckets.get(name, [])):>10,} {got:>9}")
    print()
    print(f"  Top non-CDN ASNs by affected-IP count (the "
          f"'high_concentration' stratum, TOP_ASN_COUNT={TOP_ASN_COUNT}):")
    for asn, n in stats["high_conc_asns"]:
        print(f"    AS{asn:<8} {n:>6,} IPs")
    print("    (names not resolved here on purpose - look them up on bgp.he.net)")


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description="Build a stratified target list from OONI's affected-IP data."
    )
    ap.add_argument("--count", type=int, default=20,
                    help="how many target IPs to select (default: 20)")
    ap.add_argument("--out", default="targets.txt",
                    help="output file (default: targets.txt)")
    ap.add_argument("--csv", default=None,
                    help="read a local copy of the CSV instead of downloading it")
    ap.add_argument("--url", default=OONI_CSV_URL,
                    help="override the source URL")
    ap.add_argument("--seed", type=int, default=SEED,
                    help=f"sampling seed (default: {SEED})")
    ap.add_argument("--verify", action="store_true",
                    help="show the stratum breakdown and exit without writing")
    args = ap.parse_args()

    print("Loading OONI affected-IP list...")
    try:
        rows, origin = load_rows(csv_path=args.csv, url=args.url)
    except requests.RequestException as exc:
        print(f"  ! Could not download the CSV: {exc}", file=sys.stderr)
        print("    Download it by hand and pass it with --csv.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"  ! {exc}", file=sys.stderr)
        return 1

    buckets, stats = build_strata(rows)

    if args.verify:
        print()
        print_report(buckets, stats)
        return 0

    chosen, alloc = sample_targets(buckets, args.count, seed=args.seed)
    print()
    print_report(buckets, stats, alloc)

    if len(chosen) < args.count:
        print(f"  ! Only {len(chosen)} IPs available, asked for {args.count}.")

    write_targets(args.out, chosen, origin, stats)
    print()
    print(f"  Wrote {len(chosen)} targets to {args.out}")
    print(f"  Seed {args.seed} - same seed and count gives the same list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
