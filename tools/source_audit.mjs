// Rendered from the authoritative research/jobs-sources.json; never describes jobs as open.
const grouping = id => {
  if (id.startsWith('I')) return ['interview', '面试流程参考'];
  if (id.startsWith('T')) return ['technical', '技术方法参考'];
  if (['J02','J08','J10'].includes(id)) return ['program', '项目 / 岗位族说明'];
  return ['jd', '历史岗位 JD 样本'];
};
export function renderSourceAudit(esc, records) {
  const cards = records.map(s => {
    const [group, kind] = grouping(s.id);
    const claims = s.claims.map(x => '<li>' + esc(x) + '</li>').join('');
    return '<article class="audit-card" data-kind="' + group + '" data-id="' + esc(s.id) + '" data-title="' + esc(s.title) + '" data-issuer="' + esc(s.issuer) + '" data-checked="' + esc(s.checked) + '" data-scope="' + esc(s.scope) + '" data-caveat="' + esc(s.caveat) + '" data-url="' + esc(s.url) + '">'
      + '<div class="audit-card-top"><span class="audit-code">' + esc(s.id) + ' / ' + kind + '</span><span class="audit-date">历史核验：<time datetime="' + esc(s.checked) + '">' + esc(s.checked) + '</time></span></div>'
      + '<h2>' + esc(s.title) + '</h2><p class="audit-issuer">' + esc(s.issuer) + ' · ' + esc(s.scope) + '</p>'
      + '<details><summary>历史核验要点（' + s.claims.length + ' 项）</summary><ul>' + claims + '</ul></details>'
      + '<p class="audit-limit"><strong>使用边界：</strong>' + esc(s.caveat) + '</p>'
      + '<a class="audit-source" href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">打开机构原始页面 ↗</a>'
      + '</article>';
  }).join('');
  return '<div class="audit-panel"><p class="audit-eyebrow">EVIDENCE DESK / 可追溯岗位研究</p><h1>岗位来源复核工作台</h1>'
    + '<p class="audit-lead">先读原始 JD，再决定能不能申请。这里是 <strong>' + records.length + ' 条历史研究记录</strong>，不是实时招聘平台。所有核验日期均来自原始记录，不会自动刷新。岗位是否仍开放、学历、毕业届别及工作许可，必须回到雇主与政府官方页面重新确认。</p>'
    + '<div class="notice">资料状态：历史取样。即使原页面仍可打开，也不代表今天仍在招聘；教学原型、个人案例和当前岗位资格应严格区分。</div>'
    + '<div class="audit-controls"><label for="audit-query">搜索机构、岗位、地区、核验要点</label><input id="audit-query" type="search" placeholder="例如：Amazon、AI、德国、APM" autocomplete="off">'
    + '<label for="audit-kind">来源类型</label><select id="audit-kind"><option value="all">全部类型</option><option value="jd">岗位 JD 样本</option><option value="program">项目 / 岗位族说明</option><option value="interview">面试流程参考</option><option value="technical">技术方法参考</option></select>'
    + '<button type="button" id="audit-clear">清空筛选</button><button type="button" id="audit-export">下载当前核验清单 TXT</button></div>'
    + '<p class="audit-count" id="audit-count" role="status" aria-live="polite">共 ' + records.length + ' 条历史记录</p>'
    + '<div class="audit-grid" id="audit-grid">' + cards + '</div>'
    + '<p id="audit-empty" hidden>没有匹配的来源。可以清空搜索或改选来源类型。</p>'
    + '<p id="audit-export-note" class="audit-footnote" role="status" aria-live="polite">仅浏览器本机筛选和导出，不会上传你的查询。</p>'
    + '<h2>每次申请前核对什么？</h2><ol><li>从雇主原文确认职位今天仍可申请，记录新的实际核验日期。</li><li>分别核对申请人教育阶段、毕业时间、地点、工作授权与截止日期。</li><li>任何无法从原文确认的条件保持“待核实”，不要套用历史研究描述。</li></ol>'
    + '<p class="audit-footnote">作者：AI酋长Andy · 微信 AIPMAndy · <a href="https://metaver.vip/">个人官网</a> · <a href="https://www.a6no1.cn/">公司官网</a> · <a href="https://metaver.vip/services">求职诊断与陪跑</a>。内容免费开放，不承诺 Offer。</p></div>';
}
