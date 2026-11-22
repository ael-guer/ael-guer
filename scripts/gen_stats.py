"""Builds assets/stats.svg and assets/embers-graph.svg from your public GitHub data.
Runs in the battle-stats GitHub Action. Local test: python3 scripts/gen_stats.py --mock mock.json
No data yet (or --placeholder): writes cards that say they are waiting for the first run."""
import json, os, sys, urllib.request, datetime, html

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
LOGIN = os.environ.get("LOGIN", "ael-guer")

def font_css():
    try:
        r = open(os.path.join(HERE, "anonpro-regular.woff.b64")).read().strip()
        b = open(os.path.join(HERE, "anonpro-bold.woff.b64")).read().strip()
    except OSError:
        return ""
    return (f"@font-face {{ font-family: 'AnonPro'; font-weight: 400; src: url(data:font/woff;base64,{r}) format('woff'); }}\n"
            f"    @font-face {{ font-family: 'AnonPro'; font-weight: 700; src: url(data:font/woff;base64,{b}) format('woff'); }}")

QUERY = """query($login: String!) { user(login: $login) {
  repositories(ownerAffiliations: OWNER, isFork: false, first: 100) { totalCount
    nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } } }
  contributionsCollection { totalCommitContributions
    contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }"""

def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "battle-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GitHub API error: {data['errors']}")
    return data["data"]["user"]

def crunch(user):
    days = [d for w in user["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current, i = 0, len(days) - 1
    if i >= 0 and days[i]["contributionCount"] == 0:   # today not done yet: count from yesterday
        i -= 1
    while i >= 0 and days[i]["contributionCount"] > 0:
        current += 1; i -= 1
    langs = {}
    for repo in user["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    return {
        "total": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "commits": user["contributionsCollection"]["totalCommitContributions"],
        "repos": user["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in user["repositories"]["nodes"]),
        "current": current, "longest": longest,
        "langs": [(n, s / total) for n, s in top],
        "days": days[-371:],
    }

STYLE = """
    .t  {{ font-family: 'AnonPro', 'Courier New', monospace; font-weight: 700; font-size: 15px; letter-spacing: 3px; fill: #ff2a3d; }}
    .k  {{ font-family: 'AnonPro', 'Courier New', monospace; font-size: 13px; letter-spacing: 1px; fill: #8b8b96; }}
    .v  {{ font-family: 'AnonPro', 'Courier New', monospace; font-weight: 700; font-size: 26px; fill: #f2f2f4; }}
    .l  {{ font-family: 'AnonPro', 'Courier New', monospace; font-size: 13px; fill: #d6d6dc; }}
    .in {{ opacity: 0; animation: in .7s ease-out forwards; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
    .bar {{ transform-box: fill-box; transform-origin: left center; animation: grow 1.6s cubic-bezier(.2,.8,.2,1) both; }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    .ember {{ animation: flick 2.6s ease-in-out infinite; }}
    @keyframes flick {{ 0%, 100% {{ opacity: .55; }} 50% {{ opacity: 1; }} }}
    .spark {{ animation: rise 3s linear infinite; opacity: 0; }}
    @keyframes rise {{ 0% {{ transform: translateY(0); opacity: 0; }} 15% {{ opacity: 1; }} 100% {{ transform: translateY(-46px); opacity: 0; }} }}
"""

def frame(w, h, label, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{html.escape(label)}">
  <defs><filter id="g" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <style>
    {font_css()}{STYLE.format()}  </style>
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="12" fill="#0c0709" stroke="#ff2a3d" stroke-opacity="0.6"/>
{body}
</svg>
"""

def stats_svg(s):
    W, H = 900, 270
    cells = [("CONTRIBUTIONS", s["total"]), ("COMMITS", s["commits"]), ("STREAK", f'{s["current"]}d'),
             ("LONGEST", f'{s["longest"]}d'), ("REPOS", s["repos"]), ("STARS", s["stars"])]
    b = ['  <text class="t" x="34" y="44">&#9670; BATTLE STATS</text>',
         '  <line x1="34" y1="58" x2="866" y2="58" stroke="#ff2a3d" stroke-opacity="0.4"/>']
    for i, (k, v) in enumerate(cells):
        x, y = 34 + (i % 3) * 140, 104 + (i // 3) * 80
        b.append(f'  <g class="in" style="animation-delay:{0.2 + i*0.12:.2f}s"><text class="v" x="{x}" y="{y}">{v}</text>'
                 f'<text class="k" x="{x}" y="{y+22}">{k}</text></g>')
    b.append('  <text class="k" x="480" y="90" style="fill:#ff2a3d;font-weight:700;letter-spacing:3px">TOP LANGUAGES</text>')
    shades = ["#ff2a3d", "#e0213a", "#b81a2c", "#8a0f16", "#e8dcc3"]
    for i, (name, share) in enumerate(s["langs"] or [("no code yet", 0)]):
        y = 108 + i * 30
        b.append(f'  <text class="l" x="480" y="{y+12}">{html.escape(name)}</text>')
        b.append(f'  <rect x="600" y="{y}" width="230" height="14" rx="3" fill="#14060a" stroke="#8a0f16"/>')
        if share:
            b.append(f'  <rect class="bar" style="animation-delay:{0.3 + i*0.15:.2f}s" x="600" y="{y}" width="{230*share:.1f}" height="14" rx="3" fill="{shades[i]}"/>')
        b.append(f'  <text class="k" x="866" y="{y+12}" text-anchor="end">{share*100:.0f}%</text>')
    stamp = datetime.date.today().isoformat()
    b.append(f'  <text class="k" x="866" y="254" text-anchor="end" style="font-size:11px">updated {stamp}</text>')
    return frame(W, H, "Battle stats", "\n".join(b))

def embers_svg(s):
    days = s["days"]
    CELL, GAP, X0, Y0 = 13, 3, 34, 70
    first = datetime.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7             # GitHub weeks start on Sunday
    peak = max([d["contributionCount"] for d in days] + [1])
    shades = ["#ff2a3d", "#c81c2c", "#8a0f16", "#5a0a10"]
    rects, sparks = [], []
    for i, d in enumerate(days):
        idx = i + offset
        col, row = idx // 7, idx % 7
        x, y = X0 + col * (CELL + GAP), Y0 + row * (CELL + GAP)
        c = d["contributionCount"]
        if c == 0:
            rects.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="#14060a"/>')
            continue
        lvl = 0 if c >= peak * .75 else 1 if c >= peak * .5 else 2 if c >= peak * .25 else 3
        rects.append(f'<rect class="ember" style="animation-delay:{(i*0.137)%2.6:.2f}s" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{shades[lvl]}"><title>{d["date"]}: {c}</title></rect>')
        if lvl <= 1:
            sparks.append(f'<circle class="spark" style="animation-delay:{(i*0.31)%3:.2f}s" cx="{x + CELL/2}" cy="{y}" r="1.8" fill="#ff5566"/>')
    cols = (len(days) + offset + 6) // 7
    W = X0 * 2 + cols * (CELL + GAP); H = Y0 + 7 * (CELL + GAP) + 40
    body = [f'  <text class="t" x="{X0}" y="44">&#9670; THE FORGE · {s["total"]} CONTRIBUTIONS IN THE LAST YEAR</text>',
            '  <g>' + "".join(rects) + '</g>', '  <g filter="url(#g)">' + "".join(sparks) + '</g>',
            f'  <text class="k" x="{X0}" y="{H-14}" style="font-size:11px">every square is a day · the hotter it burns, the more I built</text>']
    return frame(W, H, "Contribution graph as embers", "\n".join(body))

def placeholder(name, w, h, title):
    body = (f'  <text class="t" x="34" y="44">&#9670; {title}</text>\n'
            f'  <text class="l" x="34" y="90">waiting for the first forge...</text>\n'
            f'  <text class="k" x="34" y="116">this card fills in after the battle-stats Action runs (Actions tab &#8594; Run workflow)</text>')
    return frame(w, h, title, body)

def main():
    os.makedirs(ASSETS, exist_ok=True)
    if "--placeholder" in sys.argv:
        open(os.path.join(ASSETS, "stats.svg"), "w").write(placeholder("stats", 900, 150, "BATTLE STATS"))
        open(os.path.join(ASSETS, "embers-graph.svg"), "w").write(placeholder("embers", 900, 150, "THE FORGE"))
        print("placeholders written"); return
    if "--mock" in sys.argv:
        user = json.load(open(sys.argv[sys.argv.index("--mock") + 1]))
    else:
        user = fetch()
    s = crunch(user)
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else ASSETS
    open(os.path.join(out, "stats.svg"), "w").write(stats_svg(s))
    open(os.path.join(out, "embers-graph.svg"), "w").write(embers_svg(s))
    print(f"stats written: {s['total']} contributions, streak {s['current']}d, top {[n for n,_ in s['langs']]}")

if __name__ == "__main__":
    main()
