#!/usr/bin/env python3
"""
Generate Open Graph images for Work and Ideas posts.
Usage: python3 scripts/generate_og_images.py
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import re

ROOT = Path(__file__).parent.parent.resolve()
WORK_DIR = ROOT / "work"
IDEAS_DIR = ROOT / "ideas"
OG_DIR = ROOT / "assets" / "og"

COLORS = {
    "bg": (15, 23, 42),       # #0f172a
    "accent": (249, 115, 22),  # #f97316
    "white": (255, 255, 255),
    "muted": (148, 163, 184),  # #94a3b8
}

FONTS = {
    "inter": "/root/.local/share/fonts/Inter-Black.ttf",
    "inter_medium": "/root/.local/share/fonts/Inter-Medium.ttf",
    "jb": "/root/.local/share/fonts/JetBrainsMono-SemiBold.ttf",
}

def get_font(name, size):
    try:
        return ImageFont.truetype(FONTS[name], size)
    except Exception:
        return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + " " + word if current else word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def make_og_image(title, subtitle, output_path):
    OG_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1200, 630), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # Accent bar at bottom
    draw.rectangle([(0, 570), (1200, 630)], fill=COLORS["accent"])

    # Small logo-ish mark top-left (white K° style)
    mark_font = get_font("jb", 48)
    draw.text((80, 80), "K°", fill=COLORS["white"], font=mark_font, anchor="lt")

    # Subtitle
    sub_font = get_font("inter_medium", 24)
    draw.text((80, 170), subtitle.upper(), fill=COLORS["muted"], font=sub_font, anchor="lt")

    # Title
    title_font = get_font("inter", 72)
    lines = wrap_text(title, title_font, 1040, draw)
    y = 230
    line_height = 90
    for line in lines[:3]:
        draw.text((80, y), line, fill=COLORS["white"], font=title_font, anchor="lt")
        y += line_height

    # Domain
    domain_font = get_font("jb", 20)
    draw.text((80, 600), "kyleyuen.com", fill=COLORS["white"], font=domain_font, anchor="lb")

    img.save(output_path)
    print(f"Generated: {output_path}")

def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

def generate_all():
    # Work posts
    for p in WORK_DIR.glob("*/index.html"):
        if p.name == "index.html" and p.parent.name == "work":
            continue
        html = p.read_text(encoding="utf-8")
        title_m = re.search(r'\u003ctitle\u003e(.*?) — Kyle Yuen\u003c/title\u003e', html)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        slug = p.parent.name
        make_og_image(title, "Work", OG_DIR / f"{slug}.png")

    # Ideas posts
    for p in IDEAS_DIR.glob("*.html"):
        if p.name == "index.html":
            continue
        html = p.read_text(encoding="utf-8")
        title_m = re.search(r'\u003cmeta property="og:title" content="(.*?) — Kyle Yuen"\u003e', html)
        if not title_m:
            title_m = re.search(r'\u003ctitle\u003e(.*?) — Kyle Yuen\u003c/title\u003e', html)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        slug = p.stem
        make_og_image(title, "Ideas", OG_DIR / f"{slug}.png")

if __name__ == "__main__":
    generate_all()
