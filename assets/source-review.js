'use strict';
(() => {
  const search = document.getElementById('audit-query');
  const kind = document.getElementById('audit-kind');
  const cards = [...document.querySelectorAll('.audit-card')];
  const count = document.getElementById('audit-count');
  const empty = document.getElementById('audit-empty');
  const clear = document.getElementById('audit-clear');
  const exportButton = document.getElementById('audit-export');
  const note = document.getElementById('audit-export-note');
  if (!search || !kind || !count || !cards.length) return;

  function visibleCards() {
    return cards.filter(card => !card.hidden);
  }
  function update() {
    const text = search.value.trim().toLocaleLowerCase();
    for (const card of cards) {
      const matchKind = kind.value === 'all' || card.dataset.kind === kind.value;
      const matchText = !text || card.textContent.toLocaleLowerCase().includes(text);
      card.hidden = !(matchKind && matchText);
    }
    const found = visibleCards().length;
    count.textContent = '当前 ' + found + ' / ' + cards.length + ' 条历史记录 · 所有原始核验日均未自动更新';
    empty.hidden = found !== 0;
    exportButton.disabled = found === 0;
    clear.disabled = !text && kind.value === 'all';
  }
  search.addEventListener('input', update);
  kind.addEventListener('change', update);
  clear.addEventListener('click', () => {
    search.value = '';
    kind.value = 'all';
    update();
    search.focus();
  });
  exportButton.addEventListener('click', () => {
    const lines = [
      '中国留学生产品岗位 · 官方来源重新核验清单',
      '作者：AI酋长Andy',
      '历史材料不代表当前职位仍开放；请重新访问雇主官方链接确认。',
      '',
      '筛选：' + (search.value.trim() || '全部关键词') + ' | 类型：' + kind.selectedOptions[0].textContent,
      '共 ' + visibleCards().length + ' 条',
      ''
    ];
    for (const [index, card] of visibleCards().entries()) {
      const d = card.dataset;
      lines.push((index + 1) + '. ' + d.id + ' · ' + d.title);
      lines.push('机构：' + d.issuer);
      lines.push('研究范围：' + d.scope);
      lines.push('原始历史核验：' + d.checked + '（不是今天的核验）');
      lines.push('来源原文：' + d.url);
      lines.push('边界：' + d.caveat);
      lines.push('复核动作：确认职位是否开放、毕业/学历、地区与工作授权、截止日期；不确定时标记待核实。');
      lines.push('');
    }
    lines.push('来源：https://aipmandy.github.io/chinese-international-student-product-jobs/sources-workbench.html');
    lines.push('微信：AIPMAndy | 个人官网：https://metaver.vip/ | 公司官网：https://www.a6no1.cn/');
    lines.push('求职咨询：https://metaver.vip/services');
    const blob = new Blob(['\uFEFF' + lines.join('\n')], {type: 'text/plain;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'product-job-source-recheck.txt';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    note.textContent = '已在本机生成 ' + visibleCards().length + ' 条记录的 TXT；未上传查询或个人资料。';
  });
  update();
})();
