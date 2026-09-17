#!/usr/bin/env python3
"""
Probe density by country — is 259 probes in Spain a lot or a little?
=====================================================================
Puts the Spanish probe count in context by comparing it with
neighbouring and comparable countries, in absolute terms and per
million inhabitants.

Why: an absolute count means nothing on its own. 259 could be excellent
or poor depending on what comparable countries have.

Both inputs are fetched live, so nothing here is a hardcoded number
that quietly goes stale:
  - probe counts : RIPE Atlas public API (no key needed)
  - population   : World Bank open API (no key needed)

The World Bank indicator used is SP.POP.TOTL (total population). The
API returns a series by year; we take the most recent non-null value
and report which year it came from, so the figure in the output is
always traceable rather than assumed.

Requirements:
    pip install requests
"""

import time
import requests

ATLAS_URL = "https://atlas.ripe.net/api/v2/probes/"
WORLDBANK_URL = "https://api.worldbank.org/v2/country/{codes}/indicator/SP.POP.TOTL"

REQUEST_PAUSE = 0.3

# ISO-2 codes. The World Bank API accepts ISO-2 as well as ISO-3.
COUNTRIES = {
    "ES": "Spain",
    "FR": "France",
    "IT": "Italy",
    "PT": "Portugal",
    "DE": "Germany",
    "NL": "Netherlands",
    "GB": "United Kingdom",
    "BE": "Belgium",
    "CH": "Switzerland",
    "AT": "Austria",
    "SE": "Sweden",
    "PL": "Poland",
    "GR": "Greece",
}

FOCUS = "ES"   # the country we are putting in context


# ── Population, from the World Bank ───────────────────────────────────────────

def fetch_populations(codes):
    """
    Fetch total population for a list of ISO-2 country codes.

    Returns {code: (population, year)}. Countries the API doesn't
    return are simply absent from the result — the caller decides what
    to do about that rather than getting a silent zero.
    """
    url = WORLDBANK_URL.format(codes=";".join(codes))
    params = {
        "format": "json",
        "per_page": 20000,
        # Ask for a recent window rather than the whole series: the
        # latest year is often still null for some countries, so we
        # need a few years of slack to fall back on.
        "date": "2018:2026",
    }

    print("Fetching population data (World Bank)...")
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        raise RuntimeError(f"World Bank API failed: {e}")

    # Response shape: [metadata, [records]]
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise RuntimeError("World Bank API returned no data rows")

    latest = {}
    for row in payload[1]:
        code = (row.get("countryiso3code") or "")
        iso2 = (row.get("country") or {}).get("id")
        value = row.get("value")
        year = row.get("date")

        if value is None or not iso2:
            continue

        year = int(year)
        # Keep the most recent year with an actual value
        if iso2 not in latest or year > latest[iso2][1]:
            latest[iso2] = (int(value), year)

    print(f"  got population for {len(latest)} countries\n")
    return latest


# ── Probe counts, from RIPE Atlas ─────────────────────────────────────────────

def count_probes(country_code, connected_only=True):
    """
    Return the number of probes for a country.

    page_size=1 because only the "count" field of the response envelope
    is needed, not the probe list — keeps the request tiny.
    """
    params = {"country_code": country_code, "page_size": 1}
    if connected_only:
        params["status"] = 1

    try:
        resp = requests.get(ATLAS_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("count", 0)
    except Exception as e:
        print(f"  ! {country_code}: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    populations = fetch_populations(list(COUNTRIES))

    print("Fetching probe counts (RIPE Atlas)...")
    rows = []
    for cc, name in COUNTRIES.items():
        if cc not in populations:
            print(f"  ! {name}: no population data, skipped")
            continue

        connected = count_probes(cc, connected_only=True)
        time.sleep(REQUEST_PAUSE)
        total = count_probes(cc, connected_only=False)
        time.sleep(REQUEST_PAUSE)

        if connected is None or total is None:
            continue

        pop, pop_year = populations[cc]
        pop_m = pop / 1_000_000

        rows.append({
            "cc": cc,
            "name": name,
            "pop_m": pop_m,
            "pop_year": pop_year,
            "connected": connected,
            "total": total,
            "density": connected / pop_m,
            "live_rate": (connected / total * 100) if total else 0,
        })
        print(f"  {name:16s} {connected:>5} connected / {total:>5} registered")

    if not rows:
        raise RuntimeError("No data retrieved.")

    rows.sort(key=lambda r: r["density"], reverse=True)

    years = {r["pop_year"] for r in rows}
    year_note = (f"population: World Bank {min(years)}"
                 if len(years) == 1
                 else f"population: World Bank {min(years)}-{max(years)}, latest available per country")

    print("\n" + "=" * 82)
    print(f"PROBE DENSITY BY COUNTRY  ({year_note})")
    print("=" * 82)
    print(f"{'Country':<16} {'Pop (M)':>8} {'Yr':>5} {'Conn.':>7} "
          f"{'Regist.':>8} {'Per 1M':>8} {'Live %':>8}")
    print("-" * 82)

    for r in rows:
        marker = "  <--" if r["cc"] == FOCUS else ""
        print(f"{r['name']:<16} {r['pop_m']:>8.1f} {r['pop_year']:>5} "
              f"{r['connected']:>7} {r['total']:>8} "
              f"{r['density']:>8.1f} {r['live_rate']:>7.0f}%{marker}")

    print("-" * 82)

    focus = next((r for r in rows if r["cc"] == FOCUS), None)
    if focus:
        rank = rows.index(focus) + 1
        densities = sorted(r["density"] for r in rows)
        n = len(densities)
        median = (densities[n // 2] if n % 2
                  else (densities[n // 2 - 1] + densities[n // 2]) / 2)

        print(f"\n{focus['name']} ranks {rank} of {n} by probes per million inhabitants.")
        print(f"  {focus['name']}: {focus['density']:.1f} per 1M")
        print(f"  Median of this set: {median:.1f} per 1M")

        if focus["density"] < median:
            print(f"  -> {median / focus['density']:.1f}x below the median.")
        else:
            print(f"  -> at or above the median.")

        needed = int(median * focus["pop_m"])
        print(f"\nTo reach the median density, {focus['name']} would need about "
              f"{needed} connected probes (currently {focus['connected']}).")

    print("\nNote: 'Live %' is connected/registered. A low figure means many")
    print("probes are registered but currently offline. Those may come back,")
    print("so the connected count is a floor rather than a ceiling for a")
    print("future campaign — worth re-checking close to a measurement date.")


if __name__ == "__main__":
    main()