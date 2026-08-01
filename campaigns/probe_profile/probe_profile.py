#!/usr/bin/env python3
"""
Probe profiling — residential vs infrastructure, per Spanish ISP
================================================================
Question this answers: for each Spanish ISP we care about, how many
connected probes are plausibly on *residential* connections?

Why it matters: La Liga blocking injunctions target ISPs' consumer
subscribers. A probe sitting in a university network, a hosting
provider or a corporate line may share the same AS number but not be
subject to the same filtering. Measuring only from those would risk a
false negative — concluding "no blocking" while simply looking from
the wrong side of the filter.

IMPORTANT — this classification is heuristic, not authoritative.
RIPE Atlas publishes NO system tag for "residential" or "datacentre".
The official system tag categories are only: protocol capability,
basic connectivity, stability, DNS resolution, and probe metadata
(version, software, anchor, virtual, geolocation).
So we combine:
  - system tags   -> applied uniformly by RIPE, reliable but indirect
  - user tags     -> explicit but voluntary, so often missing
and report a confidence level rather than a hard label. Every probe
that cannot be classified is counted as UNKNOWN, not silently assumed
to be residential.

Data source: public probes API (no key, no credits). See doc page 4.

Requirements:
    pip install requests pandas
"""

import time
import requests
import pandas as pd

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

API_URL = "https://atlas.ripe.net/api/v2/probes/"
PAGE_SIZE = 500
REQUEST_PAUSE = 0.2
COUNTRY = "ES"

# AS numbers cross-checked via bgp.he.net (see SOTA / doc page 4).
# Five target ISPs, not three. DIGI and MasMovil were added after the
# both appear in OONI's set of networks with match-correlated blocking,
# and DIGI additionally has its own analysis in that report (TLS MitM
# activity observed on its network - OONI does not attribute it to the operator).
# Restricting the study to the "big three" would miss the most interesting case.
SPANISH_ISPS = {
    3352:  "Movistar / Telefonica",
    57269: "DIGI Spain",
    12479: "Orange Espana",
    15704: "MasMovil",
    12430: "Vodafone Espana",
}

# Tag taxonomy — the key distinction is between WHERE a probe sits and
# HOW it connects. These are orthogonal: an office can have fibre, a home
# can be behind NAT, and a datacentre can NAT too. Only the first
# dimension tells us anything about whether the probe is on a consumer
# subscriber line.

# WHERE: the actual signal.
LOCATION_RESIDENTIAL = {
    "home", "residential", "domestic", "home-router", "household",
}
LOCATION_INFRA = {
    "office", "datacentre", "datacenter", "dc", "hosting", "colocation",
    "colo", "server", "corporate", "company", "university", "academic",
    "school", "isp", "core", "backbone", "transit", "ixp", "pop",
}

# HOW: informational only, never used to classify. Kept explicitly so
# that it is obvious these were considered and deliberately excluded —
# an earlier version of this script counted them as residential, which
# silently mislabelled every "fibre / office" probe as a home.
CONNECTION_TECH = {
    "fibre", "fiber", "ftth", "fttb", "dsl", "adsl", "vdsl", "cable",
    "nat", "wireless", "wifi", "4g", "5g", "lte", "satellite",
}


# ── STEP 1: Fetch probes with their tags ──────────────────────────────────────

def fetch_probes(country_code=COUNTRY, max_pages=100):
    """
    Fetch connected probes for a country, including tags.

    Note: 'tags' must be requested explicitly in `fields`, otherwise
    the API omits them and every probe would come back unclassifiable.
    """
    params = {
        "country_code": country_code,
        "status": 1,
        "page_size": PAGE_SIZE,
        "fields": "id,country_code,asn_v4,tags,is_anchor,is_public,geometry",
    }

    probes, url, page = [], API_URL, 0
    print(f"Fetching connected probes in {country_code}...")

    while url and page < max_pages:
        try:
            resp = requests.get(url, params=params if page == 0 else None, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ! Failed on page {page + 1}: {e}")
            break

        probes.extend(data.get("results", []))
        page += 1
        print(f"  page {page} — {len(probes)} / {data.get('count', '?')}")

        url = data.get("next")
        if url:
            time.sleep(REQUEST_PAUSE)

    print(f"  Done: {len(probes)} probes.\n")
    return probes


# ── STEP 2: Classify ──────────────────────────────────────────────────────────

def extract_tag_slugs(probe):
    """
    Tags come back as a list of dicts: [{"name": ..., "slug": ...}, ...].
    Return the set of slugs, lowercased.
    """
    return {
        (t.get("slug") or "").lower()
        for t in (probe.get("tags") or [])
        if t.get("slug")
    }


def classify(probe):
    """
    Return (label, confidence, reason).

    Signals are checked strongest first and we stop at the first match,
    so a weak hint can never override a strong one.

    Connection-technology tags (fibre, nat, dsl...) are deliberately
    ignored: they describe HOW a probe connects, not WHERE it sits, and
    treating them as residential markers mislabels office probes.
    """
    slugs = extract_tag_slugs(probe)

    # --- Certain: anchors are infrastructure by definition
    if probe.get("is_anchor") or "system-anchor" in slugs or "system-virtual" in slugs:
        return "INFRASTRUCTURE", "certain", "anchor / virtual anchor"

    # --- Declared location (voluntary, but unambiguous when present)
    infra_hits = slugs & LOCATION_INFRA
    res_hits = slugs & LOCATION_RESIDENTIAL

    if infra_hits and not res_hits:
        return "INFRASTRUCTURE", "declared", f"location tag: {', '.join(sorted(infra_hits))}"
    if res_hits and not infra_hits:
        return "RESIDENTIAL", "declared", f"location tag: {', '.join(sorted(res_hits))}"
    if res_hits and infra_hits:
        # Genuinely contradictory self-declaration — don't guess.
        return "UNKNOWN", "conflicting", (
            f"both: {', '.join(sorted(res_hits))} / {', '.join(sorted(infra_hits))}"
        )

    # --- Indirect: private address means the probe is behind NAT.
    # Homes almost always NAT, but so do offices and some datacentres,
    # so this is a soft signal. Kept because it is the only indicator
    # RIPE applies uniformly to every probe, but flagged as weak.
    if "system-ipv4-rfc1918" in slugs:
        return "RESIDENTIAL", "soft-inference", "behind NAT (system-ipv4-rfc1918), no location tag"

    # --- Weakest: probe form factor. Hardware probes were mailed to
    # individual volunteers, software probes usually run on a machine
    # someone already operates. Too weak to label either way.
    if "system-software" in slugs:
        return "UNKNOWN", "weak-hint", "software probe, no location tag"
    if slugs & {"system-v1", "system-v2", "system-v3", "system-v4", "system-v5"}:
        return "UNKNOWN", "weak-hint", "hardware probe, no location tag"

    tech = slugs & CONNECTION_TECH
    if tech:
        return "UNKNOWN", "no-signal", f"only connection tags: {', '.join(sorted(tech))}"

    return "UNKNOWN", "no-signal", "no usable tag"


def build_dataframe(probes):
    rows = []
    for p in probes:
        label, confidence, reason = classify(p)
        asn = p.get("asn_v4")
        rows.append({
            "probe_id": p.get("id"),
            "asn": asn,
            "isp": SPANISH_ISPS.get(asn, f"Other (AS{asn})" if asn else "Other (unknown AS)"),
            "is_target_isp": asn in SPANISH_ISPS,
            "label": label,
            "confidence": confidence,
            "reason": reason,
        })
    return pd.DataFrame(rows)


# ── STEP 3: Report ────────────────────────────────────────────────────────────

def report(df):
    print("=" * 72)
    print(f"PROBE PROFILE — {COUNTRY}, connected probes")
    print("=" * 72)
    print(f"Total connected probes: {len(df)}\n")

    # Overall classification
    print("Overall classification:")
    for label, n in df["label"].value_counts().items():
        pct = n / len(df) * 100
        print(f"  {label:16s} {n:>5}  ({pct:5.1f}%)")

    print("\nConfidence breakdown:")
    for conf, n in df["confidence"].value_counts().items():
        print(f"  {conf:16s} {n:>5}")

    # Per target ISP — the number that actually drives campaign design
    print("\n" + "-" * 72)
    print("PER TARGET ISP")
    print("-" * 72)
    print(f"{'ISP':<26} {'total':>6} {'decl.':>7} {'infer.':>7} {'infra':>6} {'unk':>5}")
    print("-" * 72)

    # Residential is split into declared vs inferred on purpose: the
    # declared count is the defensible floor, the sum is the optimistic
    # ceiling. Reporting a single number would hide how much of the
    # classification rests on the weak NAT signal.
    for asn, name in SPANISH_ISPS.items():
        sub = df[df["asn"] == asn]
        res = sub[sub["label"] == "RESIDENTIAL"]
        n_decl = int((res["confidence"] == "declared").sum())
        n_infer = int((res["confidence"] == "soft-inference").sum())
        n_inf = int((sub["label"] == "INFRASTRUCTURE").sum())
        n_unk = int((sub["label"] == "UNKNOWN").sum())
        print(f"{name:<26} {len(sub):>6} {n_decl:>7} {n_infer:>7} {n_inf:>6} {n_unk:>5}")

    others = df[~df["is_target_isp"]]
    o_res = others[others["label"] == "RESIDENTIAL"]
    n_decl = int((o_res["confidence"] == "declared").sum())
    n_infer = int((o_res["confidence"] == "soft-inference").sum())
    n_inf = int((others["label"] == "INFRASTRUCTURE").sum())
    n_unk = int((others["label"] == "UNKNOWN").sum())
    print(f"{'All other Spanish ASes':<26} {len(others):>6} {n_decl:>7} {n_infer:>7} {n_inf:>6} {n_unk:>5}")

    print()
    print("decl. = host tagged it explicitly (defensible floor)")
    print("infer. = private address only, i.e. behind NAT (soft signal)")

    # Which other ASes are big enough to be worth considering?
    print("\n" + "-" * 72)
    print("OTHER SPANISH ASes WITH THE MOST PROBES (top 10)")
    print("-" * 72)
    top_other = (
        others[others["asn"].notna()]
        .groupby("asn")
        .agg(total=("probe_id", "count"),
             residential=("label", lambda s: (s == "RESIDENTIAL").sum()))
        .sort_values("total", ascending=False)
        .head(10)
    )
    for asn, row in top_other.iterrows():
        print(f"  AS{int(asn):<10} total={row['total']:<5} residential={row['residential']}")

    # Honest caveats
    print("\n" + "=" * 72)
    print("HOW TO READ THIS")
    print("=" * 72)
    print("- RIPE Atlas has NO official residential/datacentre tag. These")
    print("  labels are inferred; UNKNOWN means genuinely unclassifiable,")
    print("  not 'probably residential'.")
    print("- 'declared' comes from voluntary host tags: reliable when present,")
    print("  absent for most probes.")
    print("- 'soft-inference' relies on a private address (NAT) alone. Homes")
    print("  almost always NAT, but so do offices and some datacentres, so")
    print("  this bucket is the least certain of the RESIDENTIAL ones.")
    print("- Connection-technology tags (fibre, dsl, nat...) are ignored on")
    print("  purpose: they say how a probe connects, not where it sits. An")
    print("  earlier version counted them as residential and mislabelled")
    print("  every 'fibre + office' probe as a home.")
    print("- For any ISP where the residential count is very low, results")
    print("  from that operator will rest on few vantage points and should")
    print("  be reported with that limitation stated explicitly.")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    probes = fetch_probes()
    if not probes:
        raise RuntimeError("No probes retrieved — check your connection.")

    df = build_dataframe(probes)

    out = f"probe_profile_{COUNTRY.lower()}.csv"
    df.to_csv(out, index=False)
    print(f"Full table saved as {out}\n")

    report(df)


if __name__ == "__main__":
    main()