// @steered SNARE-1 2026-09-18
let sidebarCollapsed = true;

function toggleSidebar() {
  sidebarCollapsed = !sidebarCollapsed;
  document.getElementById('sidebar').classList.toggle('collapsed', sidebarCollapsed);
}

function formatDuration(minutes) {
  if (!minutes || minutes < 1) return Math.round((minutes || 0) * 60) + 's';
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return h > 0 ? h + 'h ' + m + 'm' : m + 'm';
}

function timeSince(ts) {
  if (!ts) return '—';
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.floor(s / 60) + 'm ago';
  return Math.floor(s / 3600) + 'h ago';
}

function fmtTime(ts) {
  if (!ts) return '—';
  return new Date(ts * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
}

function pageTypeBadge(type) {
  return '<span class="badge badge-' + type + '">' + type.replace(/_/g,' ') + '</span>';
}

function isWorkType(t)    { return ['code','code_internal','docs','wiki_internal','ticket','work_internal'].includes(t); }
function isDistractType(t){ return ['video','video_browse','social'].includes(t); }

// ── Stats ──
async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    if (!r.ok) return;
    const d = await r.json();

    const hasGoal = d.goal && d.goal !== 'No goal set';
    document.getElementById('no-goal-area').style.display   = hasGoal ? 'none'  : 'flex';
    document.getElementById('active-area').style.display    = hasGoal ? 'flex'  : 'none';
    document.getElementById('session-section').style.display= hasGoal ? 'block' : 'none';
    document.getElementById('header-goal').style.display    = hasGoal ? 'flex'  : 'none';
    document.getElementById('btn-end').style.display        = hasGoal ? 'inline-block' : 'none';
    document.getElementById('session-duration').textContent = hasGoal ? formatDuration(d.session_minutes) : '';

    const banner = document.getElementById('agent-banner');
    banner.classList.toggle('visible', hasGoal && !d.agent_running);

    // Pause state
    const now = Date.now() / 1000;
    const pausedUntil = d.paused_until || 0;
    const isPaused = pausedUntil > now;
    const pauseBanner = document.getElementById('pause-banner');
    const pauseRemaining = document.getElementById('pause-remaining');
    const btnPause = document.getElementById('btn-pause');
    const pauseWrap = document.getElementById('pause-wrap');
    if (hasGoal && pauseWrap) pauseWrap.style.display = 'block';
    if (isPaused) {
      const rem = Math.round(pausedUntil - now);
      const m = Math.floor(rem / 60), s = rem % 60;
      if (pauseRemaining) pauseRemaining.textContent = m > 0 ? m+'m '+s+'s' : s+'s';
      if (pauseBanner) pauseBanner.style.display = 'flex';
      if (btnPause) { btnPause.textContent = '▶ Resume'; btnPause.onclick = resumeAgent; }
    } else {
      if (pauseBanner) pauseBanner.style.display = 'none';
      if (btnPause) { btnPause.textContent = '⏸ Pause'; btnPause.onclick = togglePauseMenu; }
    }

    if (!hasGoal) return;

    document.getElementById('header-goal-text').textContent = d.goal;

    // State card
    const sc = document.getElementById('state-card');
    const st = (d.focus_state || 'UNKNOWN').toUpperCase();
    sc.className = 'state-card ' + (st==='FOCUSED'?'focused':st==='DRIFTING'?'drifting':'unknown');
    document.getElementById('state-label').textContent      = st;
    document.getElementById('state-confidence').textContent = d.confidence ? Math.round(d.confidence*100)+'%' : '';
    document.getElementById('state-reason').textContent     = d.reason || '';
    document.getElementById('chip-drifts').textContent      = (d.drift_count||0) + ' drifts today';
    document.getElementById('chip-session').textContent     = '⏱ ' + formatDuration(d.session_minutes);
    document.getElementById('chip-check').textContent       = d.last_check && d.last_check!=='Never' ? 'Checked '+d.last_check+' ago' : 'Not yet checked';

    // Stats tiles
    const fp = Math.round(d.relevant_percent||0);
    const ft = document.getElementById('tile-focus');
    ft.className = 'stat-tile ' + (fp>=70?'green':fp>=50?'yellow':'coral');
    document.getElementById('val-focus-score').textContent  = fp+'%';
    document.getElementById('val-drifts').textContent       = d.drift_count||0;
    document.getElementById('val-session-time').textContent = formatDuration(d.session_minutes);
    const timeLostMin = (d.drift_count||0) * 23;
    document.getElementById('val-time-lost').textContent    = timeLostMin > 0 ? formatDuration(timeLostMin) : '0m';
    const dt = document.getElementById('tile-drifts');
    dt.className = 'stat-tile ' + ((d.drift_count||0)>0?'coral':'green');

    // Timeline
    const sm  = d.session_minutes||0;
    const rp  = Math.min(100, Math.round(d.relevant_percent||0));
    const ip  = Math.min(100-rp, Math.round(d.irrelevant_percent||0));
    const idp = Math.max(0, 100-rp-ip);
    const bar = document.getElementById('timeline-bar');
    bar.innerHTML =
      '<div class="seg-focused"  style="flex:0 0 '+rp+'%"></div>'+
      '<div class="seg-drifting" style="flex:0 0 '+ip+'%"></div>'+
      '<div class="seg-idle"     style="flex:0 0 '+idp+'%"></div>';

    const ticks = document.getElementById('timeline-ticks');
    ticks.innerHTML = sm>120
      ? '<span class="tick">3h ago</span><span class="tick">2h ago</span><span class="tick">1h ago</span><span class="tick">Now</span>'
      : sm>60
      ? '<span class="tick">2h ago</span><span class="tick">1h ago</span><span class="tick">30m ago</span><span class="tick">Now</span>'
      : '<span class="tick">Start</span><span class="tick">—</span><span class="tick">—</span><span class="tick">Now</span>';

    document.getElementById('legend-focused').textContent  = 'Focused '  + formatDuration(sm*rp/100);
    document.getElementById('legend-drifting').textContent = 'Drifting ' + formatDuration(sm*ip/100);
    document.getElementById('legend-idle').textContent     = 'Idle '     + formatDuration(sm*idp/100);

  } catch(e){}
}

// ── Activity ──
async function loadActivity() {
  try {
    const r = await fetch('/api/recent-activity');
    if (!r.ok) return;
    const d = await r.json();
    const list = document.getElementById('activity-list');
    if (!d.pages||d.pages.length===0){
      list.innerHTML='<div style="color:#aaa;font-size:13px">No activity yet.</div>'; return;
    }
    list.innerHTML = d.pages.slice(0,6).map(p => {
      const cls = isWorkType(p.page_type)?'work':isDistractType(p.page_type)?'distract':'';
      return '<div class="feed-item '+cls+'">' +
        '<div class="feed-meta"><span class="feed-time">'+timeSince(p.last_seen_ts)+'</span>'+pageTypeBadge(p.page_type)+'</div>'+
        '<div class="feed-title" title="'+p.title+'">'+p.title+'</div>'+
        '<div class="feed-detail">'+p.duration_min+'min · scroll:'+p.scroll_count+' · keys:'+p.key_count+'</div>'+
      '</div>';
    }).join('');
  } catch(e){}
}

// ── Drift Log ──
async function loadDriftLog() {
  try {
    const r = await fetch('/api/drift-log');
    if (!r.ok) return;
    const d = await r.json();
    const list = document.getElementById('drift-log-list');
    if (!d.drifts||d.drifts.length===0){
      list.innerHTML='<div class="drift-empty">✨ No drifts yet — you\'re crushing it.</div>'; return;
    }
    list.innerHTML = d.drifts.slice(0,8).map(dr => {
      const pages = (dr.pages||[]).filter(Boolean).slice(0,3).join(' · ');
      return '<div class="drift-entry">' +
        '<div class="drift-entry-top">'+
          '<span class="drift-time">'+fmtTime(dr.ts)+'</span>'+
          '<span class="drift-confidence">'+Math.round((dr.confidence||0)*100)+'% confident</span>'+
        '</div>'+
        '<div class="drift-reason">"'+dr.reason+'"</div>'+
        (pages ? '<div class="drift-pages">'+pages+'</div>' : '')+
      '</div>';
    }).join('');
  } catch(e){}
}

// ── Weekly ──
async function loadWeekly() {
  try {
    const r = await fetch('/api/weekly');
    if (!r.ok) return;
    const d = await r.json();
    const days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    const vals = days.map(day => (d.days||{})[day]?.focused_min||0);
    const maxVal = Math.max(...vals, 1);
    document.getElementById('weekly-bars').innerHTML = days.map((day,i) => {
      const h = Math.round((vals[i]/maxVal)*36)+4;
      return '<div class="weekly-bar-wrap">'+
        '<div class="weekly-bar" style="height:'+h+'px"></div>'+
        '<span class="weekly-day">'+day+'</span>'+
      '</div>';
    }).join('');
    document.getElementById('weekly-summary').textContent =
      (d.total_sessions||0)+' sessions · '+(d.total_drifts||0)+' drifts this week';
  } catch(e){}
}

// ── History (sidebar) ──
async function loadHistory() {
  try {
    const r = await fetch('/api/history');
    if (!r.ok) return;
    const d = await r.json();
    const list = document.getElementById('past-goals-list');
    if (!d.sessions||d.sessions.length===0){
      list.innerHTML='<div style="padding:0 16px;font-size:12px;color:#aaa">No past sessions yet.</div>'; return;
    }
    list.innerHTML = d.sessions.slice(0,20).map((s,i) => {
      const dur  = formatDuration((s.end_ts-s.start_ts)/60);
      const fp   = s.final_confidence?Math.round(s.final_confidence*100):0;
      const date = new Date(s.end_ts*1000).toLocaleDateString(undefined,{month:'short',day:'numeric'});
      const did  = 'detail-'+i;
      return '<div class="past-goal-item" onclick="toggleDetail(\''+did+'\',this)">'+
        '<div class="past-goal-title">'+s.goal+'</div>'+
        '<div class="past-goal-stats">'+date+' · '+dur+' · '+s.drift_count+'d · '+fp+'%</div>'+
      '</div>'+
      '<div class="past-goal-detail" id="'+did+'">'+
        '<div class="detail-goal">'+s.goal+'</div>'+
        '<div class="detail-meta">'+date+' &nbsp;·&nbsp; '+dur+' &nbsp;·&nbsp; '+s.drift_count+' drifts &nbsp;·&nbsp; '+fp+'% focused</div>'+
        '<button class="btn-resume" onclick="resumeGoal(\''+s.goal.replace(/'/g,"\\'")+'\')" >Resume this Goal</button>'+
      '</div>';
    }).join('');
  } catch(e){}
}

function toggleDetail(id, itemEl) {
  const detail = document.getElementById(id);
  const isOpen = detail.classList.contains('open');
  document.querySelectorAll('.past-goal-detail.open').forEach(el=>el.classList.remove('open'));
  document.querySelectorAll('.past-goal-item.selected').forEach(el=>el.classList.remove('selected'));
  if (!isOpen){ detail.classList.add('open'); itemEl.classList.add('selected'); }
}

async function resumeGoal(goal) {
  try {
    const r = await fetch('/api/goal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal})});
    if (r.ok){ resetStateDisplay(); await loadStats(); await loadActivity(); await loadHistory(); await loadDriftLog(); }
  } catch(e){}
}

// ── Modal ──
function openModal() {
  document.getElementById('modal-overlay').classList.add('open');
  setTimeout(()=>document.getElementById('goal-input').focus(),50);
}
function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.getElementById('goal-input').value='';
}

function resetStateDisplay() {
  const sc = document.getElementById('state-card');
  sc.className = 'state-card unknown';
  document.getElementById('state-label').textContent      = 'UNKNOWN';
  document.getElementById('state-confidence').textContent = '';
  document.getElementById('state-reason').textContent     = 'Waiting for first assessment…';
  document.getElementById('chip-drifts').textContent      = '0 drifts today';
  document.getElementById('chip-session').textContent     = '⏱ 0m';
  document.getElementById('chip-check').textContent       = 'Not yet checked';
  document.getElementById('val-focus-score').textContent  = '—';
  document.getElementById('val-drifts').textContent       = '0';
  document.getElementById('val-session-time').textContent = '0m';
  document.getElementById('val-time-lost').textContent    = '0m';
  document.getElementById('activity-list').innerHTML      = '<div style="color:#aaa;font-size:13px">No activity yet.</div>';
  document.getElementById('drift-log-list').innerHTML     = '<div class="drift-empty">✨ No drifts yet — you\'re crushing it.</div>';
  document.getElementById('timeline-bar').innerHTML       = '<div class="seg-idle" style="flex:1"></div>';
}

async function submitGoal() {
  const goal = document.getElementById('goal-input').value.trim();
  if (!goal) return;
  try {
    const r = await fetch('/api/goal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal})});
    if (r.ok){ closeModal(); resetStateDisplay(); await loadStats(); await loadActivity(); await loadHistory(); await loadDriftLog(); }
  } catch(e){}
}

async function pauseAgent(minutes) {
  try {
    await fetch('/api/pause', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({minutes})});
    await loadStats();
  } catch(e) {}
}

async function resumeAgent() {
  try {
    await fetch('/api/resume', {method:'POST'});
    await loadStats();
  } catch(e) {}
}

function togglePauseMenu() {
  const menu = document.getElementById('pause-menu');
  menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

function closePauseMenu() {
  const menu = document.getElementById('pause-menu');
  if (menu) menu.style.display = 'none';
}

document.addEventListener('click', function(e) {
  const wrap = document.getElementById('pause-wrap');
  if (wrap && !wrap.contains(e.target)) closePauseMenu();
});

async function endSession() {
  if (!confirm('End this session? It will be archived to your history.')) return;
  try {
    await fetch('/api/session/end',{method:'POST'});
    resetStateDisplay();
    await loadStats(); await loadActivity(); await loadHistory(); await loadDriftLog();
  } catch(e){}
}

document.getElementById('modal-overlay').addEventListener('click',function(e){
  if(e.target===this) closeModal();
});

async function init() {
  await loadStats();
  await loadActivity();
  await loadHistory();
  await loadDriftLog();
  await loadWeekly();
  setInterval(loadStats,    10000);
  setInterval(loadActivity, 30000);
  setInterval(loadDriftLog, 15000);
}

init();
