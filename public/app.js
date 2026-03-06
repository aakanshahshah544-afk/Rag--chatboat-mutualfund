/**
 * Groww RAG Chatbot Frontend
 */

const API_BASE = '';

const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const queryInput = document.getElementById('queryInput');
const sendBtn = document.getElementById('sendBtn');
const statusEl = document.getElementById('status');
const lastUpdatedEl = document.getElementById('lastUpdated');

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    setupEventListeners();
});

function setupEventListeners() {
    chatForm.addEventListener('submit', handleSubmit);
    
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.dataset.query;
            queryInput.value = query;
            handleSubmit(new Event('submit'));
        });
    });
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const query = queryInput.value.trim();
    if (!query) return;
    
    addMessage(query, 'user');
    queryInput.value = '';
    sendBtn.disabled = true;
    
    showLoading();
    setStatus('loading', 'Processing...');
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });
        
        hideLoading();
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
        
        const data = await response.json();
        addAssistantMessage(data);
        setStatus('ready', 'Ready');
        
        if (data.last_updated) {
            updateLastUpdated(data.last_updated);
        }
        
    } catch (error) {
        hideLoading();
        addErrorMessage(error.message);
        setStatus('error', 'Error');
        
        setTimeout(() => setStatus('ready', 'Ready'), 3000);
    }
    
    sendBtn.disabled = false;
    queryInput.focus();
}

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `<p>${escapeHtml(content)}</p>`;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addAssistantMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    let answerHtml = formatAnswer(data.answer);
    contentDiv.innerHTML = `<p>${answerHtml}</p>`;
    
    if (data.citation) {
        const citationDiv = document.createElement('div');
        citationDiv.className = 'citation';
        citationDiv.innerHTML = `📎 Source: <a href="${escapeHtml(data.citation)}" target="_blank" rel="noopener noreferrer">${escapeHtml(data.citation)}</a>`;
        contentDiv.appendChild(citationDiv);
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addErrorMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content error-message';
    contentDiv.innerHTML = `<p>⚠️ ${escapeHtml(message)}</p>`;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loadingMessage';
    
    loadingDiv.innerHTML = `
        <div class="loading-indicator">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span>Searching Groww data...</span>
        </div>
    `;
    
    chatMessages.appendChild(loadingDiv);
    scrollToBottom();
}

function hideLoading() {
    const loadingMsg = document.getElementById('loadingMessage');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

function setStatus(type, text) {
    statusEl.className = `status ${type}`;
    statusEl.querySelector('.status-text').textContent = text;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatAnswer(answer) {
    let formatted = escapeHtml(answer);
    
    formatted = formatted.replace(
        /(https?:\/\/[^
    `)}]}