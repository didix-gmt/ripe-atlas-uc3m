#!/usr/bin/env python3
"""
Toy measurement campaign, ping latency vs geographic distance

Objective : verify that RTT from various vantage points around the world
            correlates with geographic distance to the target, as expected
            from the speed of light in fiber ("The Internet at the speed
            of light", Singla et al., 2014).

Requirements:
    pip install ripe-atlas-cousteau matplotlib requests
"""

import time
import math
import json
import requests
import matplotlib.pyplot as plt
from ripe.atlas.cousteau import (
    Ping,
    AtlasSource,
    AtlasCreateRequest,
    AtlasResultsRequest,
)
from dotenv import load_dotenv
import os


# CONFIGURATION

load_dotenv()
API_KEY = os.getenv("RIPE_API_KEY", "")
TARGET = "telecom-physique.fr"

# Télécom Physique Strasbourg
TARGET_LAT = 48.525696526602005
TARGET_LON = 7.737680646374015

# Countries spread across all continents: ~3 probes each
# Format: country_code -> label for the plot
COUNTRIES = {
    # Europe
    "ES": "Spain",
    "DE": "Germany",
    "GB": "UK",
    "SE": "Sweden",
    # North America
    "US": "USA",
    "CA": "Canada",
    # South America
    "BR": "Brazil",
    "AR": "Argentina",
    # Africa
    "ZA": "South Africa",
    "KE": "Kenya",
    # Asia
    "JP": "Japan",
    "IN": "India",
    "SG": "Singapore",
    # Oceania
    "AU": "Australia",
}

N_PER_COUNTRY = 3
POLL_INTERVAL = 30  # seconds between status checks
MAX_WAIT      = 900 # 15 minutes max wait

def select_probes():
    """
    Query the RIPE Atlas API to get N connected probes per country.
    Returns:
        probe_ids  : list of probe IDs to use as measurement sources
        probe_meta : dict { probe_id -> {lat, lon, country_label} }
    """
    probe_ids  = []
    probe_meta = {}

    print("Selecting probes...")
    for cc, label in COUNTRIES.items():
        url = "https://atlas.ripe.net/api/v2/probes/"
        params = {
            "country_code": cc,
            "status": 1,                    # connected probes only
            "tags": "system-ipv4-works",    # filter for working IPv4
            "page_size": N_PER_COUNTRY,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except Exception as e:
            print(f"  [{label}] Could not fetch probes: {e}")
            continue

        found = 0
        for p in results:
            pid  = p.get("id")
            geom = p.get("geometry") or {}
            coords = geom.get("coordinates", [None, None])
            # GeoJSON format: coordinates = [longitude, latitude]
            lon, lat = coords[0], coords[1]
            if pid and lat is not None and lon is not None:
                probe_ids.append(pid)
                probe_meta[pid] = {"lat": lat, "lon": lon, "label": label}
                found += 1

        print(f"  {label:15s} ({cc}): {found} probe(s) selected")

    print(f"\nTotal probes selected: {len(probe_ids)}")
    return probe_ids, probe_meta


def launch_measurement(probe_ids):
    """
    Create a one-off ping measurement from the selected probes.
    Returns the measurement ID (int).
    """
    ping = Ping(
        af=4,
        target=TARGET,
        packets=3,
        description=f"Toy campaign – ping {TARGET} from {len(probe_ids)} probes",
    )
    source = AtlasSource(
        type="probes",
        value=",".join(str(pid) for pid in probe_ids),
        requested=len(probe_ids),
    )
    request = AtlasCreateRequest(
        key=API_KEY,
        measurements=[ping],
        sources=[source],
        is_oneoff=True,
    )

    success, response = request.create()
    if not success:
        raise RuntimeError(f"Measurement creation failed: {response}")

    msm_id = response["measurements"][0]
    print(f"\nMeasurement created - ID: {msm_id}")
    print(f"View on RIPE Atlas: https://atlas.ripe.net/measurements/{msm_id}/")

    # Estimated cost: len(probe_ids) * 3 packets * 2x one-off = 6 credits/probe
    estimated_cost = len(probe_ids) * 3 * 2
    print(f"Estimated cost: ~{estimated_cost} credits")

    return msm_id


def wait_for_completion(msm_id):
    """
    Poll the measurement status until it's 'Stopped' (one-off completed).
    """
    print(f"\nWaiting for results (polling every {POLL_INTERVAL}s, max {MAX_WAIT//60} min)...")
    elapsed = 0
    while elapsed < MAX_WAIT:
        try:
            resp = requests.get(
                f"https://atlas.ripe.net/api/v2/measurements/{msm_id}/",
                headers={"Authorization": f"Key {API_KEY}"},
                timeout=10,
            )
            status = resp.json().get("status", {}).get("name", "Unknown")
        except Exception as e:
            status = f"(error: {e})"

        print(f"  [{elapsed:4d}s] {status}")
        if status == "Stopped":
            print("  Measurement complete.")
            return True

        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    print("  Timeout reached - results may be incomplete.")
    return False


def fetch_results(msm_id):
    """
    Download measurement results via cousteau.
    Returns a list of result dicts.
    """
    print(f"\nFetching results for measurement {msm_id}...")
    success, results = AtlasResultsRequest(
        msm_id=msm_id,
        key=API_KEY,
    ).create()

    if not success:
        raise RuntimeError("Failed to fetch results")

    print(f"  {len(results)} result(s) received.")
    return results


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Great-circle distance in km between two (lat, lon) points.
    Uses the Haversine formula.
    """
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def plot_results(results, probe_meta):
    """
    Scatter plot: RTT (ms) vs geographic distance (km) to target.
    Also draws the theoretical lower bound (speed of light in fiber).
    """
    distances  = []
    latencies  = []
    labels     = []

    for r in results:
        pid     = r.get("prb_id")
        avg_rtt = r.get("avg")   # average RTT in ms, computed by RIPE Atlas

        # Skip probes not in our metadata or with no valid RTT
        if pid not in probe_meta:
            continue
        if avg_rtt is None or avg_rtt < 0:
            continue

        meta = probe_meta[pid]
        dist = haversine_km(meta["lat"], meta["lon"], TARGET_LAT, TARGET_LON)
        distances.append(dist)
        latencies.append(avg_rtt)
        labels.append(meta["label"])

    if not distances:
        print("No plottable results (all probes may have failed).")
        return

    # Theoretical lower bound: speed of light in fiber ≈ 2/3 × c ≈ 200,000 km/s
    # Round-trip time (ms) = 2 × distance_km / 200,000 × 1000
    #                       = distance_km / 100
    x_theory = list(range(0, int(max(distances)) + 2000, 200))
    y_theory  = [d / 100 for d in x_theory]  # ms

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.scatter(distances, latencies, color="steelblue", zorder=5, s=70,
               label="Measured RTT (avg of 3 packets)")

    for i, lbl in enumerate(labels):
        ax.annotate(lbl, (distances[i], latencies[i]),
                    textcoords="offset points", xytext=(6, 4), fontsize=8)

    ax.plot(x_theory, y_theory, "r--", linewidth=1.5,
            label="Theoretical lower bound\n(speed of light in fiber, ~200,000 km/s)")

    ax.set_xlabel("Distance to Télécom Physique Strasbourg (km)")
    ax.set_ylabel("Average RTT (ms)")
    ax.set_title(f"Ping latency vs geographic distance - target: {TARGET}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    output_file = "latency_vs_distance.png"
    plt.savefig(output_file, dpi=150)
    print(f"\nPlot saved as {output_file}")
    plt.show()


# MAIN

def main():
    if not API_KEY:
        raise ValueError("API_KEY is empty - fill it in at the top of the script.")

    # 1. Select probes
    probe_ids, probe_meta = select_probes()
    if not probe_ids:
        raise RuntimeError("No probes selected - check your internet connection.")

    # 2. Launch measurement
    msm_id = launch_measurement(probe_ids)

    # 3. Wait for completion
    wait_for_completion(msm_id)

    # 4. Fetch results
    results = fetch_results(msm_id)

    # 5. Save raw results
    raw_file = f"results_{msm_id}.json"
    with open(raw_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Raw results saved as {raw_file}")

    # 6. Plot
    plot_results(results, probe_meta)

    print(f"\nDone. Measurement ID for reference: {msm_id}")


if __name__ == "__main__":
    main()
