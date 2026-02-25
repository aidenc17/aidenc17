"""
generate.py — Builds the neofetch-style README SVG for aidenc17
Fetches live GitHub stats via the API, then writes profile.svg
Run via GitHub Actions daily (or manually).
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Config ─────────────────────────────────────────────────────────────────
USERNAME   = "aidenc17"
TOKEN      = os.environ.get("GH_TOKEN", "")        # set as GitHub Actions secret
OUT_FILE   = "profile.svg"

# ── ASCII Art (Cardinals championship photo) ────────────────────────────────
ASCII_LINES = [
    "                   .,l,                 ",
    "                   .?Ul                 ",
    "_             ;    .;;`           -'.!_ ",
    ">!;+^;;;,^~=cXr i/,->~_'+<<<<<>>\\Xqfn[ ,",
    "zI\\Q[?IcQz/cJjc:)O=.(l'>??/?Ill<^tJ(WWcn",
    "#c L; ipjI u#mj +#[?ri>]b|``  `IIfx'Z#Q|",
    "#b/ihW#Yi-(}IXb_t#hOZ/~<m#L([`)Qt!\"=uXbQ",
    "WYtnm##f;!OU{{?h#hlcUY/tfq#0U;<]kJ\\ ~jU#",
    "n!;+]JXn~>zowd\\h#r'(ZO'?[oWd}!~ict\\'\\Y}^",
    "?x,LZ}c\":,}#ZU\\!ZnldX0W+<?(#>^i[}}+;zWqn",
    "ZOx^]/: '~i|l,. -:=#JfW<; +###uh0W+!~_`i",
    "##Wkp\"   \\vc[l`   \"?)?I=;';^\"..;fkZ'  !_",
    "?u^`(|i; [##pwu|Jx~^=<+>~;   ( =!;~,^+: ",
]

# ── GitHub API helpers ──────────────────────────────────────────────────────
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

    repos_data = []
    page = 1
    while True:
        page_data = gh_get(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner") or []
        if not page_data:
            break
        repos_data.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos_data)
    languages   = {}
    for repo in repos_data:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    top_langs = sorted(languages.items(), key=lambda x: -x[1])[:3]
    top_langs_str = ", ".join(f"{l}" for l, _ in top_langs) if top_langs else "N/A"

    # Commit count via search API (public commits authored by user)
    commits_data = gh_get(f"/search/commits?q=author:{USERNAME}&per_page=1")
    total_commits = commits_data.get("total_count", 0) if commits_data else 0

    return {
        "name":        user.get("name") or USERNAME,
        "followers":   user.get("followers", 0),
        "following":   user.get("following", 0),
        "public_repos":user.get("public_repos", len(repos_data)),
        "stars":       total_stars,
        "commits":     total_commits,
        "top_langs":   top_langs_str,
        "updated":     datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


# ── SVG builder ─────────────────────────────────────────────────────────────
def escape_xml(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_svg(stats):
    # ── Design tokens ──────────────────────────────────────────────────────
    BG          = "#0d0d0d"
    CARD_BG     = "#141414"
    BORDER      = "#8b0000"       # deep cardinal red border
    RED         = "#c8102e"       # cardinal red
    RED_LIGHT   = "#e63950"
    GOLD        = "#f5b800"
    WHITE       = "#f0f0f0"
    MUTED       = "#666666"
    MONO        = "font-family=\"'Courier New', Courier, monospace\""
    SANS        = "font-family=\"'Trebuchet MS', sans-serif\""

    W, H = 820, 380
    PAD = 24
    ASCII_X = PAD + 8
    ASCII_Y = 110
    ASCII_FONT = 11.5
    LINE_H = 14.2

    STATS_X = 390
    STATS_Y = 90

    # ── Start SVG ──────────────────────────────────────────────────────────
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs>',
        # scanline texture
        '<pattern id="scan" x="0" y="0" width="1" height="3" patternUnits="userSpaceOnUse">',
        '  <line x1="0" y1="1" x2="1000" y2="1" stroke="#ffffff" stroke-width="0.3" stroke-opacity="0.03"/>',
        '</pattern>',
        # red glow filter
        '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
        '  <feGaussianBlur stdDeviation="3" result="blur"/>',
        '  <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>',
        '</filter>',
        # subtle drop shadow
        '<filter id="shadow">',
        '  <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#c8102e" flood-opacity="0.3"/>',
        '</filter>',
        '</defs>',

        # ── Background ──
        f'<rect width="{W}" height="{H}" fill="{BG}" rx="12"/>',
        f'<rect width="{W}" height="{H}" fill="url(#scan)" rx="12"/>',

        # ── Card ──
        f'<rect x="{PAD}" y="{PAD}" width="{W-PAD*2}" height="{H-PAD*2}" '
        f'fill="{CARD_BG}" rx="8" stroke="{BORDER}" stroke-width="1.5"/>',

        # ── Top bar / title strip ──
        f'<rect x="{PAD}" y="{PAD}" width="{W-PAD*2}" height="40" '
        f'fill="{RED}" rx="8"/>',
        f'<rect x="{PAD}" y="{PAD+32}" width="{W-PAD*2}" height="8" fill="{RED}"/>',

        # Window dots
        f'<circle cx="{PAD+18}" cy="{PAD+20}" r="6" fill="#ff5f57"/>',
        f'<circle cx="{PAD+36}" cy="{PAD+20}" r="6" fill="#ffbd2e"/>',
        f'<circle cx="{PAD+54}" cy="{PAD+20}" r="6" fill="#28c841"/>',

        # Title
        f'<text x="{W//2}" y="{PAD+24}" text-anchor="middle" '
        f'{MONO} font-size="14" font-weight="bold" fill="{WHITE}" filter="url(#glow)">'
        f'aiden@cox — zsh</text>',

        # ── Divider between ASCII and stats ──
        f'<line x1="360" y1="{PAD+45}" x2="360" y2="{H-PAD-10}" '
        f'stroke="{BORDER}" stroke-width="1" stroke-dasharray="4,3"/>',
    ]

    # ── ASCII art block ──────────────────────────────────────────────────────
    lines.append(
        f'<text {MONO} font-size="{ASCII_FONT}" fill="{RED_LIGHT}" '
        f'xml:space="preserve" opacity="0.92">'
    )
    for i, row in enumerate(ASCII_LINES):
        y = ASCII_Y + i * LINE_H
        safe = escape_xml(row)
        lines.append(f'  <tspan x="{ASCII_X}" dy="0" y="{y}">{safe}</tspan>')
    lines.append('</text>')

    # ── Caption under ASCII ──────────────────────────────────────────────────
    lines.append(
        f'<text x="{ASCII_X + 130}" y="{ASCII_Y + len(ASCII_LINES)*LINE_H + 10}" '
        f'text-anchor="middle" {MONO} font-size="9" fill="{MUTED}">'
        f'OHSAA State Champions 🏆</text>'
    )

    # ── Right side: neofetch info ────────────────────────────────────────────
    def info_line(label, value, y, label_color=GOLD, value_color=WHITE):
        return (
            f'<text x="{STATS_X}" y="{y}" {MONO} font-size="13">'
            f'<tspan fill="{label_color}" font-weight="bold">{escape_xml(label)}</tspan>'
            f'<tspan fill="{value_color}"> {escape_xml(value)}</tspan>'
            f'</text>'
        )

    sy = STATS_Y

    # User header  aiden@cox
    lines.append(
        f'<text x="{STATS_X}" y="{sy}" {MONO} font-size="16" font-weight="bold" '
        f'fill="{RED_LIGHT}" filter="url(#glow)">aiden@cox</text>'
    )
    sy += 6
    # underline
    lines.append(
        f'<line x1="{STATS_X}" y1="{sy}" x2="{STATS_X+180}" y2="{sy}" '
        f'stroke="{RED}" stroke-width="1"/>'
    )
    sy += 18

    rows = [
        ("OS:",       "GitHub Profile"),
        ("Host:",     stats["name"]),
        ("Uptime:",   stats["updated"]),
        ("Repos:",    str(stats["public_repos"])),
        ("Stars:",    str(stats["stars"])),
        ("Commits:",  f"{stats['commits']:,}"),
        ("Followers:",str(stats["followers"])),
        ("Following:",str(stats["following"])),
        ("Languages:",stats["top_langs"]),
        ("Shell:",    "git bash"),
        ("Editor:",   "VS Code"),
    ]
    for label, value in rows:
        lines.append(info_line(label, value, sy))
        sy += 20

    # ── Color blocks ────────────────────────────────────────────────────────
    colors = ["#c8102e","#f5b800","#ffffff","#0d0d0d","#666666","#e63950","#8b0000","#f0f0f0"]
    sy += 8
    bx = STATS_X
    for c in colors:
        lines.append(f'<rect x="{bx}" y="{sy}" width="18" height="14" fill="{c}" rx="2"/>')
        bx += 21

    # ── Footer ──────────────────────────────────────────────────────────────
    lines.append(
        f'<text x="{W//2}" y="{H-PAD-5}" text-anchor="middle" '
        f'{MONO} font-size="9" fill="{MUTED}">Updated {escape_xml(stats["updated"])} · github.com/aidenc17</text>'
    )

    lines.append('</svg>')
    return '\n'.join(lines)


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching GitHub stats...")
    stats = get_stats()
    print(f"  Repos:    {stats['public_repos']}")
    print(f"  Stars:    {stats['stars']}")
    print(f"  Commits:  {stats['commits']}")
    print(f"  Followers:{stats['followers']}")
    print(f"  Langs:    {stats['top_langs']}")

    svg = build_svg(stats)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"\n✅  Written to {OUT_FILE}")