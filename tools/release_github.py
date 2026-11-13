#!/usr/bin/env python3
"""Publish only the reviewed v1.0.0 assets of the fixed repository.

--check-only is local, read-only and does not inspect authentication. Publishing
requires this repository's main GitHub Actions checkout and its GITHUB_TOKEN,
passed as GH_TOKEN by release.yml. No tag, release text or asset is overwritten.

Official API references checked 2026-11-13:
https://docs.github.com/en/rest/releases/releases
https://docs.github.com/en/rest/releases/assets
https://docs.github.com/en/rest/git/refs
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = "AIPMAndy/chinese-international-student-product-jobs"
TAG = "v1.0.0"
TITLE = "中国留学生产品岗位求职保姆级攻略 v1.0.0"
ASSETS = (
    "product-jobs-guide-v1.0.0.pdf",
    "product-jobs-workbook-v1.0.0.zip",
    "product-jobs-source-v1.0.0.zip",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(name: str) -> dict:
    return json.loads((ROOT / "verification" / name).read_text(encoding="utf-8"))


def local_checks() -> dict:
    result = {}
    for name in ASSETS:
        path, site = ROOT / "downloads" / name, ROOT / "dist/downloads" / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size > 0,
                "Missing or invalid committed download: " + name)
        require(site.is_file() and not site.is_symlink() and digest(path) == digest(site),
                "Root and dist download bytes differ: " + name)
        result[name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
        if name.endswith(".zip"):
            with zipfile.ZipFile(path) as archive:
                require(archive.testzip() is None, "ZIP CRC failed: " + name)
                manifests = [n for n in archive.namelist() if n.endswith("/PACKAGE-MANIFEST.json")]
                require(len(manifests) == 1, "ZIP manifest missing or ambiguous: " + name)
                manifest_path = manifests[0]
                prefix = manifest_path.rsplit("/", 1)[0] + "/"
                manifest = json.loads(archive.read(manifest_path))
                require(manifest.get("version") == "1.0.0" and bool(manifest.get("files")),
                        "ZIP manifest identity is incomplete: " + name)
                for item in manifest["files"]:
                    data = archive.read(prefix + item["path"])
                    require(len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"],
                            "ZIP manifest mismatch: " + item["path"])
    pdf = ROOT / "downloads" / ASSETS[0]
    require(pdf.read_bytes().startswith(b"%PDF-"), "The PDF signature is invalid.")
    integrity, metadata, coverage = record("integrity.json"), record("pdf-metadata.json"), record("pdf-visual-coverage.json")
    require(integrity.get("status") == "pass" and integrity.get("scope") == "source-and-dist"
            and integrity.get("failures") == [], "Full source-and-dist integrity acceptance is required.")
    for field in ("pages", "bytes", "selectable_text_characters"):
        require(type(metadata.get(field)) is int and metadata[field] > 0, "Missing PDF field: " + field)
    for field in ("blank_or_nearly_blank_pages", "text_outside_page", "missing_section_titles", "missing_images"):
        require(metadata.get(field) == [], "Unresolved PDF acceptance field: " + field)
    require(metadata["bytes"] == result[ASSETS[0]]["bytes"], "PDF metadata byte count differs.")
    require(coverage.get("status") == "pass" and coverage.get("pages") == metadata["pages"]
            and coverage.get("pdf_sha256") == result[ASSETS[0]]["sha256"]
            and coverage.get("inspected_pages") == list(range(1, metadata["pages"] + 1)),
            "Visual review does not cover this exact PDF and every page.")
    for name in ["VALIDATION.md", *coverage.get("records", [])]:
        path = (ROOT / "verification" / name).resolve()
        require(path.is_relative_to(ROOT / "verification") and path.is_file() and path.stat().st_size > 0,
                "Missing acceptance record: " + name)
    require(bool(coverage.get("records")), "Individual visual review records are missing.")
    return result


def command(args: list[str], *, data: str | None = None, missing_ok: bool = False) -> str | None:
    # gh always receives an explicit host/repository. Never print authentication.
    proc = subprocess.run(args, input=data, capture_output=True, text=True, cwd=ROOT)
    if proc.returncode:
        if missing_ok and "(HTTP 404)" in proc.stderr:
            return None
        raise RuntimeError("GitHub/local command failed without overwriting anything: "
                           + " ".join(args[:4]) + " (exit " + str(proc.returncode) + "). "
                           + proc.stderr.strip()[:800])
    return proc.stdout


def api(suffix: str = "", *, method: str = "GET", body: dict | None = None,
        missing_ok: bool = False, paginate: bool = False):
    endpoint = "repos/" + REPO + ("/" + suffix if suffix else "")
    args = ["gh", "api", "--hostname", "github.com", "--method", method, endpoint,
            "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2026-03-10"]
    if body is not None:
        args += ["--input", "-"]
    if paginate:
        args += ["--paginate", "--slurp"]
    output = command(args, data=json.dumps(body) if body is not None else None, missing_ok=missing_ok)
    if output is None:
        return None
    value = json.loads(output)
    return [item for page in value for item in page] if paginate else value


def find_release() -> dict | None:
    matches = [r for r in api("releases?per_page=100", paginate=True) if r.get("tag_name") == TAG]
    require(len(matches) <= 1, "Multiple releases use v1.0.0; refusing to choose or overwrite.")
    return matches[0] if matches else None


def tag_commit() -> str | None:
    ref = api("git/ref/tags/" + TAG, missing_ok=True)
    return api("commits/" + TAG)["sha"] if ref is not None else None


def verify_assets(release: dict, expected: dict, *, complete: bool) -> set[str]:
    assets = api("releases/" + str(release["id"]) + "/assets?per_page=100", paginate=True)
    names = [a["name"] for a in assets]
    require(len(names) == len(set(names)) and set(names).issubset(expected),
            "Existing release has duplicate or unexpected assets; refusing to replace or delete them.")
    require(not complete or set(names) == set(expected), "Published release assets are incomplete.")
    with tempfile.TemporaryDirectory(prefix="product-jobs-release-check-") as temporary:
        for asset in assets:
            name, wanted = asset["name"], expected[asset["name"]]
            require(asset.get("state") == "uploaded" and asset.get("size") == wanted["bytes"],
                    "Existing asset state/size differs; no overwrite: " + name)
            if asset.get("digest"):
                require(asset["digest"] == "sha256:" + wanted["sha256"], "Existing asset digest differs: " + name)
            command(["gh", "release", "download", TAG, "--repo", REPO,
                     "--pattern", name, "--dir", temporary])
            require(digest(Path(temporary) / name) == wanted["sha256"],
                    "Downloaded release asset bytes differ; no overwrite: " + name)
    return set(names)


def publish(expected: dict) -> dict:
    require(os.environ.get("GITHUB_ACTIONS") == "true"
            and os.environ.get("GITHUB_REPOSITORY") == REPO
            and os.environ.get("GITHUB_REF") == "refs/heads/main",
            "Publishing is only allowed in this fixed repository's main GitHub Actions run.")
    sha = os.environ.get("GITHUB_SHA", "")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "GITHUB_SHA is missing or invalid.")
    require(command(["git", "rev-parse", "HEAD"]).strip() == sha, "Checkout differs from the workflow commit.")
    require(bool(os.environ.get("GH_TOKEN")), "The workflow GITHUB_TOKEN must be supplied as GH_TOKEN.")
    os.environ["GH_HOST"] = "github.com"
    os.environ["GH_PROMPT_DISABLED"] = "1"
    repo = api()
    require(repo.get("full_name") == REPO and not repo.get("private") and not repo.get("archived")
            and repo.get("default_branch") == "main", "Repository identity/public main state differs.")
    require(api("git/ref/heads/main")["object"]["sha"] == sha,
            "main advanced after this run started; publish from the current main commit instead.")
    existing_tag = tag_commit()
    require(existing_tag is None or existing_tag == sha,
            "v1.0.0 already points to a different commit; it will never be moved.")
    release = find_release()
    if release is not None:
        require(existing_tag == sha and release.get("name") == TITLE and not release.get("prerelease"),
                "Existing release identity differs; no release text or tag will be replaced.")
        present = verify_assets(release, expected, complete=not release.get("draft", False))
    else:
        present = set()
        if existing_tag is None:
            api("git/refs", method="POST", body={"ref": "refs/tags/" + TAG, "sha": sha})
        require(tag_commit() == sha, "New tag read-back differs; stopping before release creation.")
        notes = ("作者：AI 酋长 Andy。完整中文攻略、真实岗位 JD 拆解、地区路径、OfferTrail 教学模拟、"
                 "15 份模板、中英文申请材料与面试训练。\n\n"
                 "免费内容完整开放。模拟案例没有真实访谈、上线、增长或录用结果；不承诺录用或涨薪。\n\n"
                 "微信：AIPMAndy｜公众号：AI酋长Andy\n\n"
                 "个人官网：https://metaver.vip/ ｜公司官网：https://www.a6no1.cn/\n\n"
                 "此 Release 独立于 GitHub Pages 部署状态。提交：" + sha + "\n\n"
                 + "\n".join("- " + name + " SHA256: `" + item["sha256"] + "`" for name, item in expected.items()))
        release = api("releases", method="POST", body={"tag_name": TAG, "target_commitish": sha,
                      "name": TITLE, "body": notes, "draft": True, "prerelease": False})
    if release.get("draft"):
        for name in ASSETS:
            if name not in present:
                # gh refuses an existing name. Never use --clobber or deletion.
                command(["gh", "release", "upload", TAG, str(ROOT / "downloads" / name), "--repo", REPO])
        verify_assets(release, expected, complete=True)
        require(tag_commit() == sha, "Tag changed during upload; refusing to publish the draft.")
        api("releases/" + str(release["id"]), method="PATCH", body={"draft": False})
    final = find_release()
    require(final is not None and not final.get("draft") and tag_commit() == sha,
            "Published release/tag read-back failed; no success is claimed.")
    verify_assets(final, expected, complete=True)
    return {"status": "published-and-downloads-verified", "repository": REPO, "tag": TAG,
            "commit_sha": sha, "release_url": final["html_url"], "assets": expected,
            "pages_status": "independent; this workflow does not configure or verify Pages"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Read-only local acceptance; no credentials or network.")
    args = parser.parse_args()
    expected = local_checks()
    result = {"status": "local-checks-passed", "assets": expected} if args.check_only else publish(expected)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print("Release stopped; no unverified publication success is claimed. " + str(error), file=sys.stderr)
        raise SystemExit(1)
