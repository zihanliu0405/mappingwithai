/* Local tract data; geometry is fetched once, only when Tracts is selected. */
'use strict';
(() => {
 let tracts=[], lookup=new Map(), report, loaded=false, geometryPromise, mode='counties', tractId;
 const $=id=>document.getElementById(id);
 const percent=n=>n===null?'Unavailable':`${(100*n).toFixed(1)}%`;
 const ruralColors={'urban':'#285f4f','large rural':'#0072b2','small rural':'#d55e00','isolated':'#805ba5','unknown':'#888'};
 const numeric=['total_women_19_44','uninsured_women_19_44','uninsured_rate','uninsured_rate_moe90','rate_ci90_low','rate_ci90_high','poverty_rate','medicaid_share'];

 function detail(id){
  const r=lookup.get(id); if(!r)return;
  tractId=id; $('tract-select').value=id;
  const suppressed=r.reliability==='suppressed';
  const county=rows.find(c=>c.GEOID===r.county_geoid);
  $('tract-detail').innerHTML=`<h3>Tract ${r.GEOID}</h3><p>${r.county} County · <strong>${r.reliability}</strong></p><p>County context: ${county?pct(county.uninsured_pct)+'% uninsured':'see county view'}</p>
   <div class="county-value">${suppressed?'Suppressed':percent(r.uninsured_rate)}</div>
   <p>${suppressed?'Fewer than 50 women in the denominator; rate withheld from the display.':`Approximate 90% interval: ${percent(r.rate_ci90_low)}–${percent(r.rate_ci90_high)}`}</p>
   <dl><dt>Estimated uninsured women</dt><dd>${fmt(r.uninsured_women_19_44)}</dd><dt>Total women ages 19–44</dt><dd>${fmt(r.total_women_19_44)}</dd><dt>Poverty · all ages</dt><dd>${percent(r.poverty_rate)}</dd><dt>Medicaid · all ages, both sexes</dt><dd>${percent(r.medicaid_share)}</dd><dt>RUCA 2020 group</dt><dd>${r.rurality}</dd></dl>
   <p class="small">Survey-estimated women, not patients. ${r.reliability==='low'?'CV exceeds 30% or is undefined; avoid individual tract rankings.':''}</p>`;
  if(mapReady && map.getLayer('tract-selected'))map.setFilter('tract-selected',['==',['get','GEOID'],id]);
 }

 function countyChanged(){
  if(!loaded)return;
  const rs=tracts.filter(r=>r.county_geoid===selected);
  const menu=$('tract-select');menu.innerHTML='';
  rs.forEach(r=>menu.add(new Option(`${r.GEOID} · ${r.reliability}`,r.GEOID)));
  if(rs.length)detail(rs.some(r=>r.GEOID===tractId)?tractId:rs[0].GEOID);
  drawWithin();
 }

 async function setMode(value){
  mode=value;
  $('view-counties').setAttribute('aria-pressed',String(value==='counties'));
  $('view-tracts').setAttribute('aria-pressed',String(value==='tracts'));
  $('tract-panel').hidden=value!=='tracts';
  $('county-detail').hidden=value==='tracts';
  $('tract-gray-key').hidden=value!=='tracts';
  window.tractModeActive=value==='tracts' && mapReady && map.getZoom()>=7;
  if(!mapReady){$('tract-map-note').textContent='The map is unavailable. Use the county and tract menus to explore.';return;}
  map.resize();
  if(value==='tracts'){
   document.querySelectorAll('.maplibregl-popup').forEach(el=>el.remove());
   $('tract-map-note').textContent='Loading tract boundaries…';
   try{
    if(!geometryPromise)geometryPromise=d3.json(DATA+'california_tracts_simplified.geojson').catch(e=>{geometryPromise=null;throw e;});
    const geo=await geometryPromise;
    if(!map.getSource('tracts')){
     map.addSource('tracts',{type:'geojson',data:geo});
     map.addLayer({id:'tract-fill',type:'fill',source:'tracts',minzoom:7,paint:{'fill-color':['case',['==',['get','reliability'],'reliable'],['step',['coalesce',['get','uninsured_pct'],0],colors[0],5,colors[1],8,colors[2],11,colors[3],15,colors[4]],'#b8bdbb'],'fill-opacity':.86}},'county-lines');
     map.addLayer({id:'tract-lines',type:'line',source:'tracts',minzoom:7,paint:{'line-color':'#ffffff','line-width':.35}},'county-lines');
     map.addLayer({id:'tract-selected',type:'line',source:'tracts',minzoom:7,filter:['==',['get','GEOID'],tractId||''],paint:{'line-color':'#172e29','line-width':2}},'county-lines');
     map.on('click','tract-fill',e=>selectFeature(e.features[0].properties.GEOID));
     const popup=new maplibregl.Popup({closeButton:false,closeOnClick:true,maxWidth:'300px'});
     map.on('mousemove','tract-fill',e=>{
      map.getCanvas().style.cursor='pointer';const r=lookup.get(e.features[0].properties.GEOID);if(!r)return;
      popup.setLngLat(e.lngLat).setHTML(`<strong>Tract ${r.GEOID} · ${r.county}</strong><br>${r.reliability==='suppressed'?'Rate suppressed':`${percent(r.uninsured_rate)} uninsured · 90% interval ${percent(r.rate_ci90_low)}–${percent(r.rate_ci90_high)}`}<br>${fmt(r.uninsured_women_19_44)} uninsured / ${fmt(r.total_women_19_44)} women 19–44<br>Reliability: ${r.reliability}<br>Poverty (all ages): ${percent(r.poverty_rate)}<br>Medicaid (all ages, both sexes): ${percent(r.medicaid_share)}<br>RUCA: ${r.rurality}<br><small>Click to keep details; keyboard access through the tract menu.</small>`).addTo(map);
     });
     map.on('mouseleave','tract-fill',()=>{map.getCanvas().style.cursor='';popup.remove();});
    }
    if(mode==='tracts' && map.getZoom()<7)choose(selected,true);
   }catch(e){$('tract-map-note').textContent='Tract boundaries could not load. Menus and charts remain available; select Tracts to retry.';return;}
  }
  visibility();
 }
 function selectFeature(id){const r=lookup.get(id);if(!r)return; if(selected!==r.county_geoid)choose(r.county_geoid,false);detail(id);}
 function visibility(){
  if(!mapReady)return;
  const active=mode==='tracts';
  window.tractModeActive=active && map.getZoom()>=7;
  ['tract-fill','tract-lines','tract-selected'].forEach(id=>{if(map.getLayer(id))map.setLayoutProperty(id,'visibility',active?'visible':'none');});
  map.setPaintProperty('county-fill','fill-opacity',active && map.getZoom()>=7?.08:.82);
  $('tract-map-note').textContent=active?(map.getZoom()<7?'Zoom in to level 7 to see tracts. Counties provide context at this scale.':'Gray tracts are low reliability or suppressed. Select a tract on the map or in the menu.'):'County view · select Tracts to explore within-county patterns.';
 }
 function chart(id,label,height=285){
  const host=$(id), w=Math.max(280,host.clientWidth), m={left:48,right:18,top:20,bottom:48};
  d3.select(host).selectAll('*').remove();
  const svg=d3.select(host).append('svg').attr('viewBox',`0 0 ${w} ${height}`).attr('role','img').attr('aria-label',label);
  svg.append('title').text(label);
  return {svg,w,h:height,m};
 }
 function axes(c,x,y,xlabel,ylabel){
  c.svg.append('g').attr('transform',`translate(0,${c.h-c.m.bottom})`).call(d3.axisBottom(x).ticks(5).tickFormat(d=>d+'%'));
  c.svg.append('g').attr('transform',`translate(${c.m.left},0)`).call(d3.axisLeft(y).ticks(5));
  c.svg.append('text').attr('x',(c.w+c.m.left)/2).attr('y',c.h-7).attr('text-anchor','middle').attr('font-size',11).text(xlabel);
  c.svg.append('text').attr('x',c.m.left).attr('y',11).attr('font-size',10).text(ylabel);
 }
 function drawWithin(){
  const rs=tracts.filter(r=>r.county_geoid===selected && r.reliability==='reliable');
  const county=rows.find(r=>r.GEOID===selected);if(!county)return;
  const total=tracts.filter(r=>r.county_geoid===selected).length;
  $('within-note').textContent=`${county.county}: ${rs.length} of ${total} tracts meet the reliability rule. County rate: ${pct(county.uninsured_pct)}%. Circle area represents estimated uninsured women. The dashed line includes all county residents in the study universe.`;
  const c=chart('within-chart',`${county.county} tract rates; ${rs.length} reliable tracts. County rate ${pct(county.uninsured_pct)} percent.`,200);
  const x=d3.scaleLinear().domain([0,Math.max(50,county.uninsured_pct+5)]).range([c.m.left,c.w-c.m.right]);
  c.svg.append('g').attr('transform','translate(0,150)').call(d3.axisBottom(x).ticks(5).tickFormat(d=>d+'%'));
  c.svg.append('line').attr('x1',x(county.uninsured_pct)).attr('x2',x(county.uninsured_pct)).attr('y1',20).attr('y2',150).attr('stroke','#9c7743').attr('stroke-width',2).attr('stroke-dasharray','4 3');
  const radius=d3.scaleSqrt().domain([0,d3.max(rs,r=>r.uninsured_women_19_44)||1]).range([2,10]);
  c.svg.selectAll('circle').data(rs).join('circle').attr('cx',r=>x(100*r.uninsured_rate)).attr('cy',(r,i)=>40+(i%5)*21).attr('r',r=>radius(r.uninsured_women_19_44)).attr('fill','#285f4f').attr('opacity',.7).attr('tabindex',0).attr('role','button').attr('aria-label',r=>`Tract ${r.GEOID}: ${percent(r.uninsured_rate)}, ${fmt(r.uninsured_women_19_44)} uninsured women. Show details.`).on('click',(e,r)=>openTract(r)).on('keydown',(e,r)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openTract(r);}}).append('title').text(r=>`${r.GEOID}: ${percent(r.uninsured_rate)} · ${fmt(r.uninsured_women_19_44)} women`);
  if(!rs.length)c.svg.append('text').attr('x',c.m.left).attr('y',95).attr('font-size',12).text('No tracts meet the reliability rule.');
 }
 function openTract(r){selectFeature(r.GEOID);setMode('tracts');$('tract-panel').scrollIntoView({block:'nearest'});}
 function drawConcentration(){
  const c=chart('concentration-chart','Cumulative share of statewide uninsured women in tracts ranked by uninsured rate.');
  const x=d3.scaleLinear().domain([0,100]).range([c.m.left,c.w-c.m.right]);
  const y=d3.scaleLinear().domain([0,100]).range([c.h-c.m.bottom,c.m.top]);
  axes(c,x,y,'Share of ranked tracts','Share of statewide uninsured women (%)');
  c.svg.append('path').datum(report.concentration.curve).attr('d',d3.line().x(d=>x(100*d.tract_share)).y(d=>y(100*d.uninsured_share))).attr('fill','none').attr('stroke','#285f4f').attr('stroke-width',2.5);
  const top=report.concentration;
  const tx=x(100*top.top_n/top.ranked_n),ty=y(100*top.top_share_statewide);
  c.svg.append('line').attr('x1',tx).attr('x2',tx).attr('y1',ty).attr('y2',y(0)).attr('stroke','#9c7743').attr('stroke-dasharray','4 3');
  c.svg.append('circle').attr('cx',tx).attr('cy',ty).attr('r',5).attr('fill','#9c7743');
  c.svg.append('text').attr('x',tx+9).attr('y',ty-8).attr('font-size',11).text(`Top 10%: ${percent(top.top_share_statewide)}`);
 }
 function drawScatter(id,field,label){
  const rs=tracts.filter(r=>r.reliability==='reliable' && r[field]!==null);
  const stat=report.correlations[field];
  $(id+'-note').textContent=`n = ${stat.n} reliable tracts · Pearson r = ${stat.pearson_r.toFixed(3)}. Each point describes a place, not an individual.`;
  const c=chart(id,`${label} versus uninsured rate for ${rs.length} reliable tracts. Pearson correlation ${stat.pearson_r.toFixed(3)}.`);
  const x=d3.scaleLinear().domain([0,Math.ceil(d3.max(rs,r=>100*r[field])/10)*10]).range([c.m.left,c.w-c.m.right]);
  const y=d3.scaleLinear().domain([0,50]).range([c.h-c.m.bottom,c.m.top]);
  axes(c,x,y,label,'Women ages 19–44 uninsured (%)');
  c.svg.selectAll('circle').data(rs).join('circle').attr('cx',r=>x(100*r[field])).attr('cy',r=>y(100*r.uninsured_rate)).attr('r',3.5).attr('fill',r=>ruralColors[r.rurality]).attr('opacity',.75).append('title').text(r=>`${r.GEOID}, ${r.county}, ${r.rurality}: ${percent(r.uninsured_rate)} uninsured; ${percent(r[field])} ${label}`);
 }
 function draw(){if(!loaded)return;drawWithin();drawConcentration();drawScatter('poverty-scatter','poverty_rate','Poverty · all ages');drawScatter('medicaid-scatter','medicaid_share','Medicaid · all ages, both sexes');}
 async function startTracts(){
  try{
   const [csv,stats]=await Promise.all([d3.csv(DATA+'california_tracts_women_insurance.csv'),d3.json(DATA+'tract_validation.json')]);
   tracts=csv.map(r=>{for(const k of numeric)r[k]=r[k]===''?null:+r[k];return r;});
   lookup=new Map(tracts.map(r=>[r.GEOID,r]));report=stats;loaded=true;
   $('tract-select').disabled=false;$('view-tracts').disabled=false;
   $('tract-select').addEventListener('change',e=>detail(e.target.value));
   $('view-counties').addEventListener('click',()=>setMode('counties'));
   $('view-tracts').addEventListener('click',()=>setMode('tracts'));
   countyChanged();draw();
   let timer;window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(draw,150);});
  }catch(e){$('tract-map-note').textContent='Tract data could not load. County exploration and downloadable data remain available.';console.error(e);}
 }
 window.addEventListener('countychange',countyChanged);
 window.addEventListener('countymapready',()=>{map.on('zoomend',visibility);visibility();});
 if(window.d3)startTracts();
})();
