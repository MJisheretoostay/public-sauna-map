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
Portland OR, Chicago IL, New York NY, San Francisco CA, Duluth MN (done), St. Paul MN (skipped 2026-11-04: <3 eligible venues in the city), Boston MA (done), Austin TX (done), Los Angeles CA (done), Salt Lake City UT (done), Boulder CO (done), Bozeman MT (done), Anchorage AK (done), Detroit MI (done), Philadelphia PA (done),
Brooklyn NY (skipped 2026-11-17: already covered by the New York NY page), Oakland CA (skipped 2026-11-17: <3 eligible venues; only Some Sun, others private-room or infrared-only), Madison WI (done), Milwaukee WI (done), Burlington VT (skipped 2026-11-19: <3 eligible venues; only SAVU Lakeside's community hour in town, Nordic Spa is gym-attached in Shelburne, SAVU Bathhouse opens spring 2027),
Pittsburgh PA (done; added 2026-11-19 after the backlog ran out), Houston TX (done; added 2026-11-20; includes Katy's Spa World as a metro venue), Atlanta GA (done; added 2026-11-23; all four venues are Korean spas in Duluth/Norcross/Doraville; add Atlanta Sauna Club when it opens, targeted mid-2027),
Washington DC (skipped 2026-11-24: Sauna Jungle has not opened yet; its first location is in Arlington VA, targeting Dec 15, 2026, and the DC location is targeted for winter 2027), Portland ME (done; added 2026-11-24; only Washington Baths is in town, the other three are in Scarborough and Freeport; Village Sauna in South Portland temporarily closed, Driftless and Kettle Cove are rental-only), Asheville NC (skipped 2026-11-25: <3 eligible venues; Sauna House closed July 2026, Cultivate's Bathhouse in the same building targets Dec 2026, so only Drip is open; the Lounge is inside a climbing gym, Shoji is private tubs, Horse Shoe Farm is a resort spa), Marquette MI (skipped 2026-11-25: <3 eligible venues; NMU PEIF saunas closed, YMCA is a gym, North Woods Sauna is rental-only, BeWell is infrared, Second Street Sauna's site is down), Spokane WA (skipped 2026-11-25: <3 eligible venues; only Spokane Hot Box and Sanctuary, others infrared, gym or tanning), San Diego CA (done; added 2026-11-25; Beach Sauna is in Encinitas and weekends only; add Scandinavian Heat Club in Ocean Beach when it opens). Add new cities here.

## Monetization (not live)
`data/site.json -> home_gear_links` holds placeholder affiliate links (Sweaty Yeti, Plunge, Topture,
SaunaCloud). Replace `url` and set `"placeholder": false` once an application is approved.
