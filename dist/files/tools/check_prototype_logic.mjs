import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';

// Check the prototype's actual pure date and blocking functions, without a browser.
// This is software verification, not user research or a work-permit decision.
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const html=fs.readFileSync(path.join(root,'prototypes/offertrail.html'),'utf8');
const start=html.indexOf('function zonedTime(');
const end=html.indexOf('function renderCards(');
if(start<0||end<=start)throw new Error('Pure prototype functions were not found');
const context=vm.createContext({Intl,Date,Object,String,Number});
vm.runInContext(html.slice(start,end),context);
const checks=[];
function check(id,description,actual,expected){
  checks.push({id,description,actual,expected,passed:actual===expected});
}
check('L01','London winter time to Beijing',context.beijing(context.zonedTime('2026-11-20T17:00','Europe/London').date),'2026-11-21 01:00');
check('L02','New York winter time to Beijing',context.beijing(context.zonedTime('2026-11-24T17:00','America/New_York').date),'2026-11-25 06:00');
check('L03','Missing date stays unknown',context.zonedTime('','America/New_York').error,'日期或时区待确认');
check('L04','Missing zone stays unknown',context.zonedTime('2026-11-20T17:00','').error,'日期或时区待确认');
check('L05','Impossible calendar date is rejected',context.zonedTime('2026-02-30T17:00','UTC').error,'日期或时间无效');
check('L06','New York DST spring gap is rejected',context.zonedTime('2026-03-08T02:30','America/New_York').error,'该当地时间不存在或无法解析，请人工核实');
check('L07','New York DST repeated hour requires review',context.zonedTime('2026-11-01T01:30','America/New_York').error,'夏令时切换产生重复时间，请补充明确偏移后人工核实');
check('L08','Invalid IANA zone is rejected',context.zonedTime('2026-11-20T17:00','Invalid/Zone').error,'无效 IANA 时区，请重新选择');
const missing={local:'',zone:'',sourceChecked:false,resume:true,portfolio:true,permission:true};
check('L09','Complete materials cannot cover unknown time and source',context.blockers(missing).length,2);
const explicit={local:'2026-11-20T17:00',zone:'Europe/London',sourceChecked:true,resume:true,portfolio:true,permission:true};
check('L10','Explicit information removes blockers only',context.blockers(explicit).length,0);
const report={checked:'2026-11-13',scope:'Actual pure functions extracted from prototypes/offertrail.html; no browser, no real users, no application submission',passed:checks.every(c=>c.passed),checks};
fs.writeFileSync(path.join(root,'verification/prototype-logic.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,checks:checks.length,failed:checks.filter(c=>!c.passed).map(c=>c.id)}));
if(!report.passed)process.exitCode=1;
