#!/usr/bin/env bash
# Fixed-target publisher. It never uses this working tree's Git/Sites remote.
# Read ../DEPLOYMENT.md and ../PUBLISH.md before running. No deployment is
# performed merely by creating this script.
set -euo pipefail

readonly TARGET_REPO='AIPMAndy/chinese-international-student-product-jobs'
readonly TARGET_OWNER='AIPMAndy'
readonly TARGET_SLUG='chinese-international-student-product-jobs'
readonly TARGET_REMOTE='https://github.com/AIPMAndy/chinese-international-student-product-jobs.git'
readonly TARGET_URL='https://aipmandy.github.io/chinese-international-student-product-jobs/'
readonly RELEASE_TAG='v1.0.0'
readonly PROJECT_TITLE='中国留学生产品岗位求职保姆级攻略'
readonly PDF_NAME='product-jobs-guide-v1.0.0.pdf'
readonly WORKBOOK_NAME='product-jobs-workbook-v1.0.0.zip'
readonly SOURCE_NAME='product-jobs-source-v1.0.0.zip'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
PUBLISH_STAGE='not-started'
PUBLISH_TMP=''
export GH_HOST='github.com'
export GIT_TERMINAL_PROMPT='0'

die() { printf '%s\n' "$*" >&2; exit 1; }

on_exit() {
  local status=$?
  if [[ $status -ne 0 ]]; then
    printf 'Publication stopped. Last completed stage: %s. No success is claimed.\n' "$PUBLISH_STAGE" >&2
    if [[ -n "$PUBLISH_TMP" ]]; then
      printf 'The isolated checkout and public verification files remain at: %s\n' "$PUBLISH_TMP" >&2
    fi
  elif [[ -n "$PUBLISH_TMP" && -d "$PUBLISH_TMP" ]]; then
    case "$(basename -- "$PUBLISH_TMP")" in
      product-jobs-publish.*) rm -rf -- "$PUBLISH_TMP" ;;
    esac
  fi
}
trap on_exit EXIT

if [[ $# -gt 0 ]]; then
  if [[ $# -eq 1 && "$1" == '--help' ]]; then
    printf '%s\n' 'Publish only AIPMAndy/chinese-international-student-product-jobs.' 'No target/version overrides. Requires authenticated AIPMAndy, validated dist and PDF/ZIP files.' 'The script exports a fresh checkout, refuses conflicting repositories/tags/assets, and never force-pushes.'
    exit 0
  fi
  die 'This script accepts no repository, branch, remote or version overrides.'
fi

for program in gh git python3 curl; do
  command -v "$program" >/dev/null || die "Required command is unavailable: $program"
done
[[ -f "$PROJECT_ROOT/AGENTS.md" && -f "$PROJECT_ROOT/DEPLOYMENT.md" ]] || die 'Project deployment instructions are missing.'

# Authentication is checked before any repository creation or remote mutation.
if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  die 'GitHub CLI is not authenticated for github.com. Authenticate AIPMAndy with gh auth login --hostname github.com, then rerun. No repository was created and no push was attempted.'
fi
ACTUAL_LOGIN="$(gh api --hostname github.com user --jq '.login')"
[[ "$ACTUAL_LOGIN" == "$TARGET_OWNER" ]] || die 'The authenticated GitHub account is not AIPMAndy; no remote write was attempted.'
ACCOUNT_ID="$(gh api --hostname github.com user --jq '.id')"
[[ "$ACCOUNT_ID" =~ ^[0-9]+$ ]] || die 'Could not read the authenticated account ID.'
PUBLISH_STAGE='authenticated-as-AIPMAndy'

PUBLISH_TMP="$(mktemp -d "${TMPDIR:-/tmp}/product-jobs-publish.XXXXXXXX")"
readonly EXPORT_DIR="$PUBLISH_TMP/export"
readonly CHECKOUT_DIR="$PUBLISH_TMP/checkout"

# Only reviewed source and committed-site candidates are copied. There is no
# build or PDF generation here, so the deployed bytes stay reviewable.
python3 -B "$PROJECT_ROOT/tools/package_release.py" --require-pdf --export-dir "$EXPORT_DIR" --include-dist
(
  cd -- "$EXPORT_DIR"
  python3 -B tools/check_pages_links.py \
    --repo-name "$TARGET_SLUG" --owner "$TARGET_OWNER" \
    --require "downloads/$PDF_NAME" \
    --require "downloads/$WORKBOOK_NAME" \
    --require "downloads/$SOURCE_NAME"
)
python3 - "$EXPORT_DIR" "$PDF_NAME" <<'PY'
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
meta = json.loads((root / 'package.json').read_text())
if meta.get('name') != 'chinese-international-student-product-jobs' or meta.get('version') != '1.0.0':
    raise SystemExit('Export identity/version mismatch.')
record = json.loads((root / 'verification/integrity.json').read_text())
if record.get('status') != 'pass' or record.get('scope') != 'source-and-dist':
    raise SystemExit('A passing full source-and-dist integrity report is required. Run the full validation before publishing.')
pdf_meta = json.loads((root / 'verification/pdf-metadata.json').read_text())
pdf_path = root / 'downloads' / sys.argv[2]
for field in ('pages', 'bytes', 'selectable_text_characters'):
    if type(pdf_meta.get(field)) is not int or pdf_meta[field] <= 0:
        raise SystemExit('PDF structural validation is missing a positive ' + field + ' value.')
for field in ('blank_or_nearly_blank_pages', 'text_outside_page', 'missing_section_titles', 'missing_images'):
    if not isinstance(pdf_meta.get(field), list) or pdf_meta[field]:
        raise SystemExit('PDF structural validation is incomplete or has unresolved ' + field + '.')
if not pdf_path.is_file() or pdf_path.stat().st_size != pdf_meta['bytes']:
    raise SystemExit('The exported PDF does not match the validated PDF byte count.')
if not (root / 'verification/VALIDATION.md').is_file():
    raise SystemExit('The final human-readable validation record is missing.')
PY
PUBLISH_STAGE='fresh-export-and-static-checks-passed'

api_read() {
  local endpoint="$1" destination="$2"
  if gh api --hostname github.com "$endpoint" >"$destination" 2>"$PUBLISH_TMP/api-error.txt"; then
    return 0
  fi
  if [[ "$(<"$PUBLISH_TMP/api-error.txt")" == *'(HTTP 404)'* ]]; then
    return 1
  fi
  die 'GitHub read failed for a reason other than a confirmed 404. Stopping without guessing that the resource is absent.'
}

REPO_EXISTED='true'
if ! api_read "repos/$TARGET_REPO" "$PUBLISH_TMP/repository.json"; then
  REPO_EXISTED='false'
  gh repo create "$TARGET_REPO" --public --description "$PROJECT_TITLE" --disable-wiki
  api_read "repos/$TARGET_REPO" "$PUBLISH_TMP/repository.json" || die 'Created repository could not be read back.'
fi
python3 - "$PUBLISH_TMP/repository.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
if r.get('full_name', '').lower() != 'aipmandy/chinese-international-student-product-jobs':
    raise SystemExit('Repository identity differs from the fixed target.')
if r.get('private') or r.get('archived') or r.get('fork'):
    raise SystemExit('Existing target is private, archived or a fork; it will not be changed automatically.')
if not r.get('permissions', {}).get('push'):
    raise SystemExit('The authenticated account has no confirmed push permission.')
PY
PUBLISH_STAGE='fixed-public-target-read-back'

gh_git() {
  env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE \
    git -c credential.helper= -c 'credential.https://github.com.helper=!gh auth git-credential' "$@"
}
gh_git clone --no-recurse-submodules "$TARGET_REMOTE" "$CHECKOUT_DIR"
[[ "$(gh_git -C "$CHECKOUT_DIR" remote get-url origin)" == "$TARGET_REMOTE" ]] || die 'The isolated checkout remote is not the fixed GitHub target.'

if gh_git -C "$CHECKOUT_DIR" rev-parse --verify HEAD >/dev/null 2>&1; then
  DEFAULT_BRANCH="$(python3 - "$PUBLISH_TMP/repository.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1])).get('default_branch', ''))
PY
)"
  [[ "$DEFAULT_BRANCH" == 'main' ]] || die 'Existing target does not use main; inspect its purpose before proceeding.'
  gh_git -C "$CHECKOUT_DIR" checkout main
  python3 - "$CHECKOUT_DIR" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
readme = root / 'README.md'
package = root / 'package.json'
if not readme.is_file() or not package.is_file():
    raise SystemExit('Existing repository lacks the project identity files; no content will be overwritten.')
if '中国留学生产品岗位求职保姆级攻略' not in readme.read_text(encoding='utf-8')[:1000]:
    raise SystemExit('Existing repository README has a different purpose.')
if json.loads(package.read_text()).get('name') != 'chinese-international-student-product-jobs':
    raise SystemExit('Existing repository package identity differs from this project.')
PY
else
  if [[ "$REPO_EXISTED" == 'true' ]]; then
    python3 - "$PUBLISH_TMP/repository.json" <<'PY'
import json, sys
if '中国留学生产品岗位求职' not in (json.load(open(sys.argv[1])).get('description') or ''):
    raise SystemExit('Existing empty repository has no matching purpose description; it will not be populated automatically.')
PY
  fi
  gh_git -C "$CHECKOUT_DIR" symbolic-ref HEAD refs/heads/main
fi

# Copy into a clone of the correct target. No .git is copied, and unknown remote
# files are preserved. Symlink destinations are refused rather than followed.
python3 - "$EXPORT_DIR" "$CHECKOUT_DIR" <<'PY'
from pathlib import Path
import shutil, sys
source, target = map(Path, sys.argv[1:])
for path in sorted(source.rglob('*')):
    if not path.is_file():
        continue
    rel = path.relative_to(source)
    if '.git' in rel.parts or '.openai' in rel.parts or path.is_symlink():
        raise SystemExit('Unexpected Git/Sites state or symlink in export.')
    destination = target / rel
    if any(parent.is_symlink() for parent in [destination, *destination.parents] if parent != target.parent):
        raise SystemExit('Existing checkout contains a symlink on an export destination.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
PY
gh_git -C "$CHECKOUT_DIR" config user.name 'AI 酋长 Andy'
gh_git -C "$CHECKOUT_DIR" config user.email "${ACCOUNT_ID}+${TARGET_OWNER}@users.noreply.github.com"
gh_git -C "$CHECKOUT_DIR" add --all
# ZIPs are intentionally ignored in normal source work but must accompany this
# exact release and its already reviewed dist. This is add -f, never push -f.
gh_git -C "$CHECKOUT_DIR" add -f -- \
  "downloads/$PDF_NAME" "downloads/$WORKBOOK_NAME" "downloads/$SOURCE_NAME" \
  dist

HAS_TAG='false'
if gh_git -C "$CHECKOUT_DIR" show-ref --verify --quiet "refs/tags/$RELEASE_TAG"; then
  HAS_TAG='true'
  gh_git -C "$CHECKOUT_DIR" diff --cached --quiet || die 'v1.0.0 already exists and the proposed source differs. The script will not rewrite the tag or publish changed files under the same release.'
  [[ "$(gh_git -C "$CHECKOUT_DIR" rev-parse "$RELEASE_TAG^{commit}")" == "$(gh_git -C "$CHECKOUT_DIR" rev-parse HEAD)" ]] || die 'Existing release tag is not the current main commit; inspect the version before proceeding.'
fi
if ! gh_git -C "$CHECKOUT_DIR" diff --cached --quiet; then
  gh_git -C "$CHECKOUT_DIR" -c commit.gpgsign=false commit -m 'Publish product jobs guide v1.0.0 with verified site, PDF and workbook'
fi
PUBLISHED_SHA="$(gh_git -C "$CHECKOUT_DIR" rev-parse HEAD)"
[[ "$(gh_git -C "$CHECKOUT_DIR" remote get-url origin)" == "$TARGET_REMOTE" ]] || die 'Remote identity changed before push.'
gh_git -C "$CHECKOUT_DIR" push origin HEAD:refs/heads/main
REMOTE_SHA="$(gh api --hostname github.com "repos/$TARGET_REPO/commits/main" --jq '.sha')"
[[ "$REMOTE_SHA" == "$PUBLISHED_SHA" ]] || die 'Remote main read-back does not match the pushed commit.'
PUBLISH_STAGE='commit-pushed-and-read-back'

if api_read "repos/$TARGET_REPO/pages" "$PUBLISH_TMP/pages.json"; then
  python3 - "$PUBLISH_TMP/pages.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
if p.get('cname'):
    raise SystemExit('Existing Pages custom domain requires inspection; it will not be overwritten.')
PY
  BUILD_TYPE="$(python3 - "$PUBLISH_TMP/pages.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1])).get('build_type', ''))
PY
)"
  if [[ "$BUILD_TYPE" != 'workflow' ]]; then
    gh api --hostname github.com --method PUT "repos/$TARGET_REPO/pages" -f build_type='workflow' >/dev/null
  fi
else
  gh api --hostname github.com --method POST "repos/$TARGET_REPO/pages" -f build_type='workflow' >/dev/null
fi
PUBLISH_STAGE='github-pages-workflow-source-configured'

# Dispatch after enabling Pages, so a push-triggered initial setup race can be
# retried without changing content or bypassing repository protection rules.
gh workflow run pages.yml --repo "$TARGET_REPO" --ref main
RUN_ID=''
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  RUN_ID="$(gh run list --repo "$TARGET_REPO" --workflow pages.yml --branch main --commit "$PUBLISHED_SHA" --event workflow_dispatch --limit 5 --json databaseId --jq '.[0].databaseId // empty')"
  [[ -n "$RUN_ID" ]] && break
  sleep 3
done
[[ -n "$RUN_ID" ]] || die 'No matching Pages workflow run was found. Commit exists; deployment remains unverified.'
gh run watch "$RUN_ID" --repo "$TARGET_REPO" --exit-status
PUBLISH_STAGE='github-pages-actions-succeeded'
ACTUAL_PAGES_URL="$(gh api --hostname github.com "repos/$TARGET_REPO/pages" --jq '.html_url')"
python3 - "$ACTUAL_PAGES_URL" <<'PY'
from urllib.parse import urlsplit
import sys
u = urlsplit(sys.argv[1])
if u.scheme != 'https' or u.netloc.lower() != 'aipmandy.github.io' or u.path.rstrip('/') != '/chinese-international-student-product-jobs':
    raise SystemExit('Pages returned a URL outside the fixed formal target.')
PY
curl --fail --location --silent --show-error --retry 3 --retry-delay 3 --max-time 30 "$ACTUAL_PAGES_URL" -o "$PUBLISH_TMP/online-index.html"
python3 - "$PUBLISH_TMP/online-index.html" <<'PY'
from pathlib import Path
import sys
if '产品求职' not in Path(sys.argv[1]).read_text(encoding='utf-8'):
    raise SystemExit('Online homepage does not contain the expected product-jobs guide.')
PY
mkdir -p "$PUBLISH_TMP/online-downloads"
for asset in "$PDF_NAME" "$WORKBOOK_NAME" "$SOURCE_NAME"; do
  curl --fail --location --silent --show-error --retry 3 --retry-delay 3 --max-time 60 \
    "${ACTUAL_PAGES_URL%/}/downloads/$asset" -o "$PUBLISH_TMP/online-downloads/$asset"
  python3 - "$CHECKOUT_DIR/dist/downloads/$asset" "$PUBLISH_TMP/online-downloads/$asset" <<'PY'
from hashlib import sha256
from pathlib import Path
import sys
if sha256(Path(sys.argv[1]).read_bytes()).digest() != sha256(Path(sys.argv[2]).read_bytes()).digest():
    raise SystemExit('Online download bytes differ from the reviewed committed artifact.')
PY
done
PUBLISH_STAGE='online-homepage-and-download-bytes-verified'

if api_read "repos/$TARGET_REPO/commits/$RELEASE_TAG" "$PUBLISH_TMP/tag-commit.json"; then
  TAG_SHA="$(python3 - "$PUBLISH_TMP/tag-commit.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1])).get('sha', ''))
PY
)"
  [[ "$TAG_SHA" == "$PUBLISHED_SHA" ]] || die 'Remote v1.0.0 resolves to a different commit; release creation/upload is stopped.'
fi

cat >"$PUBLISH_TMP/release-notes.md" <<'NOTES'
# 中国留学生产品岗位求职保姆级攻略 v1.0.0

作者：AI 酋长 Andy。完整中文攻略、产品岗位 JD 证据、地区核验、OfferTrail 教学模拟、15 份模板、中英文申请材料与面试训练。

附件包括成品 PDF、完整样例与模板包、可重新构建的源码包。OfferTrail 无真实访谈、上线、增长或录用结果；免费内容完整开放，不承诺录用或涨薪。

微信：AIPMAndy｜公众号：AI酋长Andy

个人官网：https://metaver.vip/ ｜公司官网：https://www.a6no1.cn/

正式网站：https://aipmandy.github.io/chinese-international-student-product-jobs/
NOTES

if ! api_read "repos/$TARGET_REPO/releases/tags/$RELEASE_TAG" "$PUBLISH_TMP/release.json"; then
  gh release create "$RELEASE_TAG" --repo "$TARGET_REPO" --target "$PUBLISHED_SHA" --draft \
    --title "$PROJECT_TITLE v1.0.0" --notes-file "$PUBLISH_TMP/release-notes.md" \
    "$CHECKOUT_DIR/downloads/$PDF_NAME" "$CHECKOUT_DIR/downloads/$WORKBOOK_NAME" "$CHECKOUT_DIR/downloads/$SOURCE_NAME"
fi
api_read "repos/$TARGET_REPO/releases/tags/$RELEASE_TAG" "$PUBLISH_TMP/release.json" || die 'Release cannot be read back.'
RELEASE_COMMIT="$(gh api --hostname github.com "repos/$TARGET_REPO/commits/$RELEASE_TAG" --jq '.sha')"
[[ "$RELEASE_COMMIT" == "$PUBLISHED_SHA" ]] || die 'Release tag read-back differs from the verified commit; the draft will not be published.'
mkdir -p "$PUBLISH_TMP/release-downloads"
for asset in "$PDF_NAME" "$WORKBOOK_NAME" "$SOURCE_NAME"; do
  HAS_ASSET="$(python3 - "$PUBLISH_TMP/release.json" "$asset" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print('yes' if any(x.get('name') == sys.argv[2] for x in r.get('assets', [])) else 'no')
PY
)"
  if [[ "$HAS_ASSET" == 'no' ]]; then
    gh release upload "$RELEASE_TAG" --repo "$TARGET_REPO" "$CHECKOUT_DIR/downloads/$asset"
  fi
  # Never --clobber: a same-named differing asset must stop, not be replaced.
  gh release download "$RELEASE_TAG" --repo "$TARGET_REPO" --pattern "$asset" --dir "$PUBLISH_TMP/release-downloads"
  python3 - "$CHECKOUT_DIR/downloads/$asset" "$PUBLISH_TMP/release-downloads/$asset" <<'PY'
from hashlib import sha256
from pathlib import Path
import sys
if sha256(Path(sys.argv[1]).read_bytes()).digest() != sha256(Path(sys.argv[2]).read_bytes()).digest():
    raise SystemExit('An existing release asset differs from the local artifact; it will not be overwritten.')
PY
done
RELEASE_DRAFT="$(gh release view "$RELEASE_TAG" --repo "$TARGET_REPO" --json isDraft --jq '.isDraft')"
if [[ "$RELEASE_DRAFT" == 'true' ]]; then
  gh release edit "$RELEASE_TAG" --repo "$TARGET_REPO" --draft=false
fi
RELEASE_URL="$(gh release view "$RELEASE_TAG" --repo "$TARGET_REPO" --json url --jq '.url')"
PUBLISH_STAGE='release-published-and-assets-read-back'

python3 - "$PUBLISHED_SHA" "$RUN_ID" "$ACTUAL_PAGES_URL" "$RELEASE_URL" <<'PY'
import json, sys
sha, run, pages, release = sys.argv[1:]
print(json.dumps({'repository':'https://github.com/AIPMAndy/chinese-international-student-product-jobs','commit_sha':sha,'actions_run':'https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/'+run,'pages_url':pages,'release_url':release,'online_homepage_and_download_hashes':'verified','scope_note':'HTTP/content and byte verification; real mobile/browser interaction acceptance is recorded separately in verification/VALIDATION.md'}, ensure_ascii=False, indent=2))
PY
