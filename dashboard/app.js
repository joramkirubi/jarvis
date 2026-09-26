'use strict';
const $ = id => document.getElementById(id);
const incoming = location.hash.slice(1);
if (incoming) {
  sessionStorage.setItem('jarvisToken', incoming);
  history.replaceState(null, '', location.pathname);
}
const token = sessionStorage.getItem('jarvisToken') || '';
let latest = null, lastTranscript = '', lastActivity = '', lastTargets = '', memoryVersion = '', toastTimer;
const names = {idle:'STANDBY',starting:'INITIALIZING',wake:'WAKE LISTENING',connecting:'CONNECTING',listening:'LISTENING',speaking:'SPEAKING',stopping:'STOPPING',error:'ATTENTION'};
const headlines = {idle:'Ready when you are.',starting:'Bringing Jarvis online.',wake:'A word is all it takes.',connecting:'Making the connection.',listening:'I’m listening.',speaking:'A voice for your ideas.',stopping:'Wrapping things up.',error:'Let’s check the connection.'};
function node(tag, text, cls) { const el=document.createElement(tag); if(text!==undefined) el.textContent=text; if(cls) el.className=cls; return el; }
function timeLabel(t) { return new Date(t*1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}); }
function toast(message) { clearTimeout(toastTimer); $('toast').textContent=message; $('toast').hidden=false; toastTimer=setTimeout(()=>{$('toast').hidden=true;},4500); }
async function api(path, body) {
  const res=await fetch('/api/'+path,{method:body===undefined?'GET':'POST', headers:{Authorization:'Bearer '+token,...(body===undefined?{}:{'Content-Type':'application/json'})},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(path.startsWith('google/') ? 120000 : 10000)});
  const data=await res.json();
  if(!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}
async function action(path, body, message) {
  try { const result=await api(path,body); if(result.ok===false) throw new Error(result.message || 'Action was not completed'); if(message) toast(message); await pollOnce(); return result; }
  catch(e) { toast(e.message); return null; }
}
function renderTranscript(items) {
  const signature=JSON.stringify(items);
  if(signature===lastTranscript) return;
  lastTranscript=signature;
  if(!items.length) return;
  const area=$('transcript'), stick=area.scrollHeight-area.scrollTop-area.clientHeight<80;
  area.replaceChildren();
  for(const item of items) {
    const row=node('article',undefined,'message '+(item.role==='user'?'user':'assistant'));
    const label=node('div',undefined,'message-label'); label.append(node('span',item.role==='user'?'YOU':'JARVIS'),node('time',timeLabel(item.time)));
    row.append(label,node('p',item.text,'message-body')); area.append(row);
  }
  if(stick) area.scrollTop=area.scrollHeight;
}
function renderActivity(items) {
  const signature=JSON.stringify(items);
  if(signature===lastActivity) return;
  lastActivity=signature;
  $('eventCount').textContent=items.length+' EVENTS';
  if(!items.length) return;
  const area=$('activity'); area.replaceChildren();
  for(const item of [...items].reverse()) {
    const row=node('div',undefined,'activity-item '+item.kind);
    row.append(node('time',timeLabel(item.time)),node('span',item.title,'event-title'),node('span',item.detail,'event-detail')); area.append(row);
  }
}
const appNames={github:'GitHub',chatgpt:'ChatGPT',vscode:'VS Code',calculator:'Calculator',notepad:'Notepad',pesaiq:'PesaIQ'};
function renderTargets(targets, permissions) {
  const signature=JSON.stringify([targets,permissions]); if(signature===lastTargets) return; lastTargets=signature;
  $('apps').replaceChildren(); $('appToggles').replaceChildren();
  for(const target of targets) {
    const name=appNames[target.id] || target.id;
    if(target.enabled) {
      const button=node('button',undefined,'app-button'); button.title=target.description; button.disabled=permissions.open!==true;
      button.append(node('span',name.slice(0,1),'app-icon'),node('span',name),node('span','↗','arrow'));
      button.addEventListener('click',()=>action('launch',{target:target.id},'Launch requested. See activity for the result.')); $('apps').append(button);
    }
    const label=node('label',undefined,'toggle-row'); label.append(node('span',name));
    const toggle=document.createElement('input'); toggle.type='checkbox'; toggle.checked=target.enabled; toggle.setAttribute('aria-label','Enable '+name);
    toggle.addEventListener('change',async()=>{ const result=await action('target',{id:target.id,enabled:toggle.checked},'Application settings saved.'); if(!result) toggle.checked=!toggle.checked; });
    label.append(toggle); $('appToggles').append(label);
  }
  if(!$('apps').children.length) $('apps').append(node('p','No targets enabled. Choose Manage to review your configured apps.','empty-note'));
}
async function memory() {
  try {
    const data=await api('memory'); const signature=JSON.stringify(data.items); if(signature===memoryVersion) return; memoryVersion=signature;
    const area=$('memory'); area.replaceChildren();
    if(!data.items.length) area.append(node('p','Nothing saved yet. Say “Remember that I prefer short answers.”','empty-note'));
    for(const item of data.items) {
      const row=node('div',undefined,'memory-item'), contents=node('div'); contents.append(node('strong',item.key),node('p',item.value));
      const button=node('button','×','delete-memory'); button.title='Delete '+item.key; button.setAttribute('aria-label','Delete memory '+item.key);
      button.addEventListener('click',async()=>{ if(confirm('Delete the saved preference “'+item.key+'”?')) { if(await action('forget',{key:item.key},'Preference deleted.')) await memory(); } });
      row.append(contents,button); area.append(row);
    }
  } catch(e) { $('memory').replaceChildren(node('p',e.message,'empty-note')); memoryVersion=''; }
}
function render(state) {
  latest=state; const idle=['idle','error'].includes(state.status), live=['wake','listening','speaking'].includes(state.status);
  $('connection').textContent='DASHBOARD ONLINE'; $('connection').style.color='';
  $('errorBanner').hidden=state.status!=='error'; $('errorBanner').textContent=state.detail;
  $('statusLabel').textContent=names[state.status] || state.status.toUpperCase();
  $('statusDot').style.background=state.status==='error'?'#f1a6a1':live?'#7de5e3':'#88a4ae';
  $('topHint').textContent=state.dry_run?'Dry run enabled. Launches and saves are simulated.':'Your workspace, at your command.';
  $('headline').textContent=headlines[state.status] || 'Ready when you are.';
  $('detail').textContent=state.detail; $('orbState').textContent=names[state.status] || 'STANDBY';
  $('orb').classList.toggle('live',live); $('orb').style.setProperty('--level',state.level);
  $('coreBadge').textContent=live?'MIC LIVE':'MIC '+(idle?'OFF':'PREPARING');
  $('micLevel').style.width=Math.round(state.level*100)+'%'; $('levelText').textContent=Math.round(state.level*100)+'%';
  $('modeTag').textContent=state.status==='wake'?'LOCAL WAKE':idle?'STANDBY':'VOICE SESSION';
  $('privacyNote').textContent=state.status==='wake'?'Wake audio stays on this computer':idle?'Microphone off':'Conversation audio uses ElevenLabs';
  $('conversationHint').textContent=state.status==='wake'?'Say “Hey Jarvis”, then wait for the greeting.':idle?'Start a session to talk with Jarvis.':'Say “Go to sleep” to return to wake listening.';
  $('keyStatus').textContent=state.has_key?'Key configured':'Key missing'; $('keyStatus').style.color=state.has_key?'':'#edc787';
  $('modelStatus').textContent=state.has_model?'Installed':'Not installed'; $('modelStatus').style.color=state.has_model?'':'#edc787';
  $('execution').textContent=state.dry_run?'Dry run':'Allowlisted';
  $('sessions').textContent=state.sessions; $('commands').textContent=state.commands;
  $('uptime').textContent=String(Math.floor(state.uptime/60)).padStart(2,'0')+':'+String(state.uptime%60).padStart(2,'0');
  $('talkButton').disabled=!idle || !state.has_key; $('wakeButton').disabled=!idle || !state.has_model || !state.has_key;
  $('sleepButton').disabled=idle || state.status==='wake' || state.status==='stopping' || !state.has_model;
  $('stopButton').disabled=idle;
  renderTranscript(state.transcript); renderActivity(state.activity); renderTargets(state.targets,state.permissions);
}
let polling=false;
async function pollOnce() {
  if(polling) return; polling=true;
  try { render(await api('state')); }
  catch(e) {
    $('connection').textContent='DISCONNECTED'; $('connection').style.color='#edc787';
    $('errorBanner').hidden=false; $('errorBanner').textContent=e.message==='Failed to fetch'?'Dashboard disconnected. Check the Python terminal.':e.message;
    $('orb').classList.remove('live'); $('micLevel').style.width='0'; $('coreBadge').textContent='STATE UNKNOWN';
    document.querySelectorAll('[data-action]').forEach(b=>b.disabled=true);
  } finally { polling=false; }
}
for(const button of document.querySelectorAll('[data-action]')) button.addEventListener('click',()=>action('control',{action:button.dataset.action}));
function settings() {
  if(!latest) return;
  const select=$('deviceSelect'); select.replaceChildren(new Option('Windows default input',''));
  for(const d of latest.devices) select.add(new Option(d.id+' · '+d.name,String(d.id)));
  if(![...select.options].some(o=>o.value===String(latest.settings.device))) select.add(new Option('Configured: '+latest.settings.device,String(latest.settings.device)));
  select.value=String(latest.settings.device); $('rateSelect').value=latest.settings.rate; $('channelsSelect').value=latest.settings.channels;
  $('deviceError').textContent=latest.device_error || 'Saved here for the dashboard; terminal launchers keep using .env settings.';
  if(!$('settingsDialog').open) $('settingsDialog').showModal();
}
$('openSettings').addEventListener('click',settings);
$('closeSettings').addEventListener('click',()=>$('settingsDialog').close());
$('refreshDevices').addEventListener('click',async()=>{await action('devices',{});settings();});
$('settingsForm').addEventListener('submit',async e=>{
  e.preventDefault(); const result=await action('settings',{device:$('deviceSelect').value,rate:Number($('rateSelect').value),channels:Number($('channelsSelect').value)},'Audio settings saved.'); if(result) $('settingsDialog').close();
});
$('manageApps').addEventListener('click',()=>$('appsDialog').showModal());
$('closeApps').addEventListener('click',()=>$('appsDialog').close());
$('refreshMemory').addEventListener('click',memory);
function clock(){const now=new Date();$('clock').textContent=now.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',hour12:false});$('date').textContent=now.toLocaleDateString([],{day:'numeric',month:'short',year:'numeric'});}
clock();setInterval(clock,1000);pollOnce();memory();setInterval(pollOnce,350);setInterval(memory,5000);
