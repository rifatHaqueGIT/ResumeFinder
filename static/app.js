/**
 * Resume Intelligence Dashboard — Frontend Logic
 *
 * Fetches data from Flask API and renders all dashboard sections:
 * Overview, Role Deep-Dive, Resume Inspector, Keyword Matrix, Resume Tips
 */

// ═══════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════

const state = {
    overview: null,
    resumes: [],
    selectedRole: null,
    selectedResumeId: null,
    roles: [],
    roleData: {},        // cached role detail data
    matrixData: null,
    resumeDetails: {},   // cached resume detail data
};


// ═══════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════

function getScoreColor(score) {
    if (score >= 65) return 'var(--score-high)';
    if (score >= 40) return 'var(--score-medium)';
    return 'var(--score-low)';
}

function getScoreClass(score) {
    if (score >= 65) return 'score-high';
    if (score >= 40) return 'score-medium';
    return 'score-low';
}

function createScoreGauge(score, size = 56) {
    const r = (size - 6) / 2;
    const circ = 2 * Math.PI * r;
    const offset = circ - (score / 100) * circ;
    const color = getScoreColor(score);

    return `
        <div class="score-gauge" style="width:${size}px;height:${size}px">
            <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
                <circle class="score-gauge-bg" cx="${size/2}" cy="${size/2}" r="${r}"
                    fill="none" stroke-width="4"/>
                <circle class="score-gauge-fill" cx="${size/2}" cy="${size/2}" r="${r}"
                    fill="none" stroke="${color}" stroke-width="4"
                    stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
                    stroke-linecap="round"/>
            </svg>
            <div class="score-gauge-text ${getScoreClass(score)}">${score}</div>
        </div>
    `;
}

function truncateFilename(name, maxLen = 30) {
    if (name.length <= maxLen) return name;
    const ext = name.slice(name.lastIndexOf('.'));
    return name.slice(0, maxLen - ext.length - 3) + '...' + ext;
}


// ═══════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}


// ═══════════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════════

function initNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.dataset.section;
            switchSection(section);
        });
    });
}

function switchSection(sectionId) {
    // Update nav
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');

    // Update sections
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(`section-${sectionId}`).classList.add('active');

    // Lazy load data
    if (sectionId === 'roles' && !state.selectedRole && state.roles.length) {
        selectRole(state.roles[0]);
    }
    if (sectionId === 'inspector' && state.selectedResumeId === null && state.resumes.length) {
        selectResume(0);
    }
    if (sectionId === 'matrix' && !state.matrixData) {
        loadMatrix();
    }
    if (sectionId === 'tips') {
        initTipsSection();
    }
}


// ═══════════════════════════════════════════════════════════════════
// OVERVIEW
// ═══════════════════════════════════════════════════════════════════

async function loadOverview() {
    const [overview, resumes] = await Promise.all([
        fetchJSON('/api/overview'),
        fetchJSON('/api/resumes'),
    ]);

    state.overview = overview;
    state.resumes = resumes;
    state.roles = overview.roles;

    renderHeroStats(overview);
    renderRoleCards(overview);
    renderRoleTabs();
    renderResumeSelector();
}

function renderHeroStats(data) {
    const container = document.getElementById('hero-stats');

    const avgAll = Object.values(data.avg_scores);
    const overallAvg = avgAll.length
        ? Math.round(avgAll.reduce((a, b) => a + b, 0) / avgAll.length)
        : 0;

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${data.total_resumes}</div>
            <div class="stat-label">Resumes Found</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.total_cover_letters}</div>
            <div class="stat-label">Cover Letters</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.roles.length}</div>
            <div class="stat-label">Target Roles</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${overallAvg}</div>
            <div class="stat-label">Avg HM Score</div>
        </div>
    `;
}

function renderRoleCards(data) {
    const container = document.getElementById('role-cards');
    container.innerHTML = '';

    for (const role of data.roles) {
        const best = data.best_per_role[role];
        if (!best) continue;

        const card = document.createElement('div');
        card.className = 'role-card';
        card.onclick = () => {
            switchSection('roles');
            selectRole(role);
        };

        card.innerHTML = `
            <div class="role-card-title">${role}</div>
            <div class="role-card-best">Best: <strong>${truncateFilename(best.filename)}</strong></div>
            <div class="role-card-score">
                ${createScoreGauge(best.score)}
                <div class="score-details">
                    <div class="score-label ${getScoreClass(best.score)}">${best.label}</div>
                    <div class="score-coverage">${best.coverage}% keyword coverage</div>
                </div>
            </div>
        `;
        container.appendChild(card);
    }
}


// ═══════════════════════════════════════════════════════════════════
// ROLE DEEP-DIVE
// ═══════════════════════════════════════════════════════════════════

function renderRoleTabs() {
    const container = document.getElementById('role-tabs');
    const matrixTabs = document.getElementById('matrix-role-tabs');
    container.innerHTML = '';
    matrixTabs.innerHTML = '';

    for (const role of state.roles) {
        // Role Deep-Dive tabs
        const tab = document.createElement('div');
        tab.className = 'role-tab';
        tab.textContent = role;
        tab.onclick = () => selectRole(role);
        container.appendChild(tab);

        // Matrix tabs
        const mTab = document.createElement('div');
        mTab.className = 'role-tab';
        mTab.textContent = role;
        mTab.onclick = () => selectMatrixRole(role);
        matrixTabs.appendChild(mTab);
    }
}

async function selectRole(role) {
    state.selectedRole = role;

    // Update tabs
    document.querySelectorAll('#role-tabs .role-tab').forEach(t => {
        t.classList.toggle('active', t.textContent === role);
    });

    // Fetch or use cache
    if (!state.roleData[role]) {
        state.roleData[role] = await fetchJSON(`/api/role/${encodeURIComponent(role)}`);
    }

    renderRoleContent(state.roleData[role]);
}

function renderRoleContent(data) {
    const container = document.getElementById('role-content');

    // Rankings
    let html = '<div class="ranking-list">';
    data.resumes.forEach((r, i) => {
        html += `
            <div class="ranking-item">
                <div class="ranking-rank">#${i + 1}</div>
                <div class="ranking-info">
                    <h3>${r.filename}</h3>
                    <div class="ranking-meta">
                        ${r.doc_type} &middot; ${r.coverage}% coverage &middot; ${r.found}/${r.total} keywords
                    </div>
                </div>
                <div class="ranking-score-area">
                    ${createScoreGauge(r.score, 48)}
                    <span class="score-label ${getScoreClass(r.score)}">${r.label}</span>
                </div>
            </div>
        `;
    });
    html += '</div>';

    // Keyword reference for this role
    html += '<div class="keyword-section">';
    html += `<h3>Keywords for ${data.role}</h3>`;
    html += '<div class="keyword-categories">';
    for (const [category, keywords] of Object.entries(data.keywords)) {
        html += `
            <div class="keyword-category">
                <div class="keyword-category-title">${category}</div>
                <div class="keyword-pills">
                    ${keywords.map(kw => `<span class="kw-pill found">${kw}</span>`).join('')}
                </div>
            </div>
        `;
    }
    html += '</div></div>';

    container.innerHTML = html;
}


// ═══════════════════════════════════════════════════════════════════
// RESUME INSPECTOR
// ═══════════════════════════════════════════════════════════════════

function renderResumeSelector() {
    const container = document.getElementById('resume-selector');
    container.innerHTML = '';

    state.resumes.forEach(r => {
        const chip = document.createElement('div');
        chip.className = 'resume-chip';
        chip.textContent = truncateFilename(r.filename, 25);
        chip.title = r.filename;
        chip.onclick = () => selectResume(r.id);
        chip.dataset.id = r.id;
        container.appendChild(chip);
    });
}

async function selectResume(id) {
    state.selectedResumeId = id;

    // Update chips
    document.querySelectorAll('.resume-chip').forEach(c => {
        c.classList.toggle('active', parseInt(c.dataset.id) === id);
    });

    // Fetch or use cache
    if (!state.resumeDetails[id]) {
        state.resumeDetails[id] = await fetchJSON(`/api/resume/${id}`);
    }

    renderInspector(state.resumeDetails[id]);
}

function renderInspector(data) {
    const container = document.getElementById('inspector-content');

    // Header info
    let html = `
        <div style="margin-bottom:24px">
            <h2 style="font-size:18px;font-weight:700;color:var(--text-bright);margin-bottom:4px">${data.filename}</h2>
            <p style="font-size:12px;color:var(--text-secondary)">
                ${data.doc_type} &middot; ${data.word_count} words &middot; ${data.size_kb} KB &middot; Modified: ${data.modified}
                ${data.companies.length ? ' &middot; Companies: ' + data.companies.join(', ') : ''}
            </p>
        </div>
    `;

    // Role comparison grid
    html += '<div class="inspector-grid">';
    for (const role of state.roles) {
        const analysis = data.role_analyses[role];
        const isBest = role === data.best_role;

        html += `
            <div class="inspector-role-card" style="${isBest ? 'border-color: rgba(0,212,255,0.3)' : ''}">
                <h3>${role} ${isBest ? '<span style="font-size:10px;color:var(--score-high)">&#9733; BEST FIT</span>' : ''}</h3>
                <div style="display:flex;align-items:center;gap:16px">
                    ${createScoreGauge(analysis.score, 64)}
                    <div>
                        <div class="score-label ${getScoreClass(analysis.score)}" style="font-size:16px">${analysis.label}</div>
                        <div class="score-coverage">${analysis.keywords.coverage_pct}% keywords</div>
                    </div>
                </div>
                <div class="breakdown-list">
                    ${Object.entries(analysis.breakdown).map(([name, b]) => `
                        <div class="breakdown-item">
                            <span class="breakdown-label">${name}</span>
                            <div class="breakdown-bar-container">
                                <div class="breakdown-bar" style="width:${(b.score / b.max) * 100}%"></div>
                            </div>
                            <span class="breakdown-value">${b.score}/${b.max}</span>
                        </div>
                    `).join('')}
                </div>

                <!-- Keywords -->
                <div style="margin-top:16px">
                    ${Object.entries(analysis.keywords.categories).map(([cat, kws]) => `
                        <div style="margin-bottom:8px">
                            <div style="font-size:11px;color:var(--accent-cyan);font-weight:600;text-transform:uppercase;margin-bottom:4px">${cat}</div>
                            <div class="keyword-pills">
                                ${kws.map(k => `<span class="kw-pill ${k.found ? 'found' : 'missing'}">${k.keyword}</span>`).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    html += '</div>';

    container.innerHTML = html;
}


// ═══════════════════════════════════════════════════════════════════
// KEYWORD MATRIX
// ═══════════════════════════════════════════════════════════════════

let matrixSelectedRole = null;

async function loadMatrix() {
    if (!state.matrixData) {
        state.matrixData = await fetchJSON('/api/keyword-matrix');
    }
    if (state.roles.length && !matrixSelectedRole) {
        selectMatrixRole(state.roles[0]);
    }
}

function selectMatrixRole(role) {
    matrixSelectedRole = role;

    document.querySelectorAll('#matrix-role-tabs .role-tab').forEach(t => {
        t.classList.toggle('active', t.textContent === role);
    });

    if (state.matrixData) {
        renderMatrix(role);
    }
}

function renderMatrix(role) {
    const container = document.getElementById('matrix-content');
    const data = state.matrixData;
    const roleMatrix = data.matrix[role];
    const resumeNames = data.resume_names;

    if (!roleMatrix || !resumeNames.length) {
        container.innerHTML = '<div class="empty-state"><p>No data available</p></div>';
        return;
    }

    let html = '<div class="matrix-table-wrapper"><table class="matrix-table">';

    // Header
    html += '<thead><tr><th>Category</th><th>Keyword</th>';
    resumeNames.forEach(name => {
        html += `<th class="resume-header" title="${name}">${truncateFilename(name, 15)}</th>`;
    });
    html += '</tr></thead><tbody>';

    // Body — grouped by category
    for (const [category, keywords] of Object.entries(roleMatrix.categories)) {
        keywords.forEach((kw, i) => {
            html += '<tr>';
            if (i === 0) {
                html += `<td class="cat-cell" rowspan="${keywords.length}">${category}</td>`;
            }
            html += `<td class="kw-cell">${kw.keyword}</td>`;
            resumeNames.forEach(name => {
                const found = kw.resumes[name];
                html += `<td><span class="matrix-dot ${found ? 'found' : 'missing'}"></span></td>`;
            });
            html += '</tr>';
        });
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}


// ═══════════════════════════════════════════════════════════════════
// RESUME TIPS
// ═══════════════════════════════════════════════════════════════════

function initTipsSection() {
    const resumeSelect = document.getElementById('tips-resume-select');
    const roleSelect = document.getElementById('tips-role-select');

    // Populate resume select
    if (resumeSelect.options.length <= 1) {
        state.resumes.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = r.filename;
            resumeSelect.appendChild(opt);
        });
    }

    // Populate role select
    if (roleSelect.options.length <= 1) {
        state.roles.forEach(role => {
            const opt = document.createElement('option');
            opt.value = role;
            opt.textContent = role;
            roleSelect.appendChild(opt);
        });
    }

    resumeSelect.onchange = loadTips;
    roleSelect.onchange = loadTips;
}

async function loadTips() {
    const resumeId = document.getElementById('tips-resume-select').value;
    const role = document.getElementById('tips-role-select').value;

    if (!resumeId || !role) {
        document.getElementById('tips-content').innerHTML =
            '<div class="empty-state"><p>Select a resume and a role to see tips</p></div>';
        return;
    }

    // Fetch resume detail
    if (!state.resumeDetails[resumeId]) {
        state.resumeDetails[resumeId] = await fetchJSON(`/api/resume/${resumeId}`);
    }

    const data = state.resumeDetails[resumeId];
    const analysis = data.role_analyses[role];

    renderTips(analysis, role, data.filename);
}

function renderTips(analysis, role, filename) {
    const container = document.getElementById('tips-content');
    const tips = analysis.tips;

    if (!tips.length) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No specific tips — this resume is well-optimized for ${role}!</p>
            </div>
        `;
        return;
    }

    // Score summary at top
    let html = `
        <div style="display:flex;align-items:center;gap:20px;margin-bottom:24px;padding:16px 20px;background:var(--bg-card);border-radius:var(--radius);border:1px solid var(--border)">
            ${createScoreGauge(analysis.score, 64)}
            <div>
                <div style="font-size:16px;font-weight:700;color:var(--text-bright)">${filename}</div>
                <div style="font-size:13px;color:var(--text-secondary)">
                    ${analysis.label} fit for <strong style="color:var(--accent-cyan)">${role}</strong>
                    &middot; ${analysis.keywords.coverage_pct}% keyword coverage
                    &middot; ${tips.length} improvement tips
                </div>
            </div>
        </div>
    `;

    // Tips list
    html += '<div class="tips-list">';
    tips.forEach(tip => {
        html += `
            <div class="tip-card severity-${tip.severity}">
                <div class="tip-header">
                    <span class="tip-badge ${tip.severity}">${tip.severity}</span>
                    <span class="tip-title">${tip.title}</span>
                </div>
                <div class="tip-description">${tip.description}</div>
                ${tip.keywords.length ? `
                    <div class="tip-keywords">
                        ${tip.keywords.map(kw => `<span class="tip-kw">${kw}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}


// ═══════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════

async function init() {
    initNavigation();

    try {
        await loadOverview();
        document.getElementById('loading-overlay').classList.add('hidden');
    } catch (err) {
        console.error('Failed to load dashboard data:', err);
        document.getElementById('loading-overlay').innerHTML = `
            <div class="loader">
                <p style="color:var(--score-low)">Failed to load data. Is the server running?</p>
                <p style="font-size:12px;color:var(--text-muted);margin-top:8px">${err.message}</p>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', init);
