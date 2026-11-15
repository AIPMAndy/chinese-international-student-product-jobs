# 构建、打包与 GitHub 发布

版本：1.0.0｜核验日期：2026-11-13

执行前先阅读 [AGENTS.md](AGENTS.md) 与 [DEPLOYMENT.md](DEPLOYMENT.md)。正式仓库固定为 `AIPMAndy/chinese-international-student-product-jobs`，正式网站唯一目标为该仓库的 **GitHub Pages**。

正式网址：[https://aipmandy.github.io/chinese-international-student-product-jobs/](https://aipmandy.github.io/chinese-international-student-product-jobs/)。Pages 工作流已成功并返回该地址，首页实际 GET 为 HTTP 200；106 个线上 URL 与文件哈希、18 项桌面与窄屏浏览器检查均通过。

## 当前发布状态

截至 **2026-11-14 00:11:05（北京时间，UTC+8）**，完整项目已上传至公开仓库，ID `1456653335`，默认分支 `main`。原始发布提交 `4d1f8923a4a2ee8527838ae9e468bffa3e313b6f`、tree `07c1c653fc73dbf5131a6d89f5b32e7873f9a61a` 已读回；远端 317 个 tree entries 中的 286 个 blob 与本地交付文件逐一比对，286/286 一致，缺失 0、不同 0。PDF、两个 ZIP 与对应 `dist/downloads/` 文件全部上传且 blob 相同。

**[v1.0.0 Release](https://github.com/AIPMAndy/chinese-international-student-product-jobs/releases/tag/v1.0.0) 已公开。** 发布时间为 2026-11-13 21:55:40（北京时间）；三个公开下载 URL 已实际 GET，均返回 HTTP 200，下载字节数及 SHA-256 与本地成品一致，[Release 工作流](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43437918137)成功。

**GitHub Pages 已上线并完成验收，106 个线上 URL 与文件哈希、18 项桌面与窄屏浏览器检查均通过。** 用户启用 Pages 后，[Pages 工作流 attempt 2](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43447871895/attempts/2)于 2026-11-13 23:57:35（北京时间）完成部署，提交为 `45e863333f86a68c4dae82b08e315699567ea516`。此前未启用时的 `Not Found` 已解决。[HTTP 验收](verification/live-http-qa.json)覆盖 106 个唯一 URL，最终全部 HTTP 200 且 SHA-256 与本地一致，含 62 个 HTML 和三个下载文件；两次读取超时分别重试一次后通过。[正式域名浏览器验收](verification/live-browser-qa.json)有 18 项通过：桌面 1363 × 936 CSS px，Chrome 400% 缩放的窄屏为 340 × 234 CSS px；覆盖目录、搜索、路线、剪贴板、下载与原型关键交互。没有执行 iOS/Android 真机或 Safari/WebKit 测试。

v1.0.0 的三个附件与 tag 保持不变。此次仅同步发布状态；源码 ZIP 内保留打包时的验证快照，最新远端状态以 [DEPLOYMENT.md](DEPLOYMENT.md)与[发布状态](verification/publication-status.json)为准。需要变更成品时发布新版本，不覆盖已有附件。

用户已授权本项目发布，无需再次授权上传。不得把 token 写入聊天、脚本、文件、Git 远端 URL 或提交。

`tools/publish-github.sh` 只接受固定目标，不接受仓库、分支或版本覆盖参数。它从当前项目导出一个独立临时目录，再克隆指定 GitHub 仓库；不会使用当前工作区的 `.git` 或 `.openai` 状态，不会推送任何 Sites 私有远程，也不会修改另外三个留学生项目、官网、个人主页或总导航。

## 1. 本地构建

网站依赖 Node.js 20 或更新版本，Python 脚本使用 Python 3.11 或更新版本。依赖清单在 `package.json`；有锁文件时使用 `npm ci`，没有锁文件时先运行 `npm install` 并保留生成的锁文件。

```bash
npm install
python3 -B tools/evaluate_baseline.py
npm run build
```

网页构建输出到 `dist/`。正式构建时，`tools/lib.mjs` 的网站源地址必须使用本项目 GitHub Pages 地址，不能指向其他网站。项目子路径由 [部署检查脚本](tools/check_pages_links.py)核验。

### 重新生成 PDF

已交付的 PDF 可以直接使用。需要重新排版时，安装渲染依赖和中文字体。例如在独立 Python 环境中：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r tools/requirements-pdf.txt
python -B tools/render_pdf.py
```

PDF 使用 ReportLab 排版，不启动浏览器。当前字体转换脚本使用 Linux 的 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` 与 `NotoSansCJK-Bold.ttc`，Debian/Ubuntu 可安装 `fonts-noto-cjk`；字体路径不同的环境先调整 `tools/prepare_fonts.py`。字体转换保留 Unicode 映射，中文可选中。ReportLab 生成目录与页码，PyMuPDF 导出逐页图；可选的 `pdffonts` 检查来自 Poppler。

三张原型截图来自实际浏览器操作，已保存在 `assets/`，PDF 构建直接读取这些经过检查的截图。修改原型后，应重新通过浏览器检查并更新对应截图，不能把旧图当作新界面的验收证据。字体许可见 `assets/Noto-CJK-license.txt`。

成品位置：`output/pdf/product-jobs-guide-v1.0.0.pdf`，同时复制到 `downloads/`。页面渲染在 `verification/pdf-pages/`，联系表在 `verification/pdf-contact-sheets/`。这些中间图不进入发布 ZIP 或源码导出；保留的原型截图位于 `assets/`。

**验收要求：** 逐页查看最新渲染，确认中文、表格、页码、目录、链接、原型截图与图表。PDF 文本和几何检查不等于视觉验收。将真实执行状态写入 `verification/VALIDATION.md`，不把“待检查”自动改成“通过”。

## 2. 生成两个发布包

```bash
python3 -B tools/package_release.py
```

| 产物 | 内容 |
| --- | --- |
| `downloads/product-jobs-workbook-v1.0.0.zip` | 15 份模板、模板说明、12 个样例文件、两章完整案例、可运行原型、必要图像、离线入口与许可 |
| `downloads/product-jobs-source-v1.0.0.zip` | 完整正文、来源、模板、样例、资产、工具、工作流、部署说明、依赖清单、验证快照与成品 PDF |

Workbook 保留原有相对路径。解压后打开 `index.html` 或 `prototypes/offertrail.html` 即可运行原型。Markdown 用编辑器阅读，CSV 可用表格软件修改。原型不发送申请，也不验证工作许可。

源码包包含成品 PDF，不复制可重新生成的 `dist/`，不递归包含自身或另一个 ZIP。解压后可重新执行打包与网页构建，得到完整网站。每个 ZIP 内有 `PACKAGE-MANIFEST.json`，列出文件哈希、包范围和模拟性质。

打包默认排除 `.git`、`.openai`、凭证文件、私钥、`node_modules`、虚拟环境、渲染中间文件、缓存和符号链接。它采用来源目录白名单，并检测常见真实 GitHub token 与私钥标记。该检查不等于通用秘密审计；不要把任何秘密放入公开项目。

若 PDF 尚未生成，普通命令会先生成 Workbook，并明确跳过不完整的源码包。完整发布使用严格模式：

```bash
python3 -B tools/package_release.py --require-pdf
npm run build
python3 -B tools/check_integrity.py
python3 -B tools/check_pages_links.py --require downloads/product-jobs-guide-v1.0.0.pdf --require downloads/product-jobs-workbook-v1.0.0.zip --require downloads/product-jobs-source-v1.0.0.zip
```

更新验证记录后，可再运行打包和网页构建，让源码包包含最近的验证快照，并用只读 Pages 检查确认最终 `dist/`。发布脚本要求 `downloads/` 与 `dist/downloads/` 的三份产物逐字节一致；若不一致，先重新构建并验收，不在发布阶段偷偷替换文件。

## 3. 使用固定目标发布脚本

先在具备相应权限的环境登录 **AIPMAndy**：

```bash
gh auth login --hostname github.com
gh auth status --hostname github.com
bash tools/publish-github.sh
```

此处登录由 GitHub CLI 的正常流程完成。脚本本身不读取或打印 token。认证失败、账号不符、网络查询失败、权限不足时会清楚退出，不把查询失败当作仓库不存在。

### 脚本实际执行顺序

1. 校验登录账号、成品 PDF、完整 `dist/`、结构记录与三个下载文件。
2. 用安全导出器生成独立临时源目录，保持已验收的静态文件字节不变。
3. 查询唯一目标仓库。确认 404 后才创建同名公开仓库。
4. 已有仓库必须是相同用途、公开、非归档、非 fork、可写，且使用 `main`。有内容时读取 README 和 package 身份；空仓库需要相符描述。用途不明就停止，不覆盖。
5. 在独立 GitHub clone 中提交源文件、成品、`dist/`、部署规范和工作流，以普通快进推送提交到 `main`，随后读回 SHA。
6. 仅为这个项目配置 Pages 的 workflow 发布源，触发并等待 `pages.yml`。现有自定义域名不会被覆盖，仓库保护规则不会被绕过。
7. 读取 Pages 返回的网址，实际访问首页，并下载线上 PDF 与两个 ZIP，逐字节核对本轮实际构建产物。
8. 创建 `v1.0.0` 草稿 release，上传三份产物，读回检查，再发布。已有同名资产只核对或补缺，不使用 `--clobber`；不同内容不能覆盖旧版本。

Git 命令始终针对临时 clone，远端固定为公开 GitHub 项目。脚本不强推、不重写 tag、不删除既有资产，不操作其他仓库。重复运行时，同一版本与同一内容可以继续验证或补齐中断的发布；如果 `v1.0.0` 已存在而内容变化，脚本会停止，要求维护者按新版本处理。

失败时会输出最后完成阶段，保留隔离目录供排查。例如“提交已读回”与“Pages 部署成功”是两个不同状态。不能因为前一项完成就宣称网站已上线。

## 4. Pages 工作流：从源码重建网站与模板包，保持已审阅 PDF 不变

自 2026-11-14 起，[.github/workflows/pages.yml](.github/workflows/pages.yml) 在精确仓库 `AIPMAndy/chinese-international-student-product-jobs` 的 `main` 上运行：先安装固定版本的网站构建依赖，再从包含 `site/home.html` 的完整源文件重新生成模板包、源码 ZIP 和 `dist/`，运行完整性、全页 canonical/OG/JSON-LD/sitemap 与 PDF 检查，最后部署并以本轮实际生成物的 SHA-256 验证在线文件。旧 `dist/` 为历史快照，不能代表本次上线字节。

全局权限为 `contents: read`；部署任务另外取得 `pages: write` 和 `id-token: write`，使用 `github-pages` 环境。Checkout 不保留 Git 凭据。工作流不会在 CI 重新生成中文 PDF，也不会调用 Sites。

核验采用的官方 action 主版本：

| Action | 本项目版本 |
| --- | --- |
| `actions/checkout` | `v6` |
| `actions/configure-pages` | `v5` |
| `actions/upload-pages-artifact` | `v4` |
| `actions/deploy-pages` | `v4` |

这些版本与 2026-11-13 阅读的 GitHub Pages 官方工作流示例一致；不是声明未来永远无需更新。[官方流程](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

## 5. 发布成功后的记录

保存脚本最后输出的仓库地址、提交 SHA、Actions run URL、实际 Pages URL 和 release URL。再完成线上手机与桌面交互检查：目录、搜索、模板、PDF、源码包、微信复制和两处官网入口。

脚本能验证 HTTP 内容与下载字节，不能代替真实浏览器交互和逐页 PDF 视觉检查。只有相应动作实际完成，才能更新 [部署状态](DEPLOYMENT.md)与验证记录；否则分别保留待办。

## 官方依据

以下资料均在 2026-11-13 核验。部署资料与招聘来源台账分开维护。

- [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)：当前 action 版本、artifact、环境与部署权限。
- [GitHub Pages 发布源设置](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)：GitHub Actions 作为发布源。
- [Pages REST API](https://docs.github.com/en/rest/pages/pages)：创建和更新本仓库 Pages 配置，`build_type: workflow` 与所需权限。
- [gh repo create](https://cli.github.com/manual/gh_repo_create)：指定完整仓库名与 `--public`；脚本没有借用当前目录的 source/remote。
- [gh release create](https://cli.github.com/manual/gh_release_create)：指定提交、草稿、附件与 release 创建过程。
- [gh release upload](https://cli.github.com/manual/gh_release_upload)：同名覆盖会先删除旧资产，因此本脚本不使用 `--clobber`。

作者：AI酋长Andy｜微信：AIPMAndy｜公众号：AI酋长Andy  
个人官网：https://metaver.vip/ ｜公司官网：https://www.a6no1.cn/
