#!/usr/bin/env python3
"""Static site builder for Public Sauna Map. No third-party dependencies.

Usage:  python3 build.py            # validate data + build into dist/
        python3 build.py --check    # validate data only
"""
import json, glob, os, re, shutil, sys, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
DIST = os.path.join(ROOT, "dist")

REQUIRED_CITY = ["slug", "city", "state", "state_name", "intro", "last_checked", "venues"]
REQUIRED_VENUE = ["name", "neighborhood", "address", "sauna_type", "drop_in_price", "session_length",
                  "cold_plunge", "schedule", "booking_url", "source_urls", "last_checked"]
# Words that usually signal a health claim. The site makes NO health claims.
HEALTH_WORDS = re.compile(r"\b(detox\w*|immun\w*|heal\w*|cure\w*|inflammat\w*|metabol\w*|longevity|"
                          r"cardio\w*|circulation|weight loss|burn calories|benefit\w*|therapeutic|"
                          r"recovery boost|toxins?)\b", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def esc(s): return html.escape(str(s), quote=True)

def load():
    site = json.load(open(os.path.join(DATA, "site.json")))
    cities = []
    for f in sorted(glob.glob(os.path.join(DATA, "cities", "*.json"))):
        c = json.load(open(f))
        c["_file"] = os.path.basename(f)
        cities.append(c)
    return site, cities

def validate(cities):
    errors, slugs = [], set()
    for c in cities:
        where = c["_file"]
        for k in REQUIRED_CITY:
            if k not in c or c[k] in ("", None, []):
                errors.append(f"{where}: missing city field '{k}'")
        if c.get("slug") and c["_file"] != c["slug"] + ".json":
            errors.append(f"{where}: filename must be <slug>.json")
        if c.get("slug") in slugs: errors.append(f"{where}: duplicate slug")
        slugs.add(c.get("slug"))
        if not re.match(r"^[a-z0-9-]+-[a-z]{2}$", c.get("slug", "")):
            errors.append(f"{where}: slug must look like 'city-name-st'")
        if not DATE_RE.match(c.get("last_checked", "")):
            errors.append(f"{where}: last_checked must be YYYY-MM-DD")
        if len(c.get("venues", [])) < 3:
            errors.append(f"{where}: need at least 3 verified venues to publish a city")
        for i, v in enumerate(c.get("venues", [])):
            vw = f"{where} venue #{i+1} ({v.get('name','?')})"
            for k in REQUIRED_VENUE:
                if k not in v or v[k] in ("", None, []):
                    errors.append(f"{vw}: missing '{k}' (use 'Unknown' if not found)")
            if not DATE_RE.match(v.get("last_checked", "")):
                errors.append(f"{vw}: last_checked must be YYYY-MM-DD")
            for u in [v.get("booking_url", "")] + list(v.get("source_urls", [])):
                if not str(u).startswith("https://"):
                    errors.append(f"{vw}: URL must start with https:// -> {u}")
            text = json.dumps(v)
            m = HEALTH_WORDS.search(text)
            if m: errors.append(f"{vw}: possible health claim word '{m.group(0)}' - remove it")
        m = HEALTH_WORDS.search(c.get("intro", ""))
        if m: errors.append(f"{where}: intro has possible health claim word '{m.group(0)}'")
    return errors

def page(site, title, desc, path, body, extra_head=""):
    canonical = site["base_url"].rstrip("/") + path
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{esc(canonical)}">
<link rel="stylesheet" href="/style.css">
{extra_head}
</head><body>
<header class="site"><div class="wrap">
<a class="logo" href="/">Public <span>Sauna</span> Map</a>
<nav><a href="/cities/">Cities</a><a href="/about/">About</a><a href="/affiliate-disclosure/">Disclosure</a></nav>
</div></header>
{body}
<footer><div class="wrap">
<a href="/">Home</a><a href="/cities/">All cities</a><a href="/about/">About</a><a href="/affiliate-disclosure/">Affiliate disclosure</a>
<p>Details change often. Always confirm prices, hours and rules on the venue's own website before you go. Nothing on this site is medical advice.</p>
<p>&copy; {datetime.date.today().year} {esc(site['name'])}</p>
</div></footer>
</body></html>"""

def at_home(site):
    items = "".join(
        f'<li><a href="{esc(l["url"])}" rel="sponsored nofollow">{esc(l["label"])}</a>'
        + ('<span class="ph">PLACEHOLDER: affiliate link not active</span>' if l.get("placeholder") else "")
        + "</li>" for l in site["home_gear_links"])
    return f"""<section class="athome"><h2 style="margin-top:0">Want one at home?</h2>
<p class="muted">Buying guides for home saunas and cold plunges are coming soon. Some of these will become affiliate links,
which means we may earn a commission if you buy (see our <a href="/affiliate-disclosure/">disclosure</a>). None are active yet.</p>
<ul>{items}</ul></section>"""

def fact(label, val):
    v = str(val)
    cls = ' class="unknown"' if v.lower().startswith("unknown") else ""
    return f"<dt>{esc(label)}</dt><dd{cls}>{esc(v)}</dd>"

def venue_schema(v, c):
    d = {"@type": "LocalBusiness", "name": v["name"], "url": v["booking_url"],
         "address": {"@type": "PostalAddress", "streetAddress": v["address"],
                     "addressLocality": c["city"], "addressRegion": c["state"], "addressCountry": "US"}}
    if not v["drop_in_price"].lower().startswith("unknown"):
        d["priceRange"] = v["drop_in_price"]
    return d

def top_tags(c, n=8):
    from collections import Counter
    cnt = Counter(t.split(' (')[0] for v in c['venues'] for t in v['sauna_type']
                  if not t.lower().startswith(('heat source', 'sauna (', 'cedar sauna')))
    return [t for t, _ in sorted(cnt.items(), key=lambda x: (-x[1], x[0]))][:n]

def city_page(site, c):
    n = len(c["venues"])
    title = f"Public Saunas in {c['city']}, {c['state']}: {n} Drop-In Saunas & Bathhouses ({c['last_checked'][:4]})"
    desc = (f"{n} drop-in saunas, bathhouses and banyas in {c['city']}, {c['state_name']}: prices, session lengths, "
            f"cold plunge options and booking links, checked {c['last_checked']}.")
    rows = "".join(f"<tr><td><a href='#v{i}'>{esc(v['name'])}</a></td><td>{esc(', '.join(v['sauna_type']))}</td>"
                   f"<td>{esc(v['drop_in_price'])}</td><td>{esc(v['session_length'])}</td></tr>"
                   for i, v in enumerate(c["venues"]))
    cards = ""
    for i, v in enumerate(c["venues"]):
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in v["sauna_type"])
        srcs = " &middot; ".join(f'<a href="{esc(u)}" rel="nofollow">{esc(u)}</a>' for u in v["source_urls"])
        notes = fact("Notes", v["notes"]) if v.get("notes") else ""
        cards += f"""<article class="venue" id="v{i}"><h3>{esc(v['name'])}</h3>
<div class="muted">{esc(v['neighborhood'])} &middot; {esc(v['address'])}</div>
<div class="tags">{tags}</div>
<dl class="facts">{fact('Drop-in price', v['drop_in_price'])}{fact('Session length', v['session_length'])}
{fact('Cold plunge', v['cold_plunge'])}{fact('Schedule / who', v['schedule'])}{notes}
{fact('Last checked', v['last_checked'])}</dl>
<a class="btn" href="{esc(v['booking_url'])}" rel="nofollow">Book / venue site</a>
<div class="sources">Sources: {srcs}</div></article>"""
    schema = {"@context": "https://schema.org", "@type": "ItemList",
              "name": f"Public saunas in {c['city']}, {c['state']}",
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": venue_schema(v, c)}
                                  for i, v in enumerate(c["venues"])]}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": site["base_url"] + "/"},
        {"@type": "ListItem", "position": 2, "name": "Cities", "item": site["base_url"] + "/cities/"},
        {"@type": "ListItem", "position": 3, "name": f"{c['city']}, {c['state']}",
         "item": f"{site['base_url']}/cities/{c['slug']}/"}]}
    head = (f'<script type="application/ld+json">{json.dumps(schema)}</script>\n'
            f'<script type="application/ld+json">{json.dumps(crumbs)}</script>')
    body = f"""<section class="hero"><div class="wrap">
<div class="crumbs" style="color:#f3d2c0"><a href="/" style="color:#f3d2c0">Home</a> / <a href="/cities/" style="color:#f3d2c0">Cities</a></div>
<h1>Public saunas in {esc(c['city'])}, {esc(c['state'])}</h1>
<p>{esc(c['intro'])}</p></div></section>
<main><div class="wrap">
<p class="notice">{n} venues, each checked against the venue's own website on {esc(c['last_checked'])}. Fields we could not confirm are marked <span class="unknown">Unknown</span>. Prices and hours change, so confirm before you go.</p>
<h2>At a glance</h2>
<div class="compare-wrap"><table class="compare"><thead><tr><th>Venue</th><th>Type</th><th>Drop-in</th><th>Session</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Venues</h2>{cards}
<p class="muted">Know a public sauna we missed, or spot something out of date? Corrections are welcome (contact coming soon).</p>
{at_home(site)}
</div></main>"""
    return title, desc, body, head

def build():
    site, cities = load()
    errs = validate(cities)
    if errs:
        print("DATA ERRORS:\n  " + "\n  ".join(errs)); sys.exit(1)
    if "--check" in sys.argv:
        print(f"OK: {len(cities)} cities, {sum(len(c['venues']) for c in cities)} venues"); return
    if os.path.exists(DIST): shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copy(os.path.join(ROOT, "static", "style.css"), DIST)
    urls = []
    def write(path, title, desc, body, head=""):
        out = os.path.join(DIST, path.strip("/"), "index.html") if path != "/" else os.path.join(DIST, "index.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").write(page(site, title, desc, path, body, head))
        urls.append(path)
    cities.sort(key=lambda c: (c["state_name"], c["city"]))
    total = sum(len(c["venues"]) for c in cities)
    city_cards = "".join(
        f"""<div class="card"><a class="city" href="/cities/{c['slug']}/">{esc(c['city'])}, {esc(c['state'])}</a>
<div class="muted">{len(c['venues'])} venues &middot; checked {esc(c['last_checked'])}</div>
<div class="tags">{''.join(f'<span class="tag">{esc(t)}</span>' for t in top_tags(c))}</div></div>"""
        for c in cities)
    # Home
    web = {"@context": "https://schema.org", "@type": "WebSite", "name": site["name"], "url": site["base_url"] + "/"}
    write("/", f"{site['name']}: Find Drop-In Public Saunas, Banyas & Bathhouses in the US",
          f"A hand-checked directory of {total} drop-in public saunas, banyas and bathhouses in {len(cities)} US cities, with prices, session lengths and booking links.",
          f"""<section class="hero"><div class="wrap"><h1>Find a real public sauna near you</h1>
<p>{esc(site['tagline'])} Wood-fired lake saunas, Russian banyas, communal bathhouses and sauna clubs. No gyms, no infrared-only pods.</p></div></section>
<main><div class="wrap">
<h2>Cities</h2><div class="grid">{city_cards}</div>
<h2>How we check venues</h2>
<p>Every listing is checked against the venue's own website (and occasionally a reputable local guide), with the source linked on the page and a "last checked" date. If we couldn't confirm something, we say <span class="unknown">Unknown</span> rather than guess. We list places you can book or walk into as an individual: no private-rental-only spots, gyms, or infrared-only studios.</p>
<p>New cities are added regularly.</p>
{at_home(site)}
</div></main>""", f'<script type="application/ld+json">{json.dumps(web)}</script>')
    # City index
    by_state = {}
    for c in cities: by_state.setdefault(c["state_name"], []).append(c)
    lists = "".join(f"<h2>{esc(s)}</h2><div class='grid'>" + "".join(
        f"<div class='card'><a class='city' href='/cities/{c['slug']}/'>{esc(c['city'])}</a><div class='muted'>{len(c['venues'])} venues</div></div>"
        for c in cs) + "</div>" for s, cs in sorted(by_state.items()))
    write("/cities/", f"All Cities | {site['name']}",
          f"Browse public sauna and bathhouse listings in {len(cities)} US cities.",
          f"<section class='hero'><div class='wrap'><h1>All cities</h1><p>{total} venues in {len(cities)} cities so far.</p></div></section><main><div class='wrap'>{lists}</div></main>")
    for c in cities:
        t, d, b, h = city_page(site, c)
        write(f"/cities/{c['slug']}/", t, d, b, h)
    # About
    write("/about/", f"About | {site['name']}", f"What {site['name']} is, how listings are checked, and how the site is run.",
          f"""<section class="hero"><div class="wrap"><h1>About {esc(site['name'])}</h1></div></section><main><div class="wrap">
<p>{esc(site['name'])} is a small, independent directory of public saunas in the United States: places where an individual can book a seat or walk in, such as community wood-fired saunas, Russian and Eastern European banyas, communal bathhouses and sauna-and-cold-plunge clubs.</p>
<h2>How it's made</h2>
<p>To be upfront: this site is built and maintained with the help of AI tools. Listings are researched from each venue's own website (sometimes supplemented by a reputable local guide), and every listing links to its sources and shows the date it was last checked. We do not visit every venue in person. If we can't confirm a detail, we mark it <span class="unknown">Unknown</span>.</p>
<h2>What we don't do</h2>
<ul><li>We don't make health or medical claims. Talk to a doctor if you have questions about whether sauna or cold water is right for you.</li>
<li>Venues don't pay to be listed, and listings aren't ranked by payment.</li></ul>
<h2>Money</h2>
<p>The site may eventually earn money through affiliate links in home sauna and cold plunge buying guides. See the <a href="/affiliate-disclosure/">affiliate disclosure</a>. As of today, no affiliate links are active.</p>
<h2>Corrections</h2><p>Venues change prices, hours and locations often. If something is wrong, we want to fix it. A contact address is coming soon.</p>
</div></main>""")
    write("/affiliate-disclosure/", f"Affiliate Disclosure | {site['name']}", f"How {site['name']} may earn money through affiliate links.",
          f"""<section class="hero"><div class="wrap"><h1>Affiliate disclosure</h1></div></section><main><div class="wrap">
<p>Some pages on {esc(site['name'])} may contain affiliate links, mainly in sections about home saunas and cold plunges. If you click one and make a purchase, we may earn a commission at no extra cost to you. Affiliate links are marked with <code>rel="sponsored"</code>.</p>
<p><strong>Current status:</strong> no affiliate partnerships are active yet. Links marked "PLACEHOLDER" don't go anywhere.</p>
<p>Affiliate relationships never affect which public saunas are listed or how they're described. Venue listings are not paid placements.</p>
<p>As an independent site, we follow the U.S. FTC's guidance on endorsements and disclosures.</p>
</div></main>""")
    # 404, robots, sitemap
    open(os.path.join(DIST, "404.html"), "w").write(page(site, f"Not found | {site['name']}", "Page not found.", "/404.html",
        "<main><div class='wrap'><h1>Page not found</h1><p><a href='/cities/'>Browse all cities</a></p></div></main>"))
    open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {site['base_url']}/sitemap.xml\n")
    lastmod = {f"/cities/{c['slug']}/": c["last_checked"] for c in cities}
    newest = max(c["last_checked"] for c in cities)
    sm = "".join(f"<url><loc>{site['base_url']}{u}</loc><lastmod>{lastmod.get(u, newest)}</lastmod></url>" for u in urls)
    open(os.path.join(DIST, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    print(f"Built {len(urls)} pages ({len(cities)} cities, {total} venues) into {DIST}")

if __name__ == "__main__":
    build()
