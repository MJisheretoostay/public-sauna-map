# Public Sauna Map (working name)

Static directory of US drop-in public saunas, banyas and bathhouses.
Plain Python 3 generator, zero dependencies. Data lives in JSON, one file per city.

```
data/site.json              site name, base URL, "Want one at home?" links (placeholders for now)
data/cities/<slug>.json     one file per city (slug = city-name-st, e.g. portland-or)
data/city-template.json.example
static/style.css
build.py                    validates data, then builds into dist/
dist/                       generated site (deploy this folder)
screenshots/
```

Build: `python3 build.py`  (validate only: `python3 build.py --check`)
Preview: `cd dist && python3 -m http.server 8765` then open http://localhost:8765

## Inclusion rules
- Include: places an individual can book a seat in or walk into: community/mobile wood-fired saunas,
  banyas, communal bathhouses, sauna + cold plunge clubs.
- Exclude: gyms/health clubs, infrared-only studios/pods, private-rental-only saunas, hotel saunas,
  permanently closed or "paused" venues (for example, Tuli Lodge Seattle was paused on 2026-10-21).
- A city is published only with at least 3 verified venues (build.py enforces this).

## Nightly "add one city" procedure
1. Pick the next city from the backlog below that isn't already in `data/cities/`.
2. Research: search "<city> public sauna", "<city> banya", "<city> bathhouse", "<city> sauna cold plunge",
   plus Reddit r/<city> threads. Make a list of candidates.
3. For each candidate, open the venue's OWN website (pricing/FAQ/booking pages). Record only facts stated
   there. A reputable local guide may fill a gap, but add it to `source_urls`. If something can't be confirmed,
   write `Unknown`. Never guess prices, temperatures or schedules.
4. Copy `data/city-template.json.example` to `data/cities/<slug>.json` and fill it in. Set `last_checked`
   (city and each venue) to today's date. Aim for 3-8 venues.
5. No health claims anywhere (no "detox", "immunity", "benefits", "recovery" etc.). The build fails if it
   spots common health-claim words.
6. Run `python3 build.py`. Fix any DATA ERRORS it prints (missing fields, non-https URLs, health words,
   bad slug/date, fewer than 3 venues).
7. Spot-check: serve `dist/`, open the new city page, and confirm every booking/source URL returns HTTP 200.
8. Deploy `dist/` (once hosting is set up) and send a one-line report: city, venue count, notable gaps.

## Monthly refresh
Re-check the oldest `last_checked` city: re-verify price, hours and open/closed status, then update the dates.
Seasonal venues (lake saunas, park permits) change the most.

## City backlog (rough priority)
Portland OR, Chicago IL, New York NY, San Francisco CA, Duluth MN, St. Paul MN, Boston MA, Austin TX,
Los Angeles CA, Salt Lake City UT, Boulder CO, Bozeman MT, Anchorage AK, Detroit MI, Philadelphia PA,
Brooklyn NY, Oakland CA, Madison WI, Milwaukee WI, Burlington VT.

## Monetization (not live)
`data/site.json -> home_gear_links` holds placeholder affiliate links (Sweaty Yeti, Plunge, Topture,
SaunaCloud). Replace `url` and set `"placeholder": false` once an application is approved.
