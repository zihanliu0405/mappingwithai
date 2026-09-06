/* Static research page. Serve from the project root with Live Server. */
'use strict';
const DATA = 'data/pcos_access/';
const colors = ['#eff3e8','#c8d9bb','#91b49b','#528a79','#205b50'];
let rows = [], geography, selected = '06037', map, mapReady = false, stateRate;
const fmt = n => Number(n).toLocaleString('en-US');
const pct = n => Number(n).toFixed(1);
function showError(message) { document.getElementById('map-status').textContent = message; }
async function start() {
 if (!window.d3) throw new Error('D3 could not load. Check your internet connection and reload.');
 const [csv, geo] = await Promise.all([d3.csv(DATA+'california_women_insurance.csv'), d3.json(DATA+'california_pcos_access.geojson')]);
 rows = csv.map(r => ({...r, female_19_44_population:+r.female_19_44_population, female_19_44_uninsured:+r.female_19_44_uninsured, uninsured_pct:+r.uninsured_pct, uninsured_pct_moe90_approx:+r.uninsured_pct_moe90_approx}));
 geography = geo;
 if(rows.length !== 58 || geo.features.length !== 58 || rows.some(r=> !geo.features.some(f=> f.properties.GEOID===r.GEOID))) throw new Error('The county datasets did not match. Please check the local data files.');
 const total = d3.sum(rows,r=>r.female_19_44_uninsured);
 stateRate=100*total/d3.sum(rows,r=>r.female_19_44_population);
 document.getElementById('state-rate').innerHTML=pct(stateRate)+'<span>%</span>';
 document.getElementById('state-count').textContent=fmt(total);
 const la=rows.find(r=>r.GEOID==='06037');
 document.getElementById('burden-insight').textContent=`Los Angeles accounts for ${pct(100*la.female_19_44_uninsured/total)}% of California's estimated uninsured women ages 19–44: ${fmt(la.female_19_44_uninsured)} people. Its uninsured rate is ${pct(la.uninsured_pct)}%.`;
 const select=document.getElementById('county-select');
 select.innerHTML=''; rows.slice().sort((a,b)=>a.county.localeCompare(b.county)).forEach(r=>select.add(new Option(r.county,r.GEOID)));
 select.disabled=false; select.addEventListener('change',()=>choose(select.value,true));
 document.getElementById('sort').addEventListener('change',drawCharts);
 choose(selected,false);
 let timer; window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(drawCharts,150);});
 if(!window.maplibregl){showError('MapLibre could not load. The county menu and charts remain available. Check your connection and reload.');return;}
 try { initMap(); } catch(e) {showError('The map needs WebGL support. Use the county menu and charts to explore the data.');console.error(e);}
}
function choose(id,zoom){
 selected=id; const r=rows.find(r=>r.GEOID===id); if(!r)return;
 document.getElementById('county-select').value=id;
 const delta=r.uninsured_pct-stateRate, moe=r.uninsured_pct_moe90_approx;
 document.getElementById('county-detail').innerHTML=`<h3 class="county-name">${r.county} County</h3><div class="county-value">${pct(r.uninsured_pct)}<span>%</span></div><p class="county-sub">uninsured · women ages 19–44</p><div class="detail-row"><span>Estimated uninsured</span><strong>${fmt(r.female_19_44_uninsured)}</strong></div><div class="detail-row"><span>Population in age group</span><strong>${fmt(r.female_19_44_population)}</strong></div><div class="detail-row"><span>California comparison</span><strong>${delta>=0?'+':''}${pct(delta)} pp</strong></div><div class="uncertainty"><strong>Uncertainty: ±${pct(moe)} pp</strong><br>Approximate 90% interval: ${pct(Math.max(0,r.uninsured_pct-moe))}–${pct(Math.min(100,r.uninsured_pct+moe))}%.${moe>r.uninsured_pct/2?' This estimate has substantial uncertainty.':''}</div>`;
 if(mapReady){map.setFilter('county-selected',['==',['get','GEOID'],id]);if(zoom){const feature=geography.features.find(f=>f.properties.GEOID===id);const points=feature.geometry.coordinates.flat(feature.geometry.type==='MultiPolygon'?2:1);let bounds=new maplibregl.LngLatBounds();points.forEach(p=>bounds.extend(p));map.fitBounds(bounds,{padding:65,maxZoom:8,duration:window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:650});}}
 drawCharts();
}
function initMap(){
 map=new maplibregl.Map({container:'map',style:'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',center:[-119.5,37.2],zoom:4.8,attributionControl:true});
 map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
 map.addControl(new maplibregl.ScaleControl({unit:'imperial'}),'bottom-right');
 const reset=()=>map.fitBounds([[-124.5,32.4],[-114.1,42.1]],{padding:{top:35,bottom:100,left:30,right:30},duration:0});
 document.getElementById('reset-map').onclick=reset;
 map.on('error',()=>showError('Some basemap resources could not load. Check your internet connection; the county menu and charts remain available.'));
 map.on('load',()=>{
  // Desaturate literal and expression-based basemap colors before adding the theme.
  const gray=value=>{if(Array.isArray(value))return value.map(gray);if(typeof value!=='string')return value;const c=d3.color(value);if(!c)return value;const rgb=c.rgb();if(!Number.isFinite(rgb.r))return value;const v=Math.round(.2126*rgb.r+.7152*rgb.g+.0722*rgb.b);return `rgba(${v},${v},${v},${c.opacity})`;};
  for(const layer of map.getStyle().layers){for(const [key,value] of Object.entries(layer.paint||{})){if(key.endsWith('-color'))map.setPaintProperty(layer.id,key,gray(value));}}
  const labelLayer=map.getStyle().layers.find(l=>l.type==='symbol')?.id;
  map.addSource('counties',{type:'geojson',data:geography});
  map.addLayer({id:'county-fill',type:'fill',source:'counties',paint:{'fill-color':['step',['get','uninsured_pct'],colors[0],5,colors[1],8,colors[2],11,colors[3],15,colors[4]],'fill-opacity':.82}},labelLayer);
  map.addLayer({id:'county-lines',type:'line',source:'counties',paint:{'line-color':'#ffffff','line-width':.8}},labelLayer);
  map.addLayer({id:'county-selected',type:'line',source:'counties',filter:['==',['get','GEOID'],selected],paint:{'line-color':'#183c32','line-width':3}},labelLayer);
  mapReady=true;reset();showError('');
  const popup=new maplibregl.Popup({closeButton:false,closeOnClick:false});
  map.on('mousemove','county-fill',e=>{map.getCanvas().style.cursor='pointer';const p=e.features[0].properties;popup.setLngLat(e.lngLat).setHTML(`<strong>${p.county} County</strong><br>${pct(p.uninsured_pct)}% uninsured · ±${pct(p.uninsured_pct_moe90_approx)} pp<br><small>Click to explore</small>`).addTo(map);});
  map.on('mouseleave','county-fill',()=>{map.getCanvas().style.cursor='';popup.remove();});
  map.on('click','county-fill',e=>{popup.remove();choose(e.features[0].properties.GEOID,false);});
 });
}
function drawCharts(){
 if(!rows.length)return;
 const container=document.getElementById('ranking'),width=Math.max(300,container.clientWidth),margin={left:100,right:32,top:35,bottom:10},step=28;
 const order=document.getElementById('sort').value;
 const sorted=rows.slice().sort(order==='name'?(a,b)=>a.county.localeCompare(b.county):order==='count'?(a,b)=>b.female_19_44_uninsured-a.female_19_44_uninsured:(a,b)=>b.uninsured_pct-a.uninsured_pct);
 d3.select(container).selectAll('*').remove();
 const svg=d3.select(container).append('svg').attr('viewBox',`0 0 ${width} ${margin.top+step*rows.length+margin.bottom}`).attr('role','img').attr('aria-label','All 58 counties: uninsured percentage with approximate 90 percent uncertainty intervals.');
 const x=d3.scaleLinear().domain([0,85]).range([margin.left,width-margin.right]);
 svg.append('g').attr('transform',`translate(0,25)`).call(d3.axisTop(x).tickValues([0,20,40,60,80]).tickFormat(d=>d+'%')).call(g=>g.select('.domain').remove()).attr('color','#64756c');
 svg.append('line').attr('x1',x(stateRate)).attr('x2',x(stateRate)).attr('y1',30).attr('y2',margin.top+step*rows.length).attr('stroke','#9c9b89').attr('stroke-dasharray','3 3');
 const g=svg.selectAll('.chart-row').data(sorted).join('g').attr('class','chart-row').attr('transform',(d,i)=>`translate(0,${margin.top+i*step})`).attr('tabindex',0).attr('role','button').attr('aria-label',d=>`${d.county}: ${pct(d.uninsured_pct)} percent uninsured, margin of error ${pct(d.uninsured_pct_moe90_approx)} percentage points. Select county.`).on('click',(e,d)=>choose(d.GEOID,true)).on('keydown',(e,d)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(d.GEOID,true);}});
 g.append('rect').attr('class','row-bg').attr('width',width).attr('height',step).attr('fill',d=>d.GEOID===selected?'#e9f0e5':'transparent');
 g.append('text').attr('x',margin.left-8).attr('y',18).attr('text-anchor','end').attr('font-size',10).attr('fill','#304d43').text(d=>d.county);
 g.append('line').attr('x1',d=>x(Math.max(0,d.uninsured_pct-d.uninsured_pct_moe90_approx))).attr('x2',d=>x(Math.min(100,d.uninsured_pct+d.uninsured_pct_moe90_approx))).attr('y1',14).attr('y2',14).attr('stroke','#809689').attr('stroke-width',2);
 g.append('circle').attr('cx',d=>x(d.uninsured_pct)).attr('cy',14).attr('r',d=>d.GEOID===selected?5:3.5).attr('fill','#285f4f');
 g.append('text').attr('x',width-2).attr('y',18).attr('text-anchor','end').attr('font-size',10).attr('fill','#496154').text(d=>pct(d.uninsured_pct));
 drawBurden();
}
function drawBurden(){
 const host=document.getElementById('burden'),w=Math.max(300,host.clientWidth),left=96,right=58,top=30,step=32;
 const data=rows.slice().sort((a,b)=>b.female_19_44_uninsured-a.female_19_44_uninsured).slice(0,10);
 d3.select(host).selectAll('*').remove();const svg=d3.select(host).append('svg').attr('viewBox',`0 0 ${w} 355`).attr('role','img').attr('aria-label','Ten counties with the largest estimated uninsured female populations ages 19 to 44.');
 const x=d3.scaleLinear().domain([0,d3.max(data,d=>d.female_19_44_uninsured)]).range([left,w-right]);
 svg.append('g').attr('transform','translate(0,22)').call(d3.axisTop(x).ticks(3).tickFormat(d3.format('~s'))).call(g=>g.select('.domain').remove()).attr('color','#64756c');
 const g=svg.selectAll('.chart-row').data(data).join('g').attr('class','chart-row').attr('transform',(d,i)=>`translate(0,${top+i*step})`).attr('tabindex',0).attr('role','button').attr('aria-label',d=>`${d.county}: ${fmt(d.female_19_44_uninsured)} estimated uninsured women. Select county.`).on('click',(e,d)=>choose(d.GEOID,true)).on('keydown',(e,d)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(d.GEOID,true);}});
 g.append('rect').attr('class','row-bg').attr('width',w).attr('height',step).attr('fill','transparent');
 g.append('text').attr('x',left-8).attr('y',20).attr('text-anchor','end').attr('font-size',10).attr('fill','#304d43').text(d=>d.county);
 g.append('rect').attr('x',left).attr('y',7).attr('width',d=>x(d.female_19_44_uninsured)-left).attr('height',18).attr('rx',2).attr('fill',d=>d.GEOID===selected?'#285f4f':'#adc4ab');
 g.append('text').attr('x',d=>x(d.female_19_44_uninsured)+5).attr('y',20).attr('font-size',10).attr('fill','#496154').text(d=>fmt(d.female_19_44_uninsured));
}
start().catch(e=>{console.error(e);showError(e.message+' Open this page through Live Server, not file://.');document.getElementById('county-detail').textContent='Interactive data are unavailable. See the methods and downloadable CSV below.';});
