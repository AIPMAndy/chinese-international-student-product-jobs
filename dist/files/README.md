# 中国留学生产品岗位求职保姆级攻略

**从真实 JD 出发，拿出能证明用户理解、产品判断、方案取舍与推进能力的材料。**

作者：**AI 酋长 Andy**。前腾讯、百度 AI 产品专家，前大模型公司 VP。版本 **1.0.0 · 2026-11-13**。

[GitHub Pages 部署说明（待发布）](DEPLOYMENT.md) · [完整 PDF](downloads/product-jobs-guide-v1.0.0.pdf) · [贯穿案例](content/case/06-end-to-end-case.md) · [完整样例](examples/README.md) · [可编辑模板](templates/README.md) · [交互原型](prototypes/offertrail.html) · [验证记录](verification/VALIDATION.md)

## 适合谁

中国留学生申请产品实习、APM/毕业生项目或正式产品岗位。包括技术背景转产品、商科背景转产品和已有相关经历。AI 产品经理在本册；算法和模型工程归 AI 求职册，商业/经营分析通常归商科册，交叉岗位以实际 JD 为准。

## 你可以直接完成什么

- 用 **7 份具体官方 JD + 2 份项目/岗位族资料**区分岗位与资格要求。
- 按 **17 个重点市场**分别核对招聘入口、毕业衔接和工作许可；其他市场提供独立官方核验入口。包含回国申请，不覆盖非洲、南美洲。
- 用 **OfferTrail** 从六条原始模拟材料走到研究计划、方案取舍、关键原型、指标、作品集、双语简历与面试讲解。
- 直接编辑 **15 份模板**，训练产品设计、指标/SQL、执行、AI 判断、项目深挖与行为面试。
- 下载完整中文 PDF；网站适配手机，免费内容全部开放。

## 第一小时

1. 打开 [00 开始](content/00-start-here.md)，填写毕业时间、地区和可到岗日。
2. 选择 3 条官网 JD，填 [岗位拆解表](templates/jd-breakdown.csv)。
3. 给每条职责找一个材料位置，填 [能力证据表](templates/capability-evidence.csv)。
4. 分清缺经历、能力还是表达，只选一个最重要的缺口开始补。

## 完整章节

| 章节 | 要交付什么 |
|---|---|
| [00 开始](content/00-start-here.md) | 一条明确的申请与证据路线 |
| [01 真实岗位](content/roles/01-role-evidence.md) | JD 拆解与职责边界 |
| [02 背景路线](content/02-route-and-gap.md) | 技术、商科、已有经历的补缺口计划 |
| [03 用户研究](content/03-user-research.md) | 原始材料、反例与问题定义 |
| [04 产品判断](content/04-product-judgment.md) | 方案取舍、原型、指标与推进 |
| [05 地区路线](content/regions/05-regions.md) | 逐国资格门、毕业与到岗衔接 |
| [06 贯穿案例](content/case/06-end-to-end-case.md) | 能追溯的完整 OfferTrail 案例 |
| [07 申请材料](content/case/07-application-materials.md) | 中英文简历、作品集与项目介绍 |
| [08 AI 产品](content/08-ai-product-lab.md) | 非 AI 基线、评测与人工接管 |
| [09 面试实验室](content/roles/09-interview-lab.md) | 六组训练、计算样例与复盘 |
| [10 定向申请](content/10-application-operations.md) | 资格核实、材料版本与申请台账 |
| [11 三十天计划](content/11-action-plan.md) | 每周产出、验收与失败处理 |
| [12 来源](content/12-sources.md) | 官方链接、日期、适用范围与读取限制 |

## 案例和证据边界

OfferTrail 的申请者、雇主、岗位数据和六条情境为**教学模拟**，不是六位受访者。没有真实访谈、用户研究、生产上线、增长、营收或录用成绩。当前材料与原型可以检查；需求和效果仍待真实验证。独立面试合成数据与本案例成绩完全分开。

读者应重做自己的项目，并注明复用及新增贡献，不能把本教材直接写成本人经历。课程项目、个人项目、实习分别标记真实身份与权限。

岗位及地区信息以 **2026-11-13** 的官方资料为依据。日期冲突、动态页面受限与未知条件均保留。核验日不代表岗位持续开放，政策公告日也不等于生效日。

## 与既有项目的边界

已只读检查 [how-to-get-offer](https://github.com/AIPMAndy/how-to-get-offer)、[teach-rd-product-handbook](https://github.com/AIPMAndy/teach-rd-product-handbook)、[andy-product-skill](https://github.com/AIPMAndy/andy-product-skill) 的目录与相关正文。[去重审查记录](research/DEDUPE-AUDIT.md)列明文件与读取快照。

通用求职流程适当引用 `how-to-get-offer`；本册完整提供产品专业案例和面试训练，不搬运产品理论。未修改其他项目、个人主页、总导航或官网。

## 本地使用与维护

`dist/` 是可直接部署的静态网站；`prototypes/offertrail.html` 可直接在浏览器打开。正文在 `content/`，模板在 `templates/`，成品在 `downloads/`，来源在 `research/`。

```bash
npm install
npm run build
python3 tools/evaluate_baseline.py
python3 tools/check_integrity.py
```

PDF 的可重复构建说明见 [PUBLISH.md](PUBLISH.md)。浏览器原型仅在当前页面保留模拟状态，不上传数据、不发送申请。

## 作者与咨询

**AI 酋长 Andy** · 微信 **AIPMAndy** · 公众号 **AI酋长Andy**

[个人官网 https://metaver.vip/](https://metaver.vip/) · [公司官网 https://www.a6no1.cn/](https://www.a6no1.cn/)

免费正文、模板、样例和 PDF 完整开放。咨询承接岗位定位、作品集诊断和模拟面试；不承诺录用或涨薪。联系前请准备目标地区、毕业月份、3 条 JD 和当前作品。

代码 MIT；原创内容 CC BY 4.0。见 [LICENSE](LICENSE) 和 [内容许可](CONTENT_LICENSE.md)。
