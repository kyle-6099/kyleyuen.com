#!/usr/bin/env python3
"""
Generate the homepage dynamic sections statically.

Rules:
- Featured work: up to 3 cards from /work/index.html.
  - Pinned cards first.
  - Then priority tags: systems-integration, workflow-automation, api-integration, unified-communications, benefits-admin.
- Latest ideas: 2 random cards from the 3 highest issue numbers.
  - Render as thumbnail-only cards with muted->highlighted hover.
"""

from pathlib import Path
import random
import re
from html import escape

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
        card_html = html[start:end]

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
        return '<!-- no work cards -->'
    html = []
    for card in cards[:3]:
        tags_html = "".join(
            f'<span class="mono text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded border border-slate-200">{escape(tag)}</span>'
            for tag in card["tags"][:3]
        )
        html.append(f'''<a href="{escape(card["href"])}" class="glass rounded-2xl p-6 md:p-8 card-hover block group bg-white">
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
    <div class="flex items-center gap-3">
      <span class="mono text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{escape(card["format_label"])}</span>
      <span class="mono text-xs text-slate-500">Project</span>
    </div>
    <div class="flex flex-wrap gap-2">{tags_html}</div>
  </div>
  <h3 class="text-xl font-semibold text-slate-900 mb-2 group-hover:text-brand-600 transition-colors">{escape(card["title"])}</h3>
  <p class="text-slate-600 text-sm leading-relaxed max-w-3xl">{escape(card["summary"])}</p>
</a>''')
    return "\n".join(html)


def parse_idea_tiles(html: str):
    tiles = []
    for m in re.finditer(r'<article class="tile idea-tile[^"]*"[^>]*>', html):
        start = m.start()
        end = html.find("</article>", start)
        tile_html = html[start:end]

        issue_m = re.search(r'<span class="mono text-xs text-brand-600[^"]*">([^<]+)</span>', tile_html)
        issue_text = issue_m.group(1).strip() if issue_m else ""
        issue_num = int(re.sub(r"\D", "", issue_text) or 0)

        link_m = re.search(r'<a href="(/ideas/[^"]+)"', tile_html)
        if not link_m:
            continue
        href = link_m.group(1)

        muted_m = re.search(r'<img src="(/ideas/assets/[^"]+-muted\.png)"', tile_html)
        highlight_m = re.search(r'<img src="(/ideas/assets/[^"]+(?<!-muted)\.png)"', tile_html)
        muted_src = muted_m.group(1) if muted_m else ""
        highlight_src = highlight_m.group(1) if highlight_m else ""

        title = m.group(0).split('data-title="')[1].split('"')[0] if 'data-title="' in m.group(0) else ""

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

    tiles_html = "".join(
        f'''<a href="{escape(tile["href"])}" class="home-idea-tile block max-w-xs mx-auto">
  <div class="aspect-square overflow-hidden bg-slate-100 rounded-2xl">
    <div class="relative aspect-square overflow-hidden">
      <img src="{escape(tile["muted_src"])}" class="absolute inset-0 w-full h-full object-cover" alt="{escape(tile["title"])}">
      <img src="{escape(tile["highlight_src"])}" class="absolute inset-0 w-full h-full object-cover opacity-0 transition-opacity duration-300 ease-out" alt="{escape(tile["title"])}">
    </div>
  </div>
</a>'''
        for tile in selected
    )
    return f'<div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">{tiles_html}</div>'


def main():
    work_html = WORK_INDEX.read_text(encoding="utf-8")
    ideas_html = IDEAS_INDEX.read_text(encoding="utf-8")
    home_html = HOME.read_text(encoding="utf-8")

    work_cards = parse_work_cards(work_html)
    work_cards.sort(key=score_work_card, reverse=True)

    idea_tiles = parse_idea_tiles(ideas_html)

    work_rendered = render_work_cards(work_cards)
    idea_rendered = render_idea_tiles(idea_tiles)

    # Replace the dynamic containers with static content
    home_html = re.sub(
        r'<div id="featured-work" class="space-y-4">.*?</div>\s*<div id="featured-work-fallback"[^>]*>.*?</div>\s*</div>',
        f'<div id="featured-work" class="space-y-4">\n{work_rendered}\n</div>\n  <div id="featured-work-fallback" class="space-y-4 hidden">\n    <!-- fallback removed -->\n  </div>\n</div>',
        home_html,
        flags=re.DOTALL,
    )

    home_html = re.sub(
        r'<div id="latest-idea">.*?</div>\s*<div id="latest-idea-fallback"[^>]*>.*?</div>\s*</div>',
        f'<div id="latest-idea">\n{idea_rendered}\n</div>\n    <div id="latest-idea-fallback" class="hidden">\n      <!-- fallback removed -->\n    </div>\n  </div>',
        home_html,
        flags=re.DOTALL,
    )

    # Remove the dynamic JS section entirely
    home_html = re.sub(
        r'<script>\n// Homepage dynamic feed rules:.*?</script>\n',
        "",
        home_html,
        flags=re.DOTALL,
    )

    HOME.write_text(home_html, encoding="utf-8")
    print("Homepage generated.")
    print(f"  Work cards: {len(work_cards[:3])}")
    print(f"  Idea tiles parsed: {len(idea_tiles)}")


if __name__ == "__main__":
    main()
