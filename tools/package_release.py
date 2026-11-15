#!/usr/bin/env python3
"""Package this project without Git/Sites state, secrets or render intermediates.

Default: create the workbook ZIP; create the source ZIP only when the final PDF
is available. --require-pdf makes a missing final PDF a hard failure.

--export-dir PATH exports a fresh source tree instead of creating ZIPs. Add
--include-dist to copy the already reviewed dist/ and the existing release ZIPs
for the fixed-target GitHub publisher. It never rebuilds dist or PDF.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from html.parser import HTMLParser
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
from urllib.parse import unquote, urlsplit
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"
PROJECT = "chinese-international-student-product-jobs"
DATE = "2026-11-13"
DOWNLOADS = ROOT / "downloads"
PDF_NAME = f"product-jobs-guide-v{VERSION}.pdf"
WORKBOOK_NAME = f"product-jobs-workbook-v{VERSION}.zip"
SOURCE_NAME = f"product-jobs-source-v{VERSION}.zip"
FORMAL_URL = "https://aipmandy.github.io/chinese-international-student-product-jobs/"
SOURCE_DIRS = {".github", "content", "templates", "examples", "prototypes", "assets", "site", "research", "tools", "verification"}
ROOT_FILES = {"README.md", "PUBLISH.md", "DEPLOYMENT.md", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE", "CONTENT_LICENSE.md", "package.json", "package-lock.json", "requirements.txt", "requirements-dev.txt", ".gitignore", ".gitattributes"}
EXCLUDED_PARTS = {".git", ".openai", "node_modules", ".venv", ".cache", "__pycache__", "output", "tmp", "pdf-pages", "pdf-contact-sheets", "browser-artifacts", "test-results", "playwright-report", ".ssh", ".npm"}
ALLOWED_SUFFIXES = {".md", ".json", ".csv", ".html", ".css", ".js", ".mjs", ".py", ".sh", ".yml", ".yaml", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".pdf", ".lock", ".xml"}
SECRET_FILENAME = re.compile(r"(^\.env($|\.)|(^|[._-])(credentials?|secrets?|auth[-_]?tokens?)([._-]|$)|^id_(rsa|ed25519)$|\.(pem|key|p12|pfx)$|^\.(npmrc|netrc)$|^hosts\.yml$)", re.I)
SECRET_BYTES = [re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{30,}\b"), re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")]


def fail(message: str) -> None:
    raise RuntimeError(message)


def allowed(path: Path, *, allow_archives: bool = False) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if SECRET_FILENAME.search(path.name) or path.name in {".DS_Store", "CNAME"}:
        return False
    if path.is_symlink():
        fail(f"Refusing a symlink in release input: {relative.as_posix()}")
    if not path.is_file():
        return False
    if path.name in ROOT_FILES or path.name == ".nojekyll":
        return True
    return path.suffix.lower() in ALLOWED_SUFFIXES or (allow_archives and path.suffix.lower() == ".zip")


def read_checked(path: Path) -> bytes:
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        fail("Release input must stay inside this repository without symlinks.")
    data = path.read_bytes()
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".zip"}:
        if any(pattern.search(data) for pattern in SECRET_BYTES):
            fail(f"Possible credential/private-key material in {path.relative_to(ROOT).as_posix()}; no archive written.")
    return data


def final_pdf() -> Path | None:
    for path in (DOWNLOADS / PDF_NAME, ROOT / "output" / "pdf" / PDF_NAME):
        if path.is_file():
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                fail("Final PDF resolves outside this repository.")
            with path.open("rb") as handle:
                if handle.read(5) != b"%PDF-":
                    fail("The final PDF candidate has no PDF header.")
            if path.stat().st_size < 1000:
                fail("Final PDF is unexpectedly small; complete PDF validation first.")
            return path
    return None


def source_payload(pdf: Path | None) -> dict[str, bytes]:
    payload = {}
    for name in sorted(ROOT_FILES):
        path = ROOT / name
        if path.is_file() and allowed(path):
            payload[name] = read_checked(path)
    for dirname in sorted(SOURCE_DIRS):
        folder = ROOT / dirname
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*")):
            if allowed(path):
                payload[path.relative_to(ROOT).as_posix()] = read_checked(path)
    if pdf:
        payload[f"downloads/{PDF_NAME}"] = read_checked(pdf)
    required = {"README.md", "package.json", "tools/build_site.mjs", "tools/lib.mjs", "tools/render_pdf.py", "tools/package_release.py", "tools/check_integrity.py", ".github/workflows/pages.yml", "DEPLOYMENT.md"}
    missing = sorted(required - payload.keys())
    if missing:
        fail("Source export is incomplete: " + ", ".join(missing))
    return payload


def workbook_readme() -> bytes:
    return f"""# 中国留学生产品岗位求职｜完整样例与可编辑模板

作者：AI酋长Andy｜版本 {VERSION}｜{DATE}

本包含 15 份模板及填写说明、12 个样例文件、完整案例章节、可本地运行的原型与所需图像。所有 OfferTrail 申请者、雇主和六条情境均为教学模拟；没有真实访谈、上线、增长或录用结果。

1. 先打开 [index.html](index.html)，或直接用浏览器打开 [原型](prototypes/offertrail.html)。无需账号、网络服务或真实申请资料。
2. 阅读 [样例入口](examples/README.md) 和 [贯穿案例](content/case/06-end-to-end-case.md)。
3. 复制 [模板](templates/README.md)，删除教学行，填写本人真实完成的工作。CSV 使用 UTF-8 编码。
4. 原型仅保存当前页面的模拟状态；核对完成不等于实际投递，也不验证工作许可。

Markdown 可在文本编辑器中阅读和修改。文件夹结构应整体保留，避免相对链接失效。

正式网站目标：{FORMAL_URL}。仅在远端部署与实际访问通过后才可视为已上线；本包不证明线上状态。

微信：AIPMAndy｜公众号：AI酋长Andy  
个人官网：https://metaver.vip/ ｜公司官网：https://www.a6no1.cn/

完整免费开放。咨询可用于岗位定位、作品集诊断和模拟面试，不承诺录用或涨薪。

代码 MIT；原创内容 CC BY 4.0，详见随包许可。PACKAGE-MANIFEST.json 记录文件哈希与包范围，不是用户研究或上线证明。
""".encode("utf-8")


def workbook_index() -> bytes:
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>产品求职练习包 · AI酋长Andy</title><style>body{font-family:system-ui,sans-serif;background:#f5f5ee;color:#243b2e;max-width:760px;padding:44px 22px;margin:auto;line-height:1.8}h1{font-size:32px}a{color:#2e5146}li{margin:14px 0}.note{background:white;padding:18px;border:1px solid #d9dfd2;border-radius:12px}footer{margin-top:40px;font-size:14px}</style><h1>把产品判断，落到材料上。</h1><p>完整样例与可编辑模板 · v1.0.0 · 2026-11-13</p><div class="note">OfferTrail 为教学模拟。没有真实访谈、上线、增长或录用结果。原型不发送申请，不判断工作许可。</div><ul><li><a href="prototypes/offertrail.html">运行 OfferTrail 交互原型</a></li><li><a href="examples/README.md">完整样例阅读顺序</a></li><li><a href="content/case/06-end-to-end-case.md">十步贯穿案例</a></li><li><a href="content/case/07-application-materials.md">中英文申请材料方法</a></li><li><a href="templates/README.md">15 份模板与填写说明</a></li><li><a href="README.md">离线使用说明</a></li></ul><p>Markdown 用文本编辑器阅读；CSV 用电子表格软件打开。请保留整个文件夹结构。</p><footer>作者：AI酋长Andy · 微信 AIPMAndy · 公众号 AI酋长Andy<br><a href="https://metaver.vip/">个人官网</a> · <a href="https://www.a6no1.cn/">公司官网</a><p>完整免费开放；咨询不承诺录用或涨薪。</p></footer></html>""".encode("utf-8")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.destinations = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src", "poster"} and value:
                self.destinations.append(value)


def workbook_payload() -> tuple[dict[str, bytes], dict]:
    payload = {"README.md": workbook_readme(), "index.html": workbook_index()}
    for dirname in ("templates", "examples", "prototypes", "content/case", "assets"):
        for path in sorted((ROOT / dirname).rglob("*")):
            if allowed(path):
                payload[path.relative_to(ROOT).as_posix()] = read_checked(path)
    for name in ("LICENSE", "CONTENT_LICENSE.md"):
        path = ROOT / name
        if path.is_file():
            payload[name] = read_checked(path)
    counts = {"templates_excluding_readme": sum(1 for name in payload if name.startswith("templates/") and name != "templates/README.md"), "example_files_including_readme": sum(1 for name in payload if name.startswith("examples/"))}
    if counts["templates_excluding_readme"] < 15 or counts["example_files_including_readme"] < 12:
        fail("Workbook requires at least 15 templates and 12 example files.")
    # Resolve the transitive local dependencies of the case. This keeps relative
    # references intact instead of bundling only the attractive final pages.
    spec = importlib.util.spec_from_file_location("release_integrity", ROOT / "tools" / "check_integrity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pending = list(payload)
    seen = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        data = payload[name]
        links = []
        if name.endswith(".md"):
            links.extend(module.markdown_destinations(data.decode("utf-8-sig")))
        elif name.endswith(".html"):
            parsed = Links(); parsed.feed(data.decode("utf-8-sig")); links.extend(parsed.destinations)
        for raw in links:
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (ROOT / Path(name).parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT):
                fail("Workbook dependency escapes this repository.")
            relative = target.relative_to(ROOT).as_posix()
            if relative in payload:
                continue
            if not target.is_file() or not allowed(target):
                fail(f"Workbook dependency is missing or excluded: {relative}")
            payload[relative] = read_checked(target)
            pending.append(relative)
    return payload, counts


def manifest(kind: str, payload: dict[str, bytes], extra: dict | None = None) -> bytes:
    value = {"project": PROJECT, "version": VERSION, "date": DATE, "package_kind": kind, "status_note": "打包记录；不证明已发布、真人可用性或业务结果", "excluded": sorted(EXCLUDED_PARTS), "files": [{"path": name, "bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in sorted(payload.items())]}
    if extra:
        value.update(extra)
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_zip(destination: Path, prefix: str, payload: dict[str, bytes], kind: str, extra: dict | None = None) -> dict:
    entries = dict(payload)
    entries["PACKAGE-MANIFEST.json"] = manifest(kind, payload, extra)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(f"{prefix}/{name}", date_time=(2026, 11, 13, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                mode = 0o755 if name.endswith((".sh", ".py")) else 0o644
                info.external_attr = (stat.S_IFREG | mode) << 16
                archive.writestr(info, data)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                fail("ZIP CRC validation failed.")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"file": destination.relative_to(ROOT).as_posix(), "entries": len(entries), "bytes": destination.stat().st_size, "sha256": sha256(destination.read_bytes()).hexdigest()}


def export_tree(destination: Path, payload: dict[str, bytes], include_dist: bool) -> dict:
    destination = destination.expanduser().absolute()
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        fail("Export destination must be absent or an empty directory.")
    if destination.resolve().is_relative_to(ROOT) or ROOT.is_relative_to(destination.resolve()):
        fail("Export destination must be outside the source repository and not its ancestor.")
    if include_dist:
        dist = ROOT / "dist"
        if not (dist / "index.html").is_file():
            fail("Reviewed dist/index.html is required for a publishing export.")
        for name in (PDF_NAME, WORKBOOK_NAME, SOURCE_NAME):
            for path in (DOWNLOADS / name, dist / "downloads" / name):
                if not path.is_file() or not path.stat().st_size:
                    fail("Publishing export requires all three nonempty downloads in root and dist.")
            if sha256((DOWNLOADS / name).read_bytes()).digest() != sha256((dist / "downloads" / name).read_bytes()).digest():
                fail(f"Root and reviewed dist download differ: {name}; rebuild and validate before publishing.")
            payload[f"downloads/{name}"] = read_checked(DOWNLOADS / name)
        for path in sorted(dist.rglob("*")):
            if allowed(path, allow_archives=True):
                payload[path.relative_to(ROOT).as_posix()] = read_checked(path)
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(payload.items()):
        output = destination / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        if name.endswith((".sh", ".py")):
            output.chmod(0o755)
    return {"mode": "fresh-source-export", "files": len(payload), "includes_reviewed_dist": include_dist, "contains_git_or_sites_state": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-pdf", action="store_true")
    parser.add_argument("--export-dir", type=Path)
    parser.add_argument("--include-dist", action="store_true", help="Only with --export-dir; copy reviewed dist without rebuilding.")
    args = parser.parse_args()
    if args.include_dist and not args.export_dir:
        parser.error("--include-dist requires --export-dir")
    try:
        package = json.loads((ROOT / "package.json").read_text())
        if package.get("name") != PROJECT or package.get("version") != VERSION:
            fail("Project name/version differs from the fixed release target.")
        pdf = final_pdf()
        if args.require_pdf and pdf is None:
            fail("Final PDF is absent. Finish rendering and validation before a complete release.")
        if args.export_dir:
            result = export_tree(args.export_dir, source_payload(pdf), args.include_dist)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        DOWNLOADS.mkdir(exist_ok=True)
        workbook, counts = workbook_payload()
        outputs = [write_zip(DOWNLOADS / WORKBOOK_NAME, f"product-jobs-workbook-v{VERSION}", workbook, "editable-workbook", counts)]
        skipped = []
        if pdf is not None:
            outputs.append(write_zip(DOWNLOADS / SOURCE_NAME, f"{PROJECT}-v{VERSION}", source_payload(pdf), "rebuildable-source", {"includes_final_pdf": True, "dist_note": "dist is regenerated by npm run build; release ZIPs are regenerated by tools/package_release.py"}))
        else:
            skipped.append("Final PDF not yet available: complete source ZIP was not created. Rerun after PDF validation.")
        print(json.dumps({"status": "complete" if not skipped else "workbook-only", "version": VERSION, "outputs": outputs, "counts": counts, "skipped": skipped, "published": False}, ensure_ascii=False))
        return 0
    except (RuntimeError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Packaging stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
