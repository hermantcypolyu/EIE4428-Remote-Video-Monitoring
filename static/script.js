const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
const toast=(m,bad=false)=>{const t=$('#toast');t.textContent=m;t.style.borderColor=bad?'#ff5571':'#20d7ff';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)};
async function post(url,body={}){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok||j.ok===false)throw new Error(j.error||'Request failed');toast(j.message);return j}
function duration(s){const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;return `${h}h ${m}m ${x}s`}
async function status(){try{const s=await (await fetch('/api/status',{cache:'no-store'})).json();
  $('#camera').textContent=s.online?'ONLINE':'OFFLINE';$('#camera').className=s.online?'good':'bad';
  $('#motion').textContent=s.motion?'DETECTED':(s.motion_enabled?'CLEAR':'DISABLED');$('#motion').className=s.motion?'bad':'good';
  $('#recording').textContent=s.recording?'ON':'OFF';$('#recording').className=s.recording?'bad':'';$('#clients').textContent=s.clients;
  $('#resolution').textContent=s.resolution;$('#fps').textContent=s.fps;$('#frameSize').textContent=s.avg_frame_kb+' KB';$('#bitrate').textContent=s.bitrate_mbps+' Mbps';
  $('#uptime').textContent=duration(s.uptime_s);$('#eventCount').textContent=s.event_count;renderEvents(s.events);
}catch(e){$('#camera').textContent='DISCONNECTED';$('#camera').className='bad'}}
function renderEvents(events){const box=$('#events');if(!events.length){box.innerHTML='<p class="muted">No event recorded yet.</p>';return}box.innerHTML=events.map(e=>`<div class="event-row"><strong>#${e.id}</strong><span>${e.time.replace('T',' ')}</span><a href="/media/events/${encodeURIComponent(e.snapshot)}">Snapshot</a><a href="/media/events/${encodeURIComponent(e.recording)}">Recording</a></div>`).join('')}
$$('[data-profile]').forEach(b=>b.addEventListener('click',async()=>{try{await post('/api/profile',{profile:b.dataset.profile});$$('[data-profile]').forEach(x=>x.classList.toggle('active',x===b))}catch(e){toast(e.message,true)}}));
$('#snapshot').onclick=()=>post('/api/snapshot').catch(e=>toast(e.message,true));$('#recordStart').onclick=()=>post('/api/record/start').catch(e=>toast(e.message,true));$('#recordStop').onclick=()=>post('/api/record/stop').catch(e=>toast(e.message,true));
$('#sensitivity').onchange=e=>post('/api/sensitivity',{sensitivity:e.target.value}).catch(x=>toast(x.message,true));$('#motionToggle').onchange=e=>post('/api/motion',{enabled:e.target.checked}).catch(x=>toast(x.message,true));
$('#clearRoi').onclick=()=>{post('/api/roi',{roi:null}).then(()=>$('#roiBox').hidden=true).catch(e=>toast(e.message,true))};
const stage=$('#stage'), roi=$('#roiBox');let start=null;
stage.addEventListener('pointerdown',e=>{const r=stage.getBoundingClientRect();start={x:e.clientX-r.left,y:e.clientY-r.top};stage.setPointerCapture(e.pointerId)});
stage.addEventListener('pointermove',e=>{if(!start)return;const r=stage.getBoundingClientRect(),x=Math.max(0,Math.min(e.clientX-r.left,r.width)),y=Math.max(0,Math.min(e.clientY-r.top,r.height));roi.hidden=false;roi.style.left=Math.min(start.x,x)+'px';roi.style.top=Math.min(start.y,y)+'px';roi.style.width=Math.abs(x-start.x)+'px';roi.style.height=Math.abs(y-start.y)+'px'});
stage.addEventListener('pointerup',e=>{if(!start)return;const r=stage.getBoundingClientRect(),x=Math.max(0,Math.min(e.clientX-r.left,r.width)),y=Math.max(0,Math.min(e.clientY-r.top,r.height)),v=[Math.min(start.x,x)/r.width,Math.min(start.y,y)/r.height,Math.max(start.x,x)/r.width,Math.max(start.y,y)/r.height];start=null;if((v[2]-v[0])*(v[3]-v[1])<.01){roi.hidden=true;return}post('/api/roi',{roi:v}).catch(x=>toast(x.message,true))});
stage.ondblclick=()=>$('#clearRoi').click();setInterval(()=>{$('#clock').textContent=new Date().toLocaleString();status()},1000);status();
