# 验证记录与待补事项

版本：1.0.0。核验日：2026-11-13。作者：AI 酋长 Andy。

**内容、原型、成品 PDF 与发布配置已完成；公开 GitHub 仓库及 README 初始化提交已确认，完整项目文件上传进行中。GitHub Pages 尚未部署或验收，Release 尚未发布。** 用户已授权发布，仓库创建与写入已验证可用。正式部署目标以 [DEPLOYMENT.md](../DEPLOYMENT.md) 为准。

远端状态更新时间：**2026-11-13 21:48（北京时间，UTC+8）**。仓库 ID `1456653335`，公开，默认分支 `main`，当前连接权限 `admin`。完整 README 写入后的提交 `f4f8324f8960dd39c57a1bf41e160cee30181896`、tree `08a6e7ce05b798a8875168bbf2e589dd3ca3bcf0` 已读回。该记录只证明 README 初始化完成，不证明其他文件已完整上传；后续状态见[发布记录](publication-status.json)。

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
| 发布包 | ZIP CRC、必需文件、文件哈希与排除项检查 | [打包记录](release-packages.json)；最后内容同步后再次打包 |
| 全量结构 | 源码与静态站点检查通过，0错误、0警告 | [结构结果](integrity.json)；软件检查不代表线上部署 |
| GitHub 初始化 | 新公开仓库已可访问，README 创建写入成功，初始化提交及 tree 已读回 | [发布记录](publication-status.json)；完整项目上传进行中，未声明 Pages 或 Release 已发布 |

## 贯穿案例实际检查结果

APP-01 的伦敦时间与 APP-03 的纽约时间正确换算为北京 2026-11-21 01:00 与 2026-11-25 06:00。APP-02 保留模糊原文，所有材料打勾也不能通过未知日期和时区。缺少作品集/人工许可核对时阻断；修改材料后旧确认失效；重置恢复初始样本。

完成流程后，界面明确写“尚未向雇主提交”。实际导出的 [JSON](offertrail-export.json) 中，`simulation=true`、`submitted=false`、`work_permission_legally_verified=false`。这些是软件行为，不是工作许可判断，也不是申请结果。

浏览器验证针对制作期的临时验收版本。最终源码另外补了卡片重渲染后的焦点保留；这项小修复以及最终PDF/ZIP在线下载仍需在GitHub Pages部署后回归。没有把旧网站或本地检查伪装成正式线上验收。

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

1. **完整上传与发布**：继续上传本项目源码、交付物、`dist/` 与工作流，完成后读回最终提交 SHA，并核对远端文件。随后配置和运行 Pages，记录成功运行与实际网站访问结果，再完成 Release 发布。当前只确认 README 初始化提交，不能把上传进行中写成完整项目或网站已发布。
2. **最终线上回归**：核对正式项目子路径、手机页面、焦点小修复、PDF与两个ZIP下载。源码中已验收的dist与downloads必须保持相同文件哈希。
3. **真人研究与真机**：OfferTrail用户访谈、独立任务测试、需求强度和业务效果仍未开展；R01–R03保持计划状态。窄屏CSS检查不等同于iOS/Android真机测试。
4. **官方冲突与时效**：新西兰公告生效日冲突、韩国新旧官方说明、法国动态门槛和部分动态网页读取限制已在正文披露，申请前按对应机关原文再核对。

作者：AI 酋长 Andy。微信：AIPMAndy。公众号：AI酋长Andy。[个人官网](https://metaver.vip/) · [公司官网](https://www.a6no1.cn/)。免费内容完整开放；咨询不承诺录用或涨薪。
