const STATE_INFO = {
    'FOCUSED': 'Working on or learning about your goal',
    'DRIFTING': 'Off-topic or distracted from your goal'
};

let currentView = 'live';
let sessionsData = [];

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const toggle = document.getElementById('sidebar-toggle');
    
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
    toggle.classList.toggle('collapsed');
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const moonIcon = document.querySelector('.moon-icon');
    const sunIcon = document.querySelector('.sun-icon');
    if (newTheme === 'light') {
        moonIcon.style.display = 'none';
        sunIcon.style.display = 'block';
    } else {
        moonIcon.style.display = 'block';
        sunIcon.style.display = 'none';
    }
}

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);
if (savedTheme === 'light') {
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelector('.moon-icon').style.display = 'none';
        document.querySelector('.sun-icon').style.display = 'block';
    });
}

function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        if (!response.ok) throw new Error('Failed to load history');
        
        const data = await response.json();
        sessionsData = data.sessions || [];
        renderHistory();
    } catch (error) {
        document.getElementById('sidebar-content').innerHTML = `
            <div style="padding: 1rem; color: var(--text-secondary); text-align: center;">
                No history available
            </div>
        `;
    }
}

function renderHistory() {
    if (sessionsData.length === 0) {
        document.getElementById('sidebar-content').innerHTML = `
            <div style="padding: 1rem; color: var(--text-secondary); text-align: center;">
                No past sessions yet
            </div>
        `;
        return;
    }

    const grouped = {};
    sessionsData.forEach((session, index) => {
        const dateKey = formatDate(session.end_ts);
        if (!grouped[dateKey]) {
            grouped[dateKey] = [];
        }
        grouped[dateKey].push({ ...session, index });
    });

    let html = '';
    Object.entries(grouped).forEach(([date, sessions]) => {
        html += `
            <div class="session-group">
                <div class="session-date">${date}</div>
                ${sessions.map(session => `
                    <div class="session-item ${currentView === session.index ? 'active' : ''}" 
                         onclick="viewSession(${session.index})">
                        <div class="session-goal">${session.goal}</div>
                        <div class="session-meta">
                            <span class="session-duration">
                                ⏱️ ${formatDuration(session.end_ts - session.start_ts)}
                            </span>
                            <span class="session-drifts">
                                ⚠️ ${session.drift_count}
                            </span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    });

    document.getElementById('sidebar-content').innerHTML = html;
}

function viewSession(index) {
    currentView = index;
    renderHistory();
    const session = sessionsData[index];
    renderSessionStats(session);
}

function viewLive() {
    currentView = 'live';
    renderHistory();
    loadDashboard();
}

function renderSessionStats(session) {
    const duration = session.end_ts - session.start_ts;
    const stateClass = `state-${session.final_state.toLowerCase()}`;
    const stateEmoji = session.final_state === 'FOCUSED' ? '✅' : '⚠️';

    document.getElementById('dashboard').innerHTML = `
        <div class="cards">
            <div class="card goal-card">
                <div class="card-title">Past Session</div>
                <div class="goal-text">
                    <span>${session.goal}</span>
                    <button class="back-to-live-btn" onclick="viewLive()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"/>
                        </svg>
                        Back to Live
                    </button>
                </div>
                <div class="state-container">
                    <span class="state-badge ${stateClass}">
                        ${stateEmoji} ${session.final_state}
                    </span>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Final Confidence</div>
                <div class="card-value">${Math.round(session.final_confidence * 100)}%</div>
                <div class="card-subtitle">End of session</div>
            </div>

            <div class="card">
                <div class="card-title">Drift Count</div>
                <div class="card-value">${session.drift_count}</div>
                <div class="card-subtitle">Times drifted</div>
            </div>

            <div class="card">
                <div class="card-title">Session Duration</div>
                <div class="card-value">${formatDuration(duration)}</div>
                <div class="card-subtitle">Total focus time</div>
            </div>

            <div class="card">
                <div class="card-title">Ended</div>
                <div class="card-value">${formatDate(session.end_ts)}</div>
                <div class="card-subtitle">${new Date(session.end_ts * 1000).toLocaleTimeString()}</div>
            </div>
        </div>
    `;
}

async function loadDashboard() {
    const dashboard = document.getElementById('dashboard');
    const refreshIcon = document.querySelector('.refresh-icon');
    
    if (refreshIcon) refreshIcon.classList.add('spinning');
    
    try {
        const response = await fetch('/api/stats');
        
        if (!response.ok) {
            throw new Error('Failed to load stats');
        }
        
        const data = await response.json();
        renderDashboard(data);
    } catch (error) {
        dashboard.innerHTML = `
            <div class="error">
                ⚠️ Error loading dashboard: ${error.message}
                <br><br>
                Make sure the Drift Watcher server is running.
            </div>
        `;
    } finally {
        if (refreshIcon) refreshIcon.classList.remove('spinning');
    }
}

function renderDashboard(data) {
    const stateClass = `state-${data.focus_state.toLowerCase()}`;
    const stateEmoji = data.focus_state === 'FOCUSED' ? '✅' : '⚠️';
    const stateInfo = STATE_INFO[data.focus_state] || 'Unknown state';

    const breakdown = data.activity_breakdown || {};
    const breakdownHTML = Object.entries(breakdown)
        .sort((a, b) => b[1] - a[1])
        .map(([category, percent]) => `
            <div class="activity-item">
                <span class="activity-label">${category.replace(/_/g, ' ')}</span>
                <div class="activity-bar">
                    <div class="activity-fill" style="width: ${percent}%"></div>
                </div>
                <span class="activity-percent">${percent}%</span>
            </div>
        `).join('');

    document.getElementById('dashboard').innerHTML = `
        <div class="cards">
            <div class="card goal-card">
                <div class="card-title">Current Goal</div>
                <div class="goal-text">
                    <span>${data.goal}</span>
                    <span class="live-badge">
                        <span class="live-dot"></span>
                        LIVE
                    </span>
                </div>
                <div class="state-container">
                    <span class="state-badge ${stateClass}">
                        ${stateEmoji} ${data.focus_state}
                    </span>
                    <div class="tooltip">
                        <svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="16" x2="12" y2="12"/>
                            <line x1="12" y1="8" x2="12.01" y2="8"/>
                        </svg>
                        <span class="tooltiptext">${stateInfo}</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Confidence</div>
                <div class="card-value">${Math.round(data.confidence * 100)}%</div>
                <div class="card-subtitle">Current state confidence</div>
            </div>

            <div class="card">
                <div class="card-title">Drift Count</div>
                <div class="card-value">${data.drift_count}</div>
                <div class="card-subtitle">Times drifted today</div>
            </div>

            <div class="card">
                <div class="card-title">Session Time</div>
                <div class="card-value">${data.session_minutes}m</div>
                <div class="card-subtitle">Active monitoring time</div>
            </div>

            <div class="card">
                <div class="card-title">Last Check</div>
                <div class="card-value">${data.last_check}</div>
                <div class="card-subtitle">Time since last assessment</div>
            </div>

            ${breakdownHTML ? `
            <div class="card" style="grid-column: 1 / -1;">
                <div class="card-title">Activity Breakdown</div>
                <div class="activity-breakdown">
                    ${breakdownHTML}
                </div>
            </div>
            ` : ''}
        </div>
    `;
}

// Auto-refresh every 30 seconds (only for live view)
setInterval(() => {
    if (currentView === 'live') {
        loadDashboard();
    }
}, 30000);

// Initial load
loadHistory();
loadDashboard();
