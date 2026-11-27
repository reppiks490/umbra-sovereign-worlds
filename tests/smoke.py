"""Browser smoke test with inlined JS; avoids sandbox restrictions on loopback/file URLs.
The production browser site serves the exact same ES-module source and CSS as separate files.
Run: python tests/smoke.py [--screenshots]"""
from pathlib import Path
from shutil import which
from playwright.sync_api import sync_playwright
import sys
ROOT=Path(__file__).resolve().parent.parent

def inline():
    html=(ROOT/'index.html').read_text()
    css=(ROOT/'world.css').read_text()
    engine=(ROOT/'engine.mjs').read_text().split('\n',1)[1].replace('export const ', 'const ').replace('export function ', 'function ')
    society=(ROOT/'society.mjs').read_text().replace('export const ', 'const ').replace('export function ', 'function ')
    court=(ROOT/'court.mjs').read_text().split('\n',3)[3].replace('export const ', 'const ').replace('export function ', 'function ')
    view=(ROOT/'observatory.mjs').read_text()
    assert view.startswith('import ')
    view=view.split('\n',3)[3]
    # Worker unavailable in sandbox inline mode; uses tested deterministic main-thread fallback.
    combined='window.Worker=undefined;\n'+society+'\n'+engine+'\n'+court+'\n'+view
    # Inject test-only access to the actual renderer, not a production debug API.
    combined += """
window.__lensCoverageProbe = quality => {
 const old={world:state.world,quality:state.quality,lens:state.lens,lon:state.lon,lat:state.lat};
 const model=createWorld(49021);
 const odd=model.sites.findIndex((site,i)=>i%2===1&&site.pos[2]>.2);
 if(odd<0)throw Error('no visible odd region');
 for(const town of model.towns)town.infected=0;
 model.towns[odd].p=100;model.towns[odd].infected=100;
 const original=ctx.createRadialGradient;let count=0;
 ctx.createRadialGradient=function(...args){
  if(this.globalCompositeOperation==='screen')count++;
  return original.apply(this,args);
 };
 try {
  Object.assign(state,{world:model,quality,lens:'infection',lon:0,lat:0});
  drawUniverse(0);
  return {odd,count};
 }finally{
  ctx.createRadialGradient=original;
  Object.assign(state,old);
 }
};
"""
    html=html.replace('<link rel="stylesheet" href="./world.css">','<style>'+css+'</style>')
    html=html.replace('<script type="module" src="./observatory.mjs"></script>','<script>'+combined+'</script>')
    return html

def test():
 with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=which('chromium') or which('chromium-browser'),args=['--no-sandbox'])
    html=inline()
    for width,height in [(1440,900),(390,844),(768,1024)]:
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded')
        page.wait_for_timeout(900)
        assert page.title()=='UMBRA Ω · Sovereign Worlds Observatory',page.title()
        assert page.locator('#stat-pop').inner_text()!='0'
        page.locator('#pause').click()
        initial=int(page.locator('#hero-turn').inner_text())
        page.locator('#step').click()
        assert int(page.locator('#hero-turn').inner_text())==initial+1
        for _ in range(4): page.locator('#step').click()
        earlier_max=int(page.locator('#turn-range').get_attribute('max'))
        page.locator('#turn-range').fill('1')
        assert int(page.locator('#hero-turn').inner_text())==1
        assert int(page.locator('#turn-range').get_attribute('max'))==earlier_max,'rewind must preserve latest observed turn'
        page.locator('#site-search').fill('Corven')
        assert page.locator('.site-entry').count()==1
        page.locator('.site-entry').click()
        assert page.locator('#selected-name').inner_text()=='Corven'
        page.locator('#site-search').fill('')
        page.locator('#policy-trade').fill('10')
        assert page.locator('#out-trade').inner_text()=='10%'
        page.locator('#experiment').click()
        page.wait_for_function('!document.querySelector("#experiment").disabled',timeout=40000)
        assert page.locator('#exp-status').inner_text().startswith('COMPLETE'),page.locator('#exp-status').inner_text()
        assert page.locator('#exp-mean').inner_text()!='—'
        page.locator('#court-run').click()
        page.wait_for_function('!document.querySelector("#court-run").disabled',timeout=40000)
        court=page.locator('#court-counts').inner_text()
        assert 'FAILED' in court and 'BLOCKED' in court, court
        assert '0 FAILED' in court, court
        assert page.locator('#court-results .court-row').count()>=13
        page.locator('#civic-layer').select_option('relations')
        assert 'DIPLOMATIC RELATIONS' in page.locator('#civic-map-label').inner_text()
        # UM-102: every planetary data lens must switch without UI or render errors.
        assert page.locator('#planet-lens').input_value()=='population'
        for lens in ['resources','infection','climate','civic','off','population']:
            page.locator('#planet-lens').select_option(lens)
            assert page.evaluate('window.__UMBRA.getStatus().lens')==lens
            assert page.locator('#planet-lens-legend').inner_text().strip()
            page.wait_for_timeout(60)
        for quality in [1,.75]:
            probe=page.evaluate('quality => window.__lensCoverageProbe(quality)',quality)
            assert probe['odd']%2==1 and probe['count']==1, (quality,probe)
        # Model and renderer diagnostics must report real numbers rather than infinite/theoretical FPS.
        status=page.evaluate('window.__UMBRA.getStatus()')
        assert 0 <= status['fps'] <= 200, status
        assert status['renderMs'] >= 0 and status['stepMs'] >= 0, status
        viewport_width=page.evaluate('document.documentElement.scrollWidth')
        assert viewport_width<=width+1,f'horizontal overflow {width}: {viewport_width}'
        assert errors==[],f'JS errors for {width}: {errors}'
        print(f'PASS viewport={width}x{height} turn={initial+1}, world pop={page.locator("#stat-pop").inner_text()}, experiment={page.locator("#exp-mean").inner_text()}, overflow={viewport_width-width}')
        if '--screenshots' in sys.argv:
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(ROOT/f'screen-{width}.png'),full_page=True)
            print('Screenshot:',str(ROOT/f'screen-{width}.png'))
        page.close()
    # Reduced-motion mode must keep lens selection functional without animated flicker.
    reduced=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
    reduced_errors=[]
    reduced.on('pageerror',lambda e:reduced_errors.append(str(e)))
    reduced.set_content(html,wait_until='domcontentloaded')
    reduced.wait_for_timeout(350)
    assert reduced.locator('#reduced-status').inner_text()=='YES'
    reduced.locator('#planet-lens').select_option('climate')
    assert reduced.evaluate('window.__UMBRA.getStatus().lens')=='climate'
    for quality in [1,.75]:
        probe=reduced.evaluate('quality => window.__lensCoverageProbe(quality)',quality)
        assert probe['odd']%2==1 and probe['count']==1, (quality,probe)
    assert reduced_errors==[],reduced_errors
    assert reduced.evaluate('document.documentElement.scrollWidth')<=391
    print('PASS reduced-motion mobile lens=climate, zero JS errors and overflow')
    reduced.close()
    browser.close()
if __name__=='__main__':test()
