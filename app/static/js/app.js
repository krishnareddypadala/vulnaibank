// VulnAIBank - Client-side JavaScript

// ---- Chat Functions ----
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    // Add user message to UI
    appendChatMessage('user', message);
    input.value = '';

    // Show loading
    const loadingId = showLoading();

    try {
        const response = await fetch('/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        removeLoading(loadingId);

        // DELIBERATE VULNERABILITY (LLM05): AI response rendered as raw HTML
        appendChatMessage('assistant', data.message, true);
    } catch (error) {
        removeLoading(loadingId);
        appendChatMessage('assistant', `Error: ${error.message}`);
    }
}

function appendChatMessage(role, content, isHtml = false) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const div = document.createElement('div');
    div.className = `chat-message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    if (isHtml) {
        // DELIBERATE VULNERABILITY: Rendering AI output as raw HTML
        bubble.innerHTML = content;
    } else {
        bubble.textContent = content;
    }

    div.appendChild(avatar);
    div.appendChild(bubble);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function clearChat() {
    if (!confirm('Clear all chat history?')) return;
    await fetch('/chat/clear', { method: 'POST' });
    document.getElementById('chat-messages').innerHTML = '';
}

// ---- Transfer Functions ----
async function aiTransfer() {
    const instruction = document.getElementById('transfer-instruction').value.trim();
    if (!instruction) return;

    const resultDiv = document.getElementById('transfer-result');
    resultDiv.innerHTML = '<div class="spinner"></div> Processing...';

    try {
        const response = await fetch('/transfers/ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction })
        });
        const data = await response.json();

        if (data.status === 'success') {
            resultDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            if (data.tool_results) {
                resultDiv.innerHTML += '<pre>' + JSON.stringify(data.tool_results, null, 2) + '</pre>';
            }
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

async function quickTransfer(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    try {
        const response = await fetch('/transfers/quick', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        const resultDiv = document.getElementById('transfer-result');
        if (data.status === 'success') {
            resultDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        }
    } catch (error) {
        document.getElementById('transfer-result').innerHTML =
            `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// ---- Loan Functions ----
async function applyLoan() {
    const amount = document.getElementById('loan-amount').value;
    const purpose = document.getElementById('loan-purpose').value;
    if (!amount || !purpose) return;

    const resultDiv = document.getElementById('loan-result');
    resultDiv.innerHTML = '<div class="spinner"></div> AI is evaluating your application...';

    try {
        const response = await fetch('/loans/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: parseFloat(amount), purpose })
        });
        const data = await response.json();

        if (data.status === 'success') {
            const statusClass = data.loan_status === 'approved' ? 'success' :
                               data.loan_status === 'denied' ? 'danger' : 'warning';
            resultDiv.innerHTML = `
                <div class="alert alert-${statusClass}">
                    <strong>Status: ${data.loan_status.toUpperCase()}</strong>
                </div>
                <div class="card" style="margin-top: 1rem;">
                    <h3>AI Recommendation</h3>
                    <p>${data.recommendation}</p>
                    <p><strong>Interest Rate:</strong> ${data.interest_rate}%</p>
                </div>`;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

async function getFinancialAdvice() {
    const question = document.getElementById('advice-question').value.trim();
    if (!question) return;

    const resultDiv = document.getElementById('advice-result');
    resultDiv.innerHTML = '<div class="spinner"></div> Getting advice...';

    try {
        const response = await fetch('/loans/advice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await response.json();
        // DELIBERATE VULNERABILITY: AI advice rendered as HTML
        resultDiv.innerHTML = data.advice || data.message;
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// ---- Document Functions ----
async function uploadDocument() {
    const filename = document.getElementById('doc-filename').value.trim();
    const content = document.getElementById('doc-content').value.trim();
    if (!filename || !content) return;

    try {
        const response = await fetch('/documents/upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, content })
        });
        const data = await response.json();
        alert(data.message || data.error);
        if (data.status === 'success') location.reload();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function installPlugin() {
    const name = document.getElementById('plugin-name').value.trim();
    const description = document.getElementById('plugin-desc').value.trim();
    const code = document.getElementById('plugin-code').value.trim();
    if (!name || !code) return;

    try {
        const response = await fetch('/documents/install-plugin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, code })
        });
        const data = await response.json();
        alert(data.message);
        if (data.status === 'success' || data.status === 'warning') location.reload();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// ---- Feedback Functions ----
async function submitFeedback() {
    const query = document.getElementById('fb-query').value.trim();
    const response_text = document.getElementById('fb-response').value.trim();
    const rating = document.querySelector('.star.active')?.dataset.rating || 3;
    const comment = document.getElementById('fb-comment').value.trim();

    try {
        const response = await fetch('/feedback/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, response: response_text, rating: parseInt(rating), comment })
        });
        const data = await response.json();
        alert(data.message);
        if (data.status === 'success') location.reload();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function submitTrainingData() {
    const textarea = document.getElementById('training-data');
    try {
        const examples = JSON.parse(textarea.value);
        const response = await fetch('/feedback/training-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ examples: Array.isArray(examples) ? examples : [examples] })
        });
        const data = await response.json();
        alert(data.message);
    } catch (error) {
        alert('Invalid JSON or error: ' + error.message);
    }
}

// ---- Report Functions ----
async function generateReport() {
    const type = document.getElementById('report-type').value;
    const prompt = document.getElementById('report-prompt').value.trim();
    const outputDiv = document.getElementById('report-output');
    outputDiv.innerHTML = '<div class="spinner"></div> Generating report...';

    try {
        const response = await fetch('/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, prompt })
        });
        const data = await response.json();
        // DELIBERATE VULNERABILITY (LLM05): Raw HTML injection
        outputDiv.innerHTML = data.report_html || data.message;
    } catch (error) {
        outputDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

async function queryReport() {
    const question = document.getElementById('report-question').value.trim();
    if (!question) return;

    const outputDiv = document.getElementById('query-output');
    outputDiv.innerHTML = '<div class="spinner"></div> Generating query...';

    try {
        const response = await fetch('/reports/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await response.json();

        if (data.status === 'success') {
            let html = `<p><strong>SQL Query:</strong></p><pre>${data.query}</pre>`;
            if (data.results) {
                html += '<table><thead><tr>';
                if (data.results.length > 0) {
                    Object.keys(data.results[0]).forEach(key => {
                        html += `<th>${key}</th>`;
                    });
                }
                html += '</tr></thead><tbody>';
                data.results.forEach(row => {
                    html += '<tr>';
                    Object.values(row).forEach(val => {
                        html += `<td>${val}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
            }
            outputDiv.innerHTML = html;
        } else {
            outputDiv.innerHTML = `<div class="alert alert-danger">${data.message}<br><pre>${data.query || ''}</pre></div>`;
        }
    } catch (error) {
        outputDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// ---- Account Search ----
async function searchAccounts() {
    const search = document.getElementById('account-search').value.trim();
    const resultDiv = document.getElementById('search-results');

    try {
        const formData = new FormData();
        formData.append('search', search);

        const response = await fetch('/accounts/search', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.results) {
            let html = '<table><thead><tr><th>Username</th><th>Full Name</th><th>Email</th><th>Aadhaar</th><th>Account</th><th>Balance</th></tr></thead><tbody>';
            data.results.forEach(row => {
                html += `<tr><td>${row.username}</td><td>${row.full_name}</td><td>${row.email}</td><td>${row.ssn}</td><td>${row.account_number}</td><td>$${row.balance}</td></tr>`;
            });
            html += '</tbody></table>';
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// ---- Star Rating ----
function initStarRating() {
    document.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', () => {
            const rating = star.dataset.rating;
            document.querySelectorAll('.star').forEach(s => {
                s.classList.toggle('active', s.dataset.rating <= rating);
            });
        });
    });
}

// ---- Loading Helpers ----
let loadingCounter = 0;
function showLoading() {
    const id = ++loadingCounter;
    const container = document.getElementById('chat-messages');
    if (!container) return id;

    const div = document.createElement('div');
    div.id = `loading-${id}`;
    div.className = 'chat-message assistant';
    div.innerHTML = '<div class="chat-avatar">AI</div><div class="chat-bubble"><div class="spinner"></div> Thinking...</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeLoading(id) {
    const el = document.getElementById(`loading-${id}`);
    if (el) el.remove();
}

// ---- Chat Enter Key ----
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChatMessage();
        });
    }
    initStarRating();
});
