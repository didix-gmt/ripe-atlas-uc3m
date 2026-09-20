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
The published list holds 7,374 addresses. A campaign measures every target from
every probe at every interval, so cost scales linearly with the number of
targets: measuring all of them is not affordable. What we want is a few dozen
addresses that between them represent the *shape* of the blocking, rather than
a random handful that all turn out to be the same thing.

What the data actually looks like
---------------------------------
Measured on the published CSV (September 2026):

    total                 7,374 addresses across 33 ASNs
    Amazon AWS            5,097   69.1%   (AS16509 4,286 + AS14618 811)
    Cloudflare            2,215   30.0%   (AS13335)
    everything else          62    0.8%   (30 ASNs, the largest holding 6)

So this is a two-provider story: AWS and Cloudflare together account for 99.2%
of all affected addresses, and by address count **AWS is the larger half**.

That is worth stating carefully, because it does not contradict OONI's
write-up, which foregrounds Cloudflare. The two measure different things. By
*address* count AWS dominates. By *sites affected* Cloudflare dominates, since
a single Cloudflare anycast address fronts a very large number of unrelated
sites while an AWS address usually fronts few. Both statements are true; a
write-up has to say which one it is making.

Two things that are NOT in the data, despite being worth checking: Google
(AS15169), Fastly (AS54113) and Akamai's AS16625 contribute zero affected
addresses. Akamai's AS20940 contributes 4 and Microsoft 2 - trace amounts that
sit in the tail, not a category of their own.

Canary targets
--------------
Two addresses go into every target list that are NOT from OONI's data and are
NOT sampled: `1.1.1.1` and `8.8.8.8`, the Cloudflare and Google public
resolvers. They are expected never to be blocked. If one of them goes
unreachable from Spain during a match, the measurement is broken rather than
the network — they are there to fail loudly when something is wrong with our
own pipeline.

This is a different job from the out-of-country control *probes* in
`campaign_match.py`. Those answer "is this target up at all?". The canaries
answer "is our measurement working at all from inside Spain?". Both are
needed: without canaries, a measurement-side failure reads as blocking.

They cost credits like any other target, which is why there are two and not
ten. `--no-canaries` omits them.

Stratification
--------------
Five strata, all computed from the CSV itself:

  cloudflare_dense   AS13335, in a /24 holding many other affected addresses.
  cloudflare_sparse  AS13335, in a /24 holding few. Individually caught
                     addresses rather than swept ranges.
  aws_dense          AS16509/AS14618, same /24 test.
  aws_sparse         AS16509/AS14618, sparse.
  other_providers    The 0.8% tail - 30 small ASNs.

The dense/sparse split is applied to both big providers for the same reason:
it distinguishes range-level sweeps from individually targeted addresses, which
is a question about *how* the blocking is implemented and therefore about how
much collateral damage it can do. Run `--verify` to see how each provider
actually splits - that result is itself a finding worth recording.

THE SAMPLE IS DELIBERATELY NOT PROPORTIONAL - read this before quoting any
per-stratum figure
-----------------------------------------------------------------------
Proportional to address count, a sample would be ~69% AWS, ~30% Cloudflare,
~1% everything else. The quotas below give AWS 50%, Cloudflare 40% and the
tail 10%. That is a choice, not an oversight:

  - Cloudflare is over-weighted (40% of the sample, 30% of the addresses)
    because each of its anycast addresses carries more collateral damage than
    an AWS address does. OONI puts a number on this: **501,305 of the 554,507
    affected domains — 90.4% — sat behind just 2,218 Cloudflare addresses.**
    So 30% of the addresses account for roughly 90% of the domain-level
    damage. The research question is about damage to legitimate sites, so the
    sample leans toward where that damage concentrates. Note that a *purely*
    impact-weighted design would go much further than 40%; this is a middle
    position that still characterises the address-dominant provider.
  - `other_providers` is heavily over-weighted (10% of the sample, 0.8% of the
    addresses) for a different reason: with 62 addresses in total it can never
    support a rate, but including two or three of them is what tells you
    whether the blocking reaches beyond the two big platforms at all. Treat
    findings there as presence/absence, never as a percentage.

If a future analysis needs address-proportional representativeness instead -
to state what fraction of *addresses* were blocked, say - set QUOTAS to the
shares above and say so in the write-up. Either choice is defensible; leaving
it unstated is not. Worth putting to Pablo before the first real campaign is
analysed.

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

# The two providers that between them hold 99.2% of the affected addresses.
CLOUDFLARE_ASN = 13335
AWS_ASNS = {16509, 14618}

# Addresses expected NEVER to be blocked, written into every list. Not sampled,
# not from OONI's data. If one of these goes unreachable from Spain during a
# match, the fault is ours, not the network's. See the docstring.
CANARY_TARGETS = {
    "1.1.1.1": "Cloudflare public resolver - canary, must never be blocked",
    "8.8.8.8": "Google public resolver - canary, must never be blocked",
}

# Names for readable output only - they play no part in classification. Each
# was cross-checked against RIPE WHOIS / bgp.he.net. Google (15169), Fastly
# (54113) and Akamai's 16625 are listed because they were checked and found to
# contribute zero affected addresses; that absence is itself worth recording.
KNOWN_ASNS = {
    13335: "Cloudflare",
    16509: "Amazon AWS",
    14618: "Amazon AWS",
    20940: "Akamai",
    16625: "Akamai",
    54113: "Fastly",
    15169: "Google",
    8075: "Microsoft",
}

# A /24 holding at least this many affected addresses counts as a swept range
# rather than an individually caught address. Tunable - run --verify after
# changing it. On the real data this puts 82% of Cloudflare's addresses in the
# dense bucket, matching OONI's description of range-level sweeps.
DENSE_24_THRESHOLD = 8

# Reporting only: how many tail ASNs --verify lists. No effect on sampling.
TOP_ASN_COUNT = 10

# Share of the sample given to each stratum. Must sum to 1.0.
# Deliberately not proportional to address counts - see the docstring.
QUOTAS = [
    ("cloudflare_dense", 0.25),
    ("cloudflare_sparse", 0.15),
    ("aws_dense", 0.30),
    ("aws_sparse", 0.20),
    ("other_providers", 0.10),
]

# Fixed so the same --count gives the same list on every run of THIS version.
SEED = 42

STRATUM_NOTES = {
    "cloudflare_dense": "Cloudflare, swept /24 range",
    "cloudflare_sparse": "Cloudflare, isolated address",
    "aws_dense": "Amazon AWS, swept /24 range",
    "aws_sparse": "Amazon AWS, isolated address",
    "other_providers": "small provider - presence check only, never a rate",
}


def asn_label(asn):
    name = KNOWN_ASNS.get(asn)
    return f"AS{asn}" + (f" {name}" if name else "")


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_rows(csv_path=None, url=OONI_CSV_URL, timeout=30):
    """Return ([(ip, asn), ...], origin) from a local CSV or the OONI file."""
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
            asn = 0  # unknown / unparseable - falls into other_providers
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

    buckets = defaultdict(list)
    for ip, asn in rows:
        dense = per_24[slash24(ip)] >= DENSE_24_THRESHOLD
        if asn == CLOUDFLARE_ASN:
            buckets["cloudflare_dense" if dense else "cloudflare_sparse"].append((ip, asn))
        elif asn in AWS_ASNS:
            buckets["aws_dense" if dense else "aws_sparse"].append((ip, asn))
        else:
            buckets["other_providers"].append((ip, asn))

    big = AWS_ASNS | {CLOUDFLARE_ASN}
    tail = [(asn, n) for asn, n in per_asn.most_common() if asn not in big]

    stats = {
        "total": len(rows),
        "distinct_asns": len(per_asn),
        "tail_asns": tail,
        "cloudflare": per_asn[CLOUDFLARE_ASN],
        "aws": sum(per_asn[a] for a in AWS_ASNS),
        "absent_checked": [a for a in (15169, 54113, 16625) if per_asn[a] == 0],
    }
    return buckets, stats


def allocate(count, buckets):
    """Turn the quota shares into integer per-stratum counts."""
    alloc = {}
    for name, share in QUOTAS:
        alloc[name] = min(int(count * share), len(buckets.get(name, [])))

    # Hand out whatever rounding left over, largest stratum first, never asking
    # a stratum for more addresses than it actually holds. This is also what
    # keeps the script correct if a stratum turns out much smaller than its
    # quota assumes - the shortfall moves to the strata that can absorb it.
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
                # No pick from the validation IP's own stratum to swap out. Take
                # the place of another pick rather than growing past `count`, so
                # the file never holds more addresses than were asked for.
                if chosen and len(chosen) >= count:
                    chosen[-1] = (VALIDATION_IP, CLOUDFLARE_ASN, home)
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


def write_targets(path, chosen, origin, stats, canaries=True):
    """Write targets.txt.

    Annotations are full-line comments above each block rather than inline, so
    the file parses under any reasonable reader - including one that only
    strips lines starting with '#'.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n_canary = len(CANARY_TARGETS) if canaries else 0
    lines = [
        "# Target IPs for a LALIGA match campaign.",
        f"# Generated {now} by select_targets.py",
        f"# Source: {origin}",
        f"# {len(chosen)} addresses sampled from {stats['total']} affected "
        f"across {stats['distinct_asns']} ASNs"
        + (f", plus {n_canary} canaries." if n_canary else "."),
        "#",
        "# The sample is NOT proportional to the source distribution -",
        "# Cloudflare and the small-provider tail are deliberately",
        "# over-weighted. Read the header of select_targets.py before quoting",
        "# any per-stratum figure.",
        "#",
        f"# Cost scales with every address below, canaries included:",
        f"# {len(chosen) + n_canary} targets is the number the cost estimate uses.",
        "#",
        "# One IP per line. Lines starting with '#' are comments.",
        "",
    ]

    if canaries:
        lines += [
            "# === Canaries ======================================================",
            "# Expected NEVER to be blocked, and not part of the OONI sample. If",
            "# one of these goes unreachable from Spain during a match, the",
            "# measurement is broken rather than the network. They are here to",
            "# fail loudly when the fault is ours.",
        ]
        for ip, note in CANARY_TARGETS.items():
            lines.append(f"{ip}  # {note}")
        lines.append("")

    lines.append("# === Sampled from OONI's affected-address list =====================")
    current = None
    for ip, asn, stratum in chosen:
        if stratum != current:
            current = stratum
            n = sum(1 for _, _, s in chosen if s == stratum)
            lines.append(f"# --- {stratum} ({n}) - {STRATUM_NOTES[stratum]}")
        label = asn_label(asn)
        if ip == VALIDATION_IP:
            label += "  <- OONI worked example, validation ground truth"
        lines.append(f"{ip}  # {label}")
    lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def print_report(buckets, stats, alloc=None):
    tot = stats["total"] or 1
    other = tot - stats["cloudflare"] - stats["aws"]
    print(f"  Affected addresses : {tot:,}")
    print(f"  Distinct ASNs      : {stats['distinct_asns']:,}")
    print()
    print(f"  By provider:")
    print(f"    Amazon AWS       {stats['aws']:>7,}  {stats['aws'] / tot:>6.1%}")
    print(f"    Cloudflare       {stats['cloudflare']:>7,}  {stats['cloudflare'] / tot:>6.1%}")
    print(f"    everything else  {other:>7,}  {other / tot:>6.1%}")
    print(f"    -> the two big providers hold "
          f"{(stats['aws'] + stats['cloudflare']) / tot:.1%} of all addresses")
    print()
    print(f"  {'stratum':<20} {'available':>10} {'sampled':>9}")
    print(f"  {'-' * 20} {'-' * 10} {'-' * 9}")
    for name, _ in QUOTAS:
        got = alloc.get(name, 0) if alloc else 0
        print(f"  {name:<20} {len(buckets.get(name, [])):>10,} {got:>9}")
    print()
    print(f"  Largest {TOP_ASN_COUNT} ASNs outside AWS/Cloudflare "
          f"(all in 'other_providers'):")
    for asn, n in stats["tail_asns"][:TOP_ASN_COUNT]:
        print(f"    {asn_label(asn):<22} {n:>5}")
    if stats["absent_checked"]:
        names = ", ".join(asn_label(a) for a in stats["absent_checked"])
        print(f"  Checked and absent from this data: {names}")


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
                    help="show the breakdown and exit without writing")
    ap.add_argument("--no-canaries", action="store_true",
                    help="omit the never-blocked canary addresses "
                         f"({', '.join(CANARY_TARGETS)})")
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
        print(f"\n  ! Only {len(chosen)} addresses available, asked for {args.count}.")

    canaries = not args.no_canaries
    write_targets(args.out, chosen, origin, stats, canaries=canaries)
    n_canary = len(CANARY_TARGETS) if canaries else 0
    total = len(chosen) + n_canary
    print()
    print(f"  Wrote {args.out}: {len(chosen)} sampled"
          + (f" + {n_canary} canaries" if n_canary else "")
          + f" = {total} targets")
    print(f"  Seed {args.seed} - same seed and count gives the same list.")
    print(f"  Cost scales with all {total} of them, not just the sampled ones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())