# 7. Open questions / to validate

This page lists what is **not yet settled** and must be validated with the supervisors (Pablo, Marco) or checked yourself. Update it as answers come in.

## Authorisation and logistics

- [ ] **UC3M network authorisation**: Pablo must request it from the UC3M team before any probe is brought online. → *current status: pending.*
- [ ] **Existing RIPE Atlas account?** Does UC3M already have a RIPE Atlas account with credits, or does a new one need to be created? (Would settle the whole credits question.)
- [ ] **RIPE NCC member status?** Unlikely and disproportionate (€1,800/year), but to be confirmed so the path can be cleanly ruled out.

## Measurement strategy

- [ ] **Existing coverage**: how many connected probes in Spain, and on which ISPs? To measure via the public API:
  - Spain total: `https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1`
  - Per ISP: add `&asn_v4=XXXX` (AS of Movistar/Telefónica, Orange ES, Vodafone ES).
- [ ] **Spanish ISP AS numbers**: find and document the AS numbers of Movistar/Telefónica, Orange ES, Vodafone ES (via bgp.he.net or stat.ripe.net). → *to fill in here once found.*
- [ ] **One probe or several?** Decide, with the supervisors, between relying on the existing fleet (free, broad) and deploying our own probes (fine control over ISP / city / timing). Multiplying software probes on the **same** network brings nothing (see [page 2](02-hardware-vs-software-probe.md)).
- [ ] **Credit budget per match**: estimate the cost of a typical campaign (number of IPs × frequency × match duration) and check it fits within the available credits (see [page 3](03-credit-system.md)).

## Technical points to verify

- [ ] **Official RAM/CPU requirements** of the software probe: not found in the official docs. The Pi 3B is more than sufficient based on the hardware probes' specs, but no official minimum is published. → *to confirm if a precise figure is required for the report.*
- [ ] **Exact model of the provided Pi**: confirm it's a 3B (or newer) compatible with **arm64 / 64-bit** (mandatory for the official package).
- [ ] **Repo package version** (`ripe-atlas-repo_x.y-z`): check the up-to-date command on the official README at install time, the number changes.

## Statements heard, still to confirm

- [ ] *"Once one probe is connected, you can connect the others easily"*: origin and exact meaning to be clarified. The official docs instead **limit** the number of software probes per account/network to prevent "credit farming". If the idea was to multiply probes to earn more credits, that's explicitly discouraged.

## Sources

- *Credits* — <https://atlas.ripe.net/docs/getting-started/credits/>
- *Probes, Hosts, Anchors & Sponsors* — <https://atlas.ripe.net/docs/faq/probes-hosts-anchors-sponsors/>
- *Listing probes* (API filters) — <https://atlas.ripe.net/docs/apis/rest-api-manual/probes/listing-probes/>
