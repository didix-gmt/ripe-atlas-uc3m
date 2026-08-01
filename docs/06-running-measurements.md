---
layout: default
title: Running measurements
nav_order: 7
---

# 6. Running measurements (web UI + Python API)

Three ways to interact with RIPE Atlas, from simplest to most automatable:
1. the **web UI** (to understand and test by hand);
2. the **public read API** (fetch data, no credits or account);
3. the **official Python library `ripe-atlas-cousteau`** (create measurements and fetch results via code).

> `is_oneoff=True` costs 2× more per result than a periodic measurement (see [page 3](03-credit-system.md)).

> **Your own probe is not your only source.** When you create a measurement, you choose which probes execute it, this can be your own Pi, but also any probe from the global RIPE Atlas fleet. You select them by country, ASN, or individual ID. The probes receive the instruction from RIPE's infrastructure, run the test from their local network, and send results back (you never have direct access to those machines, only to their results).

---

## 1. Web UI (to get started)

On <https://atlas.ripe.net>, the *Measurements* page → green **"Create a Measurement"** button. You choose the type (ping, traceroute, DNS, SSL, NTP, HTTP), the target, and the source probes. This is the best way to **actually see** what a measurement and its result look like before automating.

> Reminder: creating a measurement (UDM) **consumes credits** (see [page 3](03-credit-system.md)).

---

## 2. Public read API (no credits, no account)

To **read** existing data, a simple URL is enough. Example - count connected probes in Spain:

```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1
```

In Python, without any special library:

```python
import requests

url = "https://atlas.ripe.net/api/v2/probes/"
params = {"country_code": "ES", "status": 1}
r = requests.get(url, params=params)
data = r.json()

print("Number of connected probes in Spain:", data["count"])
```

> See [page 4](04-existing-data.md) for details on the public API.

---

## 3. Official Python library `ripe-atlas-cousteau`

This is the wrapper maintained by the RIPE Atlas developers, so the best choice for automation. It wraps most of the v2 API.

### Installation

```bash
pip install ripe-atlas-cousteau
```

### Prerequisite: an API key

Creating your **own** measurements via code requires an **API key** (generated in your RIPE Atlas account's key manager). Reading **public** measurements does not need one; downloading results of a **non-public** measurement needs a key with the right permission.

### Example: create a measurement (ping + traceroute)

Example adapted from the official Cousteau docs:

```python
from datetime import datetime
from ripe.atlas.cousteau import (
    Ping,
    Traceroute,
    AtlasSource,
    AtlasCreateRequest,
)

ATLAS_API_KEY = ""  # your API key

ping = Ping(af=4, target="www.google.com", description="test ping")

traceroute = Traceroute(
    af=4,
    target="www.ripe.net",
    description="test traceroute",
    protocol="ICMP",
)

# Where the measurements run from: here 5 probes in Spain
source = AtlasSource(
    type="country",
    value="ES",
    requested=5,
    tags={"include": ["system-ipv4-works"]},
)

atlas_request = AtlasCreateRequest(
    key=ATLAS_API_KEY,
    measurements=[ping, traceroute],
    sources=[source],
    is_oneoff=True,
)

(is_success, response) = atlas_request.create()
print(is_success, response)
```

### Example: fetch a measurement's results

```python
from datetime import datetime
from ripe.atlas.cousteau import AtlasResultsRequest

kwargs = {
    "msm_id": 2016892,            # the measurement ID
    "start": datetime(2015, 5, 19),
    "stop": datetime(2015, 5, 20),
    "probe_ids": [1, 2, 3, 4],
}

is_success, results = AtlasResultsRequest(**kwargs).create()
if is_success:
    print(results)
```

### Example: list probes by filters

```python
from ripe.atlas.cousteau import ProbeRequest

filters = {"country_code": "ES", "asn_v4": "3352"}  # 3352 = example AS
probes = ProbeRequest(**filters)

for probe in probes:
    print(probe["id"])

print("Total found:", probes.total_count)
```

### To parse results cleanly: Sagan

RIPE also maintains **Sagan**, a library that handles result format changes and returns native Python objects. Useful as soon as you process many results. (`pip install ripe.atlas.sagan`)

---

## Sources

- *Cousteau - Use & Examples* (official docs, all examples above) - <https://ripe-atlas-cousteau.readthedocs.io/en/latest/use.html>
- *ripe-atlas-cousteau* (official repo) - <https://github.com/RIPE-NCC/ripe-atlas-cousteau>
- *Measuring IP Connectivity with RIPE Atlas* (RIPE Labs, full example) - <https://labs.ripe.net/author/branimir_petricevic/measuring-ip-connectivity-with-ripe-atlas/>
- *Sagan* (result parsing) - <https://atlas.ripe.net/docs/tools-and-code/sagan/>
- *RIPE Atlas: Presentations, Tutorials and Videos* (RIPE Labs) — <https://labs.ripe.net/atlas/user-experiences/presentations-tutorials-and-videos>