"""Reads your public repos and redraws everything on the profile:
   - 1337 projects (repos named like the projects in "order"): projects.json, NOW LOADING board, progress bar, project map
   - labs: a repo whose Website field points to your labs site gets a LAB link (any other Website link = LIVE)
   - your own projects (every other public repo, minus "exclude"): assets/power.svg + the "Unleashing my power" table
   - README tables between the <!-- ...:START --> / <!-- ...:END --> markers
   Run by the progress Action. Local tests:
     python3 scripts/gen_progress.py --repos libft,ft_printf          (names only)
     python3 scripts/gen_progress.py --fake tests/fake-repos.json     (full repo objects, like the API)"""
import json, math, os, re, sys, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ASSETS = os.path.join(ROOT, "assets")
CFG = json.load(open(os.path.join(ROOT, "projects-config.json"), encoding="utf-8"))
USER, ORDER, LABS = CFG["user"], CFG["order"], CFG.get("labs", {})
LABS_BASE = CFG.get("labs_base", "https://ael-guer-labs.ael-guer.workers.dev").rstrip("/")
EXCLUDE = {n.lower() for n in CFG.get("exclude", [])} | {USER.lower()}

def font_face():
    try:
        r = open(os.path.join(HERE, "anonpro-regular.woff.b64")).read().strip()
        b = open(os.path.join(HERE, "anonpro-bold.woff.b64")).read().strip()
    except OSError:
        return ""
    return (f"@font-face {{ font-family: 'AnonPro'; font-weight: 400; src: url(data:font/woff;base64,{r}) format('woff'); }}\n"
            f"    @font-face {{ font-family: 'AnonPro'; font-weight: 700; src: url(data:font/woff;base64,{b}) format('woff'); }}\n    ")
FONT = "'AnonPro', 'Courier New', monospace"

def public_repos():
    """Public, non-fork repos as dicts: name, description, language, homepage, pushed_at, html_url."""
    if "--repos" in sys.argv:                                   # local test without the API (names only)
        names = [n.strip() for n in sys.argv[sys.argv.index("--repos") + 1].split(",") if n.strip()]
        return [{"name": n} for n in names]
    if "--fake" in sys.argv:                                    # local test with full repo objects
        return [r for r in json.load(open(sys.argv[sys.argv.index("--fake") + 1], encoding="utf-8"))
                if not r.get("private") and not r.get("fork")]
    out, page = [], 1
    while True:
        req = urllib.request.Request(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "progress-bot",
                                              **({"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]} if os.environ.get("GITHUB_TOKEN") else {})})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        out += [repo for repo in batch if not repo.get("private") and not repo.get("fork")]
        if len(batch) < 100: return out
        page += 1

def link_kind(url):
    """Website field -> ('lab', url) if it points to the labs site, ('live', url) for anything else, (None, None) if empty."""
    url = (url or "").strip()
    if not url: return None, None
    if not re.match(r"^https?://", url): url = "https://" + url
    return ("lab", url) if url.startswith(LABS_BASE) else ("live", url)

def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# ---------------- LED board: NOW LOADING: <project> ----------------
F = {
 'A':"01110 10001 10001 11111 10001 10001 10001", 'B':"11110 10001 10001 11110 10001 10001 11110",
 'C':"01110 10001 10000 10000 10000 10001 01110", 'D':"11110 10001 10001 10001 10001 10001 11110",
 'E':"11111 10000 10000 11110 10000 10000 11111", 'F':"11111 10000 10000 11110 10000 10000 10000",
 'G':"01110 10001 10000 10111 10001 10001 01111", 'H':"10001 10001 10001 11111 10001 10001 10001",
 'I':"01110 00100 00100 00100 00100 00100 01110", 'J':"00111 00010 00010 00010 00010 10010 01100",
 'K':"10001 10010 10100 11000 10100 10010 10001", 'L':"10000 10000 10000 10000 10000 10000 11111",
 'M':"10001 11011 10101 10101 10001 10001 10001", 'N':"10001 11001 10101 10011 10001 10001 10001",
 'O':"01110 10001 10001 10001 10001 10001 01110", 'P':"11110 10001 10001 11110 10000 10000 10000",
 'Q':"01110 10001 10001 10001 10101 10010 01101", 'R':"11110 10001 10001 11110 10100 10010 10001",
 'S':"01111 10000 10000 01110 00001 00001 11110", 'T':"11111 00100 00100 00100 00100 00100 00100",
 'U':"10001 10001 10001 10001 10001 10001 01110", 'V':"10001 10001 10001 10001 10001 01010 00100",
 'W':"10001 10001 10001 10101 10101 10101 01010", 'X':"10001 10001 01010 00100 01010 10001 10001",
 'Y':"10001 10001 01010 00100 00100 00100 00100", 'Z':"11111 00001 00010 00100 01000 10000 11111",
 '0':"01110 10001 10011 10101 11001 10001 01110", '1':"00100 01100 00100 00100 00100 00100 01110",
 '2':"01110 10001 00001 00010 00100 01000 11111", '3':"11110 00001 00001 01110 00001 00001 11110",
 '4':"00010 00110 01010 10010 11111 00010 00010", '5':"11111 10000 11110 00001 00001 10001 01110",
 '6':"00110 01000 10000 11110 10001 10001 01110", '7':"11111 00001 00010 00100 01000 01000 01000",
 '8':"01110 10001 10001 01110 10001 10001 01110", '9':"01110 10001 10001 01111 00001 00010 01100",
 '_':"00000 00000 00000 00000 00000 00000 11111", '-':"00000 00000 00000 11111 00000 00000 00000",
 ':':"0 1 0 0 0 1 0", '.':"0 0 0 0 0 0 1", ' ':"000 000 000 000 000 000 000", '!':"1 1 1 1 1 0 1",
}
def led(text):
    text = text.upper()
    CELL, DOT, PADX, PADY = 7, 5.6, 34, 22
    cols = []
    for ch in text:
        rows = F.get(ch, F[' ']).split()
        for c in range(len(rows[0])): cols.append([rows[r][c] == '1' for r in range(7)])
        cols.append([False] * 7)
    cols.pop()
    W = round(len(cols) * CELL + PADX * 2 + 30); H = round(7 * CELL + PADY * 2)
    grid, lit = [], []
    for ci, col in enumerate(cols):
        for r in range(7): grid.append(f'<rect x="{PADX + ci*CELL}" y="{PADY + r*CELL}" width="{DOT}" height="{DOT}" rx="1.2"/>')
        dots = "".join(f'<rect x="{PADX + ci*CELL}" y="{PADY + r*CELL}" width="{DOT}" height="{DOT}" rx="1.2"/>' for r, on in enumerate(col) if on)
        if dots: lit.append(f'<g class="c" style="animation-delay:{ci*0.03:.2f}s">{dots}</g>')
    cx = PADX + len(cols) * CELL + 8
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{text}">
  <defs><filter id="g" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <style>
    .c {{ animation: wave 3s ease-in-out infinite; }}
    @keyframes wave {{ 0%, 100% {{ opacity: .5; }} 10% {{ opacity: 1; fill: #ffd7da; }} 25% {{ opacity: 1; }} }}
    .cur {{ animation: blink 1s step-end infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    .scan {{ animation: scan 4s linear infinite; }}
    @keyframes scan {{ from {{ transform: translateX(-120px); }} to {{ transform: translateX({W}px); }} }}
  </style>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="#050507" stroke="#8a0f16" stroke-width="2"/>
  <g fill="#1d0508">{"".join(grid)}</g>
  <g fill="#ff2a3d" filter="url(#g)">{"".join(lit)}</g>
  <rect class="cur" x="{cx}" y="{PADY}" width="14" height="{7*CELL - 1.4}" fill="#e8dcc3"/>
  <rect class="scan" x="0" y="2" width="80" height="{H-4}" fill="#ff2a3d" fill-opacity="0.07"/>
</svg>
'''

# ---------------- progress bar ----------------
def progress(done, current):
    total, n = len(ORDER), len(done)
    W, bx, bw = 900, 40, 820
    fill = bw * n / total
    ticks = "".join(f'<line x1="{bx + bw*i/total:.1f}" y1="58" x2="{bx + bw*i/total:.1f}" y2="82" stroke="#050507" stroke-width="2"/>' for i in range(1, total))
    slain = ", ".join(done) if done else "none yet"
    battle = f"  &#183;  in battle: {current}" if current else "  &#183;  the path is complete"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 120" width="{W}" height="120" role="img" aria-label="Common core progress: {n} of {total} cleared">
  <defs>
    <linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="#8a0f16"/><stop offset="1" stop-color="#ff2a3d"/></linearGradient>
    <filter id="g" x="-10%" y="-80%" width="120%" height="260%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <style>
    {font_face()}.t {{ font-family: {FONT}; font-weight: 700; font-size: 14px; letter-spacing: 3px; fill: #ff2a3d; }}
    .n {{ font-family: {FONT}; font-weight: 700; font-size: 14px; letter-spacing: 2px; fill: #f2f2f4; }}
    .s {{ font-family: {FONT}; font-size: 12px; letter-spacing: 1px; fill: #8b8b96; }}
    .bar {{ transform-box: fill-box; transform-origin: left center; animation: grow 2s cubic-bezier(.2,.8,.2,1) both; }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    .tip {{ animation: pulse 1.4s ease-in-out infinite; }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .5; }} 50% {{ opacity: 1; }} }}
    .spark {{ animation: rise 2.4s linear infinite; }}
    @keyframes rise {{ 0% {{ transform: translateY(0); opacity: 1; }} 100% {{ transform: translateY(-40px); opacity: 0; }} }}
  </style>
  <rect width="{W}" height="120" rx="12" fill="#0c0709" stroke="#ff2a3d" stroke-opacity="0.6"/>
  <text class="t" x="{bx}" y="40">&#9670; COMMON CORE</text>
  <text class="n" x="{bx+bw}" y="40" text-anchor="end">{n} / {total} CLEARED</text>
  <rect x="{bx}" y="58" width="{bw}" height="24" rx="4" fill="#14060a" stroke="#8a0f16"/>
  <rect class="bar" x="{bx}" y="58" width="{fill:.1f}" height="24" rx="4" fill="url(#f)" filter="url(#g)"/>
  {ticks}
  <rect class="tip" x="{bx+fill-3:.1f}" y="54" width="6" height="32" fill="#ffd7da"/>
  <circle class="spark" cx="{bx+fill-6:.1f}" cy="58" r="2" fill="#ff5566"/>
  <circle class="spark" cx="{bx+fill+2:.1f}" cy="58" r="1.5" fill="#e8dcc3" style="animation-delay:1.1s"/>
  <text class="s" x="{bx}" y="104">slain: {slain}{battle}</text>
</svg>
'''

# ---------------- project map ----------------
def project_map(done_idx, next_idx):
    names, CX, CY = ORDER, 300, 380
    rings = [(110, list(range(0, 5))), (195, list(range(5, 13))), (280, list(range(13, len(names))))]
    pts = {}
    for r, idxs in rings:
        for k, i in enumerate(idxs):
            a = math.radians(-90 + k * 360.0 / len(idxs))
            pts[i] = (round(CX + r * math.cos(a), 1), round(CY + r * math.sin(a), 1))
    order = [pts[i] for i in range(len(names))]
    path_d = "M" + " L".join(f"{x} {y}" for x, y in order)
    nodes, legend = [], []
    for i in range(len(names)):
        x, y = pts[i]; num = f"{i + 1:02d}"
        if i in done_idx:
            nodes.append(f'<circle cx="{x}" cy="{y}" r="14" fill="#e8dcc3" filter="url(#glow)"/><text x="{x}" y="{y + 5}" class="ok" text-anchor="middle">&#10003;</text>')
        elif i == next_idx:
            nodes.append(f'<circle class="pulse" cx="{x}" cy="{y}" r="15" fill="#ff2a3d" filter="url(#glow)"/><text x="{x}" y="{y + 4}" class="num" text-anchor="middle" fill="#050507">{num}</text>')
        else:
            nodes.append(f'<circle class="dim" cx="{x}" cy="{y}" r="12" fill="#120608" stroke="#ff2a3d" stroke-width="1.5"/><text x="{x}" y="{y + 4}" class="num" text-anchor="middle">{num}</text>')
    for i, name in enumerate(names):
        col = 0 if i < 12 else 1; row = i if col == 0 else i - 12
        x = 630 if col == 0 else 820; y = 130 + row * 26
        if i in done_idx: legend.append(f'<text x="{x}" y="{y}" class="lg-done">&#10003; {name}</text>')
        elif i == next_idx: legend.append(f'<text x="{x}" y="{y}" class="lg-next">&#9654; {name}</text>')
        else: legend.append(f'<text x="{x}" y="{y}" class="lg">&#9670; {name}</text>')
    n = len(done_idx); total = len(names)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 740" width="1000" height="740" role="img" aria-label="Project map: {n} cleared, {total - n} to conquer">
  <defs>
    <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#8a0f16" stop-opacity="0.55"/><stop offset="1" stop-color="#8a0f16" stop-opacity="0"/></radialGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <style>
    {font_face()}.num  {{ font-family: {FONT}; font-size: 10px; font-weight: 700; fill: #f2f2f4; }}
    .ok   {{ font-family: {FONT}; font-size: 13px; font-weight: 700; fill: #050507; }}
    .lg   {{ font-family: {FONT}; font-size: 11px; fill: #8b8b96; }}
    .lg-done {{ font-family: {FONT}; font-size: 11px; font-weight: 700; fill: #e8dcc3; }}
    .lg-next {{ font-family: {FONT}; font-size: 11px; font-weight: 700; fill: #ff2a3d; }}
    .hd   {{ font-family: {FONT}; font-size: 13px; font-weight: 700; letter-spacing: 3px; fill: #ff2a3d; }}
    .foot {{ font-family: {FONT}; font-size: 11px; letter-spacing: 2px; fill: #8b8b96; }}
    .sigil {{ font-family: {FONT}; font-size: 26px; font-weight: 700; fill: #ff2a3d; }}
    .path {{ fill: none; stroke: #5a0f16; stroke-width: 2; stroke-dasharray: 3 7; animation: march 1.4s linear infinite; }}
    .ring {{ fill: none; stroke: #3a0a10; stroke-width: 1; stroke-dasharray: 2 6; transform-origin: {CX}px {CY}px; animation: spin 40s linear infinite; }}
    .spin {{ fill: none; stroke: #ff2a3d; stroke-width: 1.2; stroke-dasharray: 14 10; stroke-opacity: 0.6; transform-origin: {CX}px {CY}px; animation: spin -18s linear infinite; }}
    .dim  {{ animation: edge 2.8s ease-in-out infinite; }}
    .pulse {{ animation: beat 1.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    .packet {{ fill: #ff2a3d; filter: url(#glow); }}
    .halo {{ transform-origin: {CX}px {CY}px; animation: breathe 3.5s ease-in-out infinite; }}
    @keyframes march {{ to {{ stroke-dashoffset: -40; }} }}
    @keyframes spin  {{ to {{ transform: rotate(360deg); }} }}
    @keyframes edge  {{ 0%, 100% {{ stroke-opacity: 0.45; }} 50% {{ stroke-opacity: 1; }} }}
    @keyframes beat  {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.3); }} }}
    @keyframes breathe {{ 0%, 100% {{ opacity: 0.45; }} 50% {{ opacity: 0.95; }} }}
  </style>
  <rect width="1000" height="740" fill="#050507"/>
  <circle class="halo" cx="{CX}" cy="{CY}" r="300" fill="url(#halo)"/>
  <circle class="ring" cx="{CX}" cy="{CY}" r="110"/><circle class="ring" cx="{CX}" cy="{CY}" r="195"/><circle class="ring" cx="{CX}" cy="{CY}" r="280"/>
  <polyline class="path" points="{" ".join(f"{x},{y}" for x, y in order)}"/>
  <circle class="packet" r="5"><animateMotion dur="22s" repeatCount="indefinite" path="{path_d}"/></circle>
  <circle class="packet" r="3" opacity="0.6"><animateMotion dur="22s" begin="-11s" repeatCount="indefinite" path="{path_d}"/></circle>
  {"".join(nodes)}
  <circle cx="{CX}" cy="{CY}" r="48" fill="#120608" stroke="#ff2a3d" stroke-width="2" filter="url(#glow)"/>
  <circle class="spin" cx="{CX}" cy="{CY}" r="62"/>
  <text x="{CX}" y="{CY + 9}" class="sigil" text-anchor="middle">AEL</text>
  <text x="630" y="98" class="hd">THE PATH</text>
  {"".join(legend)}
  <text x="630" y="676" class="foot">{n} / {total} CLEARED</text>
  <text x="630" y="698" class="foot">&#10003; cleared  &#183;  &#9654; next  &#183;  &#9670; still to conquer</text>
</svg>
'''

# ---------------- UNLEASHING MY POWER: your own projects ----------------
LANG_COLORS = {"C": "#a8b9cc", "C++": "#f34b7d", "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
               "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584", "Java": "#b07219",
               "Makefile": "#427819", "Lua": "#000080", "PHP": "#4F5D95", "Dart": "#00B4AB", "Kotlin": "#A97BFF"}

def cut(t, n):
    t = (t or "").strip()
    return t if len(t) <= n else t[:n - 1].rstrip() + "…"

def wrap2(t, n):
    """description on up to 2 lines of n characters"""
    words, lines, cur, used = (t or "").split(), [], "", 0
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= n:
            cur = (cur + " " + w).strip(); used += 1
        else:
            lines.append(cur); cur = w; used += 1
            if len(lines) == 2: used -= 1; cur = ""; break
    if cur and len(lines) < 2: lines.append(cur)
    if used < len(words) and lines: lines[-1] = cut(lines[-1] + " …", n)
    return [cut(l, n) for l in lines[:2]]

def power(personal):
    W, CW, CH, GAP, X0, TOP = 1000, 300, 128, 20, 30, 104
    shown = personal[:6]
    rows = max(1, math.ceil(len(shown) / 3))
    H = TOP + rows * (CH + GAP) + (40 if len(personal) > 6 else 16)
    cards = []
    for i, p in enumerate(shown):
        in_row = min(3, len(shown) - (i // 3) * 3)                 # a short last row is centred
        x = X0 + (3 - in_row) * (CW + GAP) / 2 + (i % 3) * (CW + GAP)
        y = TOP + (i // 3) * (CH + GAP)
        lang = p.get("language") or ""
        col = LANG_COLORS.get(lang, "#8b8b96")
        d = wrap2(p.get("description") or "no description yet", 34)
        badges, bx = [], x + CW - 14
        for label, on in (("&#9650; LIVE", p.get("live")), ("&#9670; LAB", p.get("lab"))):
            if not on: continue
            w = 62
            badges.append(f'<rect x="{bx - w}" y="{y + CH - 32}" width="{w}" height="20" rx="10" fill="#2a0709" stroke="#ff2a3d"/>'
                          f'<text x="{bx - w / 2}" y="{y + CH - 18}" class="bd" text-anchor="middle">{label}</text>')
            bx -= w + 8
        when = (p.get("pushed_at") or "")[:10]
        d0 = esc(d[0]) if d else ""
        d1 = esc(d[1]) if len(d) > 1 else ""
        meta = esc(lang or "code") + (" · " + when if when else "")
        cards.append(
            f'  <g class="card" style="animation-delay:{i * 0.12:.2f}s">\n'
            f'    <rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="10" fill="#0c0709" stroke="#8a0f16" stroke-width="1.5"/>\n'
            f'    <rect class="run" x="{x}" y="{y}" width="{CW}" height="{CH}" rx="10" fill="none" stroke="#ff2a3d" stroke-width="2" style="animation-delay:{i * 0.7:.1f}s"/>\n'
            f'    <text x="{x + 16}" y="{y + 30}" class="nm">{esc(cut(p["name"], 24))}</text>\n'
            f'    <text x="{x + 16}" y="{y + 54}" class="ds">{d0}</text>\n'
            f'    <text x="{x + 16}" y="{y + 72}" class="ds">{d1}</text>\n'
            f'    <circle cx="{x + 21}" cy="{y + CH - 22}" r="5" fill="{col}"/>\n'
            f'    <text x="{x + 32}" y="{y + CH - 18}" class="lg">{meta}</text>\n'
            f'    {"".join(badges)}\n'
            f'  </g>')
    if not shown:
        cards.append(f'  <text x="{W / 2}" y="{TOP + 52}" text-anchor="middle" class="sleep">THE POWER SLEEPS</text>\n'
                     f'  <text x="{W / 2}" y="{TOP + 84}" text-anchor="middle" class="lg">push a project of your own to awaken it</text>')
    more = (f'<text x="{W / 2}" y="{H - 16}" text-anchor="middle" class="lg">+ {len(personal) - 6} more in the table below</text>'
            if len(personal) > 6 else "")
    embers = "".join(f'<circle class="em" cx="{60 + i * 110}" cy="{H + 5}" r="{1.6 + (i % 3) * 0.6:.1f}" fill="#ff2a3d" '
                     f'style="animation-delay:{(i * 0.9) % 5:.1f}s"/>' for i in range(9))
    n = len(personal)
    css = (
        f"    {font_face()}text {{ font-family: {FONT}; }}\n"
        "    .tt { font-size: 30px; font-weight: 700; fill: #f2f2f4; letter-spacing: 6px; }\n"
        "    .st { font-size: 13px; fill: #8b8b96; letter-spacing: 3px; }\n"
        "    .nm { font-size: 19px; font-weight: 700; fill: #f2f2f4; }\n"
        "    .ds { font-size: 13px; fill: #b9b2a6; }\n"
        "    .lg { font-size: 12px; fill: #8b8b96; letter-spacing: 1px; }\n"
        "    .bd { font-size: 10px; font-weight: 700; fill: #ffd7da; letter-spacing: 1px; }\n"
        "    .sleep { font-size: 26px; font-weight: 700; fill: #ff2a3d; letter-spacing: 8px; animation: pulse 2.4s ease-in-out infinite; }\n"
        "    .flick { animation: flick 4s linear infinite; }\n"
        "    .card { animation: rise .7s ease-out both; }\n"
        "    .run { stroke-dasharray: 90 760; animation: run 4.2s linear infinite; filter: url(#g); }\n"
        "    .em { animation: up 6s linear infinite; }\n"
        "    @keyframes rise { from { opacity: 0; transform: translateY(12px); } }\n"
        "    @keyframes run { to { stroke-dashoffset: -850; } }\n"
        "    @keyframes pulse { 0%,100% { opacity: .45; } 50% { opacity: 1; } }\n"
        "    @keyframes flick { 0%,92%,100% { opacity: 1; } 93% { opacity: .35; } 95% { opacity: 1; } 96% { opacity: .6; } }\n"
        f"    @keyframes up {{ 0% {{ transform: translateY(0); opacity: .9; }} 100% {{ transform: translateY(-{H}px); opacity: 0; }} }}\n")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Unleashing my power: {n} own projects">\n'
        '  <defs><filter id="g" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="3" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>\n'
        f"  <style>\n{css}  </style>\n"
        f'  <rect width="{W}" height="{H}" rx="14" fill="#050507" stroke="#ff2a3d" stroke-opacity=".55"/>\n'
        f"  {embers}\n"
        f'  <text x="{W / 2}" y="50" text-anchor="middle" class="tt flick" filter="url(#g)">UNLEASHING MY POWER</text>\n'
        f'  <text x="{W / 2}" y="76" text-anchor="middle" class="st">{n} PROJECT{"" if n == 1 else "S"} FORGED OUTSIDE THE PATH</text>\n'
        + "\n".join(cards) + f"\n  {more}\n</svg>\n")

# ---------------- README tables (only the text between the markers is rewritten) ----------------
def md(t):
    return (t or "").replace("|", "\\|").replace("\n", " ").strip()

def path_table(done, repos_url, labs):
    if not done: return "_No project cleared yet._"
    rows = ["| # | Project | Source | Lab |", "|:-:|---|:-:|:-:|"]
    for p in done:
        lab = f"[🔒 open the lab]({labs[p]})" if labs.get(p) else "—"
        rows.append(f"| {ORDER.index(p) + 1:02d} | **{p}** | [repo]({repos_url[p]}) | {lab} |")
    return "\n".join(rows)

def power_table(personal):
    if not personal: return "_Nothing unleashed yet._"
    rows = ["| Project | What it is | Language | Links |", "|---|---|:-:|:-:|"]
    for p in personal:
        links = ([f"[repo]({p['url']})"] + ([f"[live]({p['live']})"] if p.get("live") else [])
                 + ([f"[🔒 lab]({p['lab']})"] if p.get("lab") else []))
        rows.append(f"| **{md(p['name'])}** | {md(p.get('description')) or '—'} | {md(p.get('language')) or '—'} | {' · '.join(links)} |")
    return "\n".join(rows)

def fill(readme, key, body):
    start, end = f"<!-- {key}:START -->", f"<!-- {key}:END -->"
    return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: f"{start}\n{body}\n{end}", readme, flags=re.S)

def ensure_sections(readme):
    """first run only: add the new sections without touching anything else"""
    if "<!-- PATH-LINKS:START -->" not in readme:
        i = readme.find('<img src="assets/progress.svg"')
        if i != -1:
            j = readme.find("</p>", i) + len("</p>")
            readme = readme[:j] + "\n\n<!-- PATH-LINKS:START -->\n<!-- PATH-LINKS:END -->" + readme[j:]
        else:
            readme += "\n\n<!-- PATH-LINKS:START -->\n<!-- PATH-LINKS:END -->\n"
    if "<!-- POWER:START -->" not in readme:
        block = ('## 🔥 Unleashing my power\n\n<p align="center">\n  <img src="assets/power.svg" alt="Unleashing my power: my own projects" width="100%"/>\n</p>\n\n'
                 "<!-- POWER:START -->\n<!-- POWER:END -->\n\n")
        i = readme.find("## ⚔️ Battle Stats")
        readme = readme[:i] + block + readme[i:] if i != -1 else readme + "\n\n" + block
    return readme

def main():
    repos = public_repos()
    by_name = {r["name"].lower(): r for r in repos}
    order_low = {p.lower() for p in ORDER}
    done = [p for p in ORDER if p.lower() in by_name]
    current = next((p for p in ORDER if p.lower() not in by_name), None)
    repos_url = {p: by_name[p.lower()].get("html_url") or f"https://github.com/{USER}/{p}" for p in done}
    labs, live = {}, {}
    for p in done:                                              # 1337 projects: Website field first, config "labs" as a fallback
        kind, url = link_kind(by_name[p.lower()].get("homepage"))
        if kind == "lab": labs[p] = url
        elif kind == "live": live[p] = url
        if p not in labs and LABS.get(p): labs[p] = LABS[p]
    personal = []
    for r in repos:                                             # every other public repo = your own project
        low = r["name"].lower()
        if low in order_low or low in EXCLUDE: continue
        kind, url = link_kind(r.get("homepage"))
        personal.append({"name": r["name"], "description": r.get("description") or "", "language": r.get("language") or "",
                         "url": r.get("html_url") or f"https://github.com/{USER}/{r['name']}", "pushed_at": r.get("pushed_at") or "",
                         "lab": url if kind == "lab" else None, "live": url if kind == "live" else None})
    personal.sort(key=lambda p: p["pushed_at"], reverse=True)
    state = {"user": USER, "order": ORDER, "done": done, "current": current, "labs": labs, "live": live,
             "repos": repos_url, "personal": personal}
    def write(path, text):
        full = os.path.join(ROOT, path); old = open(full, encoding="utf-8").read() if os.path.exists(full) else None
        if old != text: open(full, "w", encoding="utf-8").write(text); print("updated", path)
    write("projects.json", json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    write("assets/forging.svg", led(f"NOW LOADING: {current}" if current else "ALL CLEARED!"))
    write("assets/progress.svg", progress(done, current))
    write("assets/project-map-v2.svg", project_map({ORDER.index(p) for p in done}, ORDER.index(current) if current else -1))
    write("assets/power.svg", power(personal))
    readme = ensure_sections(open(os.path.join(ROOT, "README.md"), encoding="utf-8").read())
    readme = fill(readme, "PATH-LINKS", path_table(done, repos_url, labs))
    readme = fill(readme, "POWER", power_table(personal))
    write("README.md", readme)
    print(f"done: {done} | now loading: {current} | labs: {list(labs)} | own projects: {[p['name'] for p in personal]}")

if __name__ == "__main__":
    main()
