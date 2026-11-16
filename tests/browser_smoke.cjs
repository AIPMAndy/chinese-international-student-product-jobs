'use strict';
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {chromium} = require('playwright');
const {setTimeout: delay} = require('node:timers/promises');

const PORT = 8765;
const ORIGIN = 'http://127.0.0.1:' + PORT + '/';
const server = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1', '--directory', 'dist'], {stdio:'ignore'});
async function waitForServer() {
  for(let n=0;n<50;n++){
    try {const response=await fetch(ORIGIN);if(response.ok)return;}
    catch (_) {}
    await delay(250);
  }
  throw new Error('local dist server did not start');
}
async function main() {
  await waitForServer();
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  try{
    for(const width of [360,390,1280]){
      const context=await browser.newContext({viewport:{width,height:840},acceptDownloads:true});
      const page=await context.newPage();
      const response=await page.goto(ORIGIN,{waitUntil:'networkidle'});
      assert.equal(response.status(),200);
      assert.equal(await page.locator('h1').count(),1,'one H1');
      assert.match(await page.title(),/中国留学生产品求职/);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
      assert.ok(overflow<=2,'horizontal overflow at '+width+': '+overflow);
      assert.equal(await page.locator('.chapter-item').count(),13);
      await page.locator('#chapter-query').fill('不存在的关键词z9876');
      assert.match(await page.locator('#chapter-count').innerText(),/^0 \/ 13/);
      assert.equal(await page.locator('#chapter-empty').isVisible(),true);
      await page.locator('#chapter-clear').click();
      assert.equal(await page.locator('#chapter-query').inputValue(),'');
      assert.equal(await page.locator('#chapter-clear').isDisabled(),true);
      assert.equal(await page.locator('.chapter-item:visible').count(),13);
      assert.equal(await page.locator('#chapter-query').evaluate(el=>document.activeElement===el),true);
      await page.locator('[data-background="business"]').click();
      await page.locator('#plan-role').selectOption('aipm');
      await page.locator('#plan-region').selectOption('sg');
      await page.locator('#build-plan').click();
      assert.match(await page.locator('#plan-title').innerText(),/商科背景 → AI 产品经理/);
      assert.match(await page.locator('#plan-explain').innerText(),/新加坡/);
      const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-plan').click()]);
      assert.equal(download.suggestedFilename(),'product-job-action-plan.txt');
      const stream=await download.createReadStream();
      const parts=[];for await(const chunk of stream)parts.push(chunk);
      const txt=Buffer.concat(parts).toString('utf8');
      assert.equal(txt.charCodeAt(0),0xFEFF,'UTF-8 BOM for Chinese TXT');
      assert.match(txt,/\n选择背景：商科背景/);
      assert.match(txt,/\n目标市场：新加坡/);
      assert.match(txt,/AIPMAndy/);
      assert.match(txt,/教学练习/);assert.match(txt,/AI 产品经理/);
      assert.match(await page.locator('#export-note').innerText(),/未向网站发送/);
      assert.equal(await page.locator('a[href="https://www.a6no1.cn/"]').count()>0,true);
      assert.equal(await page.locator('a[href="https://metaver.vip/services"]').count()>0,true);
      const pdf=await page.request.get(ORIGIN+'downloads/product-jobs-guide-v1.0.0.pdf');
      assert.equal(pdf.status(),200);
      const bytes=await pdf.body();assert.equal(bytes.subarray(0,5).toString(),'%PDF-');
      if(width<820){
        const menu=page.locator('.mobile-menu');
        await menu.click();
        assert.equal(await menu.getAttribute('aria-expanded'),'true');
        await page.keyboard.press('Escape');
        assert.equal(await menu.getAttribute('aria-expanded'),'false');
      }
      console.log('PASS product job workbench at '+width+'px: planner, TXT, search reset, PDF, links, overflow');
      await context.close();
    }
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>{server.kill('SIGTERM');});
