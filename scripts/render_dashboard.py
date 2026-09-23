"""Build light and dark profile cards from public GitHub data."""

import argparse
from collections import Counter
from datetime import datetime
import json
import math
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


THEMES = {
    "dark": {
        "background": "#0d1117",
        "card": "#161b22",
        "border": "#30363d",
        "text": "#f0f6fc",
        "muted": "#9da7b3",
        "accent": "#57d4c8",
        "track": "#2d333b",
    },
    "light": {
        "background": "#f6f8fa",
        "card": "#ffffff",
        "border": "#d0d7de",
        "text": "#1f2933",
        "muted": "#576574",
        "accent": "#087e83",
        "track": "#e8edf1",
    },
}
LANGUAGE_COLORS = ["#f3ce59", "#438dd3", "#f06a42", "#8e62c8", "#48a888", "#7d8996"]
FONT = "Arial, Segoe UI, sans-serif"


def github_json(path, token):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "n335h-max-profile-dashboard",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com{path}", headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def fetch_profile(username, token):
    encoded_user = quote(username, safe="")
    user = github_json(f"/users/{encoded_user}", token)
    repos = []
    page = 1
    while True:
        batch = github_json(
            f"/users/{encoded_user}/repos?per_page=100&page={page}", token
        )
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    languages = {}
    for repo in repos:
        if repo["fork"] or repo["name"] == username:
            continue
        encoded_repo = quote(repo["name"], safe="")
        languages[repo["name"]] = github_json(
            f"/repos/{encoded_user}/{encoded_repo}/languages", token
        )
    return user, repos, languages


def build_snapshot(user, repos, repo_languages, display_name=None):
    language_bytes = Counter()
    for repo in repos:
        if repo["fork"] or repo["name"] == user["login"]:
            continue
        language_bytes.update(repo_languages.get(repo["name"], {}))
    joined = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    return {
        "username": user["login"],
        "display_name": display_name or user.get("name") or user["login"],
        "public_repos": user["public_repos"],
        "stars": sum(repo["stargazers_count"] for repo in repos if not repo["fork"]),
        "followers": user["followers"],
        "joined": joined.strftime("%b %Y").upper(),
        "languages": language_bytes.most_common(),
    }


def svg_open(width, height, description):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{escape(description)}">'
    )


def render_hero(snapshot, theme):
    color = THEMES[theme]
    name = escape(snapshot["display_name"])
    username = escape(snapshot["username"])
    return "".join(
        [
            svg_open(1000, 265, f"Introduction to {snapshot['display_name']}"),
            f'<rect width="1000" height="265" rx="22" fill="{color["background"]}"/>',
            f'<rect x="8" y="8" width="984" height="249" rx="18" fill="{color["card"]}" '
            f'stroke="{color["border"]}" stroke-width="2"/>',
            f'<rect x="34" y="37" width="7" height="191" rx="3.5" fill="{color["accent"]}"/>',
            f'<text x="70" y="73" fill="{color["accent"]}" font-family="{FONT}" '
            f'font-size="23" font-weight="700" letter-spacing="3">WELCOME TO MY GITHUB HUB</text>',
            f'<text x="69" y="143" fill="{color["text"]}" font-family="{FONT}" '
            f'font-size="54" font-weight="700">{name}</text>',
            f'<text x="70" y="189" fill="{color["muted"]}" font-family="{FONT}" '
            'font-size="26">Student developer  ·  web apps  ·  AI tools</text>',
            f'<text x="70" y="228" fill="{color["muted"]}" font-family="{FONT}" '
            f'font-size="21">@{username}</text>',
            f'<g fill="none" stroke="{color["accent"]}" stroke-width="5" '
            'stroke-linecap="round" opacity=".72">',
            '<path d="M770 65h180v135H770z"/>',
            '<path d="M805 65v44h55v44h90M770 153h45v47M860 109h-40"/>',
            '</g>',
            f'<g fill="{color["accent"]}">',
            '<circle cx="790" cy="132" r="6"/><circle cx="850" cy="178" r="6"/>',
            '<circle cx="900" cy="95" r="6"/><circle cx="925" cy="178" r="6"/>',
            '</g>',
            '<circle cx="815" cy="169" r="26" fill="#f3ce59"/>',
            f'<path d="M815 169l24-16v32z" fill="{color["card"]}"/>',
            '</svg>',
        ]
    )


def render_stats(snapshot, theme):
    color = THEMES[theme]
    items = [
        (str(snapshot["public_repos"]), "PUBLIC REPOSITORIES"),
        (str(snapshot["stars"]), "STARS RECEIVED"),
        (str(snapshot["followers"]), "FOLLOWERS"),
        (snapshot["joined"], "ON GITHUB SINCE"),
    ]
    parts = [
        svg_open(1000, 475, f"GitHub statistics for {snapshot['username']}"),
        f'<rect width="1000" height="475" rx="22" fill="{color["background"]}"/>',
        f'<text x="30" y="50" fill="{color["muted"]}" font-family="{FONT}" '
        'font-size="27" font-weight="700" letter-spacing="2">PROFILE AT A GLANCE</text>',
    ]
    for index, (value, label) in enumerate(items):
        x = 20 + (index % 2) * 490
        y = 75 + (index // 2) * 195
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="470" height="180" rx="20" '
                f'fill="{color["card"]}" stroke="{color["border"]}" stroke-width="2"/>',
                f'<rect x="{x + 24}" y="{y + 26}" width="6" height="54" rx="3" '
                f'fill="{color["accent"]}"/>',
                f'<text x="{x + 49}" y="{y + 92}" fill="{color["text"]}" '
                f'font-family="{FONT}" font-size="70" font-weight="700">{escape(value)}</text>',
                f'<text x="{x + 28}" y="{y + 146}" fill="{color["muted"]}" '
                f'font-family="{FONT}" font-size="26" font-weight="700" '
                f'letter-spacing="1">{escape(label)}</text>',
                f'<text x="{x + 425}" y="{y + 47}" fill="{color["accent"]}" '
                f'font-family="{FONT}" font-size="23" text-anchor="end">0{index + 1}</text>',
            ]
        )
    parts.append('</svg>')
    return "".join(parts)


def render_languages(snapshot, theme):
    color = THEMES[theme]
    languages = snapshot["languages"]
    total = sum(value for _, value in languages)
    top = languages[:5]
    remainder = total - sum(value for _, value in top)
    entries = top + ([("Other", remainder)] if remainder else [])
    cx, cy, radius = 248, 246, 126
    circumference = 2 * math.pi * radius
    parts = [
        svg_open(1000, 465, f"Language breakdown for {snapshot['username']}"),
        f'<rect width="1000" height="465" rx="22" fill="{color["background"]}"/>',
        f'<rect x="8" y="8" width="984" height="449" rx="18" fill="{color["card"]}" '
        f'stroke="{color["border"]}" stroke-width="2"/>',
        f'<text x="38" y="57" fill="{color["text"]}" font-family="{FONT}" '
        'font-size="30" font-weight="700">LANGUAGES ACROSS MY PUBLIC REPOS</text>',
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" '
        f'stroke="{color["track"]}" stroke-width="48"/>',
    ]
    if total:
        offset = 0.0
        for index, (_, value) in enumerate(entries):
            length = circumference * value / total
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" '
                f'stroke="{LANGUAGE_COLORS[index]}" stroke-width="48" '
                f'stroke-dasharray="{length:.3f} {circumference - length:.3f}" '
                f'stroke-dashoffset="{-offset:.3f}" transform="rotate(-90 {cx} {cy})"/>'
            )
            offset += length
        parts.extend(
            [
                f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" '
                f'fill="{color["text"]}" font-family="{FONT}" font-size="37" '
                'font-weight="700">TOP 5</text>',
                f'<text x="{cx}" y="{cy + 31}" text-anchor="middle" '
                f'fill="{color["muted"]}" font-family="{FONT}" '
                'font-size="22">BY CODE SIZE</text>',
            ]
        )
        for index, (name, value) in enumerate(entries):
            y = 133 + index * 50
            parts.extend(
                [
                    f'<circle cx="510" cy="{y - 10}" r="11" fill="{LANGUAGE_COLORS[index]}"/>',
                    f'<text x="540" y="{y}" fill="{color["text"]}" '
                    f'font-family="{FONT}" font-size="27">{escape(name[:22])}</text>',
                    f'<text x="948" y="{y}" text-anchor="end" fill="{color["muted"]}" '
                    f'font-family="{FONT}" font-size="27">{value / total:.0%}</text>',
                ]
            )
    else:
        parts.append(
            f'<text x="500" y="250" text-anchor="middle" fill="{color["muted"]}" '
            f'font-family="{FONT}" font-size="29">No language data yet</text>'
        )
    parts.extend(
        [
            f'<text x="38" y="430" fill="{color["muted"]}" font-family="{FONT}" '
            f'font-size="21">Language bytes in non-fork public repositories  ·  @{escape(snapshot["username"])}</text>',
            '</svg>',
        ]
    )
    return "".join(parts)


def render_languages_mobile(snapshot, theme):
    color = THEMES[theme]
    languages = snapshot["languages"]
    total = sum(value for _, value in languages)
    top = languages[:5]
    remainder = total - sum(value for _, value in top)
    entries = top + ([("Other", remainder)] if remainder else [])
    parts = [
        svg_open(500, 515, f"Mobile language breakdown for {snapshot['username']}"),
        f'<rect width="500" height="515" rx="20" fill="{color["background"]}"/>',
        f'<rect x="6" y="6" width="488" height="503" rx="17" fill="{color["card"]}" '
        f'stroke="{color["border"]}" stroke-width="2"/>',
        f'<text x="25" y="49" fill="{color["text"]}" font-family="{FONT}" '
        'font-size="26" font-weight="700">LANGUAGES IN PUBLIC REPOS</text>',
    ]
    if total:
        for index, (name, value) in enumerate(entries):
            y = 97 + index * 62
            width = 450 * value / total
            parts.extend(
                [
                    f'<circle cx="35" cy="{y - 9}" r="9" fill="{LANGUAGE_COLORS[index]}"/>',
                    f'<text x="58" y="{y}" fill="{color["text"]}" '
                    f'font-family="{FONT}" font-size="26">{escape(name[:20])}</text>',
                    f'<text x="470" y="{y}" text-anchor="end" fill="{color["muted"]}" '
                    f'font-family="{FONT}" font-size="26">{value / total:.0%}</text>',
                    f'<rect x="25" y="{y + 14}" width="450" height="9" rx="4.5" '
                    f'fill="{color["track"]}"/>',
                    f'<rect x="25" y="{y + 14}" width="{width:.2f}" height="9" '
                    f'rx="4.5" fill="{LANGUAGE_COLORS[index]}"/>',
                ]
            )
    else:
        parts.append(
            f'<text x="250" y="250" text-anchor="middle" fill="{color["muted"]}" '
            f'font-family="{FONT}" font-size="26">No language data yet</text>'
        )
    parts.extend(
        [
            f'<text x="25" y="482" fill="{color["muted"]}" font-family="{FONT}" '
            f'font-size="19">Code size in non-fork repos  ·  @{escape(snapshot["username"])}</text>',
            '</svg>',
        ]
    )
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", required=True)
    parser.add_argument("--display-name", default="Navaneesh Balakrishnan")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    user, repos, languages = fetch_profile(args.user, os.environ.get("GITHUB_TOKEN"))
    snapshot = build_snapshot(user, repos, languages, args.display_name)
    args.output.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        for label, renderer in (
            ("hero", render_hero),
            ("stats", render_stats),
            ("languages", render_languages),
            ("languages-mobile", render_languages_mobile),
        ):
            (args.output / f"{label}-{theme}.svg").write_text(
                renderer(snapshot, theme), encoding="utf-8"
            )
    print(f"Rendered profile cards for @{snapshot['username']} in {args.output}")


if __name__ == "__main__":
    main()
