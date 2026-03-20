const BACKEND_BASE = "http://127.0.0.1:8000";
const API_BASE = `${BACKEND_BASE}/admin`;
let JWT_TOKEN = localStorage.getItem('aura_admin_token');

// Initialize Lucide Icons
lucide.createIcons();

// Init checking
document.addEventListener("DOMContentLoaded", () => {
    if (JWT_TOKEN) {
        showView('dashboardView');
        loadDashboard();
        loadFAQs();
    } else {
        showView('authView');
    }
});

// View Management
function showView(viewId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
}

function switchTab(tabId) {
    document.querySelectorAll('.side-menu li').forEach(li => li.classList.remove('active'));
    event.currentTarget.classList.add('active');

    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    document.getElementById(tabId + 'Tab').classList.add('active');

    // Route to appropriate loader based on active tab
    if (tabId === 'dashboard') loadDashboard();
    if (tabId === 'users') loadUsers();
    if (tabId === 'faqs') loadFAQs();
    if (tabId === 'prompts') loadPrompts();
    if (tabId === 'api_keys') loadApiKeys();
    if (tabId === 'logs') loadLogs();
    if (tabId === 'documents') loadDocuments();
    if (tabId === 'timetables') loadTimetables();
    if (tabId === 'faculty') loadFaculty();
}

function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

// Show error utility
function showError(elementId, msg) {
    const el = document.getElementById(elementId);
    el.textContent = msg;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
}

// Authentication
async function handleLogin(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = 'PROCESSING...';

    const formData = new URLSearchParams();
    formData.append('username', document.getElementById('username').value);
    formData.append('password', document.getElementById('password').value);

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!res.ok) throw new Error("Invalid credentials");

        const data = await res.json();
        JWT_TOKEN = data.access_token;
        localStorage.setItem('aura_admin_token', JWT_TOKEN);

        document.getElementById('loginForm').reset();
        showView('dashboardView');
        loadDashboard();
        loadFAQs();

    } catch (err) {
        showError('loginError', err.message);
    } finally {
        btn.innerHTML = originalText;
    }
}

function logout() {
    JWT_TOKEN = null;
    localStorage.removeItem('aura_admin_token');
    showView('authView');
}

// Interceptor for Auth Headers
function authHeaders() {
    return {
        'Authorization': `Bearer ${JWT_TOKEN}`,
        'Content-Type': 'application/json'
    };
}

// FAQs Management
async function loadFAQs() {
    try {
        const res = await fetch(`${API_BASE}/all-faq`, { headers: authHeaders() });

        if (res.status === 401) return logout();

        const data = await res.json();
        const tbody = document.getElementById('faqTableBody');
        tbody.innerHTML = '';

        data.forEach(faq => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${faq.question}</strong></td>
                <td><span style="background: rgba(165,86,251,0.2); padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; color: #A556FB;">${faq.category}</span></td>
                <td><small style="color: #a0a0b0;">${faq.keywords.join(', ')}</small></td>
                <td>
                    <button class="action-btn" onclick="deleteFaq('${faq.id}')" title="Delete Node">
                        <i data-lucide="trash-2" size="18"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        lucide.createIcons(); // Re-init icons for dynamic content
    } catch (err) {
        console.error(err);
    }
}

async function handleAddFaq(e) {
    e.preventDefault();
    const payload = {
        question: document.getElementById('faqQuestion').value,
        answer: document.getElementById('faqAnswer').value,
        category: document.getElementById('faqCategory').value,
        keywords: document.getElementById('faqKeywords').value.split(',').map(k => k.trim())
    };

    try {
        const res = await fetch(`${API_BASE}/add-faq`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });
        if (res.status === 401) return logout();
        if (!res.ok) throw new Error("Failed to inject data");

        document.getElementById('faqForm').reset();
        closeModal('addFaqModal');
        loadFAQs();
    } catch (err) {
        alert(err.message);
    }
}

async function deleteFaq(id) {
    if (!confirm("Purge this node from the database?")) return;
    try {
        const res = await fetch(`${API_BASE}/delete-faq/${id}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        if (res.status === 401) return logout();
        if (res.ok) loadFAQs();
    } catch (err) {
        console.error(err);
    }
}

// Documents Management
async function loadDocuments() {
    try {
        const res = await fetch(`${API_BASE}/all-documents`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        
        const container = document.getElementById('documentsContainer');
        if (!container) return;
        container.innerHTML = '';

        // Grouping logic
        const groups = {};
        data.forEach(doc => {
            const branch = doc.branch || 'GENERAL';
            if (!groups[branch]) groups[branch] = [];
            groups[branch].push(doc);
        });

        // Render each group
        Object.keys(groups).sort().forEach(branch => {
            const branchDocs = groups[branch];
            const section = document.createElement('div');
            section.className = 'branch-section mb-5';
            section.innerHTML = `
                <div class="section-subheader" style="display:flex; align-items:center; gap:10px; margin-bottom:15px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">
                    <i data-lucide="layers" size="18" color="#a556fb"></i>
                    <h3 style="color:#a556fb; margin:0; font-size:1.1rem; letter-spacing:1px;">${branch.toUpperCase()} MATRIX</h3>
                </div>
                <div class="table-container">
                    <table class="cyber-table">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Subject</th>
                                <th>Sem</th>
                                <th>Year</th>
                                <th>Branch</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${branchDocs.map(doc => `
                                <tr>
                                    <td><strong>${doc.title}</strong></td>
                                    <td><span style="color:#00d2ff">${doc.subject || 'N/A'}</span></td>
                                    <td><span style="color:#00ff88">${doc.semester || '-'}</span></td>
                                    <td><span style="color:#ffcc00">${doc.year || '-'}</span></td>
                                    <td><small style="color:var(--text-dim)">${doc.branch || 'GEN'}</small></td>
                                    <td>
                                        <button class="action-btn" onclick="deleteDocument('${doc.id}')" title="Delete Document">
                                            <i data-lucide="trash-2" size="18"></i>
                                        </button>
                                        <button class="action-btn" style="color:#00d2ff" onclick="window.open('${BACKEND_BASE}/chat/download/${doc.id}', '_blank')" title="Download">
                                             <i data-lucide="download" size="18"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            container.appendChild(section);
        });

        if (data.length === 0) {
            container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-dim);">No knowledge nodes active in the neural grid.</div>';
        }

        lucide.createIcons();
    } catch (e) { console.error(e); }
}

async function handleUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('branch', document.getElementById('uploadBranch').value);
    formData.append('semester', document.getElementById('uploadSemester').value);
    formData.append('subject', document.getElementById('uploadSubject').value);
    formData.append('year', document.getElementById('uploadYear').value);

    const btn = e.target.querySelector('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = 'UPLOADING...';

    try {
        const res = await fetch(`${API_BASE}/upload-document`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${JWT_TOKEN}` },
            body: formData
        });

        if (res.status === 401) return logout();
        if (!res.ok) throw new Error("Upload failed");

        closeModal('uploadModal');
        e.target.reset();
        loadDocuments();
    } catch (err) {
        alert(err.message);
    } finally {
        btn.innerHTML = originalText;
    }
}

async function deleteDocument(id) {
    if (!confirm("Purge this document node? This will remove all neural references.")) return;
    try {
        const res = await fetch(`${API_BASE}/delete-document/${id}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        if (res.status === 401) return logout();
        if (res.ok) loadDocuments();
    } catch (e) { console.error(e); }
}

// -----------------------------------------
// TIMETABLE MANAGEMENT
// -----------------------------------------

async function loadTimetables() {
    try {
        const res = await fetch(`${API_BASE}/timetables`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        
        const tbody = document.getElementById('timetableTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(entry => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${entry.day}</strong></td>
                <td><span style="color:#a556fb">${entry.branch}</span></td>
                <td><span style="color:#00ff88">${entry.semester}</span></td>
                <td><span style="color:#00d2ff">${entry.time}</span></td>
                <td><strong>${entry.subject}</strong></td>
                <td><small>${entry.room || ''} ${entry.professor ? ' / ' + entry.professor : ''}</small></td>
                <td>
                    <button class="action-btn" onclick="deleteTimetable('${entry.id}')" title="Delete Entry">
                        <i data-lucide="trash-2" size="18"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        lucide.createIcons();
    } catch (e) { console.error(e); }
}

async function saveTimetable(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = 'SYNCHRONIZING...';

    const entry = {
        day: document.getElementById('ttDay').value,
        branch: document.getElementById('ttBranch').value,
        semester: parseInt(document.getElementById('ttSemester').value),
        time: document.getElementById('ttTime').value,
        subject: document.getElementById('ttSubject').value,
        room: document.getElementById('ttRoom').value,
        professor: document.getElementById('ttProfessor').value
    };

    try {
        const res = await fetch(`${API_BASE}/timetables`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(entry)
        });

        if (res.status === 401) return logout();
        if (!res.ok) throw new Error("Synchronization failed");

        closeModal('addTimetableModal');
        e.target.reset();
        loadTimetables();
    } catch (err) {
        alert(err.message);
    } finally {
        btn.innerHTML = originalText;
    }
}

async function deleteTimetable(id) {
    if (!confirm("Remove this timing sequence from the neural grid?")) return;
    try {
        const res = await fetch(`${API_BASE}/timetables/${id}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        if (res.status === 401) return logout();
        if (res.ok) loadTimetables();
    } catch (e) { console.error(e); }
}

async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard-stats`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        
        document.getElementById("kpiTotalUsers").textContent = data.total_users;
        document.getElementById("kpiActiveUsers").textContent = data.active_users;
        document.getElementById("kpiTotalConvs").textContent = data.total_conversations;
        document.getElementById("kpiApiRequests").textContent = data.api_requests_today;
    } catch (e) {
        console.error("Dashboard err", e);
    }
}

async function loadUsers() {
    try {
        const res = await fetch(`${API_BASE}/users`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        
        const tbody = document.getElementById('userTableBody');
        tbody.innerHTML = '';
        data.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.id.substring(0,8)}...</td>
                <td>${u.name}</td>
                <td>${new Date(u.signup_date).toLocaleDateString()}</td>
                <td><span style="color: ${u.status === 'active' ? '#00ff88' : '#ff3366'}">${u.status.toUpperCase()}</span></td>
                <td>
                    <button class="action-btn" onclick="blockUser('${u.id}')" title="Block User">
                        <i data-lucide="shield-ban" size="18"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        lucide.createIcons();
    } catch (e) { console.error(e); }
}

async function blockUser(id) {
    if (!confirm("Initiate user block override?")) return;
    try {
        await fetch(`${API_BASE}/users/${id}`, { method: 'DELETE', headers: authHeaders() });
        loadUsers();
    } catch (e) { console.error(e); }
}

async function loadPrompts() {
    try {
        const res = await fetch(`${API_BASE}/prompts`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        
        document.getElementById("promptSystem").value = data.system_prompt;
        document.getElementById("promptTemp").value = data.temperature;
        document.getElementById("promptLength").value = data.response_length;
    } catch (e) { console.error(e); }
}

async function handlePromptUpdate(e) {
    e.preventDefault();
    const payload = {
        system_prompt: document.getElementById("promptSystem").value,
        temperature: parseFloat(document.getElementById("promptTemp").value),
        response_length: parseInt(document.getElementById("promptLength").value),
        creativity_level: "Balanced"
    };

    try {
        const res = await fetch(`${API_BASE}/prompts`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });
        if (res.status === 401) return logout();
        const stat = document.getElementById("promptStatus");
        stat.textContent = "PROMPT DIRECTIVES OVERRIDDEN.";
        setTimeout(() => stat.textContent = "", 3000);
    } catch (e) { console.error(e); }
}

async function loadApiKeys() {
    try {
        const res = await fetch(`${API_BASE}/api-keys`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        
        const tbody = document.getElementById('apiKeysTableBody');
        tbody.innerHTML = '';
        data.forEach(k => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${k.api_provider}</td>
                <td><code style="background:#111; padding:2px 5px; border-radius:3px;">${k.api_key}</code></td>
                <td>${k.request_limit}</td>
                <td>${k.requests_today}</td>
                <td><span style="color:#00ff88">${k.status.toUpperCase()}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
}

async function loadLogs() {
    try {
        const res = await fetch(`${API_BASE}/activity-logs`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        
        const tbody = document.getElementById('logsTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        data.forEach(l => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><small style="color:#a0a0b0">${new Date(l.timestamp).toLocaleString()}</small></td>
                <td>${l.admin_id.toUpperCase()}</td>
                <td style="color:#00d2ff">${l.action}</td>
                <td>${l.details || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) { console.error(e); }
}

// --- Faculty Management ---

async function loadFaculty() {
    const tbody = document.getElementById('facultyTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Analyzing Faculty Data...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/all-faculty`, { headers: authHeaders() });
        const data = await res.json();

        tbody.innerHTML = '';
        data.forEach(fac => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <img src="${BACKEND_BASE}${fac.photo_url}" style="width:40px; height:40px; border-radius:50%; object-fit:cover; border:2px solid #a556fb;">
                </td>
                <td><strong>${fac.name}</strong></td>
                <td><small>${fac.qualification}</small></td>
                <td><span style="color:#00ff88">${fac.designation}</span></td>
                <td><span style="color:#00d2ff">${fac.department}</span></td>
                <td>
                    <button class="action-btn" onclick="deleteFaculty('${fac.id}')" title="Remove Faculty">
                        <i data-lucide="trash-2" size="18"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No faculty data found in matrix.</td></tr>';
        }
        lucide.createIcons();
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#ff4d4d;">Extraction Error</td></tr>';
    }
}

async function handleAddFaculty(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.disabled = true;
    btn.innerText = "INJECTING...";

    const formData = new FormData();
    formData.append('name', document.getElementById('facName').value);
    formData.append('qualification', document.getElementById('facQual').value);
    formData.append('designation', document.getElementById('facDesignation').value);
    formData.append('department', document.getElementById('facDept').value);
    formData.append('about', document.getElementById('facAbout').value);
    formData.append('file', document.getElementById('facPhoto').files[0]);

    try {
        const res = await fetch(`${API_BASE}/add-faculty`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${JWT_TOKEN}` },
            body: formData
        });

        if (res.status === 401) return logout();

        if (res.ok) {
            closeModal('addFacultyModal');
            e.target.reset();
            loadFaculty();
        } else {
            const errData = await res.json().catch(() => ({}));
            alert(`Upload Failed: ${errData.detail || "Check connection or auth."}`);
        }
    } catch (err) {
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.innerText = "INJECT PROFILE";
    }
}

async function deleteFaculty(id) {
    if (!confirm("Are you sure you want to remove this faculty profile?")) return;
    await fetch(`${API_BASE}/delete-faculty/${id}`, {
        method: 'DELETE',
        headers: authHeaders()
    });
    loadFaculty();
}

