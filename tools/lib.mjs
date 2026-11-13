import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
let marked;
try{({marked}=require('marked'));}catch{({marked}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES||'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','marked')));}
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export const ORIGIN=(process.env.SITE_ORIGIN||'https://aipmandy.github.io/chinese-international-student-product-jobs').replace(/\/$/,'');
export const DATE='2026-11-13';
export const VERSION='1.0.0';
export const chapters=[
 ['00','先完成一条能投递的证据链','起点、交付物与使用顺序','content/00-start-here.md'],
 ['01','看懂真实产品岗位要求','七份具体JD与两份官方项目/岗位族','content/roles/01-role-evidence.md'],
 ['02','按背景判断申请路线','技术、商科、已有经历的三种缺口','content/02-route-and-gap.md'],
 ['03','从真实用户问题开始','招募、观察、反例和研究证据边界','content/03-user-research.md'],
 ['04','用方案取舍证明判断','比较方案、关键原型、指标与推进','content/04-product-judgment.md'],
 ['05','逐国核对申请路径','17个重点市场、毕业衔接与回国申请','content/regions/05-regions.md'],
 ['06','贯穿案例：OfferTrail','从六条原始模拟材料到完整产品案例','content/case/06-end-to-end-case.md'],
 ['07','中英文申请材料','课程、个人项目、实习如何如实表达','content/case/07-application-materials.md'],
 ['08','AI 产品专项证据','基线、评测、成本与人工接管','content/08-ai-product-lab.md'],
 ['09','产品面试实验室','设计、指标、执行、AI、项目与行为题','content/roles/09-interview-lab.md'],
 ['10','定向申请与毕业衔接','版本、日期、资格核实和投递记录','content/10-application-operations.md'],
 ['11','三十天交付计划','每周产出、验收与失败处理','content/11-action-plan.md'],
 ['12','来源与核验边界','官方资料、读取状态和更新方法','content/12-sources.md']
].map(([id,title,desc,file])=>({id,title,desc,file,route:`chapters/${path.basename(file,'.md')}.html`}));
export const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const read=p=>fs.readFileSync(path.join(ROOT,p),'utf8').replace(/^\uFEFF/,'');
export function sources(){return ['method','jobs','regions'].flatMap(x=>JSON.parse(read(`research/${x}-sources.json`)));}
export function slug(text){return text.replace(/<[^>]*>/g,'').replace(/&[^;]+;/g,'').trim().toLowerCase().replace(/[^\p{L}\p{N}]+/gu,'-').replace(/^-|-$/g,'');}
export function routeFor(file){if(file.startsWith('downloads/')||file.startsWith('assets/'))return file;const c=chapters.find(x=>x.file===file);if(c)return c.route;if(file==='prototypes/offertrail.html')return 'prototype.html';if(file.endsWith('.md')||file.endsWith('.csv'))return `read/${file.replace(/\//g,'-').replace(/\.(md|csv)$/,'.html')}`;return `files/${file}`;}
export function relativeRoute(fromRoute,toRoute){return path.posix.relative(path.posix.dirname(fromRoute),toRoute)||'index.html';}
export function markdown(file,{route=routeFor(file),pdf=false}={}){
 let html=marked.parse(read(file),{gfm:true,breaks:false});const ids=new Map();
 html=html.replace(/<h([1-6])>([\s\S]*?)<\/h\1>/g,(_,n,t)=>{let id=slug(t),count=ids.get(id)||0;ids.set(id,count+1);if(count)id+='-'+count;return `<h${n} id="${id}">${t}</h${n}>`;});
 html=html.replace(/href="([^"\s]+)"/g,(all,href)=>{
  if(/^(https?:|mailto:|tel:|#)/.test(href))return all;
  const [p,hash]=href.split('#');let target=path.posix.normalize(path.posix.join(path.posix.dirname(file),decodeURI(p)));
  if(target==='index.html')return `href="${pdf?ORIGIN+'/':relativeRoute(route,'index.html')}"`;
  const c=chapters.find(x=>x.file===target);
  if(pdf&&c)return `href="#chapter-${c.id}"`;
  const routed=routeFor(target);return `href="${pdf?ORIGIN+'/'+routed:relativeRoute(route,routed)}${hash?'#'+hash:''}"`;
 });
 if(!pdf){html=html.replace(/<table>/g,'<div class="table-wrap"><table>').replace(/<\/table>/g,'</table></div>');
 html=html.replace(/src="([^"\s]+)"/g,(all,src)=>{if(/^(https?:|data:|file:)/.test(src))return all;const target=path.posix.normalize(path.posix.join(path.posix.dirname(file),src));return `src="${relativeRoute(route,target)}"`;});}
 return html;
}
export function parseCSV(text){const rows=[];let row=[],cell='',quote=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quote&&text[i+1]==='"'){cell+='"';i++;}else quote=!quote;}else if(c===','&&!quote){row.push(cell);cell='';}else if((c==='\n'||c==='\r')&&!quote){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(Boolean))rows.push(row);row=[];cell='';}else cell+=c;}if(cell||row.length){row.push(cell);rows.push(row);}return rows;}
export const friendly={
 'jd-breakdown.csv':'岗位拆解表','capability-evidence.csv':'能力证据表','application-timeline.csv':'申请倒排表','decision-log.csv':'决策日志','interview-retrospective.csv':'面试复盘表','metric-dictionary.csv':'指标口径表','research-observations.csv':'原始观察表','offertrail-decision-log.csv':'OfferTrail 完整决策日志','offertrail-metrics.csv':'OfferTrail 指标与验证表','offertrail-test-cases.csv':'OfferTrail 技术与研究测试计划'
};
export function titleFor(file){if(friendly[path.basename(file)])return friendly[path.basename(file)];const m=read(file).match(/^#\s+(.+)$/m);return m?m[1]:path.basename(file);}
export function csvHTML(file){const [head,...rows]=parseCSV(read(file));return `<h1>${esc(titleFor(file))}</h1><p>可编辑 CSV。下载后保留示例的教学标签，再填入自己的真实材料。空白不代表已经完成。</p>`+rows.map((r,i)=>`<section class="data-card"><h3>记录 ${i+1}${i===0?' · 填写示例 / 说明':''}</h3><dl>${head.map((h,j)=>`<dt>${esc(h)}</dt><dd>${esc(r[j]||'待填')}</dd>`).join('')}</dl></section>`).join('');}
export function makeSourcesMarkdown(){
 let out='# 12 来源、核验日期与更新方法\n\n版本：1.0.0。统一核验日：2026-11-13。作者：AI 酋长 Andy。\n\n';
 out+='## 如何判断证据强度\n\n岗位要求使用雇主原文；招聘方式与资格使用政府、学校、雇主官方资料。记录核验日期不代表岗位仍开放，也不代表所有规则都在当天生效。读取状态分为官方正文已读、官方检索摘录、动态页面受限。来源冲突保留双方，不能凭偏好选择一条。\n\n';
 out+='正文中的路线、练习数量、评分锚点和交付计划是作者教学设计；不是雇主招聘标准。OfferTrail 和独立数据题均为教学模拟。官网链接与引用用于核验，不表示对本项目的背书。\n\n';
 out+='## 更新一次国家或岗位卡\n\n**输入：** 原官方来源、现有卡片和上次核验日期。**操作：** 打开官方页面，对比适用对象、生效日、毕业区间与职责；把变化单独记录。**产出：** 新日期、变更内容、旧版本范围和必要的未知状态。**验收：** 新结论能对应原文，未生效政策没有写成当前可用。**失败处理：** 页面关闭就把JD转历史样本；正文受限就保留检索限制；官方冲突就停止给确定的时间结论，并向主管机关核实。\n\n';
 out+='完整机器可读记录在 research/*-sources.json；去重审查见 [DEDUPE-AUDIT](../research/DEDUPE-AUDIT.md)。\n\n';
 const groups=[['方法与申请表达','method'],['岗位与面试官方依据','jobs'],['地区与毕业衔接','regions']];
 for(const [title,key] of groups){out+=`## ${title}\n\n`;for(const s of JSON.parse(read(`research/${key}-sources.json`))){out+=`### ${s.id} · ${s.title}\n\n`;out+=`[${s.issuer} · 官方原文](${s.url}) · 核验 ${s.checked}\n\n`;out+=`**用于：** ${s.claims.join('；')}。\n\n**适用范围：** ${s.scope}。\n\n**限制：** ${s.caveat}；读取状态：${s.verification||'见原始记录'}。\n\n`;}}
 out+='## 作者与咨询\n\n作者：AI 酋长 Andy。微信：**AIPMAndy**。公众号：**AI酋长Andy**。个人官网：[metaver.vip](https://metaver.vip/)。公司官网：[a6no1.cn](https://www.a6no1.cn/)。正文完整免费。咨询可用于岗位定位、作品集诊断和模拟面试，不承诺录用或涨薪。\n';
 fs.writeFileSync(path.join(ROOT,'content/12-sources.md'),out);
}
