# PDF 构建与自动检查记录

核验日期：2026-11-13。版本：1.0.0。

## 成品

- 文件：`output/pdf/product-jobs-guide-v1.0.0.pdf`。
- 下载副本：`downloads/product-jobs-guide-v1.0.0.pdf`，与输出文件逐字节一致。
- 128 页，1,486,561 字节。
- SHA-256：`2a1abf1a37f1a75f1e6265737a4ae23e71cbeba12df5d0a75408e334e0e1df1c`。
- 可提取文本 122,611 字符，430 个书签，87 个内部链接，358 个外部链接。
- 13 个编号章节（00–12）、5 个附录分区、35 个源文档、15 份模板、68 条来源记录/63 个去重官方 URL。
- 原始材料、研究计划、完整作品集、中英文简历与中英文项目讲解均保留全文。
- PDF 中保留 7 份 CSV 的全部字段及完整填写示例；7 条全空白记录改为同字段下载填写提示，源 CSV 的空白行没有修改。

## 构建路径

本次使用 ReportLab，构建不启动浏览器、不联网安装依赖、不抓取新的截图。此前环境中的本地 Chromium 文档导出失败后，改用系统已安装的排版库和字体完成。

```bash
npm install
python3 -m pip install -r tools/requirements-pdf.txt
python3 tools/render_pdf.py --require-images --dpi 120
```

以上是供维护者复现的依赖安装说明，不表示本次执行过联网安装。本次直接使用已有依赖。系统需提供 Noto Sans CJK、DejaVu Sans Mono 与 Poppler 的 `pdffonts`；当前字体路径为 Debian/Linux 常见路径。

- `tools/export_book_ast.mjs` 使用项目固定版本的 marked 17.0.5 只读导出 Markdown/CSV 结构。
- `tools/prepare_fonts.py` 提取项目使用的 1,270 个 Unicode 码位，将本机 Noto CJK SC 的 CFF 字形转为 TrueType 二次曲线，派生字体重命名并缓存到 `tmp/pdf-fonts/`。
- `tools/render_pdf_reportlab.py` 完成封面、真实页码目录、书签、正文、记录卡、图像、来源和逐页渲染。
- `tools/render_pdf.py` 为兼容入口，直接调用同一 ReportLab 实现。

## 排版与内容边界

正文 10.6 pt，正文行距 17.2 pt；模板保留同样字号，只减少段落与标题留白。表格使用可读字号、重复表头，并禁止拆开单个表格行。宽 CSV 按键值记录卡展开。

三幅精确图使用矢量形状及可选中文字。三张 OfferTrail 图片来自实际浏览器中的原型状态，分别呈现整体核对、未知信息阻断和本地人工核对完成；文字没有把本地核对描述成真实提交或工作许可决定。

字体来源、SIL Open Font License 1.1、派生处理与 DejaVu 许可入口记录在 `verification/pdf-font-license.md`，字体嵌入与 Unicode 映射见 `verification/pdf-metadata.json`。Noto 中文及 SQL 等宽字体都作为 TrueType 子集嵌入。标准 Helvetica 是 PDF 库的默认资源，不承担中文正文。

## 自动检查

| 检查 | 结果 |
| --- | --- |
| 18 个分区标题可提取 | 全部存在 |
| 正文文字超出页面 | 0 |
| 空白或近空白页 | 0 |
| 缺失图像 | 0 |
| 内部链接目标页无效 | 0 |
| URI 解码后误吸入中文/中文标点 | 0 |
| 输出与下载 PDF 一致 | 通过 |
| 每页 PNG | 128 张，120 DPI |
| 四页拼图 | 32 张 |

链接检查核验的是 PDF 内部链接结构与 URL 文本，不等于所有外部政策页或正式网站在线状态已验收。网站部署与真实线上访问另有记录。

## 视觉验收材料

- 单页图：`verification/pdf-pages/page-001.png` 至 `page-128.png`。
- 四页拼图：`verification/pdf-contact-sheets/sheet-001.png` 至 `sheet-032.png`。
- 自动元数据：`verification/pdf-metadata.json`。
- 提取全文：`verification/pdf-extracted-text.txt`。
- URI 与前版像素对照：`verification/pdf-final-link-and-pixel-check.json`。
- 前段记录：`verification/pdf-visual-review-001-048.md`。
- 中段记录：`verification/pdf-visual-review-049-096.md`。
- 模板独立复核：`verification/pdf-visual-review-templates.md`，第 93–115 页已通过；另按 CSV 源文件逐项核对 7 份填写例。
- 来源区最终验收由主审查记录补齐，不以自动检查替代逐页查看。

已修复的问题包括：主目录多出单独尾页、SVG 三位十六进制白色被解析成蓝色、地区标签未解析为粗体、04 章末提示形成孤页、CSV 空白行重复铺版、模板 checkbox 重复、模板标题与表格脱离、模板末尾署名孤页，以及来源 R34 裸 URL 误吸入后续中文。
