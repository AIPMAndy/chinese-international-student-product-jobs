# GitHub Pages 部署

部署要求更新：2026-11-13。用户已明确授权推送本项目，正式网站使用 GitHub Pages。

## 正式目标

- 仓库：`AIPMAndy/chinese-international-student-product-jobs`。
- 分支：`main`。
- 工作流：`.github/workflows/pages.yml`。
- 静态目录：`dist/`。
- 预期项目地址：`https://aipmandy.github.io/chinese-international-student-product-jobs/`。**此地址待发布，不代表已经上线。** 最终以部署返回值与实际访问结果为准。

**完整项目已上传，v1.0.0 Release 已公开并核对三个附件。GitHub Pages 尚未启用，正式网站尚未上线。** Pages 工作流在 Configure GitHub Pages 步骤返回 `Not Found`；需先在[本仓库 Pages 设置](https://github.com/AIPMAndy/chinese-international-student-product-jobs/settings/pages)中将 Source 选为 **GitHub Actions**，再重新运行部署。ChatGPT Pages / Sites 不作为本项目的正式部署目标。

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

状态更新时间：**2026-11-13 22:57:48（北京时间，UTC+8）**。以下完整文件核对固定到原始发布提交 `4d1f8923a4a2ee8527838ae9e468bffa3e313b6f`；本次状态文档同步不改变该提交或 v1.0.0 附件。

| 项目 | 状态 |
| --- | --- |
| 远端仓库可访问 | 已核实为公开仓库，ID `1456653335`，默认分支 `main` |
| 当前连接仓库权限 | `admin`，完整项目写入成功 |
| 完整项目提交 SHA | [`4d1f8923a4a2ee8527838ae9e468bffa3e313b6f`](https://github.com/AIPMAndy/chinese-international-student-product-jobs/commit/4d1f8923a4a2ee8527838ae9e468bffa3e313b6f)，已读回 |
| 完整项目 tree | `07c1c653fc73dbf5131a6d89f5b32e7873f9a61a`，317 个 tree entries；其中 286 个 blob 与本地交付文件逐一对比，286/286 Git blob SHA 一致，缺失 0、不同 0 |
| 下载文件 | 根目录与 `dist/downloads/` 的 PDF、模板 ZIP、源码 ZIP 全部上传，同名文件 blob 相同 |
| GitHub Release | [v1.0.0](https://github.com/AIPMAndy/chinese-international-student-product-jobs/releases/tag/v1.0.0) 已公开，发布时间 2026-11-13 21:55:40（北京时间）；三个公开下载 URL 实际 GET 均为 HTTP 200，下载字节数与 SHA-256 均与本地成品一致 |
| Release Actions | [成功运行](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43437918137) |
| Pages Actions | [运行 attempt 2](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43437918445) 失败；Configure GitHub Pages 返回 `Not Found`，仓库尚未启用 Pages |
| 实际网站 URL | 尚未部署成功；上方 URL 仅为目标地址 |
| 首页、章节、PDF / ZIP 的 Pages 线上检查 | 未执行；Release 附件核对不等于 Pages 下载验收 |
| 手机页面与关键交互的 Pages 线上检查 | 未执行；制作期浏览器检查另见验证记录 |

### 完成 Pages 的剩余操作

1. 打开[本仓库 Settings → Pages](https://github.com/AIPMAndy/chinese-international-student-product-jobs/settings/pages)，在 **Build and deployment → Source** 选择 **GitHub Actions**。
2. 返回[Pages 运行](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43437918445)，重新运行失败任务，或手动触发 `pages.yml`。
3. 只有工作流成功后，才访问返回的网站地址，检查首页、章节、下载及手机阅读，并更新线上验收记录。

当前连接器没有 Pages 设置接口；本地浏览器扩展不可用，云浏览器的 GitHub 会话未登录，因此此设置尚需仓库所有者完成。用户已有发布授权，无需重复授权上传；剩余事项是启用 Pages。

v1.0.0 的 PDF 与两个 ZIP 保持已发布字节，tag 不移动。后续状态记录可单独更新；需要改变成品内容时使用新版本，不能覆盖本版附件。

## 官方依据

核验日：2026-11-13。

- [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [配置 Pages 发布源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
