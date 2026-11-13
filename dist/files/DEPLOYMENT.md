# GitHub Pages 部署

部署要求更新：2026-11-13。用户已明确授权推送本项目，正式网站使用 GitHub Pages。

## 正式目标

- 仓库：`AIPMAndy/chinese-international-student-product-jobs`。
- 分支：`main`。
- 工作流：`.github/workflows/pages.yml`。
- 静态目录：`dist/`。
- 正式网站：[https://aipmandy.github.io/chinese-international-student-product-jobs/](https://aipmandy.github.io/chinese-international-student-product-jobs/)。工作流返回该地址，实际首页 GET 为 HTTP 200，内容与已部署的 `dist/index.html` 一致。

**完整项目已上传，v1.0.0 Release 已公开，GitHub Pages 已上线并完成验收：106 个线上 URL 与文件哈希检查、18 项桌面和窄屏浏览器检查均通过。** 用户启用 Pages 后，[成功运行 attempt 2](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43447871895/attempts/2)完成配置、上传与部署。正式网站使用本仓库的 GitHub Pages。

## 发布步骤

1. 确认 GitHub 账号为 AIPMAndy，且上述仓库存在并可写。不存在时创建同名公开空仓库；不覆盖已有仓库。
2. 完成网站和下载打包，保证以下文件非空：
   - `dist/downloads/product-jobs-guide-v1.0.0.pdf`
   - `dist/downloads/product-jobs-workbook-v1.0.0.zip`
   - `dist/downloads/product-jobs-source-v1.0.0.zip`
3. 在项目根目录检查提交中的静态网站：

```bash
python3 tools/check_pages_links.py --require downloads/product-jobs-guide-v1.0.0.pdf --require downloads/product-jobs-workbook-v1.0.0.zip --require downloads/product-jobs-source-v1.0.0.zip
```

检查脚本仅使用 Python 标准库，按仓库子路径解析本地 HTML 链接、锚点与 CSS 资源，也检查 PDF / ZIP 文件是否存在。它不验证外部来源、JavaScript 动态加载、交互或真实线上状态。

4. 完成原有内容、案例、PDF 和浏览器验收。实际打开手机与桌面页面，验证目录、搜索、模板、PDF、源码下载、微信复制和官网入口。
5. 将本项目源码、交付物、`dist/`、本部署规范及工作流提交并推送到目标仓库 `main`。确认成品下载未因忽略规则漏掉。不得在源码、提交或远端 URL 写入凭据。
6. 在 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。之后由 `main` 推送触发工作流，也可手动运行。
7. 等待部署成功，实际打开工作流返回的网站地址，核验首页 HTTP 200、子路径资源、章节、PDF / ZIP 和手机阅读。完成后再将 README 的网站标为已上线。

## 部署已验收产物

工作流检查并上传提交中的 `dist/`。发布阶段不重新生成中文 PDF，也不执行依赖当前工作区路径的构建。内容修改后先按项目原有构建说明更新和验收 `dist/`，再提交；这样部署的文件与本地验收对象一致。

工作流限制为本项目精确仓库的 `main`，支持 push 和手动触发，使用 `github-pages` 环境。全局仅授予 `contents: read`，部署任务额外取得 `pages: write` 和 `id-token: write`。

## 发布与线上验收记录

状态更新时间：**2026-11-14 00:11:05（北京时间，UTC+8）**。以下完整文件核对固定到原始发布提交 `4d1f8923a4a2ee8527838ae9e468bffa3e313b6f`；本次状态文档同步不改变该提交或 v1.0.0 附件。

| 项目 | 状态 |
| --- | --- |
| 远端仓库可访问 | 已核实为公开仓库，ID `1456653335`，默认分支 `main` |
| 当前连接仓库权限 | `admin`，完整项目写入成功 |
| 完整项目提交 SHA | [`4d1f8923a4a2ee8527838ae9e468bffa3e313b6f`](https://github.com/AIPMAndy/chinese-international-student-product-jobs/commit/4d1f8923a4a2ee8527838ae9e468bffa3e313b6f)，已读回 |
| 完整项目 tree | `07c1c653fc73dbf5131a6d89f5b32e7873f9a61a`，317 个 tree entries；其中 286 个 blob 与本地交付文件逐一对比，286/286 Git blob SHA 一致，缺失 0、不同 0 |
| 下载文件 | 根目录与 `dist/downloads/` 的 PDF、模板 ZIP、源码 ZIP 全部上传，同名文件 blob 相同 |
| GitHub Release | [v1.0.0](https://github.com/AIPMAndy/chinese-international-student-product-jobs/releases/tag/v1.0.0) 已公开，发布时间 2026-11-13 21:55:40（北京时间）；三个公开下载 URL 实际 GET 均为 HTTP 200，下载字节数与 SHA-256 均与本地成品一致 |
| Release Actions | [成功运行](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43437918137) |
| Pages Actions | [运行 43447871895 / attempt 2](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43447871895/attempts/2)成功；部署提交 `45e863333f86a68c4dae82b08e315699567ea516`，全部步骤成功，完成于 2026-11-13 23:57:35（北京时间） |
| 实际网站 URL | [https://aipmandy.github.io/chinese-international-student-product-jobs/](https://aipmandy.github.io/chinese-international-student-product-jobs/)，与部署返回地址相同；首页实际 GET 为 HTTP 200 |
| 首页、章节、PDF / ZIP 的 Pages 线上检查 | [HTTP 记录](verification/live-http-qa.json)：106/106 个 URL 最终均 HTTP 200，SHA-256 与本地已部署文件一致；覆盖 62 个 HTML、13 个静态资源、3 个下载、16 个模板文件（含 README）、12 个样例文件。两次首轮读取超时各重试一次通过，共 108 次请求 |
| 窄屏页面与关键交互的 Pages 线上检查 | [浏览器记录](verification/live-browser-qa.json)：18 项通过；桌面 1363 × 936 CSS px，Chrome 400% 缩放后为 340 × 234 CSS px。首页、原型与抽查章节无整页横向溢出；窄屏模拟不等同于移动真机 |

### 本次线上验收

Pages 已启用，部署及正式域名验收完成。正式项目子路径的章节、静态资源、模板、样例和三个下载文件已通过 HTTP 与 SHA-256 核对；18 项浏览器检查覆盖搜索、背景路线、复制微信、目录与阅读、实际 CSV/JSON 下载，以及原型中的阻断、人工确认、修改后失效和焦点保留。

窄屏以原生 Chrome 400% 缩放得到 340 × 234 CSS px，首页、原型、地区和面试章节的 documentWidth 为 337 CSS px，无整页横向溢出。地区章五个表格在宽 257 CSS px 的独立滚动容器中展示 480 CSS px 内容。此记录没有把桌面窄屏模拟称为 iOS/Android 真机测试。

此前的 `Not Found` 来自启用 Pages 前的运行，属于历史失败记录。启用后重跑已成功。

v1.0.0 的 PDF 与两个 ZIP 保持已发布字节，tag 不移动。后续状态记录可单独更新；需要改变成品内容时使用新版本，不能覆盖本版附件。

## 官方依据

核验日：2026-11-13。

- [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [配置 Pages 发布源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
