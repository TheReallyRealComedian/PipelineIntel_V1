// backend/static/js/llm_chat_ui.js

// Helper to get CSRF token from meta tag
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

document.addEventListener('DOMContentLoaded', function() {
    // This script will only run if it finds the main chat page container
    if (!document.querySelector('.llm-chat-page')) {
        return;
    }

    const chatDisplay = document.getElementById('chatDisplay');
    const chatInput = document.getElementById('chatInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const llmModelSelect = document.getElementById('llmModelSelect');
    const systemPromptInput = document.getElementById('systemPromptInput');
    const saveSystemPromptBtn = document.getElementById('saveSystemPromptBtn');
    const savePromptStatus = document.getElementById('savePromptStatus');

    // --- Helper Functions ---
    function markdownToHtml(markdownText) {
        if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
            return marked.parse(markdownText, { gfm: true, breaks: true });
        }
        // Basic fallback if marked.js is not available
        return markdownText.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>');
    }

    function addMessageToChat(role, content) {
        const placeholder = chatDisplay.querySelector('.chat-placeholder');
        if (placeholder) placeholder.remove();

        const messageElement = document.createElement('div');
        // A container for the bubble to control alignment
        const bubbleContainer = document.createElement('div');
        bubbleContainer.classList.add('d-flex', 'flex-column', role === 'user' ? 'align-items-end' : 'align-items-start', 'mb-2');
        
        messageElement.classList.add('chat-bubble', `chat-bubble-${role}`);
        messageElement.innerHTML = markdownToHtml(content);
        
        bubbleContainer.appendChild(messageElement);
        chatDisplay.appendChild(bubbleContainer);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }

    // --- API Calls ---
    async function fetchModels() {
        try {
            const response = await fetch('/llm/api/get_models');
            const data = await response.json();
            llmModelSelect.innerHTML = '';
            if (data.success && data.models && data.models.length > 0) {
                data.models.forEach(model => {
                    const option = new Option(model, model);
                    llmModelSelect.appendChild(option);
                });
            } else {
                llmModelSelect.innerHTML = '<option value="">No models available</option>';
                sendMessageBtn.disabled = true;
            }
        } catch (error) {
            console.error('Failed to fetch LLM models:', error);
            llmModelSelect.innerHTML = '<option value="">Error loading models</option>';
        }
    }

    async function fetchHistory() {
        try {
            const response = await fetch('/llm/api/get_history');
            const data = await response.json();
            if (data.success && data.history.length > 0) {
                chatDisplay.innerHTML = '';
                data.history.forEach(msg => addMessageToChat(msg.role, msg.content));
            }
        } catch (error) {
            console.error('Failed to fetch chat history:', error);
        }
    }

    async function sendMessage() {
        const message = chatInput.value.trim();
        const model = llmModelSelect.value;
        if (!message || !model) return;

        addMessageToChat('user', message);
        chatInput.value = '';
        chatInput.style.height = 'auto'; // Reset height after sending
        sendMessageBtn.disabled = true;

        const loadingBubble = document.createElement('div');
        loadingBubble.classList.add('chat-bubble', 'chat-bubble-assistant');
        loadingBubble.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        const loadingContainer = document.createElement('div');
        loadingContainer.classList.add('d-flex', 'flex-column', 'align-items-start', 'mb-2');
        loadingContainer.appendChild(loadingBubble);
        chatDisplay.appendChild(loadingContainer);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;

        try {
            const response = await fetch('/llm/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ message, model })
            });
            const data = await response.json();
            loadingContainer.remove();
            if (data.success) {
                addMessageToChat('assistant', data.message);
            } else {
                addMessageToChat('assistant', `Error: ${data.message}`);
            }
        } catch (error) {
            loadingContainer.remove();
            addMessageToChat('assistant', `Network error: ${error.message}`);
        } finally {
            sendMessageBtn.disabled = false;
        }
    }

    // --- Event Listeners ---
    sendMessageBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
    });


    clearChatBtn.addEventListener('click', async () => {
        if (confirm('Are you sure you want to clear this conversation?')) {
            await fetch('/llm/api/clear_history', { method: 'POST', headers: { 'X-CSRFToken': getCSRFToken() } });
            chatDisplay.innerHTML = '<div class="chat-placeholder text-center text-muted p-5"><i class="fas fa-comments fa-3x"></i><p class="mt-3">History cleared. Start a new conversation.</p></div>';
        }
    });

    saveSystemPromptBtn.addEventListener('click', async () => {
        const prompt = systemPromptInput.value;
        savePromptStatus.textContent = 'Saving...';
        try {
            const response = await fetch('/llm/api/system_prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ prompt })
            });
            const result = await response.json();
            savePromptStatus.textContent = result.message;
            savePromptStatus.style.color = result.success ? 'var(--bi-positive-800)' : 'var(--bi-negative-800)';
        } catch (error) {
            savePromptStatus.textContent = 'Network error.';
            savePromptStatus.style.color = 'var(--bi-negative-800)';
        } finally {
            setTimeout(() => { savePromptStatus.textContent = ''; }, 3000);
        }
    });

    // --- Initial Load ---
    fetchModels();
    fetchHistory();
});