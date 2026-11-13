#!/usr/bin/env python3
"""Repeatable, offline structural checks for this repository only.

Usage:
    python3 tools/check_integrity.py --source-only
    python3 tools/check_integrity.py

The report is written to verification/integrity.json. This checks structure and
fixed teaching fixtures; it is not a real-user usability study or a factual,
legal, accessibility, or external-link audit. No external network calls occur.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date, datetime
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REPORT = ROOT / "verification" / "integrity.json"
EXCLUDED_PARTS = {".git", "node_modules", ".venv", "__pycache__", "tmp"}
COUNTS: Counter = Counter()
FAILURES: list[dict] = []
WARNINGS: list[dict] = []
SKIPPED: list[dict] = []
JSON_DATA: dict[Path, object] = {}
HTML_CACHE: dict[Path, "Document"] = {}


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return "[outside repository]"


def issue(check: str, path: Path, detail: str, *, warning: bool = False) -> None:
    item = {"check": check, "path": relative(path), "detail": detail}
    (WARNINGS if warning else FAILURES).append(item)


def contained(path: Path, boundary: Path = ROOT) -> bool:
    try:
        path.resolve().relative_to(boundary.resolve())
        return True
    except (ValueError, OSError, RuntimeError):
        return False


def source_files() -> list[Path]:
    found = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if "dist" in rel.parts or any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if path == REPORT or not path.is_file():
            continue
        if not contained(path):
            issue("repository_boundary", path, "Source symlink resolves outside repository.")
            continue
        found.append(path)
    return sorted(found)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (UnicodeError, OSError) as exc:
        issue("text_read", path, f"Cannot read UTF-8 text ({type(exc).__name__}).")
        return None


def without_code(markdown: str) -> str:
    # Fenced and inline examples are not rendered Markdown links/citations.
    markdown = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", markdown)
    return re.sub(r"`+[^`\n]*`+", "", markdown)


def markdown_destinations(markdown: str):
    """Yield inline/image and reference-definition destinations.

    A small balanced-parenthesis scanner avoids truncating URL paths containing
    parentheses. Markdown titles and fragment-only links are handled later.
    """
    text = without_code(markdown)
    cursor = 0
    while True:
        start = text.find("](", cursor)
        if start < 0:
            break
        i = start + 2
        while i < len(text) and text[i].isspace():
            i += 1
        if i < len(text) and text[i] == "<":
            end = text.find(">", i + 1)
            if end >= 0:
                yield text[i + 1 : end]
                cursor = end + 1
                continue
        depth, end = 0, i
        while end < len(text):
            char = text[end]
            if char == "\\" and end + 1 < len(text):
                end += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() and depth == 0:
                break
            end += 1
        if end > i:
            yield text[i:end].replace("\\(", "(").replace("\\)", ")")
        cursor = max(end + 1, start + 2)
    for match in re.finditer(r"(?m)^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)", text):
        yield match.group(1).strip("<>")


def resolve_link(owner: Path, raw: str, boundary: Path):
    try:
        parsed = urlsplit(raw)
    except ValueError:
        issue("url_syntax", owner, "Malformed link URL.")
        return None
    if parsed.scheme or parsed.netloc:
        COUNTS["external_or_scheme_links_skipped"] += 1
        return None
    if not parsed.path:
        return owner, unquote(parsed.fragment)
    decoded = unquote(parsed.path)
    if decoded.startswith("/"):
        target = boundary / decoded.lstrip("/")
    else:
        target = owner.parent / decoded
    if not contained(target, boundary):
        issue("link_boundary", owner, "Local link escapes the checked repository/site boundary.")
        return None
    target = target.resolve()
    if target.is_dir():
        index = target / "index.html"
        if boundary == DIST and index.is_file():
            target = index
    return target, unquote(parsed.fragment)


def check_sources(files: list[Path]) -> dict[Path, str]:
    markdown = {}
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in {".md", ".json", ".csv"}:
            continue
        text = read_text(path)
        if text is None:
            continue
        if suffix == ".md":
            COUNTS["source_markdown_files"] += 1
            markdown[path] = text
            for raw in markdown_destinations(text):
                result = resolve_link(path, raw, ROOT)
                if result is None:
                    continue
                target, fragment = result
                COUNTS["source_local_links"] += 1
                if not target.exists():
                    issue("markdown_local_link", path, f"Missing target: {relative(target)}")
                if fragment:
                    COUNTS["source_fragments_not_checked"] += 1
        elif suffix == ".json":
            COUNTS["source_json_files"] += 1
            try:
                JSON_DATA[path] = json.loads(text)
            except json.JSONDecodeError as exc:
                issue("json_parse", path, f"Invalid JSON at line {exc.lineno}, column {exc.colno}.")
        else:
            COUNTS["source_csv_files"] += 1
            try:
                rows = list(csv.reader(io.StringIO(text), strict=True))
            except csv.Error as exc:
                issue("csv_parse", path, f"Cannot parse CSV ({type(exc).__name__}).")
                continue
            if not rows or not rows[0]:
                issue("csv_structure", path, "Missing CSV header.")
                continue
            if len(rows[0]) != len(set(rows[0])):
                issue("csv_structure", path, "Duplicate CSV header names.")
            for row_number, row in enumerate(rows[1:], start=2):
                if len(row) != len(rows[0]):
                    issue("csv_structure", path, f"Row {row_number} has {len(row)} columns; expected {len(rows[0])}.")
    return markdown


def check_ledgers(markdown: dict[Path, str]) -> None:
    ledgers = sorted((ROOT / "research").glob("*sources.json"))
    if not ledgers:
        issue("source_ledger", ROOT / "research", "No *sources.json ledgers found.")
        return
    ids: dict[str, Path] = {}
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    for path in ledgers:
        COUNTS["source_ledgers"] += 1
        records = JSON_DATA.get(path)
        if not isinstance(records, list):
            issue("source_ledger", path, "Source ledger must be a JSON list.")
            continue
        for number, record in enumerate(records, start=1):
            COUNTS["source_records"] += 1
            if not isinstance(record, dict):
                issue("source_record", path, f"Record {number} must be an object.")
                continue
            sid = record.get("id")
            label = sid if isinstance(sid, str) and re.fullmatch(r"[A-Z][A-Z0-9-]*", sid) else f"record {number}"
            if label == f"record {number}":
                issue("source_id", path, f"Record {number} has a missing or invalid ID.")
            elif sid in ids:
                issue("source_id", path, f"Duplicate source ID {sid}; also in {relative(ids[sid])}.")
            else:
                ids[sid] = path
            for field in ("title", "issuer", "scope", "caveat"):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    issue("source_metadata", path, f"{label}: missing/nonempty string field {field}.")
            claims = record.get("claims")
            if not isinstance(claims, list) or not claims or any(not isinstance(c, str) or not c.strip() for c in claims):
                issue("source_metadata", path, f"{label}: claims must be a nonempty string list.")
            checked = record.get("checked")
            try:
                if not isinstance(checked, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked):
                    raise ValueError
                checked_date = date.fromisoformat(checked)
                if checked_date > today:
                    raise ValueError
            except ValueError:
                issue("source_date", path, f"{label}: checked must be a valid, nonfuture YYYY-MM-DD date.")
            url = record.get("url")
            try:
                parsed = urlsplit(url if isinstance(url, str) else "")
                if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                    raise ValueError
            except ValueError:
                issue("source_url", path, f"{label}: expected an HTTPS URL without embedded credentials.")
            verification = record.get("verification")
            if not isinstance(verification, str) or not verification.startswith("official_"):
                issue("official_source_field", path, f"{label}: missing official_* verification metadata.")
            elif any(term in verification for term in ("excerpt", "conflict", "dynamic")):
                COUNTS["source_records_with_qualified_verification"] += 1
            used_paths = record.get("used_in", [])
            if not isinstance(used_paths, list):
                issue("source_used_in", path, f"{label}: used_in must be a list of paths.")
                used_paths = []
            for used_in in used_paths:
                if not isinstance(used_in, str):
                    issue("source_used_in", path, f"{label}: used_in entries must be paths.")
                elif not contained(ROOT / used_in) or not (ROOT / used_in).is_file():
                    issue("source_used_in", path, f"{label}: used_in target is absent or outside repository.")

    # Source-reference syntax is deliberately narrower than all capital IDs.
    # H1/S01/D01/P01 and case research tasks R01-R03 are not inferred as citations.
    prefixes = sorted({re.sub(r"\d+$", "", sid) for sid in ids}, key=len, reverse=True)
    if not prefixes:
        return
    id_pattern = r"(?:" + "|".join(re.escape(p) for p in prefixes) + r")\d{2,}"
    patterns = [
        re.compile(r"\[(" + id_pattern + r")(?=[\]\s])"),
        re.compile(r"来源\s*[:：]?\s*(" + id_pattern + r")\b"),
        re.compile(r"(?m)^#{1,6}\s+(" + id_pattern + r")\b"),
    ]
    for path, text in markdown.items():
        if not (path.is_relative_to(ROOT / "content") or path == ROOT / "README.md"):
            continue
        text = without_code(text)
        candidates = set()
        for pattern in patterns:
            candidates.update(pattern.findall(text))
        COUNTS["source_id_references"] += len(candidates)
        for sid in sorted(candidates - ids.keys()):
            issue("unknown_source_id", path, f"Unknown cited source ID {sid}.")


def check_offertrail(markdown: dict[Path, str]) -> None:
    path = ROOT / "examples" / "offertrail-facts.json"
    facts = JSON_DATA.get(path)
    if not isinstance(facts, dict):
        issue("offertrail_facts", path, "Missing or invalid fixed-fact JSON object.")
        return
    expected = {
        "APP-01": ("Product Intern", "2026-11-20 17:00", "Europe/London", "2026-11-20T17:00:00Z", "2026-11-21 01:00", ["作品集待补", "工作许可要求待核实"]),
        "APP-02": ("APM", "Friday end of day", None, None, None, ["日期待确认", "时区待确认"]),
        "APP-03": ("Junior PM", "2026-11-24 17:00", "America/New_York", "2026-11-24T22:00:00Z", "2026-11-25 06:00", ["简历待更新"]),
    }
    if facts.get("project") != "OfferTrail" or facts.get("raw_material_count") != 6:
        issue("offertrail_facts", path, "Project name or six-material count differs from fixed case.")
    if facts.get("raw_material_ids") != [f"S{i:02d}" for i in range(1, 7)]:
        issue("offertrail_facts", path, "Raw material IDs must be S01-S06 in order.")
    if facts.get("options_compared") != ["表格和日历", "人工来源核对加规则提示", "AI抽取并自动判断"]:
        issue("offertrail_facts", path, "Three-option comparison differs from the fixed case.")
    if "待验证" not in str(facts.get("chosen_option", "")):
        issue("offertrail_facts", path, "Chosen option must retain its unvalidated status.")
    required_unperformed = {"真实访谈", "真实用户可用性测试", "真实职位申请", "真实产品上线", "增长或收入验证"}
    if not required_unperformed.issubset(set(facts.get("not_completed", []))):
        issue("offertrail_facts", path, "Missing unperformed-research/launch/outcome boundaries.")
    apps = facts.get("applications")
    if not isinstance(apps, list) or len(apps) != 3 or not all(isinstance(a, dict) for a in apps):
        issue("offertrail_facts", path, "Expected three application objects.")
        return
    if {a.get("id") for a in apps} != set(expected):
        issue("offertrail_facts", path, "Application IDs must be APP-01, APP-02 and APP-03.")
    keys = ("role", "deadline_original", "deadline_zone", "deadline_utc", "beijing", "initial_blockers")
    for app in apps:
        sid = app.get("id")
        if sid not in expected:
            continue
        COUNTS["offertrail_application_fixtures"] += 1
        for key, value in zip(keys, expected[sid]):
            if app.get(key) != value:
                issue("offertrail_facts", path, f"{sid}: fixed field {key} differs.")
        if app.get("deadline_zone"):
            try:
                local = datetime.strptime(app["deadline_original"], "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(app["deadline_zone"]))
                if local.astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M") != app["beijing"]:
                    issue("offertrail_timezone", path, f"{sid}: Beijing time does not match zoneinfo conversion.")
                if local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ") != app["deadline_utc"]:
                    issue("offertrail_timezone", path, f"{sid}: UTC time does not match zoneinfo conversion.")
                COUNTS["offertrail_timezone_checks"] += 1
            except (KeyError, ValueError, TypeError) as exc:
                issue("offertrail_timezone", path, f"{sid}: timezone fixture cannot be evaluated ({type(exc).__name__}).")

    raw_path = ROOT / "examples" / "offertrail-raw-materials.md"
    raw = markdown.get(raw_path, "")
    if re.findall(r"(?m)^###\s+(S\d{2})\s", raw) != [f"S{i:02d}" for i in range(1, 7)]:
        issue("offertrail_materials", raw_path, "Expected exactly six source headings S01-S06.")
    required_fragments = {
        "examples/README.md": ["六条情境", "2026-11-21 01:00", "2026-11-25 06:00", "Friday end of day", "尚未开展"],
        "examples/offertrail-prototype-spec.md": ["教学模拟", "2026-11-21 01:00", "2026-11-25 06:00", "Friday end of day", "尚未向雇主提交"],
        "content/case/06-end-to-end-case.md": ["教学模拟", "2026-11-21 01:00", "2026-11-25 06:00", "Friday end of day", "没有开展真实访谈"],
        "examples/offertrail-portfolio.md": ["教学模拟", "Friday end of day", "尚未采集真实用户数据"],
        "examples/project-pitch-zh-en.md": ["教学模拟", "Friday end of day", "没有真实访谈"],
    }
    for rel, fragments in required_fragments.items():
        artifact = ROOT / rel
        text = markdown.get(artifact, "")
        COUNTS["offertrail_text_fixture_files"] += 1
        for fragment in fragments:
            if fragment not in text:
                issue("offertrail_text_fixture", artifact, "A required fixed-fact or disclosure phrase is missing.")
    csv_path = ROOT / "examples" / "offertrail-metrics.csv"
    if csv_path.is_file():
        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    if row.get("当前结果") != "未采集":
                        issue("offertrail_metric_boundary", csv_path, "Teaching metric dictionary contains a non-uncollected result.")
        except (OSError, csv.Error):
            issue("offertrail_metric_boundary", csv_path, "Cannot inspect metric dictionary.")
    else:
        issue("offertrail_metric_boundary", csv_path, "Missing metric dictionary.")


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: Counter = Counter()
        self.names: set[str] = set()
        self.links: list[tuple[str, str, bool]] = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids[attributes["id"]] += 1
        if tag == "a" and attributes.get("name"):
            self.names.add(attributes["name"])
        for attribute in ("href", "src", "poster", "data"):
            if attribute == "data" and tag != "object":
                continue
            value = attributes.get(attribute)
            if value is not None:
                self.links.append((value, f"{tag}.{attribute}", "download" in attributes))
        if attributes.get("srcset"):
            for candidate in attributes["srcset"].split(","):
                bits = candidate.strip().split()
                if bits and not bits[0].startswith("data:"):
                    self.links.append((bits[0], f"{tag}.srcset", False))
        if attributes.get("style"):
            for value in re.findall(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", attributes["style"]):
                self.links.append((value, f"{tag}.style", False))


def parse_html(path: Path) -> Document | None:
    if path in HTML_CACHE:
        return HTML_CACHE[path]
    text = read_text(path)
    if text is None:
        return None
    document = Document()
    try:
        document.feed(text)
        document.close()
    except Exception as exc:
        issue("html_parse", path, f"HTMLParser failed ({type(exc).__name__}).")
        return None
    HTML_CACHE[path] = document
    COUNTS["dist_html_files"] += 1
    for identifier, count in document.ids.items():
        if count > 1:
            # Report the duplicate count, not arbitrary authored content.
            issue("html_duplicate_id", path, f"An HTML id occurs {count} times.")
    return document


def check_dist() -> None:
    if not DIST.is_dir():
        issue("dist_exists", DIST, "No dist directory; build the site or use --source-only.")
        return
    html_files = sorted(DIST.rglob("*.html"))
    if not html_files:
        issue("dist_html", DIST, "No HTML files found in dist.")
        return
    for path in html_files:
        if contained(path, DIST):
            parse_html(path)
        else:
            issue("dist_boundary", path, "HTML symlink resolves outside dist.")
    downloads: dict[str, set[Path]] = {".pdf": set(), ".zip": set()}
    for path, document in list(HTML_CACHE.items()):
        for raw, location, download_attribute in document.links:
            result = resolve_link(path, raw, DIST)
            if result is None:
                continue
            target, fragment = result
            COUNTS["dist_local_links_and_resources"] += 1
            if target.suffix.lower() in downloads:
                downloads[target.suffix.lower()].add(target)
            if not target.exists():
                issue("html_local_target", path, f"{location} target missing: {relative(target)}")
                continue
            if download_attribute and not target.is_file():
                issue("html_download", path, f"Download target is not a file: {relative(target)}")
            if fragment and target.suffix.lower() in {".html", ".htm"}:
                target_document = parse_html(target)
                COUNTS["dist_fragment_links"] += 1
                if target_document is not None and fragment not in target_document.ids and fragment not in target_document.names:
                    issue("html_fragment", path, f"Fragment target absent in {relative(target)}.")
            elif fragment:
                COUNTS["dist_nonhtml_fragments_skipped"] += 1
    # CSS resources are not HTML attributes, but a missing font/image would
    # otherwise pass an HTML-only check. This remains an offline existence check.
    for path in sorted(DIST.rglob("*.css")):
        if not contained(path, DIST):
            issue("dist_boundary", path, "CSS symlink resolves outside dist.")
            continue
        text = read_text(path)
        if text is None:
            continue
        COUNTS["dist_css_files"] += 1
        for raw in re.findall(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", text):
            result = resolve_link(path, raw, DIST)
            if result is not None:
                target, _ = result
                COUNTS["dist_css_resources"] += 1
                if not target.exists():
                    issue("css_local_target", path, f"CSS resource missing: {relative(target)}")
    for extension, targets in downloads.items():
        if not targets:
            issue("required_download", DIST, f"No local {extension} download link found in generated HTML.")
        for target in targets:
            if not target.is_file():
                issue("required_download", target, f"Linked {extension} download does not exist as a file.")
                continue
            COUNTS["dist_download_files"] += 1
            try:
                if extension == ".pdf":
                    with target.open("rb") as handle:
                        if handle.read(5) != b"%PDF-":
                            issue("download_format", target, "Linked PDF lacks a PDF file header.")
                elif not zipfile.is_zipfile(target):
                    issue("download_format", target, "Linked ZIP is not a readable ZIP container.")
                else:
                    with zipfile.ZipFile(target) as archive:
                        if not archive.infolist():
                            issue("download_format", target, "Linked ZIP is empty.")
                        if archive.testzip() is not None:
                            issue("download_format", target, "ZIP member failed CRC validation.")
            except (OSError, zipfile.BadZipFile) as exc:
                issue("download_format", target, f"Download could not be read ({type(exc).__name__}).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only", action="store_true", help="Explicitly skip dist HTML/download checks.")
    args = parser.parse_args()
    files = source_files()
    markdown = check_sources(files)
    check_ledgers(markdown)
    check_offertrail(markdown)
    if args.source_only:
        SKIPPED.append({"check": "dist", "reason": "Explicit --source-only mode; no site/download pass is claimed."})
    else:
        check_dist()
    report = {
        "schema_version": 1,
        "project": "chinese-international-student-product-jobs",
        "generated_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "scope": "source-only" if args.source_only else "source-and-dist",
        "assessment_kind": "结构检查，非真人可用性测试",
        "status": "pass" if not FAILURES else "fail",
        "counts": dict(sorted(COUNTS.items())),
        "failures": FAILURES,
        "warnings": WARNINGS,
        "skipped": SKIPPED,
        "limits": [
            "No external URLs are fetched; HTTPS and official-source metadata do not prove authenticity or current accuracy.",
            "Markdown local target existence is checked; Markdown fragments are intentionally not checked.",
            "Source-ID checks use bracket citations, explicit source labels and source headings in content/ and README.md, not arbitrary H/S/R case labels.",
            "HTML checks cover static local references, fragments and duplicate IDs; generated runtime DOM, JavaScript behavior and real-user usability require separate tests.",
            "OfferTrail checks enforce fixed teaching fixtures and selected disclosure phrases; they do not replace human review of every claim.",
            "PDF header and ZIP container checks do not replace PDF rendering or page-by-page visual inspection.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "scope": report["scope"], "assessment_kind": report["assessment_kind"], "failures": len(FAILURES), "warnings": len(WARNINGS), "report": relative(REPORT), "counts": report["counts"]}, ensure_ascii=False))
    for item in FAILURES[:40]:
        print(f"FAIL [{item['check']}] {item['path']}: {item['detail']}")
    if len(FAILURES) > 40:
        print(f"Additional failures are recorded in {relative(REPORT)}.")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
