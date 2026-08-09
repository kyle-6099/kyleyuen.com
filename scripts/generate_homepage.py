#!/usr/bin/env python3
"""
Generate the homepage dynamic sections statically.

Rules:
- Featured work: up to 3 cards from /work/index.html.
  - Pinned cards first.
  - Then priority tags: systems-integration, workflow-automation, api-integration, unified-communications, benefits-admin.
- Latest ideas: 2 random cards from the 3 highest issue numbers.
  - Render as thumbnail-only cards with muted->highlighted hover.

After adding a new Work or Ideas post, run:
    python3 scripts/generate_homepage.py
"""

from pathlib import Path
import random
import re
from html import escape
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent.resolve()
WORK_INDEX = ROOT / "work" / "index.html"
IDEAS_INDEX = ROOT / "ideas" / "index.html"
HOME = ROOT / "index.html"

PRIORITY_TAGS = [
    "systems-integration",
    "workflow-automation",
    "api-integration",
    "unified-communications",
    "benefits-admin",
]


def parse_work_cards(html: str):
    cards = []
    for m in re.finditer(r'<article class="tile[^"]*"[^>]*data-tags="([^"]*)"[^>]*data-format="([^"]*)"[^>]*>', html):
        start = m.start()
        end = html.find("</article>", start)
        if end == -1:
            continue
        card_html = html[start:end + len("</article>")]

        link_m = re.search(r'<a href="(/work/[^"]+)"', card_html)
        if not link_m:
            continue
        href = link_m.group(1)

        title_m = re.search(r'<h2[^>]*>(.*?)</h2>', card_html, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""

        summary_m = re.search(r'<p[^>]*>(.*?)</p>', card_html, re.DOTALL)
        summary = re.sub(r"<[^>]+>", "", summary_m.group(1)).strip() if summary_m else ""

        format_m = re.search(r'<span class="mono text-xs text-slate-600 bg-slate-100[^"]*">([^<]+)</span>', card_html)
        format_label = format_m.group(1).strip() if format_m else "Work"

        tags = m.group(1).strip().split()
        cards.append({
            "href": href,
            "title": title,
            "summary": summary,
            "format_label": format_label,
            "tags": tags,
        })
    return cards


def score_work_card(card):
    score = 0
    if "pinned" in card["format_label"].lower():
        score += 1000
    for tag in card["tags"]:
        if tag in PRIORITY_TAGS:
            score += (len(PRIORITY_TAGS) - PRIORITY_TAGS.index(tag)) * 10
    return score


def render_work_cards(cards):
    if not cards:
        return "<!-- no work cards -->"
    html_lines = []
    for card in cards[:3]:
        tags_html = "".join(
            f'<span class="mono text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded border border-slate-200">{escape(tag)}</span>'
            for tag in card["tags"][:3]
        )
        html_lines.append(
            f'<a href="{escape(card["href"])}" class="glass rounded-2xl p-6 md:p-8 card-hover block group bg-white">\n'
            f'  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">\n'
            f'    <div class="flex items-center gap-3">\n'
            f'      <span class="mono text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{escape(card["format_label"])}</span>\n'
            f'      <span class="mono text-xs text-slate-500">Project</span>\n'
            f'    </div>\n'
            f'    <div class="flex flex-wrap gap-2">{tags_html}</div>\n'
            f'  </div>\n'
            f'  <h3 class="text-xl font-semibold text-slate-900 mb-2 group-hover:text-brand-600 transition-colors">{escape(card["title"])}</h3>\n'
            f'  <p class="text-slate-600 text-sm leading-relaxed max-w-3xl">{escape(card["summary"])}</p>\n'
            f'</a>'
        )
    return "\n".join(html_lines)


def parse_idea_tiles(html: str):
    tiles = []
    for m in re.finditer(r'<article class="tile idea-tile[^"]*"[^>]*>', html):
        start = m.start()
        end = html.find("</article>", start)
        if end == -1:
            continue
        tile_html = html[start:end + len("</article>")]

        issue_m = re.search(r'<span class="mono text-xs text-brand-600[^"]*">([^<]+)</span>', tile_html)
        issue_text = issue_m.group(1).strip() if issue_m else ""
        issue_num = int(re.sub(r"\D", "", issue_text) or 0)

        link_m = re.search(r'<a href="(/ideas/[^"]+)"', tile_html)
        if not link_m:
            continue
        href = link_m.group(1)

        muted_m = re.search(r'<img src="(/ideas/assets/[^"]+-muted\.png)"', tile_html)
        highlight_m = re.search(r'<img src="(/ideas/assets/[^"]+)"[^>]*class="[^"]*opacity-0[^"]*"', tile_html)

        muted_src = muted_m.group(1) if muted_m else ""
        highlight_src = highlight_m.group(1) if highlight_m else ""

        title_m = re.search(r'data-title="([^"]+)"', m.group(0))
        title = title_m.group(1) if title_m else ""

        tiles.append({
            "issue_num": issue_num,
            "href": href,
            "muted_src": muted_src,
            "highlight_src": highlight_src,
            "title": title,
        })
    return tiles


def render_idea_tiles(tiles):
    if len(tiles) < 2:
        return "<!-- not enough idea tiles -->"
    top3 = sorted(tiles, key=lambda x: x["issue_num"], reverse=True)[:3]
    selected = random.sample(top3, 2) if len(top3) >= 2 else top3

    tiles_html = "\n".join(
        f'<a href="{escape(tile["href"])}" class="home-idea-tile block">\n'
        f'  <div class="aspect-square overflow-hidden bg-slate-100 rounded-2xl">\n'
        f'    <div class="relative aspect-square overflow-hidden">\n'
        f'      <img src="{escape(tile["muted_src"])}" class="absolute inset-0 w-full h-full object-cover" alt="{escape(tile["title"])}">\n'
        f'      <img src="{escape(tile["highlight_src"])}" class="absolute inset-0 w-full h-full object-cover opacity-0 transition-opacity duration-300 ease-out" alt="{escape(tile["title"])}">\n'
        f'    </div>\n'
        f'  </div>\n'
        f'</a>'
        for tile in selected
    )
    return f'<div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-2xl mx-auto px-8">\n{tiles_html}\n</div>'


def insert_between(haystack: str, start_marker: str, end_marker: str, content: str) -> str:
    """Replace content between two markers."""
    start_idx = haystack.find(start_marker)
    end_idx = haystack.find(end_marker)
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        raise ValueError(f"Markers not found: {start_marker!r} or {end_marker!r}")
    return haystack[:start_idx + len(start_marker)] + "\n" + content + "\n" + haystack[end_idx:]



def generate_sitemap():
    """Regenerate sitemap.xml based on live pages."""
    page_set = set()
    for p in [
        ROOT / "index.html",
        ROOT / "about/index.html",
        ROOT / "work/index.html",
        ROOT / "ideas/index.html",
        ROOT / "contact/index.html",
    ] + list((ROOT / "work").glob("*/index.html")) + list((ROOT / "ideas").glob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.name == "index.html":
            parts = rel.parts[:-1]
            url = "/" + "/".join(parts) + "/" if parts else "/"
        else:
            url = "/" + "/".join(rel.parts)
        page_set.add(url)

    main_urls = {"/about/", "/work/", "/ideas/", "/contact/"}
    urls = []
    for url in sorted(page_set):
        if url == "/":
            priority = "1.0"
        elif url in main_urls:
            priority = "0.9"
        else:
            priority = "0.8"
        urls.append((url, priority))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>https://kyleyuen.com{url}</loc>")
        lines.append(f"    <lastmod>{now}</lastmod>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Sitemap updated: {len(urls)} URLs")


def main():
    work_html = WORK_INDEX.read_text(encoding="utf-8")
    ideas_html = IDEAS_INDEX.read_text(encoding="utf-8")
    home_html = HOME.read_text(encoding="utf-8")

    work_cards = parse_work_cards(work_html)
    work_cards.sort(key=score_work_card, reverse=True)

    idea_tiles = parse_idea_tiles(ideas_html)

    work_rendered = render_work_cards(work_cards)
    idea_rendered = render_idea_tiles(idea_tiles)

    home_html = insert_between(
        home_html,
        '<div id="featured-work" class="space-y-4">',
        '  </div>\n  \n  <div id="featured-work-fallback"',
        "    " + work_rendered.replace("\n", "\n    ")
    )

    home_html = insert_between(
        home_html,
        '<div id="latest-idea">',
        '    </div>\n    \n    <div id="latest-idea-fallback"',
        "      " + idea_rendered.replace("\n", "\n      ")
    )

    HOME.write_text(home_html, encoding="utf-8")
    print("Homepage generated.")
    print(f"  Work cards: {len(work_cards[:3])}")
    print(f"  Idea tiles parsed: {len(idea_tiles)}")


if __name__ == "__main__":
    main()
