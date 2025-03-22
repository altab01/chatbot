document.addEventListener('DOMContentLoaded', function() {
    const chatArea = document.getElementById('chat-area');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const settingsButton = document.getElementById('settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const closeModalButton = document.getElementById('close-modal');
    const apiKeyInput = document.getElementById('api-key-input');
    const saveApiKeyButton = document.getElementById('save-api-key');
    const statusMessage = document.getElementById('status-message');
    
    // Function to add messages to the chat
    function addMessage(message, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(isUser ? 'user-message' : 'bot-message');
        messageElement.textContent = message;
        
        // Insert before typing indicator
        chatArea.insertBefore(messageElement, typingIndicator);
        
        // Scroll to bottom
        chatArea.scrollTop = chatArea.scrollHeight;
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        typingIndicator.style.display = 'block';
        chatArea.scrollTop = chatArea.scrollHeight;
    }
    
    // Function to hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }
    
    // Function to send message to the server
    async function sendMessage(message) {
        try {
            showTypingIndicator();
            
            const response = await fetch('/get_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Add a small delay to simulate typing
            setTimeout(() => {
                hideTypingIndicator();
                addMessage(data.response);
            }, 1000);
        } catch (error) {
            hideTypingIndicator();
            addMessage('Sorry, I had trouble connecting. Please try again.', false);
            console.error('Error:', error);
        }
    }
    
    // Function to handle sending a message
    function handleSendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            addMessage(message, true);
            messageInput.value = '';
            sendMessage(message);
        }
    }
    
    // Function to check API key status
    async function checkApiKeyStatus() {
        try {
            const response = await fetch('/check_api_key');
            const data = await response.json();
            
            if (data.status.includes("not configured")) {
                addMessage("Welcome! To get the best responses, please set your OpenAI API key by clicking the ⚙️ icon.");
            }
        } catch (error) {
            console.error('Error checking API key status:', error);
        }
    }
    
    // Function to save API key
    async function saveApiKey() {
        const apiKey = apiKeyInput.value.trim();
        
        if (!apiKey) {
            showStatusMessage('Please enter an API key', false);
            return;
        }
        
        try {
            const response = await fetch('/set_api_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                showStatusMessage(data.message, true);
                setTimeout(() => {
                    closeModal();
                    apiKeyInput.value = '';
                }, 2000);
            } else {
                showStatusMessage(data.message, false);
            }
        } catch (error) {
            showStatusMessage('Network error. Please try again.', false);
            console.error('Error:', error);
        }
    }
    
    // Function to show status message
    function showStatusMessage(message, isSuccess) {
        statusMessage.textContent = message;
        statusMessage.style.display = 'block';
        
        if (isSuccess) {
            statusMessage.className = 'status-message status-success';
        } else {
            statusMessage.className = 'status-message status-error';
        }
        
        // Hide after 5 seconds
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    }
    
    // Function to open settings modal
    function openModal() {
        settingsModal.style.display = 'flex';
    }
    
    // Function to close settings modal
    function closeModal() {
        settingsModal.style.display = 'none';
    }
    
    // Event Listeners
    sendButton.addEventListener('click', handleSendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
    
    settingsButton.addEventListener('click', openModal);
    
    closeModalButton.addEventListener('click', closeModal);
    
    saveApiKeyButton.addEventListener('click', saveApiKey);
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === settingsModal) {
            closeModal();
        }
    });
    
    // Function to load chat history
    async function loadChatHistory() {
        try {
            const response = await fetch('/get_chat_history');
            const data = await response.json();
            
            if (data.status === 'success' && data.history && data.history.length > 0) {
                // Clear any existing messages
                const existingMessages = chatArea.querySelectorAll('.message');
                existingMessages.forEach(message => {
                    if (!message.classList.contains('typing-indicator')) {
                        message.remove();
                    }
                });
                
                // Add messages from history, most recent first
                // We'll reverse the order to display oldest first
                const historyItems = [...data.history].reverse();
                
                historyItems.forEach(item => {
                    addMessage(item.user_message, true);
                    addMessage(item.bot_response, false);
                });
                
                console.log('Chat history loaded successfully');
            } else if (data.status === 'error') {
                console.log('Error loading chat history:', data.message);
            } else {
                console.log('No chat history found');
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
    
    // Initialize
    checkApiKeyStatus();
    loadChatHistory();
});
