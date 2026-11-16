'use strict';
(function(){
  const root=document;
  const $=id=>root.getElementById(id);
  const menu=root.querySelector('.mobile-menu');
  const nav=$('global-nav');
  function closeMenu(){if(!menu||!nav)return;menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','打开网站导航');nav.classList.remove('open');}
  if(menu&&nav){
    menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'关闭网站导航':'打开网站导航');nav.classList.toggle('open',open);});
    nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
    root.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});
  }
  const backgroundRoutes={
    tech:{label:'技术背景',goal:'从已有技术项目出发，把实现能力转成用户需求、约束、方案比较和产品决策证据。',step2:'选一个自己完成的技术项目，补齐用户问题与至少两个方案的取舍。'},
    business:{label:'商科背景',goal:'从业务理解和用户流程出发，证明你能把分析问题转成可实施、可验证的产品方案。',step2:'从真实用户任务出发，补出流程、字段、异常状态和一棵可计算的指标树。'},
    experienced:{label:'有相关经历',goal:'从真正参与的项目中，厘清个人权限、贡献、事实结果和未由你控制的因素。',step2:'挑一项有证据的决策，明确你负责什么、有哪些替代方案与协作约束。'}
  };
  const regionNames={cn:'中国内地 / 回国求职',us:'美国',uk:'英国',ca:'加拿大',au:'澳大利亚',sg:'新加坡',hk:'中国香港',other:'其他覆盖市场'};
  let background='tech';
  root.querySelectorAll('[data-background]').forEach(btn=>{
    btn.addEventListener('click',()=>{
      background=btn.dataset.background;
      root.querySelectorAll('[data-background]').forEach(b=>{const active=b===btn;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});
    });
  });
  function buildPlan(){
    const bg=backgroundRoutes[background];
    const role=$('plan-role').value;
    const region=$('plan-region').value;
    const roleLabel=role==='aipm'?'AI 产品经理':'产品经理 / APM';
    $('plan-title').textContent=bg.label+' → '+roleLabel;
    $('plan-explain').textContent=bg.goal+(region?' 目标地区：'+regionNames[region]+'。':' 请进一步选择目标市场，以核对当地申请资格。');
    const steps=[
      '找一份真实 '+roleLabel+' JD，核对学历、毕业日期、岗位要求与申请截止。',
      bg.step2,
      role==='aipm'?'补上AI产品的评测集、失败处理、成本风险和人工接管；整理成作品集与面试证据。':'完成案例、双语简历和一轮能够被追问的模拟面试。'
    ];
    if(region)steps[0]+=' 同时核对'+regionNames[region]+'的官方资格与工作许可说明。';
    $('plan-list').replaceChildren(...steps.map((s,i)=>{const el=root.createElement('div');const n=root.createElement('b');n.textContent=String(i+1).padStart(2,'0');const t=root.createElement('span');t.textContent=s;el.append(n,t);return el;}));
    $('plan-link').href=role==='aipm'?'chapters/08-ai-product-lab.html':'chapters/02-route-and-gap.html';
    $('plan-link').innerHTML=role==='aipm'?'进入 AI 产品专项训练 <span aria-hidden="true">→</span>':'进入背景与能力诊断 <span aria-hidden="true">→</span>';
    const tag=root.querySelector('.result-tag');if(tag)tag.textContent=region?'定制练习建议':'示例路径';
  }
  if($('build-plan'))$('build-plan').addEventListener('click',buildPlan);
  const exportPlan=$('export-plan');
  if(exportPlan)exportPlan.addEventListener('click',()=>{
    const steps=[...root.querySelectorAll('#plan-list>div span')].map((node,i)=>String(i+1)+'. '+node.textContent);
    const region=$('plan-region').value;
    const text=['中国留学生产品求职 · 我的行动清单','作者：AI酋长Andy | https://metaver.vip/','',
      '选择背景：'+backgroundRoutes[background].label,'岗位方向：'+$('plan-role').selectedOptions[0].textContent,
      '目标市场：'+(region?regionNames[region]:'未选择（需自行确定）'),'',
      $('plan-title').textContent,$('plan-explain').textContent,'',...steps,'',
      '本清单是教学练习，不是岗位、签证或工作许可结论。','请以雇主、政府和学校最新官方信息核验资格及日期。',
      '来源与说明：https://aipmandy.github.io/chinese-international-student-product-jobs/chapters/12-sources.html',
      '咨询与陪跑：https://metaver.vip/services','微信：AIPMAndy'].join('\n');
    const url=URL.createObjectURL(new Blob(['\uFEFF'+text],{type:'text/plain;charset=utf-8'}));
    const link=root.createElement('a');link.href=url;link.download='product-job-action-plan.txt';root.body.append(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('export-note').textContent='清单已在本机生成；请查看浏览器下载列表。未向网站发送所选信息。';
  });
  const regionDetails={
    uk:{heading:'英国 · United Kingdom',desc:'先核实岗位属于 internship、graduate scheme 还是 experienced hire；对照毕业时间窗口、雇主岗位资格和当前适用的工作许可要求。',checks:['官方招聘入口','毕业生项目周期','工作资格核验']},
    us:{heading:'美国 · United States',desc:'按雇主的实习/毕业生岗位 JD 核对教育阶段与申请资格；涉及实习授权、毕业后工作安排时，以学校和相关政府机构说明为准。',checks:['校招/实习职责','校园职业中心','工作授权核验']},
    sg:{heading:'新加坡 · Singapore',desc:'重点核对雇主岗位描述、工作经验要求、毕业生申请入口和雇佣许可；不能把其他国家的工作资格规则直接套用。',checks:['岗位原文','雇主要求','准证官方规则']},
    cn:{heading:'中国内地 · 回国求职',desc:'区分国内校招、留学生专项/补招和社招，核对毕业届别、学历认证材料、用人单位要求与投递时间。',checks:['校招届别','回国材料','作品集与面试']},
    other:{heading:'其他地区 · 独立核验',desc:'覆盖亚洲、欧洲、北美和大洋洲的其他就业市场。先确定具体国家，再逐一查看政府、学校和雇主官方招聘信息。',checks:['明确国家与城市','逐国官方来源','岗位资格与日期']}
  };
  root.querySelectorAll('[data-region]').forEach(btn=>btn.addEventListener('click',()=>{
    const detail=regionDetails[btn.dataset.region];
    root.querySelectorAll('[data-region]').forEach(b=>{let active=b===btn;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
    $('region-heading').textContent=detail.heading;
    $('region-text').textContent=detail.desc;
    const tags=root.querySelector('.region-checks');tags.replaceChildren(...detail.checks.map(t=>{const el=root.createElement('span');el.textContent=t;return el;}));
    const widget=$('region-display');widget.querySelector('.region-number').textContent='COUNTRY PATH / '+String([...root.querySelectorAll('[data-region]')].indexOf(btn)+1).padStart(2,'0');
  }));
  const search=$('chapter-query');
  if(search){
    search.addEventListener('input',()=>{
      const query=search.value.trim().toLocaleLowerCase();
      let n=0;
      root.querySelectorAll('.chapter-item').forEach(item=>{
        const hay=(item.textContent+' '+item.dataset.search).toLocaleLowerCase();
        item.hidden=!!query&&!hay.includes(query);
        if(!item.hidden)n++;
      });
      $('chapter-count').textContent=n+' / '+root.querySelectorAll('.chapter-item').length+' CHAPTERS';
      $('chapter-empty').hidden=n!==0;
      const clear=$('chapter-clear');if(clear)clear.disabled=!query;
    });
  }
  const clearSearch=$('chapter-clear');
  if(clearSearch&&search)clearSearch.addEventListener('click',()=>{search.value='';search.dispatchEvent(new Event('input',{bubbles:true}));search.focus();});
  const copy=$('copy-wechat');
  if(copy)copy.addEventListener('click',async()=>{
    try{
      await navigator.clipboard.writeText('AIPMAndy');
      copy.textContent='已复制 AIPMAndy';
    }catch(_){
      copy.textContent='微信：AIPMAndy（可手动复制）';
    }
  });
})();