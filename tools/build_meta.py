"""Regenerate everything that's derived from blog/posts.json:

  og/*.png          link-preview images (home, blog, one per post)
  <head> meta       canonical, Open Graph + Twitter tags, RSS link, favicon
  sitemap.xml       every page, for search engines
  feed.xml          RSS feed of the blog
  robots.txt        points crawlers at the sitemap

Run it after adding or editing a post:   python tools/build_meta.py
Needs Pillow (pip install pillow). Safe to re-run.
"""
import html
import io
import json
import os
import re
import textwrap
from datetime import datetime, timezone
from email.utils import format_datetime

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://avinashk.in"
NAME = "Avinash Kamadri"
FONTS = os.path.join(ROOT, "tools", "fonts")

BG, FG, DIM, LINE, ACCENT = "#141413", "#e9e6dc", "#8f8b80", "#2a2a27", "#d9775a"
INK = {"#": ACCENT, "p": FG, "w": "#a5523a", "h": "#f1c3a8", "e": BG}   # fire (f/F) stays hidden


def read(path):
    return io.open(os.path.join(ROOT, path), encoding="utf-8").read()


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    io.open(full, "w", encoding="utf-8", newline="\n").write(text)


def sprites():
    """Pull the character maps out of assets/pixel.js so icons match the site."""
    js = read("assets/pixel.js")
    out = {}
    for m in re.finditer(r"(\w+): \{\s*map: \[([\s\S]*?)\]", js):
        out[m.group(1)] = re.findall(r'"([^"]*)"', m.group(2))
    return out


SPRITES = sprites()


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONTS, f"JetBrainsMono-{weight}.ttf"), size)


def draw_sprite(d, name, x, y, px, cols=None):
    rows = SPRITES[name]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row[:cols] if cols else row):
            if ch in INK:
                d.rectangle([x + i * px, y + j * px, x + (i + 1) * px - 1, y + (j + 1) * px - 1], fill=INK[ch])


def og_image(out, title, sub, tag=None, icon="dragon", footer="avinashk.in"):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([24, 24, W - 25, H - 25], outline=LINE, width=2)
    # window dots + title bar, like the site's terminal panes
    for k, c in enumerate([ACCENT, LINE, LINE]):
        d.ellipse([52 + k * 30, 50, 68 + k * 30, 66], fill=c)
    d.line([24, 92, W - 25, 92], fill=LINE, width=2)
    d.text((W / 2, 58), "avinash@avinashk.in: ~", font=font("Regular", 22), fill=DIM, anchor="mm")

    # icon
    px = 12 if icon == "dragon" else 10
    draw_sprite(d, icon, 72, 128, px, cols=14 if icon == "dragon" else None)

    y = 300 if icon == "dragon" else 128 + len(SPRITES[icon]) * px + 30
    if tag:
        f = font("Regular", 24)
        w = d.textlength(tag, font=f)
        d.rectangle([72, y - 6, 72 + w + 28, y + 34], outline=LINE, width=2)
        d.text((86, y), tag, font=f, fill=FG)
        y += 64
    # title: wrap to fit, shrinking if it gets too long
    for size in (60, 54, 48, 42):
        f = font("Bold", size)
        per_line = int((W - 150) / (size * 0.6))
        lines = textwrap.wrap(title, per_line)
        if len(lines) <= 2:
            break
    for ln in lines[:3]:
        d.text((72, y), ln, font=f, fill=FG)
        y += int(size * 1.2)
    if sub:
        f = font("Regular", 26)
        lines = textwrap.wrap(sub, int((W - 150) / (26 * 0.6)))
        room = max(0, (H - 100 - y) // 38)          # keep clear of the footer line
        if len(lines) > room and room:
            lines = lines[:room]
            lines[-1] = lines[-1].rstrip(".,; ") + "…"
        for ln in lines[:room]:
            y += 8
            d.text((72, y), ln, font=f, fill=DIM)
            y += 30
    d.text((72, H - 78), "guest@avinashk.in >", font=font("Bold", 24), fill=FG)
    d.text((W - 72, H - 78), footer, font=font("Regular", 24), fill=ACCENT, anchor="ra")
    img.save(os.path.join(ROOT, out), optimize=True)


def meta_block(url, title, desc, image, kind="website", published=None):
    tags = [
        f'<link rel="canonical" href="{url}" />',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml" />',
        f'<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/feed.xml" />',
        f'<meta property="og:type" content="{kind}" />',
        f'<meta property="og:site_name" content="{NAME}" />',
        f'<meta property="og:title" content="{html.escape(title)}" />',
        f'<meta property="og:description" content="{html.escape(desc)}" />',
        f'<meta property="og:url" content="{url}" />',
        f'<meta property="og:image" content="{SITE}/{image}" />',
        '<meta property="og:image:width" content="1200" />',
        '<meta property="og:image:height" content="630" />',
        '<meta name="twitter:card" content="summary_large_image" />',
    ]
    if published:
        tags.append(f'<meta property="article:published_time" content="{published}" />')
        tags.append(f'<meta property="article:author" content="{NAME}" />')
    return "<!-- meta:start -->\n" + "\n".join(tags) + "\n<!-- meta:end -->"


def inject(path, block):
    s = read(path)
    if "<!-- meta:start -->" in s:
        s = re.sub(r"<!-- meta:start -->[\s\S]*?<!-- meta:end -->", lambda m: block, s)
    else:
        s = re.sub(r'(<meta name="description"[^>]*>\n)', lambda m: m.group(1) + block + "\n", s, count=1)
    assert "<!-- meta:start -->" in s, f"couldn't place meta tags in {path}"
    write(path, s)


def favicon():
    rows = SPRITES["dragon"]
    rects = "".join(
        f'<rect x="{i}" y="{j}" width="1.02" height="1.02" fill="{INK[ch]}"/>'
        for j, row in enumerate(rows) for i, ch in enumerate(row[:14]) if ch in INK
    )
    write("favicon.svg", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -3 14 14" shape-rendering="crispEdges">{rects}</svg>\n')


def main():
    posts = json.loads(read("blog/posts.json"))
    os.makedirs(os.path.join(ROOT, "og"), exist_ok=True)
    favicon()

    home_desc = "Full-stack developer working on web apps, front end and back end. A terminal homepage, a blog about F1 and a Red Bull lapping Spa."
    og_image("og/home.png", NAME, "Full-stack developer. Type /help on avinashk.in", icon="dragon")
    inject("index.html", meta_block(SITE + "/", NAME, home_desc, "og/home.png"))

    og_image("og/blog.png", "Blog", "Notes on what I'm building and learning, and a lot of F1.", icon="pen", footer="avinashk.in/blog")
    inject("blog/index.html", meta_block(SITE + "/blog/", f"Blog · {NAME}", "Notes on what I'm building and learning.", "og/blog.png"))

    if os.path.exists(os.path.join(ROOT, "resume/index.html")):
        og_image("og/resume.png", "Resume", "Full-stack developer: web apps, front end and back end.", icon="prompt", footer="avinashk.in/resume")
        inject("resume/index.html", meta_block(SITE + "/resume/", f"Resume · {NAME}", "Avinash Kamadri's resume: full-stack developer working on web apps.", "og/resume.png"))

    for p in posts:
        img = f"og/{p['slug']}.png"
        og_image(img, p["title"], p["summary"], tag=p["tag"], icon=p.get("icon", "dragon"), footer="avinashk.in/blog")
        inject(f"blog/{p['slug']}/index.html",
               meta_block(f"{SITE}/blog/{p['slug']}/", p["title"], p["summary"], img, kind="article", published=p["date"]))

    # sitemap
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [(SITE + "/", today), (SITE + "/blog/", posts[0]["date"] if posts else today)]
    if os.path.exists(os.path.join(ROOT, "resume/index.html")):
        urls.append((SITE + "/resume/", today))
    urls += [(f"{SITE}/blog/{p['slug']}/", p["date"]) for p in posts]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n")

    # RSS
    def rfc822(d):
        return format_datetime(datetime.fromisoformat(d + "T12:00:00+00:00"))
    items = "".join(
        f"""  <item>
    <title>{html.escape(p['title'])}</title>
    <link>{SITE}/blog/{p['slug']}/</link>
    <guid isPermaLink="true">{SITE}/blog/{p['slug']}/</guid>
    <pubDate>{rfc822(p['date'])}</pubDate>
    <category>{html.escape(p['tag'])}</category>
    <description>{html.escape(p['summary'])}</description>
  </item>
""" for p in posts)
    write("feed.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{NAME}</title>
  <link>{SITE}/blog/</link>
  <description>Notes on what I'm building and learning, and a lot of F1.</description>
  <language>en</language>
  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />
  <lastBuildDate>{rfc822(posts[0]['date']) if posts else ''}</lastBuildDate>
{items}</channel>
</rss>
""")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"built: {len(posts)} posts, {len(urls)} sitemap urls, og images, feed, robots, favicon")


if __name__ == "__main__":
    main()
