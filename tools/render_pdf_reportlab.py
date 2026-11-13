#!/usr/bin/env python3
"""Build the complete, selectable Chinese handbook without a browser.

Requires the local ReportLab, fontTools, Pillow and PyMuPDF packages. No network
access is used. Markdown is exported by the project's existing marked parser;
the source Markdown and deployed website are never modified by this renderer.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote, urlsplit

import fitz
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Flowable, Frame, HRFlowable, Image,
    KeepTogether, LongTable, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, XPreformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents

from prepare_fonts import prepare_fonts

ROOT = Path(__file__).resolve().parents[1]
PAGE_W, PAGE_H = A4
LEFT, RIGHT, TOP, BOTTOM = 51, 51, 57, 55
WIDTH = PAGE_W - LEFT - RIGHT
HEIGHT = PAGE_H - TOP - BOTTOM
GREEN = colors.HexColor("#2d4e40")
INK = colors.HexColor("#202820")
MUTED = colors.HexColor("#66755b")
PALE = colors.HexColor("#f1f4ed")
RULE = colors.HexColor("#d3ddcb")
WHITE = colors.white


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def plain(value: str) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(value))


def stable_anchor(file: str, fragment: str = "") -> str:
    return "d-" + hashlib.sha1((file + "#" + fragment).encode()).hexdigest()[:16]


def register_fonts() -> dict:
    # FontTools may report timestamp conversion details for the source TTC.
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    manifest = prepare_fonts()
    for face in manifest["faces"]:
        name = "Guide-Bold" if face["style"] == "Bold" else "Guide"
        pdfmetrics.registerFont(TTFont(name, face["output"]))
    pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="Guide-Bold", italic="Guide", boldItalic="Guide-Bold")
    for name, suffix in [("Mono", ""), ("Mono-Bold", "-Bold")]:
        pdfmetrics.registerFont(TTFont(name, f"/usr/share/fonts/truetype/dejavu/DejaVuSansMono{suffix}.ttf"))
    pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono", boldItalic="Mono-Bold")
    return manifest


def make_styles() -> dict:
    common = dict(fontName="Guide", bulletFontName="Guide", bulletFontSize=9, textColor=INK, wordWrap="CJK", splitLongWords=True, allowWidows=0, allowOrphans=0)
    styles = {
        "body": ParagraphStyle("Body", fontSize=10.6, leading=17.2, spaceAfter=8, **common),
        "small": ParagraphStyle("Small", fontSize=8.6, leading=13.4, spaceAfter=7, **common),
        "source": ParagraphStyle("Source", fontSize=9.5, leading=15, spaceAfter=7, **common),
        "h1": ParagraphStyle("H1", fontSize=25, leading=34, spaceAfter=19, fontName="Guide-Bold", textColor=GREEN, wordWrap="CJK", keepWithNext=True),
        "h2": ParagraphStyle("H2", fontSize=15, leading=22, spaceBefore=18, spaceAfter=10, fontName="Guide-Bold", textColor=GREEN, wordWrap="CJK", keepWithNext=True),
        "h3": ParagraphStyle("H3", fontSize=11.8, leading=18.2, spaceBefore=12, spaceAfter=8, fontName="Guide-Bold", textColor=INK, wordWrap="CJK", keepWithNext=True),
        "h4": ParagraphStyle("H4", fontSize=10.6, leading=17, spaceBefore=10, spaceAfter=6, fontName="Guide-Bold", textColor=GREEN, wordWrap="CJK", keepWithNext=True),
        "label": ParagraphStyle("Label", fontName="Guide", fontSize=8.1, leading=12.5, textColor=MUTED, spaceAfter=15, keepWithNext=True),
        "cell": ParagraphStyle("Cell", fontSize=9.25, leading=14.3, spaceAfter=0, **common),
        "cellsmall": ParagraphStyle("CellSmall", fontSize=8.65, leading=13.3, spaceAfter=0, **common),
        "cellhead": ParagraphStyle("CellHead", fontName="Guide-Bold", fontSize=9.25, leading=14.3, textColor=GREEN, wordWrap="CJK", spaceAfter=0),
        "quote": ParagraphStyle("Quote", fontSize=9.8, leading=16, leftIndent=11, rightIndent=9, borderPadding=10, borderColor=RULE, borderWidth=.6, backColor=PALE, spaceBefore=6, spaceAfter=11, **common),
        "caption": ParagraphStyle("Caption", fontSize=8.1, leading=12.5, spaceBefore=6, spaceAfter=13, **{**common, "textColor": MUTED}),
        "code": ParagraphStyle("Code", fontName="Mono", fontSize=8.35, leading=12.2, textColor=INK, leftIndent=10, rightIndent=10, borderPadding=10, backColor=PALE, borderColor=RULE, borderWidth=.5, spaceBefore=7, spaceAfter=12),
        "toc": ParagraphStyle("TOC", fontName="Guide", fontSize=10.8, leading=16.3, textColor=GREEN, leftIndent=0, rightIndent=30, spaceBefore=5, spaceAfter=0, wordWrap="CJK"),
        "toccompact": ParagraphStyle("TOCCompact", fontName="Guide", fontSize=11.2, leading=17, textColor=GREEN, leftIndent=0, rightIndent=30, spaceBefore=17, spaceAfter=0, wordWrap="CJK"),
    }
    # Templates retain body font sizes while using workbook spacing. This keeps
    # reusable one-page forms together without dropping their instructions.
    styles["template_body"] = ParagraphStyle("TemplateBody", parent=styles["body"], leading=16.3, spaceAfter=5)
    styles["template_h1"] = ParagraphStyle("TemplateH1", parent=styles["h1"], spaceAfter=12)
    styles["template_h2"] = ParagraphStyle("TemplateH2", parent=styles["h2"], spaceBefore=10, spaceAfter=6)
    styles["template_h3"] = ParagraphStyle("TemplateH3", parent=styles["h3"], spaceBefore=7, spaceAfter=5)
    styles["template_h4"] = ParagraphStyle("TemplateH4", parent=styles["h4"], spaceBefore=6, spaceAfter=4)
    return styles


class SimpleSVG(Flowable):
    """Render this repository's exact SVG diagrams as selectable vector art."""
    def __init__(self, filename: Path, width: float):
        Flowable.__init__(self)
        self.root = ET.parse(filename).getroot()
        vb = [float(x) for x in self.root.get("viewBox", "0 0 1000 500").split()]
        self.source_w, self.source_h = vb[2], vb[3]
        self.width = width
        self.height = width * self.source_h / self.source_w

    def wrap(self, aw, ah):
        return self.width, self.height

    @staticmethod
    def colour(value, default="#202820"):
        if value in (None, "inherit"):
            value = default
        if re.fullmatch(r"#[0-9A-Fa-f]{3}", value):
            value = "#"+"".join(ch*2 for ch in value[1:])
        return None if value == "none" else colors.HexColor(value)

    def draw(self):
        c = self.canv
        c.saveState()
        c.scale(self.width / self.source_w, self.width / self.source_w)
        H = self.source_h

        def node(el, inherited):
            tag = el.tag.split("}")[-1]
            if tag in {"defs", "marker", "title", "desc"}:
                return
            attrs = dict(inherited)
            attrs.update(el.attrib)
            if "style" in attrs:
                attrs.update(dict(v.split(":", 1) for v in attrs["style"].split(";") if ":" in v))
            fill = self.colour(attrs.get("fill", "#202820"))
            stroke = self.colour(attrs.get("stroke", "none"))
            c.saveState()
            if fill:
                c.setFillColor(fill)
            if stroke:
                c.setStrokeColor(stroke)
            c.setLineWidth(float(attrs.get("stroke-width", 1)))
            opacity = float(attrs.get("opacity", 1))
            if hasattr(c, "setFillAlpha"):
                c.setFillAlpha(opacity)
                c.setStrokeAlpha(opacity)
            if tag == "rect":
                x, y, w, h = [float(attrs.get(k, 0)) for k in ["x", "y", "width", "height"]]
                radius = float(attrs.get("rx", 0))
                if radius:
                    c.roundRect(x, H-y-h, w, h, radius, fill=int(bool(fill)), stroke=int(bool(stroke)))
                else:
                    c.rect(x, H-y-h, w, h, fill=int(bool(fill)), stroke=int(bool(stroke)))
            elif tag == "circle":
                c.circle(float(attrs.get("cx", 0)), H-float(attrs.get("cy", 0)), float(attrs.get("r", 0)), fill=int(bool(fill)), stroke=int(bool(stroke)))
            elif tag == "line":
                c.line(float(attrs.get("x1", 0)), H-float(attrs.get("y1", 0)), float(attrs.get("x2", 0)), H-float(attrs.get("y2", 0)))
            elif tag == "text":
                size = float(str(attrs.get("font-size", 16)).replace("px", ""))
                weight = attrs.get("font-weight", "400")
                c.setFont("Guide-Bold" if weight in ("bold", "600", "700", "800") else "Guide", size)
                txt = "".join(el.itertext())
                x, y = float(attrs.get("x", 0)), H-float(attrs.get("y", 0))
                anchor = attrs.get("text-anchor", "start")
                if anchor == "middle":
                    c.drawCentredString(x, y, txt)
                elif anchor == "end":
                    c.drawRightString(x, y, txt)
                else:
                    c.drawString(x, y, txt)
            elif tag == "path":
                toks = re.findall(r"[MLHVZmlhvz]|[-+]?(?:\d*\.\d+|\d+)", attrs.get("d", ""))
                p = c.beginPath()
                x = y = 0.0
                last = None
                cmd = None
                i = 0
                while i < len(toks):
                    if toks[i].isalpha():
                        cmd = toks[i]
                        i += 1
                        if cmd in "Zz":
                            p.close()
                            continue
                    if cmd in "MmLl":
                        nx, ny = float(toks[i]), float(toks[i+1]); i += 2
                        if cmd.islower(): nx, ny = x+nx, y+ny
                        if cmd in "Mm": p.moveTo(nx, H-ny)
                        else: p.lineTo(nx, H-ny)
                        last = (x, y, nx, ny); x, y = nx, ny
                        if cmd == "M": cmd = "L"
                        if cmd == "m": cmd = "l"
                    elif cmd in "Hh":
                        nx = float(toks[i]); i += 1
                        if cmd == "h": nx += x
                        p.lineTo(nx, H-y); last = (x, y, nx, y); x = nx
                    elif cmd in "Vv":
                        ny = float(toks[i]); i += 1
                        if cmd == "v": ny += y
                        p.lineTo(x, H-ny); last = (x, y, x, ny); y = ny
                    else:
                        raise ValueError(f"Unsupported SVG path command: {cmd}")
                c.drawPath(p, fill=int(bool(fill)), stroke=int(bool(stroke)))
                if attrs.get("marker-end") and last:
                    x1, y1, x2, y2 = last
                    angle = math.atan2(y2-y1, x2-x1)
                    size = 9
                    tip = c.beginPath(); tip.moveTo(x2, H-y2)
                    for delta in [-.48, .48]:
                        tip.lineTo(x2-size*math.cos(angle+delta), H-(y2-size*math.sin(angle+delta)))
                    tip.close()
                    c.setFillColor(stroke or GREEN)
                    c.drawPath(tip, fill=1, stroke=0)
            if tag not in {"text", "path"}:
                for child in el:
                    node(child, attrs)
            c.restoreState()

        node(self.root, {})
        c.restoreState()


class BookDoc(BaseDocTemplate):
    def __init__(self, target, book, styles):
        BaseDocTemplate.__init__(self, str(target), pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT, topMargin=TOP, bottomMargin=BOTTOM, title=book["title"], author=book["author"], subject="中国留学生产品岗位申请、产品案例与面试训练", creator="AI 酋长 Andy / ReportLab", pageCompression=1, allowSplitting=1)
        self.book, self.styles = book, styles
        self.section_name = "阅读地图"
        self.section_pages = {}
        self.last_outline_level = -1
        frame = Frame(LEFT, BOTTOM, WIDTH, HEIGHT, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="body")
        self.addPageTemplates(PageTemplate(id="Book", frames=frame, onPage=self.decorate))

    def beforeDocument(self):
        self.section_name = "阅读地图"
        self.section_pages = {}
        self.last_outline_level = -1

    def decorate(self, c, doc):
        if doc.page == 1:
            self.cover(c)
            return
        c.saveState()
        c.setStrokeColor(RULE); c.setLineWidth(.45)
        c.line(LEFT, PAGE_H-35, PAGE_W-RIGHT, PAGE_H-35)
        c.setFillColor(MUTED); c.setFont("Guide", 7.5)
        c.drawString(LEFT, PAGE_H-27, "中国留学生 · 产品岗位求职")
        c.drawRightString(PAGE_W-RIGHT, PAGE_H-27, "AI 酋长 Andy")
        c.line(LEFT, 40, PAGE_W-RIGHT, 40)
        c.setFont("Guide", 7.1)
        c.drawString(LEFT, 26, f"完整免费开放  ·  V{self.book['version']}  ·  {self.book['date']}")
        c.drawRightString(PAGE_W-RIGHT, 26, f"{doc.page:03d}")
        c.linkURL(self.book["origin"]+"/", (LEFT, 20, LEFT+260, 35), relative=0, thickness=0)
        c.restoreState()

    def cover(self, c):
        c.saveState()
        c.setFillColor(colors.HexColor("#fbfcf8")); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(GREEN); c.rect(LEFT, PAGE_H-61, WIDTH, 2, fill=1, stroke=0)
        c.setFont("Guide", 8); c.setFillColor(MUTED)
        c.drawString(LEFT, PAGE_H-82, "AI CHIEF ANDY / CAREER FIELD GUIDE")
        c.drawRightString(PAGE_W-RIGHT, PAGE_H-82, f"V{self.book['version']} · {self.book['date']}")
        c.setFont("Guide", 13); c.drawString(LEFT, PAGE_H-146, "中国留学生")
        c.setFillColor(INK); c.setFont("Guide-Bold", 34)
        c.drawString(LEFT-1, PAGE_H-201, "产品岗位求职")
        c.setFillColor(GREEN); c.drawString(LEFT-1, PAGE_H-249, "保姆级攻略")
        c.setFont("Guide", 12.2); c.setFillColor(MUTED)
        c.drawString(LEFT, PAGE_H-293, "从真实 JD 出发，")
        c.drawString(LEFT, PAGE_H-316, "拿出能够解释判断、取舍与推进的证据。")
        y = PAGE_H-482
        c.setFillColor(PALE); c.roundRect(LEFT, y, WIDTH, 130, 3, fill=1, stroke=0)
        cards = [("01 / UNDERSTAND", "理解用户的问题"), ("02 / DECIDE", "解释方案的取舍"), ("03 / DELIVER", "让关键流程可执行"), ("04 / VERIFY", "用证据检验判断")]
        for i, (label, title) in enumerate(cards):
            x = LEFT+20+(i%2)*(WIDTH/2)
            yy = y+104-(i//2)*59
            c.setFillColor(MUTED); c.setFont("Guide", 7.2); c.drawString(x, yy, label)
            c.setFillColor(GREEN); c.setFont("Guide", 12.6); c.drawString(x, yy-23, title)
        c.setFillColor(MUTED); c.setFont("Guide", 9)
        c.drawString(LEFT, y-28, "产品实习 · 毕业生项目 · 正式产品岗位 · AI 产品经理")
        c.drawString(LEFT, y-46, f"15 份可编辑模板 / 1 套完整贯穿样例 / {self.book['sourceCount']} 个官方资料链接")
        c.setStrokeColor(RULE); c.line(LEFT, 218, PAGE_W-RIGHT, 218)
        c.setFillColor(INK); c.setFont("Guide-Bold", 14); c.drawString(LEFT, 189, self.book["author"])
        c.setFont("Guide", 9.1); c.drawString(LEFT, 167, "前腾讯、百度 AI 产品专家 · 前大模型公司 VP")
        c.drawString(LEFT, 143, "微信：AIPMAndy  ·  公众号：AI酋长Andy")
        c.setFont("Guide", 8.6)
        c.drawString(LEFT, 123, "个人官网：https://metaver.vip/")
        c.drawString(LEFT, 105, "公司官网：https://www.a6no1.cn/")
        c.linkURL("https://metaver.vip/", (LEFT, 119, LEFT+220, 135), relative=0, thickness=0)
        c.linkURL("https://www.a6no1.cn/", (LEFT, 101, LEFT+240, 117), relative=0, thickness=0)
        c.setFont("Guide", 7.8); c.setFillColor(MUTED)
        c.drawString(LEFT, 63, "完整免费开放 · 咨询支持岗位定位、作品集诊断与模拟面试")
        c.drawRightString(PAGE_W-RIGHT, 46, "不承诺录用或涨薪")
        c.bookmarkPage("cover"); c.addOutlineEntry("封面", "cover", 0, False)
        c.restoreState()

    def afterFlowable(self, f):
        if not isinstance(f, Paragraph) or not hasattr(f, "_bookmark"):
            return
        key = f._bookmark
        self.canv.bookmarkPage(key)
        for extra in getattr(f, "_extra_bookmarks", []):
            self.canv.bookmarkPage(extra)
        level = min(getattr(f, "_outline_level", 0), self.last_outline_level+1)
        self.canv.addOutlineEntry(f._outline_title, key, level, False)
        self.last_outline_level = level
        if hasattr(f, "_section"):
            section = f._section
            self.section_name = section["title"]
            self.section_pages[section["key"]] = self.page
            label = f"<font color='#66755b'>{section['id']}</font>  {e(section['title'])}<br/><font size='7.6' color='#78836d'>{e(section.get('description', ''))}</font>"
            kind = "TOCMain" if section["kind"] == "chapter" else "TOCAppendix"
            self.notify(kind, (0, label, self.page, key))


class Builder:
    def __init__(self, book, styles):
        self.book, self.styles = book, styles
        self.files = {d["file"]: stable_anchor(d["file"]) for s in book["sections"] for d in s["documents"]}
        self.missing_images = []
        self.image_records = []
        self.wide_tables_as_cards = 0
        self.csv_records = 0
        self.csv_blank_records_collapsed = 0
        self.headings = 0
        self.figure_states_added = False
        self.compact_template = False

    def link(self, href, source):
        if re.match(r"^(?:https?://|mailto:|tel:)", href):
            return href
        if href.startswith("#"):
            return "#"+stable_anchor(source, href[1:])
        path_part, _, fragment = href.partition("#")
        path = os.path.normpath(os.path.join(os.path.dirname(source), path_part)).replace(os.sep, "/")
        if path in self.files:
            return "#"+(stable_anchor(path, fragment) if fragment else self.files[path])
        if path == "prototypes/offertrail.html" or path.endswith("prototype.html") or href in ("/prototype.html", "prototype.html"):
            return self.book["origin"]+"/prototype.html"
        return self.book["origin"]+"/files/"+quote(path, safe="/-_.")+("#"+fragment if fragment else "")

    def inline(self, tokens, source):
        out = []
        for t in tokens or []:
            kind = t["type"]
            txt = self.inline(t.get("tokens"), source) if t.get("tokens") else e(t.get("text", ""))
            if kind == "strong": out.append("<b>"+txt+"</b>")
            elif kind == "em": out.append("<i>"+txt+"</i>")
            elif kind == "codespan": out.append("<font size='9' backcolor='#eef2e8'>"+txt+"</font>")
            elif kind == "br": out.append("<br/>")
            elif kind == "link": out.append(f"<a href='{e(self.link(t['href'], source))}' color='#2d4e40'><u>{txt}</u></a>")
            elif kind == "del": out.append("<strike>"+txt+"</strike>")
            elif kind == "checkbox": out.append("[x] " if t.get("checked") else "[ ] ")
            elif kind == "escape": out.append(txt)
            elif kind == "image": out.append(e(t.get("text", "")))
            elif kind == "html": out.append(e(t.get("raw", "")))
            else: out.append(txt)
        return "".join(out).replace("\n", " ")

    def paragraph(self, text, style="body", **kwargs):
        if self.compact_template and style in {"body", "h1", "h2", "h3", "h4"}:
            style = "template_"+style
        return Paragraph(text, self.styles[style], **kwargs)

    def heading(self, text, depth, source, bookmark=None):
        self.headings += 1
        p = self.paragraph(text, f"h{min(depth, 4)}")
        title = plain(text)
        # Match ordinary GitHub-style heading links, and retain a unique key.
        slug = re.sub(r"[^\w\-\u3400-\u9fff ]", "", title.lower()).replace(" ", "-")
        p._bookmark = bookmark or f"h-{self.headings}"
        p._extra_bookmarks = [stable_anchor(source, slug)]
        p._outline_title = title
        p._outline_level = min(depth-1, 2)
        return p

    def image(self, t, source):
        raw = t.get("href", "")
        filename = (ROOT / source).parent / raw
        filename = filename.resolve()
        if not filename.exists():
            self.missing_images.append(str(filename.relative_to(ROOT)))
            return [self.paragraph("原型截图待补。请在网站打开可交互原型核对关键状态。", "caption")]
        record = {"path": str(filename.relative_to(ROOT)), "caption": t.get("text", ""), "kind": filename.suffix.lstrip(".")}
        if filename.suffix.lower() == ".svg":
            figure = SimpleSVG(filename, WIDTH)
        else:
            with PILImage.open(filename) as im:
                w, h = im.size
            target_w = min(WIDTH, (HEIGHT-90)*w/h)
            figure = Image(str(filename), width=target_w, height=target_w*h/w)
            figure.hAlign = "CENTER"
            record.update({"pixels": [w, h], "display_points": [target_w, target_w*h/w], "effective_dpi": round(w/(target_w/72), 1)})
        self.image_records.append(record)
        block = [Spacer(1, 6), figure, self.paragraph(e(t.get("text", "")), "caption")]
        result = [KeepTogether(block)]
        if filename.name == "offertrail-overview.png" and not self.figure_states_added:
            self.figure_states_added = True
            for state_name, caption in [("offertrail-blocked.png", "原型状态：原文缺少日期或时区时，阻止确认并提示回到官方来源。"), ("offertrail-complete.png", "原型状态：人工核对完成。此状态不代表已投递，也不代表取得工作许可。")]:
                state = ROOT / "assets" / state_name
                if state.exists():
                    result.extend(self.image({"href": "../../assets/"+state_name, "text": caption}, "content/case/06-end-to-end-case.md"))
                else:
                    self.missing_images.append("assets/"+state_name)
        return result

    def record_card(self, labels, values, title, source, rich=False):
        rows = [[self.paragraph(e(title), "cellhead"), ""]]
        for k, v in zip(labels, values):
            value = v if rich else e(v).replace("\n", "<br/>")
            rows.append([self.paragraph(k if rich else e(k), "cellhead"), self.paragraph(value or "（留空，待填写）", "cell")])
        table = LongTable(rows, colWidths=[WIDTH*.225, WIDTH*.775], repeatRows=1, splitByRow=1, splitInRow=0, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, 0), .7, RULE), ("LINEBELOW", (0, 1), (-1, -1), .35, RULE),
            ("BOX", (0, 0), (-1, -1), .5, RULE),
        ]))
        return [CondPageBreak(90), table, Spacer(1, 12)]

    def table(self, t, source):
        labels = [self.inline(x.get("tokens"), source) or e(x.get("text", "")) for x in t["header"]]
        values = [[self.inline(x.get("tokens"), source) or e(x.get("text", "")) for x in row] for row in t["rows"]]
        n = len(labels)
        if n >= 6:
            self.wide_tables_as_cards += 1
            result = [self.paragraph("本表按记录展开，保留全部字段。", "caption")]
            for i, row in enumerate(values):
                result.extend(self.record_card(labels, row, f"记录 {i+1} · {plain(row[0])[:38]}", source, rich=True))
            return result
        # Flexible columns based on cell length, with enough room for short labels.
        weights = []
        for col in range(n):
            lengths = [len(plain(row[col])) for row in values if col < len(row)] or [1]
            weights.append(max(4, min(23, math.sqrt(sum(lengths)/len(lengths))*3)))
        if n == 2:
            frac = max(.24, min(.44, weights[0]/sum(weights)))
            widths = [WIDTH*frac, WIDTH*(1-frac)]
        else:
            widths = [WIDTH*w/sum(weights) for w in weights]
        style_name = "cellsmall" if n == 5 else "cell"
        rows = [[self.paragraph(x, "cellhead") for x in labels]]
        rows += [[self.paragraph(x or " ", style_name) for x in row] for row in values]
        table = LongTable(rows, colWidths=widths, repeatRows=1, splitByRow=1, splitInRow=0, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#f9faf7")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5 if self.compact_template else 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 5 if self.compact_template else 7),
            ("LINEBELOW", (0, 0), (-1, 0), .8, RULE), ("LINEBELOW", (0, 1), (-1, -1), .35, RULE),
        ]))
        # Convert any unusually tall row into a readable record instead of splitting it.
        table.wrap(WIDTH, HEIGHT)
        if max(table._rowHeights, default=0) > HEIGHT-80:
            self.wide_tables_as_cards += 1
            out = []
            for i, row in enumerate(values):
                out.extend(self.record_card(labels, row, f"记录 {i+1}", source, rich=True))
            return out
        if self.compact_template:
            # A separate leading Spacer breaks the heading's keepWithNext chain.
            # Let the table own the gap so the heading follows its first rows.
            table.spaceBefore = 5
            return [table, Spacer(1, 8)]
        return [Spacer(1, 5), table, Spacer(1, 12)]

    def tokens(self, tokens, source, body="body", depth=0, omit_h1=False):
        out = []
        for t in tokens:
            kind = t["type"]
            if kind == "heading":
                if omit_h1 and t["depth"] == 1:
                    omit_h1 = False
                    continue
                out.append(self.heading(self.inline(t.get("tokens"), source), max(2, t["depth"]), source))
            elif kind in {"paragraph", "text"}:
                children = t.get("tokens", [])
                if len(children) == 1 and children[0]["type"] == "image":
                    out.extend(self.image(children[0], source))
                else:
                    txt = self.inline(children, source) if children else e(t.get("text", ""))
                    if txt.strip(): out.append(self.paragraph(txt, body))
            elif kind == "image":
                out.extend(self.image(t, source))
            elif kind == "table":
                out.extend(self.table(t, source))
            elif kind == "list":
                start = t.get("start", 1) or 1
                for index, item in enumerate(t["items"]):
                    marker = f"{start+index}." if t.get("ordered") else "-"
                    if item.get("task"): marker = "[x]" if item.get("checked") else "[ ]"
                    # marked emits a block-level checkbox before the item's text.
                    # The list bullet already draws it, so do not create a second
                    # standalone checkbox paragraph.
                    item_tokens = [tok for tok in item.get("tokens", []) if tok["type"] != "checkbox"]
                    inner = self.tokens(item_tokens, source, body=body, depth=depth+1)
                    first = True
                    for f in inner:
                        if isinstance(f, Paragraph) and not hasattr(f, "_bookmark"):
                            style = copy.copy(f.style)
                            style.name += "List"
                            style.leftIndent = 17*(depth+1)
                            style.bulletIndent = 3+17*depth
                            style.spaceAfter = 3 if self.compact_template else 5
                            p = Paragraph(f.text, style, bulletText=marker if first else None)
                            first = False
                            out.append(p)
                        else:
                            out.append(f)
                out.append(Spacer(1, 4))
            elif kind == "blockquote":
                out.extend(self.tokens(t.get("tokens", []), source, body="quote", depth=depth))
            elif kind == "code":
                text = t.get("text", "")
                p = XPreformatted(e(text), self.styles["code"])
                out.extend([CondPageBreak(min(HEIGHT-10, 30+12.2*len(text.splitlines()))), p])
            elif kind == "hr":
                out.append(HRFlowable(width="100%", thickness=.5, color=RULE, spaceBefore=10, spaceAfter=12))
            elif kind in {"space", "def"}:
                continue
            else:
                txt = e(t.get("text", t.get("raw", "")))
                if txt.strip(): out.append(self.paragraph(txt, body))
        return out

    def source_link(self, file):
        url = self.book["origin"]+"/files/"+file
        return self.paragraph(f"可编辑源文件：<a href='{e(url)}' color='#2d4e40'>{e(file)}</a>", "small")

    def story(self):
        story = [Spacer(1, HEIGHT-1), PageBreak()]
        for which in ["main", "appendix"]:
            story.append(self.paragraph("READING MAP / 可点击目录" if which == "main" else "WORKBOOK / 完整样例与模板", "label"))
            heading = self.heading("先找到你的问题。" if which == "main" else "把方法，落到材料上。", 1, "toc", "toc-"+which)
            story.append(heading)
            if which == "main":
                story.append(self.paragraph("每章交付一项可以检查的材料。点击标题或页码可跳转；PDF 保留全文、填写示例和原始来源。", "small"))
            toc = TableOfContents(notifyKind="TOCMain" if which == "main" else "TOCAppendix", levelStyles=[self.styles["toc" if which == "main" else "toccompact"]], dotsMinLevel=-1)
            toc.tableStyle = TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 3 if which == "main" else 5)])
            story.append(toc)
            if which == "appendix":
                story.append(Spacer(1, 25))
                story.append(self.paragraph("<b>案例真实性</b><br/>OfferTrail 的雇主、申请、候选人与六条情境均为教学模拟。没有真实访谈、用户增长、营收或录用成绩。真实求职者必须使用自己实际完成的工作。", "quote"))
                story.append(self.paragraph(f"<b>资料边界</b><br/>本版含 {self.book['sourceCount']} 个去重官方资料链接。核验日为 {self.book['date']}，核验日不等于生效日。岗位可能关闭，规则可能更新；正文保留读取限制与官方信息冲突。", "small"))
                story.append(self.paragraph(f"在线阅读与下载：<a href='{e(self.book['origin'])}/' color='#2d4e40'>{e(self.book['origin'])}/</a>", "small"))
            story.append(PageBreak())

        for s_index, section in enumerate(self.book["sections"]):
            if s_index: story.append(PageBreak())
            label = f"CHAPTER {section['id']} / PRODUCT JOBS" if section["kind"] == "chapter" else f"APPENDIX {section['id']} / WORKBOOK" if section["kind"] != "sources" else "SOURCES / VERSION & VERIFICATION"
            story.append(self.paragraph(label, "label"))
            title = self.heading(e(section["title"]), 1, section["documents"][0]["file"], section["key"])
            title._section = section
            title._extra_bookmarks.append(self.files[section["documents"][0]["file"]])
            story.append(title)
            for d_index, document in enumerate(section["documents"]):
                file = document["file"]
                self.compact_template = section["kind"] == "templates" and d_index > 0
                if d_index:
                    story.append(PageBreak())
                    if section["kind"] == "templates":
                        story.append(self.paragraph(f"TEMPLATE {d_index:02d} / {document['format'].upper()}", "label"))
                    title = self.heading(e(document["title"]), 1, file, self.files[file])
                    title._outline_level = 1
                    story.append(title)
                if section["kind"] in {"appendix", "templates"}:
                    story.append(self.source_link(file))
                if document["format"] == "csv":
                    rows = document["rows"]
                    labels = rows[0]
                    story.append(self.paragraph("CSV 在 PDF 中按记录展开，字段与源文件一致。下载 CSV 后可在表格软件里继续填写。", "small"))
                    for index, row in enumerate(rows[1:]):
                        if row and row[0].strip() == "待填写" and not any(v.strip() for v in row[1:]):
                            self.csv_blank_records_collapsed += 1
                            story.append(self.paragraph("空白记录字段同上。下载 CSV 后复制空白行填写自己的事实；源文件保留完整空白记录。", "small"))
                            continue
                        self.csv_records += 1
                        title = f"记录 {index+1} · "+(row[0] or "空白填写行")
                        story.extend(self.record_card(labels, row, title, file))
                else:
                    story.extend(self.tokens(document["tokens"], file, body="source" if section["kind"] == "sources" else "body", omit_h1=True))
            self.compact_template = False
        return story


def export_ast():
    node = os.environ.get("CODEX_PRIMARY_RUNTIME_NODE", "node")
    result = subprocess.run([node, str(ROOT/"tools/export_book_ast.mjs")], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    print(result.stdout.strip(), flush=True)
    return json.loads((ROOT/"tmp/pdfs/book-ast.json").read_text())


def audit_and_render(pdf, book, builder, font_manifest, doc, render=True, dpi=120):
    directory = ROOT / "verification"
    directory.mkdir(exist_ok=True)
    pages_dir = directory / "pdf-pages"
    sheets_dir = directory / "pdf-contact-sheets"
    for folder in [pages_dir, sheets_dir]:
        folder.mkdir(exist_ok=True)
        for file in folder.glob("*.png"): file.unlink()
    data = fitz.open(pdf)
    data[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(ROOT/"assets/pdf-cover.png")
    outside, blank, page_stats, missing_text = [], [], [], []
    texts = []
    links = {"internal": 0, "external": 0}
    images = []
    for i, page in enumerate(data):
        txt = page.get_text()
        texts.append(txt)
        if len(txt.strip()) < 40: blank.append(i+1)
        for link in page.get_links():
            if link.get("uri"): links["external"] += 1
            else: links["internal"] += 1
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block: continue
            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    if x0 < -.5 or y0 < -.5 or x1 > PAGE_W+.5 or y1 > PAGE_H+.5:
                        outside.append({"page": i+1, "bbox": [round(x, 2) for x in (x0,y0,x1,y1)], "text": span["text"][:100]})
        page_stats.append({"page": i+1, "characters": len(txt), "links": len(page.get_links()), "images": len(page.get_images())})
        if render:
            outfile = pages_dir / f"page-{i+1:03d}.png"
            page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False).save(outfile)
            images.append(outfile)
    extracted = "\n".join(texts)
    (directory/"pdf-extracted-text.txt").write_text(extracted, encoding="utf-8")
    compact = re.sub(r"\s+", "", extracted)
    for section in book["sections"]:
        if re.sub(r"\s+", "", section["title"]) not in compact:
            missing_text.append(section["title"])
    contact_records = []
    if render:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
        thumb_w, thumb_h, margin, gap, label_h = 570, 807, 24, 22, 29
        for start in range(0, len(images), 4):
            sheet = PILImage.new("RGB", (2*thumb_w+2*margin+gap, 2*(thumb_h+label_h)+2*margin+gap), "#e9eee4")
            draw = ImageDraw.Draw(sheet)
            for j, source in enumerate(images[start:start+4]):
                thumb = PILImage.open(source).convert("RGB")
                thumb.thumbnail((thumb_w, thumb_h), PILImage.Resampling.LANCZOS)
                x = margin+(j%2)*(thumb_w+gap)
                y = margin+(j//2)*(thumb_h+label_h+gap)
                draw.text((x, y), f"PAGE {start+j+1:03d}", font=label_font, fill="#2d4e40")
                sheet.paste(thumb, (x, y+label_h))
            out = sheets_dir / f"sheet-{start//4+1:03d}.png"
            sheet.save(out)
            contact_records.append({"file": str(out.relative_to(ROOT)), "pages": list(range(start+1, min(start+5, len(images)+1)))})
    font_proc = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True)
    unique_fonts = sorted({tuple(item[1:5]) for page in data for item in page.get_fonts(full=False)})
    metadata = {
        "file": str(pdf.relative_to(ROOT)), "version": book["version"], "verified_date": book["date"],
        "engine": "ReportLab (no browser)", "pages": len(data), "bytes": pdf.stat().st_size,
        "selectable_text_characters": len(extracted), "text_extraction": "verification/pdf-extracted-text.txt",
        "missing_section_titles": missing_text, "blank_or_nearly_blank_pages": blank,
        "text_outside_page": outside, "links": links, "bookmarks": len(data.get_toc()),
        "section_pages": doc.section_pages, "sources_unique_urls": book["sourceCount"],
        "documents": sum(len(s["documents"]) for s in book["sections"]), "templates": book["templateCount"],
        "wide_tables_as_record_cards": builder.wide_tables_as_cards, "csv_records": builder.csv_records,
        "csv_blank_records_collapsed": builder.csv_blank_records_collapsed,
        "table_policy": "Repeated header; rows never split across pages; wide CSV tables become key/value record cards.",
        "images": builder.image_records, "missing_images": sorted(set(builder.missing_images)),
        "fonts": unique_fonts, "pdffonts": font_proc.stdout, "font_derivation": font_manifest,
        "font_license": {"name": "SIL Open Font License 1.1", "upstream": "https://github.com/notofonts/noto-cjk", "local_license": "tmp/pdf-fonts/Noto-CJK-license.txt", "derived_family": "Andy Career Guide SC", "embedding": "Unicode TrueType subset; CFF curves converted to quadratic curves locally"},
        "render_dpi": dpi if render else None, "page_images": str(pages_dir.relative_to(ROOT)),
        "contact_sheets": contact_records, "page_stats": page_stats,
        "visual_review": "Pending independent page-by-page review; automated checks do not replace visual inspection.",
    }
    (directory/"pdf-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n")
    (directory/"pdf-font-license.md").write_text("# PDF 字体与授权\n\n使用本机 Noto Sans CJK SC 字体，来源为 https://github.com/notofonts/noto-cjk ，许可为 SIL Open Font License 1.1。\n\n构建时仅转换书籍实际使用的字形，派生字体重命名为 Andy Career Guide SC，并以可搜索、可选中的 Unicode TrueType 子集嵌入 PDF。源字体不随仓库分发；完整许可副本写入本地 tmp/pdf-fonts/Noto-CJK-license.txt。\n\n英文 SQL 示例使用本机 DejaVu Sans Mono，其自由字体许可见 https://dejavu-fonts.github.io/License.html 。\n\n生成器仅使用系统已安装的字体与库，不在构建中联网下载字体。\n", encoding="utf-8")
    data.close()
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-renders", action="store_true")
    parser.add_argument("--require-images", action="store_true")
    parser.add_argument("--dpi", type=int, default=120)
    args = parser.parse_args()
    book = export_ast()
    manifest = register_fonts()
    styles = make_styles()
    builder = Builder(book, styles)
    story = builder.story()
    if args.require_images and builder.missing_images:
        raise RuntimeError("Missing required images: "+", ".join(sorted(set(builder.missing_images))))
    out = ROOT / "output/pdf" / f"product-jobs-guide-v{book['version']}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = BookDoc(out, book, styles)
    print(json.dumps({"stage": "layout", "flowables": len(story), "missing_images": builder.missing_images}), flush=True)
    doc.multiBuild(story, maxPasses=6)
    downloads = ROOT / "downloads" / out.name
    downloads.parent.mkdir(exist_ok=True)
    shutil.copyfile(out, downloads)
    metadata = audit_and_render(out, book, builder, manifest, doc, render=not args.skip_renders, dpi=args.dpi)
    print(json.dumps({k:metadata[k] for k in ["file", "pages", "bytes", "selectable_text_characters", "links", "bookmarks", "missing_images", "text_outside_page", "blank_or_nearly_blank_pages", "missing_section_titles"]}, ensure_ascii=False), flush=True)
    if metadata["text_outside_page"] or metadata["missing_section_titles"]:
        raise SystemExit("PDF generated, but automated layout verification found issues.")


if __name__ == "__main__":
    main()
