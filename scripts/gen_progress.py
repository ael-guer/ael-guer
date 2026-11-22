"""Reads which projects you pushed (public repos named like the projects) and redraws:
   projects.json, assets/forging.svg (NOW LOADING), assets/progress.svg, assets/project-map-v2.svg.
   Run by the progress Action. Local test: python3 scripts/gen_progress.py --repos libft,ft_printf"""
import json, math, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
ASSETS = os.path.join(ROOT, "assets")
CFG = json.load(open(os.path.join(ROOT, "projects-config.json"), encoding="utf-8"))
USER, ORDER, LABS = CFG["user"], CFG["order"], CFG.get("labs", {})

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
    if "--repos" in sys.argv:                                   # local test without the API
        return {n.strip().lower() for n in sys.argv[sys.argv.index("--repos") + 1].split(",") if n.strip()}
    names, page = set(), 1
    while True:
        req = urllib.request.Request(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "progress-bot",
                                              **({"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]} if os.environ.get("GITHUB_TOKEN") else {})})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        names |= {repo["name"].lower() for repo in batch if not repo.get("private") and not repo.get("fork")}
        if len(batch) < 100: return names
        page += 1

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

def main():
    repos = public_repos()
    done = [p for p in ORDER if p.lower() in repos]
    current = next((p for p in ORDER if p.lower() not in repos), None)
    state = {"user": USER, "order": ORDER, "done": done, "current": current, "labs": LABS,
             "repos": {p: f"https://github.com/{USER}/{p}" for p in done}}
    def write(path, text):
        full = os.path.join(ROOT, path); old = open(full, encoding="utf-8").read() if os.path.exists(full) else None
        if old != text: open(full, "w", encoding="utf-8").write(text); print("updated", path)
    write("projects.json", json.dumps(state, indent=2) + "\n")
    write("assets/forging.svg", led(f"NOW LOADING: {current}" if current else "ALL CLEARED!"))
    write("assets/progress.svg", progress(done, current))
    write("assets/project-map-v2.svg", project_map({ORDER.index(p) for p in done}, ORDER.index(current) if current else -1))
    print(f"done: {done} | now loading: {current}")

if __name__ == "__main__":
    main()
