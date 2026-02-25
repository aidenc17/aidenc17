"""
generate.py — Builds the neofetch-style README SVG for aidenc17
Fetches live GitHub stats via the API, then writes profile.svg
Run via GitHub Actions daily (or manually).
"""

import os
import json
import urllib.request
from datetime import date, datetime, timezone

USERNAME = "aidenc17"
TOKEN    = os.environ.get("GH_TOKEN", "")
OUT_FILE = "profile.svg"

ASCII_LINES = [
    "{}{))i?l())}|))|)|)}i)r(iriftttjucXL>rWW&#@@",
    "|(ii(>] r]n))((({jnfYru++)xXYcnnzzz@ v@W#@@@",
    "i(ij]f| rir|fjruxt~><    ,  .InCJUz@ L@&#@@@",
    "fijn)tx nr(|nx[;               :CLJ@ W@&#@@@",
    "ttrn|nn vnjnY,    <v@@@@@@i     .}r@ &@&###@",
    "jjjxtfc vXjQ; , @@@@@@@@@@@@@.     {rQOB##&#",
    "jjnnj|Y xv-<: : @@@@@@@@@@@@@z      -OXLQ@@W",
    "trrjrjc jU<  ,  @@@@@@@@@@cCUt      >@vrvvYJ",
    "ffrttYY jU)  ]  oi   0@         ,    @@@vvcv",
    "fjjjx|Q (;    ,  J,<~@@} i0t)t?      i@@Ot|j",
    "ftftj n;])     z@@@@@@@@J@@@@@c      @@@?  >",
    "ijfj|l<+       Q@@j @ .   +}        @@@@@@@@",
    "ifij|vnz@#}|   }@O:}Bf|     @@ .    @@@@@@@@",
    "tfij|~]r@@@u    }@@@cU@@C+;C@|.   : |@@@@@@@",
    "tffffj)n&@#WzzI  IL#@@#MB0OJ<,I n@@@@@@@@@@@",
]

def gh_get(path):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {TOKEN}" if TOKEN else "",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "aidenc17-readme-bot",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"API error for {path}: {e}")
        return None

def get_stats():
    user = gh_get(f"/users/{USERNAME}") or {}
    repos_data, page = [], 1
    while True:
        chunk = gh_get(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner") or []
        if not chunk: break
        repos_data.extend(chunk)
        if len(chunk) < 100: break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos_data)
    languages = {}
    for repo in repos_data:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    top_langs = [l for l, _ in sorted(languages.items(), key=lambda x: -x[1])[:4]]

    commits_data = gh_get(f"/search/commits?q=author:{USERNAME}&per_page=1")
    total_commits = commits_data.get("total_count", 0) if commits_data else 0

    created_at = user.get("created_at", "")
    if created_at:
        created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").date()
        uptime_days = (date.today() - created).days
        uptime_str = f"{uptime_days:,} days on GitHub"
    else:
        uptime_str = "N/A"

    return {
        "name":         user.get("name") or USERNAME,
        "followers":    user.get("followers", 0),
        "following":    user.get("following", 0),
        "public_repos": user.get("public_repos", len(repos_data)),
        "stars":        total_stars,
        "commits":      total_commits,
        "top_langs":    top_langs,
        "uptime":       uptime_str,
        "updated":      date.today().isoformat(),
    }

def escape_xml(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

def build_svg(stats):
    BG       = "#ffffff"
    BORDER   = "#e0e0e0"
    RED      = "#c8102e"
    DARK_RED = "#8b0000"
    GOLD     = "#b8860b"
    GRAY     = "#888888"
    MONO     = "'Courier New', Courier, monospace"

    W, H = 860, 420
    PAD  = 20

    ASCII_X  = PAD + 14
    ASCII_Y  = PAD + 52
    ASCII_FS = 13
    ASCII_LH = 16
    # Estimate pixel width of ascii block (monospace ~7.8px per char at font-size 13)
    ASCII_PX_W = len(ASCII_LINES[0]) * 7.8

    DIVIDER_X = ASCII_X + ASCII_PX_W + 8
    STATS_X   = int(DIVIDER_X) + 16
    STATS_Y   = PAD + 46

    def dot_line(label, value, y, lcolor=RED, vcolor=GOLD):
        return (
            f'<text x="{STATS_X}" y="{y}" font-family="{MONO}" font-size="12.5">'
            f'<tspan fill="{lcolor}" font-weight="bold">{escape_xml(label)}</tspan>'
            f'<tspan fill="{GRAY}"> .. </tspan>'
            f'<tspan fill="{vcolor}">{escape_xml(str(value))}</tspan>'
            f'</text>'
        )

    def section_header(title, y):
        dashes = "-" * 28
        return (
            f'<text x="{STATS_X}" y="{y}" font-family="{MONO}" font-size="12.5" '
            f'fill="{DARK_RED}" font-weight="bold">- {escape_xml(title)} {dashes}</text>'
        )

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    # Background + border
    svg.append(f'<rect width="{W}" height="{H}" fill="{BG}" rx="10" stroke="{BORDER}" stroke-width="1.5"/>')

    # Top bar
    svg.append(f'<rect x="{PAD}" y="{PAD}" width="{W-PAD*2}" height="30" fill="{RED}" rx="6"/>')
    svg.append(f'<rect x="{PAD}" y="{PAD+24}" width="{W-PAD*2}" height="6" fill="{RED}"/>')

    # Window dots
    for ci, color in enumerate(["#ff5f57", "#ffbd2e", "#28c841"]):
        svg.append(f'<circle cx="{PAD+14+ci*19}" cy="{PAD+15}" r="5" fill="{color}"/>')

    # Title
    svg.append(
        f'<text x="{W//2}" y="{PAD+19}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="13" font-weight="bold" fill="#ffffff">'
        f'aiden@cox \u2014 zsh</text>'
    )

    # Vertical divider
    svg.append(
        f'<line x1="{int(DIVIDER_X)}" y1="{PAD+30}" x2="{int(DIVIDER_X)}" y2="{H-PAD-10}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )

    # ASCII art
    svg.append(f'<text font-family="{MONO}" font-size="{ASCII_FS}" fill="{RED}" xml:space="preserve">')
    for i, row in enumerate(ASCII_LINES):
        y = ASCII_Y + i * ASCII_LH
        svg.append(f'  <tspan x="{ASCII_X}" y="{y}">{escape_xml(row)}</tspan>')
    svg.append('</text>')

    # Caption under ASCII
    cap_y = ASCII_Y + len(ASCII_LINES) * ASCII_LH + 10
    svg.append(
        f'<text x="{ASCII_X + int(ASCII_PX_W/2)}" y="{cap_y}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="10" fill="{GRAY}">OHSAA State Champions \U0001f3c6</text>'
    )

    # Stats
    sy = STATS_Y

    # Header
    hdr = "aiden@cox"
    svg.append(
        f'<text x="{STATS_X}" y="{sy}" font-family="{MONO}" font-size="15" '
        f'font-weight="bold" fill="{RED}">{hdr}</text>'
    )
    sy += 4
    svg.append(f'<line x1="{STATS_X}" y1="{sy}" x2="{STATS_X + len(hdr)*9}" y2="{sy}" stroke="{RED}" stroke-width="1.2"/>')
    sy += 17

    svg.append(dot_line("OS:", "GitHub Profile", sy)); sy += 18
    svg.append(dot_line("Host:", stats["name"], sy)); sy += 18
    svg.append(dot_line("Uptime:", stats["uptime"], sy)); sy += 18
    svg.append(dot_line("Shell:", "git bash", sy)); sy += 18
    svg.append(dot_line("Editor:", "VS Code", sy)); sy += 24

    svg.append(section_header("Languages", sy)); sy += 19
    langs_str = ", ".join(stats["top_langs"]) if stats["top_langs"] else "N/A"
    svg.append(dot_line("Languages.Code:", langs_str, sy)); sy += 18
    svg.append(dot_line("Languages.Markup:", "HTML, CSS, Markdown", sy)); sy += 24

    svg.append(section_header("GitHub Stats", sy)); sy += 19
    svg.append(dot_line("Repos:", str(stats["public_repos"]), sy)); sy += 18
    svg.append(dot_line("Stars:", str(stats["stars"]), sy)); sy += 18
    svg.append(dot_line("Commits:", f"{stats['commits']:,}", sy)); sy += 18
    svg.append(dot_line("Followers:", f"{stats['followers']}  |  Following: {stats['following']}", sy)); sy += 26

    # Color swatches
    colors = [RED, DARK_RED, GOLD, "#1a1a1a", "#888888", "#c8102e", "#e63950", "#ffffff"]
    bx = STATS_X
    for c in colors:
        stroke = "#cccccc" if c == "#ffffff" else "none"
        svg.append(f'<rect x="{bx}" y="{sy}" width="21" height="14" fill="{c}" rx="2" stroke="{stroke}" stroke-width="0.8"/>')
        bx += 24

    # Footer
    svg.append(
        f'<text x="{W//2}" y="{H - PAD + 4}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="9.5" fill="{GRAY}">'
        f'Updated {escape_xml(stats["updated"])} \u00b7 github.com/aidenc17</text>'
    )

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == "__main__":
    print("Fetching GitHub stats...")
    stats = get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    svg = build_svg(stats)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\nWritten to {OUT_FILE}")