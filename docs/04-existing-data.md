# 4. Using existing data (without installing anything)

The vast majority of RIPE Atlas data is public: you can browse, download and use it without hosting a probe or even having an account. This is the first thing to exploit. There are three ways to get at it, roughly from simplest to most involved - pick the one that matches what you actually need.

## 1. Simplest: just use the web UI

For a quick, one-off check - "how many probes are connected in Spain right now?" - the fastest way is to go straight to <https://atlas.ripe.net/probes>, filter by country and status, and read the count on screen.

## 2. Bulk data: daily archives (still no coding)

If you need a lot of data at once - every probe, or every result of a given measurement type for a given day - RIPE publishes ready-made downloadable files instead of making you crawl the API page by page. Fetching one file via FTP to get the full list of known probes is explicitly simpler than paging through the probes API.
Two different archives exist, with different retention:

- **Probe archive**: a daily snapshot of all known probes and their metadata, kept historically - not limited to a recent window.

- **Measurement result archives**: daily files of public measurement results, split by measurement type and IP version, available at <https://ftp.ripe.net/ripe/atlas/data> - but only for a sliding window of the last 30 days; older data has to go through the API instead.

For something like "map every probe in Spain by ISP, refreshed once a day," the probe archive is the simplest source - one file, no filters to write, no pagination to manage.

> For heavy computation across large amounts of historical measurement data, RIPE also makes the dataset queryable in Google BigQuery (`RIPE-NCC/ripe-atlas-bigquery` on GitHub)

## 3. The API (when you actually need to automate something)

The API is the right tool once you're scripting something repeatable - for example, a Python pipeline that checks specific ISPs' probe counts before every match, or that needs to combine probe data with our own measurement results. It's an interface you query via a URL (or via code) that returns structured data in JSON. Part of this API is anonymous: no key, no account.

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

The response contains a `"count"` field giving the total number of results. The full list of accepted filter parameters for this endpoint (country, status, ASN, and many others) is documented on the official "Listing probes" page. *(Source: official docs, REST API Manual → Probes → "Listing probes".)*

### Useful examples for the project

Number of connected probes in Spain:
```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1
```

Filter further by operator (replace `XXXX` with the ISP's AS, e.g. for Movistar/Telefónica : 3352):
```
https://atlas.ripe.net/api/v2/probes/?country_code=ES&status=1&asn_v4=XXXX
```
> To find an ISP's AS: use bgp.he.net or stat.ripe.net.

### Reading JSON comfortably

- **Browser**: Firefox formats JSON automatically; on Chrome, a "JSON Viewer" extension does the job or you can just use an online viewer.
- **In Python**: see [page 6](06-running-measurements.md).

## Limit to keep in mind

Whether through the web UI, the API, or the daily probe archive, a "connected" status only reflects the moment the snapshot was taken — it doesn't guarantee that probe will still be connected during a specific future match, since public probes belong to individuals who can unplug them at any time.

## Sources

- *REST API Manual — Introduction* — <https://atlas.ripe.net/docs/apis/rest-api-manual/introduction/>
- *Anonymous access* (which endpoints need no key) — <https://atlas.ripe.net/docs/apis/rest-api-manual/authentication/anonymous-access/>
- *Listing probes* (filter parameters) — <https://atlas.ripe.net/docs/apis/rest-api-manual/probes/listing-probes/>
- *Announcing Daily RIPE Atlas Data Archives* (RIPE Labs — archive format, 30-day window for measurement results) — <https://labs.ripe.net/author/petros_gigis/announcing-daily-ripe-atlas-data-archives/>
- *RIPE Atlas API Changes* (RIPE Labs — probe archive vs. measurement archive, why archives beat crawling the API for bulk data) — <https://labs.ripe.net/author/kistel/ripe-atlas-api-changes/>
- *RIPE Atlas: Presentations, Tutorials and Videos* (RIPE Labs) — <https://labs.ripe.net/atlas/user-experiences/presentations-tutorials-and-videos>