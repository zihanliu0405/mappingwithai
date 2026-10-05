"""Browser smoke checks. Optional: pip install playwright; uses installed Chrome.

Run from the repo root. Screenshots are written to ignored preview_checks/.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}'
    output=ROOT/'preview_checks'
    output.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-webgl','--use-gl=angle','--use-angle=swiftshader'])
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[]; requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url))
        page.goto(url,wait_until='networkidle',timeout=90000)
        page.wait_for_function("document.querySelector('#county-select').options.length===58 && !document.querySelector('#view-tracts').disabled",timeout=60000)
        page.wait_for_function('mapReady',timeout=60000)
        assert not any('california_tracts_simplified.geojson' in r for r in requests),'Geometry was not lazy loaded'
        assert page.locator('#ranking .chart-row').count()==58
        assert page.locator('#poverty-scatter circle').count()==349
        page.locator('#view-tracts').click()
        page.wait_for_function("map.getLayer('tract-fill') && map.getZoom()>=7",timeout=60000)
        page.wait_for_function("map.isSourceLoaded('tracts')",timeout=60000)
        assert page.locator('#tract-panel').is_visible()
        assert page.evaluate("map.getPaintProperty('county-fill','fill-opacity')") == .08
        page.locator('#county-select').select_option('06091')
        assert 'No tracts meet' in page.locator('#within-chart').inner_text()
        page.locator('#county-select').select_option('06037')
        page.wait_for_function("!map.isMoving() && map.isSourceLoaded('tracts')")
        hit=page.evaluate("""() => {
          const box=map.getContainer().getBoundingClientRect();
          for(let y=120;y<box.height-150;y+=60)for(let x=80;x<box.width-60;x+=60){
            const f=map.queryRenderedFeatures([x,y],{layers:['tract-fill']})[0];
            if(f)return {x,y,id:f.properties.GEOID};
          }
          return null;
        }""")
        assert hit,'No rendered tract found'
        page.locator('#map').hover(position={'x':hit['x'],'y':hit['y']})
        assert 'Medicaid (all ages, both sexes)' in page.locator('.maplibregl-popup-content').inner_text()
        page.locator('#map').click(position={'x':hit['x'],'y':hit['y']})
        assert hit['id'] in page.locator('#tract-detail').inner_text()
        page.locator('#county-select').select_option('06037')
        page.locator('#tract-select').focus()
        page.keyboard.press('ArrowDown');page.keyboard.press('Enter')
        assert page.locator('#tract-select').input_value() in page.locator('#tract-detail').inner_text()
        page.locator('#explore').screenshot(path=str(output/'desktop-explorer.png'))
        page.locator('#tract-findings').screenshot(path=str(output/'desktop-findings.png'))
        page.locator('#view-counties').click()
        assert page.evaluate("map.getLayoutProperty('tract-fill','visibility')")=='none'
        assert page.evaluate("map.getPaintProperty('county-fill','fill-opacity')")==.82
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(500)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Horizontal overflow'
        page.locator('#view-tracts').click()
        page.locator('#explore').screenshot(path=str(output/'mobile-explorer.png'))
        assert not errors,errors
        nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
        fallback=nojs.new_page();fallback.goto(url)
        assert '9,129 ACS tracts' in fallback.locator('#tract-check-summary').inner_text()
        assert fallback.locator('noscript').is_visible()
        print('PASS: lazy geometry, county/tract modes, 58 county rows, 349 scatter points, empty-county state, keyboard tract menu, mobile overflow, no-JS findings; no page errors.')
        browser.close()
    server.shutdown()

if __name__=='__main__':
    main()
