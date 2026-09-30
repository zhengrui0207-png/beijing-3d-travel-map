async (page) => {
  await page.waitForFunction(() => !!window.atlas, null, {timeout:30000});
  await page.screenshot({path:'beijing-atlas/output/playwright/overview.png'});
  await page.getByRole('button',{name:'央视大楼',exact:true}).click();
  await page.waitForFunction(()=>{const a=window.atlas,l=a.meta.landmarks.find(l=>l.id==='cctv');return a.selected==='cctv'&&Math.abs(a.controls.target.x-l.x)<.02;});
  await page.screenshot({path:'beijing-atlas/output/playwright/cctv.png'});
  await page.getByRole('switch',{name:'真实路网'}).uncheck();
  const roadsHidden=await page.evaluate(()=>window.atlas.city.children.filter(o=>/^roads/.test(o.userData.layer||'')).every(o=>!o.visible));
  if(!roadsHidden)throw Error('Road toggle did not hide roads');
  await page.getByRole('switch',{name:'真实路网'}).check();
  await page.getByRole('slider',{name:'建筑高度'}).fill('1');
  const scaleCorrect=await page.evaluate(()=>window.atlas.height===1&&window.atlas.city.children.filter(o=>/^(buildings|palace|landmark)/.test(o.userData.layer||'')).every(o=>o.scale.y===1));
  if(!scaleCorrect)throw Error('Height control failed');
  await page.getByRole('slider',{name:'建筑高度'}).fill('2.6');
  await page.getByRole('button',{name:'正上方',exact:true}).click();
  await page.waitForFunction(()=>window.atlas.controls.getPolarAngle()<.03);
  await page.screenshot({path:'beijing-atlas/output/playwright/top.png'});
  await page.getByRole('button',{name:'数据与比例说明'}).click();
  if(!await page.locator('dialog').isVisible())throw Error('About dialog missing');
  await page.getByRole('button',{name:'关闭说明'}).click();
  await page.getByRole('button',{name:'斜俯鸟瞰',exact:true}).click();
  await page.waitForFunction(()=>window.atlas.camera.zoom===1&&window.atlas.controls.getPolarAngle()>.7);
  const report=await page.evaluate(()=>({ready:!!window.atlas,meshCount:window.atlas.city.children.length,landmarks:document.querySelectorAll('.map-label').length,height:window.atlas.height,roadsVisible:window.atlas.city.children.filter(o=>/^roads/.test(o.userData.layer||'')).every(o=>o.visible),width:innerWidth,heightPixels:innerHeight}));
  console.log(JSON.stringify({status:'passed',roadsHidden,scaleCorrect,...report}));
}
