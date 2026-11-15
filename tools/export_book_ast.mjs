import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {ROOT,ORIGIN,DATE,VERSION,chapters,read,parseCSV,titleFor,sources} from './lib.mjs';

const require=createRequire(import.meta.url);
let marked;
try{({marked}=require('marked'));}catch{({marked}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES||'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','marked')));}

// Read-only export. The website build owns source Markdown generation.
function document(file){
  const text=read(file);
  return {file,title:titleFor(file),characters:text.length,format:file.endsWith('.csv')?'csv':'markdown',
    ...(file.endsWith('.csv')?{rows:parseCSV(text)}:{tokens:marked.lexer(text,{gfm:true,breaks:false})})};
}
const appendices=[
 {id:'A',title:'原始材料与研究计划',description:'六条模拟情境、研究假设与真实验证计划',files:['examples/offertrail-raw-materials.md','examples/offertrail-research-plan.md']},
 {id:'B',title:'完整产品作品集',description:'把问题、方案、原型与证据边界串成一个案例',files:['examples/offertrail-portfolio.md']},
 {id:'C',title:'中英文简历成品',description:'保留真实边界的中文与英文申请表达',files:['examples/resume-zh.md','examples/resume-en.md']},
 {id:'D',title:'中英文项目讲解',description:'两分钟与五分钟版本、追问和复盘',files:['examples/project-pitch-zh-en.md']},
];
const templateFiles=fs.readdirSync(path.join(ROOT,'templates')).filter(x=>x!=='README.md'&&/\.(md|csv)$/.test(x)).sort().map(x=>'templates/'+x);
const sections=chapters.filter(c=>c.id!=='12').map(c=>({id:c.id,key:`chapter-${c.id}`,kind:'chapter',title:c.title,description:c.desc,documents:[document(c.file)]}));
sections.push(...appendices.map(a=>({id:a.id,key:`appendix-${a.id}`,kind:'appendix',title:a.title,description:a.description,documents:a.files.map(document)})));
sections.push({id:'E',key:'appendix-E',kind:'templates',title:`${templateFiles.length} 份模板与填写示例`,description:'保留说明、空白模板与完整填写示例',documents:['templates/README.md',...templateFiles].map(document)});
const sourceChapter=chapters.find(c=>c.id==='12');
sections.push({id:'12',key:'chapter-12',kind:'sources',title:'官方来源与核验边界',description:'来源、日期、适用范围、读取限制和政策冲突',documents:[document(sourceChapter.file)]});
const data={title:'中国留学生产品岗位求职保姆级攻略',subtitle:'从真实 JD 出发，拿出能够解释判断、取舍与推进的证据。',author:'AI酋长Andy',date:DATE,version:VERSION,origin:ORIGIN,sourceCount:new Set(sources().map(s=>s.url)).size,templateCount:templateFiles.length,sections};
const out=path.join(ROOT,'tmp/pdfs/book-ast.json');
fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(data,null,2));
const counts={};
function walk(tokens){for(const t of tokens||[]){counts[t.type]=(counts[t.type]||0)+1;walk(t.tokens);if(t.items)for(const i of t.items)walk(i.tokens);}}
for(const s of sections)for(const d of s.documents)walk(d.tokens);
console.log(JSON.stringify({output:out,sections:sections.length,documents:sections.reduce((n,s)=>n+s.documents.length,0),templates:templateFiles.length,uniqueSources:data.sourceCount,tokenTypes:counts}));
