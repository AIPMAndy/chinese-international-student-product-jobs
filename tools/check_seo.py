#!/usr/bin/env python3
"""Validate public site metadata and PDF presence after source-driven build."""
from __future__ import annotations
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
site = root / "dist"
name = root.name
base = "https://aipmandy.github.io/" + name + "/"
business = name.endswith("-business-jobs")
pages = [site / "index.html", site / "404.html"]
pages += sorted((site / ("read" if business else "chapters")).glob("*.html"))
if not business:
    pages += [site / "resources.html", site / "verification.html", site / "sources-workbench.html"]
errors = []
def check(ok, desc):
    if not ok: errors.append(desc)

try:
    xml = ET.parse(site / "sitemap.xml")
    locs = {el.text for el in xml.iter() if el.tag.endswith("}loc") or el.tag == "loc"}
except Exception as exc:
    locs = set()
    errors.append("sitemap parse: " + str(exc))
check(("Sitemap: " + base + "sitemap.xml") in (site / "robots.txt").read_text(encoding="utf-8"), "robots sitemap is missing")
for file in pages:
    rel = file.relative_to(site).as_posix()
    if not file.is_file():
        errors.append(rel + ": missing HTML")
        continue
    content = file.read_text(encoding="utf-8")
    expected = base if rel == "index.html" else base + rel
    matches = re.findall(r'<link rel="canonical" href="([^"]+)"', content)
    check(matches == [expected], rel + ": missing/wrong/duplicate canonical")
    check('<meta name="description"' in content, rel + ": no description")
    check('<meta property="og:title"' in content, rel + ": no OG title")
    check('<meta property="og:url" content="' + expected + '"' in content, rel + ": wrong OG URL")
    image = base + "assets/social-preview.png"
    check('<meta property="og:image" content="' + image + '"' in content, rel + ": missing og:image")
    check('<meta property="og:image:width" content="1280"' in content, rel + ": missing og:image width")
    check('<meta property="og:image:height" content="640"' in content, rel + ": missing og:image height")
    check('<meta name="twitter:card" content="summary_large_image"' in content, rel + ": missing summary_large_image")
    check('<meta name="robots" content="' + ("noindex,follow" if rel == "404.html" else "index,follow") + '"' in content, rel + ": wrong robots")
    data = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.S)
    if not data:
        errors.append(rel + ": missing JSON-LD")
    else:
        try:
            obj = json.loads(html.unescape(data.group(1)))
            check(obj.get("@type") == "WebPage" and obj.get("url") == expected, rel + ": invalid JSON-LD identity")
            check(obj.get("isAccessibleForFree") is True, rel + ": incorrectly describes free content")
            check(obj.get("image") == image, rel + ": JSON-LD image missing")
            check("aggregateRating" not in obj and "reviewRating" not in obj, rel + ": unexpected rating")
            if rel == "sources-workbench.html":
                source_records = json.loads((root / "research/jobs-sources.json").read_text(encoding="utf-8"))
                expected_urls = [row["url"] for row in source_records]
                check(obj.get("citation") == expected_urls, rel + ": citations diverge from source JSON")
                check(obj.get("dateModified") == "2026-11-19", rel + ": incorrect evidence workbench revision date")
                check(content.count('class="audit-card"') == len(source_records), rel + ": source cards diverge from original JSON")
                check("不是实时招聘平台" in content, rel + ": missing historical evidence limitation")
            check(obj.get("author", {}).get("name") == "AI酋长Andy", rel + ": no known author")
            check(obj.get("publisher", {}).get("url") == "https://www.a6no1.cn/", rel + ": no known company")
        except (ValueError, TypeError) as exc:
            errors.append(rel + ": invalid JSON-LD: " + str(exc))
    if rel != "404.html":
        check(expected in locs, rel + ": not in sitemap")
homepage = (site / "index.html").read_text(encoding="utf-8")
for token in ("AIPMAndy", "https://metaver.vip/", "https://www.a6no1.cn/"):
    check(token in homepage, "homepage missing public business reference: " + token)
preview = site / "assets/social-preview.png"
check(preview.is_file() and preview.stat().st_size > 1000, "social preview missing")
pdf = site / ("downloads/business-careers-guide.pdf" if business else "downloads/product-jobs-guide-v1.0.0.pdf")
check(pdf.is_file() and pdf.stat().st_size > 100_000 and pdf.open("rb").read(5) == b"%PDF-", "PDF missing/invalid")
print(json.dumps({"site": name, "pages_checked": len(pages), "sitemap_entries": len(locs), "error_count": len(errors), "errors": errors[:30]}, ensure_ascii=False))
sys.exit(1 if errors else 0)
