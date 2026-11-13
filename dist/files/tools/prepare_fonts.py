#!/usr/bin/env python3
"""Create a local, embedded-font subset for the PDF, without downloading fonts.

Noto CJK system fonts use CFF outlines. ReportLab expects TrueType outlines.
This script converts only glyphs used by this project, retaining their Unicode
mapping and metrics. The derived font uses a new family name under SIL OFL 1.1.
Generated font files are reproducible cache files, not repository assets.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tmp" / "pdf-fonts"
FONT_SOURCE = Path("/usr/share/fonts/opentype/noto")
LICENSE_FILE = Path("/usr/share/doc/fonts-noto-cjk/copyright")
EXTRA = "中国留学生产品岗位求职保姆级攻略目录附录页版本作者核验资料限制原型截图填写示例教学模拟完整免费开放理解用户问题解释方案取舍让关键流程可执行用证据检验判断年月日来源文件官方原文可点击目录样例与工具阅读地图记录续正文填写待补墨绿笔记"


def project_characters() -> set[int]:
    chars = set(chr(i) for i in range(32, 127)) | set(EXTRA)
    for folder in ["content", "examples", "templates", "research", "assets", "tools"]:
        for file in (ROOT / folder).rglob("*"):
            if file.is_file() and file.suffix in {".md", ".csv", ".json", ".svg", ".py", ".mjs"}:
                chars.update(file.read_text(encoding="utf-8").replace("\ufeff", ""))
    return {ord(c) for c in chars if ord(c) >= 32 and c not in "\u200b\u200c\u200d\ufeff"}


def convert_face(source: Path, dest: Path, codepoints: set[int], style: str) -> dict:
    original = TTFont(source, fontNumber=2, lazy=False)
    cmap = original.getBestCmap()
    missing = sorted(codepoints - set(cmap))
    if missing:
        raise RuntimeError("Noto SC font is missing required characters: " + repr([chr(n) for n in missing]))
    selected = sorted(codepoints)
    names = [".notdef"] + [f"u{cp:06X}" for cp in selected]
    mapping = {cp: f"u{cp:06X}" for cp in selected}
    glyph_set = original.getGlyphSet()
    metrics = original["hmtx"].metrics
    glyphs = {}
    hmetrics = {}
    for cp, new_name in [(None, ".notdef")] + list(mapping.items()):
        old_name = ".notdef" if cp is None else cmap[cp]
        pen = TTGlyphPen(None)
        glyph_set[old_name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        glyphs[new_name] = pen.glyph()
        hmetrics[new_name] = metrics[old_name]
    upem = original["head"].unitsPerEm
    builder = FontBuilder(upem, isTTF=True)
    builder.setupGlyphOrder(names)
    builder.setupCharacterMap(mapping)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(hmetrics)
    builder.setupHorizontalHeader(ascent=original["hhea"].ascent, descent=original["hhea"].descent)
    builder.setupNameTable({
        "familyName": "Andy Career Guide SC",
        "styleName": style,
        "uniqueFontIdentifier": f"AndyCareerGuideSC-{style}-v1",
        "fullName": f"Andy Career Guide SC {style}",
        "psName": f"AndyCareerGuideSC-{style}",
        "version": "Version 1.0",
        "copyright": original["name"].getDebugName(0) or "Derived from Noto Sans CJK SC. SIL Open Font License 1.1.",
        "licenseDescription": "SIL Open Font License, Version 1.1. Glyph subset and outline conversion for this document.",
        "licenseInfoURL": "https://openfontlicense.org/",
    })
    os2 = original["OS/2"]
    builder.setupOS2(
        sTypoAscender=os2.sTypoAscender,
        sTypoDescender=os2.sTypoDescender,
        sTypoLineGap=os2.sTypoLineGap,
        usWinAscent=os2.usWinAscent,
        usWinDescent=os2.usWinDescent,
        usWeightClass=700 if style == "Bold" else 400,
        fsType=0,
        fsSelection=0x20 if style == "Bold" else 0x40,
    )
    builder.setupPost()
    builder.setupMaxp()
    builder.font["head"].macStyle = 1 if style == "Bold" else 0
    builder.save(dest)
    original.close()
    return {"source": str(source), "font_number": 2, "family": "Andy Career Guide SC", "style": style, "glyph_count": len(names), "output": str(dest), "license": "SIL Open Font License 1.1", "upstream": "https://github.com/notofonts/noto-cjk", "source_license_file": str(LICENSE_FILE), "missing_characters": []}


def prepare_fonts() -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    chars = project_characters()
    recipe = Path(__file__).read_bytes()
    fingerprint = hashlib.sha256(recipe + ("|" + ",".join(map(str, sorted(chars)))).encode()).hexdigest()
    manifest_path = CACHE / "manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        if old.get("fingerprint") == fingerprint and all(Path(x["output"]).exists() for x in old.get("faces", [])):
            return old
    faces = []
    for style in ["Regular", "Bold"]:
        faces.append(convert_face(FONT_SOURCE / f"NotoSansCJK-{style}.ttc", CACHE / f"AndyCareerGuideSC-{style}.ttf", chars, style))
    if LICENSE_FILE.exists():
        (CACHE / "Noto-CJK-license.txt").write_text(LICENSE_FILE.read_text())
    result = {"fingerprint": fingerprint, "codepoints": len(chars), "faces": faces}
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(prepare_fonts(), ensure_ascii=False, indent=2))
