# 验证记录与待补事项

版本：1.0.0。核验日：2026-11-13。作者：AI 酋长 Andy。

**完整项目已上传，v1.0.0 Release 已公开，三个附件已核对。GitHub Pages 尚未启用，正式网站尚未上线，Pages 线上验收未执行。** 正式部署目标以 [DEPLOYMENT.md](../DEPLOYMENT.md) 为准。

远端状态更新时间：**2026-11-13 22:57:48（北京时间，UTC+8）**。仓库 ID `1456653335`，公开，默认分支 `main`。原始发布提交 [`4d1f8923a4a2ee8527838ae9e468bffa3e313b6f`](https://github.com/AIPMAndy/chinese-international-student-product-jobs/commit/4d1f8923a4a2ee8527838ae9e468bffa3e313b6f)、tree `07c1c653fc73dbf5131a6d89f5b32e7873f9a61a` 已读回；317 个 tree entries 中的 286 个 blob 与本地交付文件逐一比较，Git blob SHA 286/286 一致，缺失 0、不同 0。此完整性证据固定到该原始发布提交；本次只同步状态文档，不改变 v1.0.0 下载附件。详细状态见[发布记录](publication-status.json)。

## 已完成的验证

| 范围 | 实际执行 | 证据与边界 |
| --- | --- | --- |
| 去重 | 只读查看三个既有项目的目录和相关正文，记录文件/树快照 | [去重记录](../research/DEDUPE-AUDIT.md)；没有改动其他仓库 |
| 招聘与地区资料 | 68条来源记录、63个去重官方URL；正文保留核验日、适用范围与读取限制 | [来源章](../content/12-sources.md)；并非63份正文全部成功读取 |
| 内容一致性 | 交叉检查案例、地区规则、AI评测口径与面试数据 | [内容审查](content-independent-review.md)、[地区审查](region-independent-review.md) |
| AI确定性基线 | 12个合成用例实际执行，12/12符合预期 | [执行结果](ai-baseline.json)；没有调用模型，不是用户或业务成绩 |
| 原型纯逻辑 | 实际HTML中的日期/阻断函数通过10项检查，含无效日期、DST缺失/重复时间 | [结果](prototype-logic.json)；不代替浏览器和真人研究 |
| 浏览器交互 | 桌面操作、键盘核心任务、窄屏阅读、搜索、背景选择、复制微信、CSV与JSON导出 | [浏览器记录](browser-qa.json)；340 CSS px普通缩放，非移动真机 |
| PDF | 128页逐页渲染和分段视觉检查；中文可选中，目录与书签可用 | 下节说明范围、最终hash与修复 |
| 发布包 | ZIP CRC、必需文件、文件哈希与排除项检查 | [打包记录](release-packages.json)；已发布附件保持原字节，包内状态为打包时快照 |
| 全量结构 | 源码与静态站点检查通过，0错误、0警告 | [结构结果](integrity.json)；软件检查不代表线上部署 |
| GitHub 完整上传 | 原始发布提交及 tree 已读回；286/286 blob 与本地一致，缺失 0、不同 0 | [发布记录](publication-status.json)；包括正文、模板、案例、PDF、ZIP、dist 与工作流 |
| GitHub Release | v1.0.0 已公开；三个公开下载 URL 实际 GET 均为 HTTP 200，字节数及 SHA-256 与本地一致 | [成功运行](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43437918137)、[公开版本](https://github.com/AIPMAndy/chinese-international-student-product-jobs/releases/tag/v1.0.0)；与 Pages 状态独立 |
| GitHub Pages | attempt 2 在 Configure GitHub Pages 返回 Not Found | [失败运行](https://github.com/AIPMAndy/chinese-international-student-product-jobs/actions/runs/43437918445)；待启用 Pages，未完成部署和线上验收 |

## 贯穿案例实际检查结果

APP-01 的伦敦时间与 APP-03 的纽约时间正确换算为北京 2026-11-21 01:00 与 2026-11-25 06:00。APP-02 保留模糊原文，所有材料打勾也不能通过未知日期和时区。缺少作品集/人工许可核对时阻断；修改材料后旧确认失效；重置恢复初始样本。

完成流程后，界面明确写“尚未向雇主提交”。实际导出的 [JSON](offertrail-export.json) 中，`simulation=true`、`submitted=false`、`work_permission_legally_verified=false`。这些是软件行为，不是工作许可判断，也不是申请结果。

浏览器验证针对制作期的临时验收版本。最终源码另外补了卡片重渲染后的焦点保留；这项小修复以及正式网站上的PDF/ZIP下载仍需在GitHub Pages部署后回归；Release附件已单独核对。没有把旧网站或本地检查伪装成正式线上验收。

## PDF 逐页验收

最终文件：`downloads/product-jobs-guide-v1.0.0.pdf`，128页，1,486,561 bytes。

SHA-256：`2a1abf1a37f1a75f1e6265737a4ae23e71cbeba12df5d0a75408e334e0e1df1c`。

| 检查范围 | 记录 |
| --- | --- |
| 1–48页 | [前段视觉记录](pdf-visual-review-001-048.md) |
| 49–96页 | [中段视觉记录](pdf-visual-review-049-096.md) |
| 93–115页 | [全部模板视觉记录](pdf-visual-review-templates.md) |
| 第3页及116–128页 | [最终目录与来源视觉记录](pdf-visual-review-sources.md) |

所有页均由真实渲染图检查覆盖。最终模板修复前后的1–92页仅第3页像素变化，该页已经重新查看；未变化页面沿用此前实际检查，见 [像素和链接记录](pdf-final-link-and-pixel-check.json)。

已经修复：目录溢页、SVG短色值、地区步骤标签星号、章节末尾孤页、PDF重复空白CSV记录、复选框重复、模板署名孤页、表格前孤立标题、R34链接吸入后文。部分章节或模板有正常结束留白，未通过删内容或过度缩字挤页。

[PDF元数据](pdf-metadata.json)记录128页、122,611个可提取字符、87个内部链接、358个外部链接、430个书签；缺图、缺章节、越界文字和空白页检查均为0。表格行不拆开，跨页重复表头。三张实际原型截图清楚，三幅图示为矢量绘制。所有URL可点击不等于目标网络永久可达；GitHub Pages地址在发布后才生效。

## 可复现命令

```bash
npm install
node tools/build_site.mjs
python3 -B tools/evaluate_baseline.py
node tools/check_prototype_logic.mjs
python3 -B tools/check_integrity.py
python3 -B tools/check_pages_links.py --require downloads/product-jobs-guide-v1.0.0.pdf --require downloads/product-jobs-workbook-v1.0.0.zip --require downloads/product-jobs-source-v1.0.0.zip
```

PDF复现依赖与操作见 [PUBLISH.md](../PUBLISH.md)、[构建记录](pdf-build-record.md)。两个ZIP包含可编辑源文件和完整依赖路径；不要用修改后的文件冒充本版hash对应的验收结果。

## 仍需补齐

1. **启用并部署 Pages**：完整上传与 Release 已完成。在[本仓库 Pages 设置](https://github.com/AIPMAndy/chinese-international-student-product-jobs/settings/pages)将 Source 选为 GitHub Actions，再重新运行 Pages。attempt 2 的配置步骤返回 Not Found；当前没有成功部署或线上验收记录。
2. **最终线上回归**：核对正式项目子路径、手机页面、焦点小修复、PDF与两个ZIP下载。源码中已验收的dist与downloads必须保持相同文件哈希。
3. **真人研究与真机**：OfferTrail用户访谈、独立任务测试、需求强度和业务效果仍未开展；R01–R03保持计划状态。窄屏CSS检查不等同于iOS/Android真机测试。
4. **官方冲突与时效**：新西兰公告生效日冲突、韩国新旧官方说明、法国动态门槛和部分动态网页读取限制已在正文披露，申请前按对应机关原文再核对。

作者：AI 酋长 Andy。微信：AIPMAndy。公众号：AI酋长Andy。[个人官网](https://metaver.vip/) · [公司官网](https://www.a6no1.cn/)。免费内容完整开放；咨询不承诺录用或涨薪。
