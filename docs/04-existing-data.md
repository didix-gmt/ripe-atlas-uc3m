# 4. Using existing data (without installing anything)

The vast majority of RIPE Atlas data is **public**: you can browse, download and use it **without hosting a probe or even having an account**. This is the first thing to exploit before even thinking about installing hardware.

## How the public API works

RIPE Atlas exposes an **API**: an interface you query via a URL (or via code) that returns structured data in **JSON** (text that machines read easily). Part of this API is **anonymous**: no key, no account.

### Anatomy of an API URL

```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1
└────────┬───────────┘└──┬──┘└──┬──┘ └──────────┬──────────┘
     the server         the   the      the filters (after the ?,
                        API v2 resource separated by &)
```

- `?` opens the list of filters;
- `&` separates multiple filters;
- here: probes located in Spain (`country_code=ES`) and connected (`status=1`).

The response notably contains a `"count"` field = the total number of results. This is the fastest way to answer "how many connected probes in Spain?".

### Useful examples for the project

Number of connected probes in Spain:
```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1
```

Filter further by operator (replace `XXXX` with the ISP's AS, e.g. Movistar/Telefónica, Orange ES, Vodafone ES):
```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1&asn_v4=XXXX
```

> To find an ISP's AS: use bgp.he.net or stat.ripe.net. To be documented as we go in the [open questions page](07-open-questions.md).

### Reading JSON comfortably

- **Browser**: Firefox formats JSON automatically; on Chrome, a "JSON Viewer" extension does the job.
- **In Python**: see [page 6](06-running-measurements.md).

## Not all APIs are public

Many services offer an API, but it often requires an authentication key or is paid. RIPE Atlas is notable for exposing **a large part of it for free and anonymously**, because their mission is to share network measurements. This is valuable for us: we can start working **before** having a single probe of our own.

## Limit to keep in mind

The `status=1` filter gives probes connected **at time T**. A probe "connected now" is not guaranteed to be so during a specific match: public probes belong to individuals who can unplug them at any time. For **critical** measurements (during a given match), this is an argument in favour of having **our own probes**, whose availability we control.

## What we can do right now (without network authorisation)

- count and map existing probes in Spain, by ISP;
- fetch results of public measurements already launched;
- estimate whether the existing coverage is enough, or whether we need our own probes.

This is typically the first analysis to present to the supervisors to decide on the deployment strategy.

## Sources

- *Why You Should Host a RIPE Atlas Probe* (public data, open access) — <https://chrisgrundemann.com/index.php/2025/ripe-atlas-probe/>
- *REST API Manual* — <https://atlas.ripe.net/docs/apis/rest-api-manual/>
- *Listing probes* (filter parameters) — <https://atlas.ripe.net/docs/apis/rest-api-manual/probes/listing-probes/>
