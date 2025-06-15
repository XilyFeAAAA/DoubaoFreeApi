// DOM元素
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-btn');
const chatContainer = document.getElementById('chat-container');
const fileUpload = document.getElementById('file-upload');
const imagePreviewContainer = document.getElementById('image-preview-container');
const newChatButton = document.getElementById('new-chat-btn');
const deleteChatButton = document.getElementById('delete-chat-btn');
const conversationList = document.getElementById('conversation-list');
const currentConversationTitle = document.getElementById('current-conversation-title');
const useAutoCotCheckbox = document.getElementById('use-auto-cot');
const useDeepThinkCheckbox = document.getElementById('use-deep-think');
const loginStatusToggle = document.getElementById('login-status-toggle');
const loginStatusText = document.querySelector('.login-status-text');

// 状态变量
let currentConversationId = null;
let currentSectionId = null;
let uploadedImages = [];
let conversations = [];
let isLoading = false;
let isLoggedIn = true; // 默认为登录状态

// 从本地存储加载会话列表和登录状态
function loadSettings() {
    // 加载会话列表
    const savedConversations = localStorage.getItem('conversations');
    if (savedConversations) {
        conversations = JSON.parse(savedConversations);
        renderConversationList();
    }
    
    // 加载登录状态
    const savedLoginStatus = localStorage.getItem('isLoggedIn');
    if (savedLoginStatus !== null) {
        isLoggedIn = savedLoginStatus === 'true';
        loginStatusToggle.checked = isLoggedIn;
        updateLoginStatusText();
    }
}

// 更新登录状态文本
function updateLoginStatusText() {
    loginStatusText.textContent = isLoggedIn ? '已登录状态' : '未登录状态';
    
    // 在未登录状态下，侧边栏会话列表应该被禁用
    if (!isLoggedIn) {
        // 如果当前有选中的会话，切换到新会话
        if (currentConversationId !== null) {
            createNewChat();
        }
        
        // 禁用会话列表中的所有项
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.add('disabled');
        });
        
        // 禁用删除按钮
        deleteChatButton.disabled = true;
        deleteChatButton.classList.add('disabled');
    } else {
        // 启用会话列表中的所有项
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('disabled');
        });
        
        // 启用删除按钮
        deleteChatButton.disabled = false;
        deleteChatButton.classList.remove('disabled');
    }
}

// 保存会话列表到本地存储
function saveConversations() {
    localStorage.setItem('conversations', JSON.stringify(conversations));
}

// 保存登录状态到本地存储
function saveLoginStatus() {
    localStorage.setItem('isLoggedIn', isLoggedIn);
}

// 渲染会话列表
function renderConversationList() {
    conversationList.innerHTML = '';
    conversations.forEach(conversation => {
        const item = document.createElement('div');
        item.className = `conversation-item ${conversation.id === currentConversationId ? 'active' : ''}`;
        if (!isLoggedIn) {
            item.className += ' disabled';
        }
        item.innerHTML = `
            <i class="bi bi-chat-dots"></i>
            <span>${conversation.title}</span>
        `;
        item.dataset.id = conversation.id;
        item.dataset.sectionId = conversation.sectionId;
        
        item.addEventListener('click', () => {
            if (isLoggedIn) {
                selectConversation(conversation.id, conversation.sectionId, conversation.title);
            }
        });
        
        conversationList.appendChild(item);
    });
}

// 选择会话
function selectConversation(id, sectionId, title) {
    // 如果是未登录状态，只允许新会话
    if (!isLoggedIn && id !== null) {
        showError('未登录状态下不能选择历史会话');
        return;
    }
    
    currentConversationId = id;
    currentSectionId = sectionId;
    currentConversationTitle.textContent = title;
    
    // 保存当前会话ID到本地存储
    if (id !== null) {
        localStorage.setItem('currentConversationId', id);
        if (sectionId) {
            localStorage.setItem('currentSectionId', sectionId);
        } else {
            localStorage.removeItem('currentSectionId');
        }
    } else {
        localStorage.removeItem('currentConversationId');
        localStorage.removeItem('currentSectionId');
    }
    
    // 更新活动状态
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id === id);
    });
    
    // 清空聊天区域，加载会话历史
    chatContainer.innerHTML = '';
    
    // 如果是新会话，显示欢迎消息
    if (id === null) {
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>欢迎使用豆包API聊天界面</h2>
                <p>开始一个新的对话或从侧边栏选择已有会话</p>
                <p class="login-status-info">${isLoggedIn ? '当前为已登录状态，支持多轮对话' : '当前为未登录状态，仅支持单轮对话'}</p>
            </div>
        `;
    } else {
        // 这里可以实现加载历史消息的功能
        // 由于API没有提供获取历史消息的功能，这里暂时不实现
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>${title}</h2>
                <p>继续您的对话</p>
            </div>
        `;
    }
}

// 创建新会话
function createNewChat() {
    selectConversation(null, null, "新会话");
    uploadedImages = [];
    imagePreviewContainer.innerHTML = '';
}

// 删除当前会话
async function deleteCurrentChat() {
    if (currentConversationId === null || !isLoggedIn) return;
    
    try {
        const response = await fetch(`/api/chat/delete?conversation_id=${currentConversationId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.ok) {
                // 从会话列表中移除
                conversations = conversations.filter(conv => conv.id !== currentConversationId);
                saveConversations();
                renderConversationList();
                createNewChat();
            } else {
                showError(`删除会话失败: ${data.msg}`);
            }
        } else {
            showError('删除会话请求失败');
        }
    } catch (error) {
        showError(`删除会话错误: ${error.message}`);
    }
}

// 上传图片
async function uploadImage(file) {
    try {
        // 创建URL参数
        const params = new URLSearchParams({
            file_type: 2,
            file_name: file.name
        });
        
        // 发送请求
        const response = await fetch(`/api/file/upload?${params}`, {
            method: 'POST',
            body: file
        });
        
        if (response.ok) {
            const data = await response.json();
            return data;
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || '上传图片失败');
        }
    } catch (error) {
        showError(`上传图片错误: ${error.message}`);
        return null;
    }
}

// 添加图片预览
function addImagePreview(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'image-preview';
        previewDiv.innerHTML = `
            <img src="${e.target.result}" alt="预览">
            <button class="remove-image"><i class="bi bi-x"></i></button>
        `;
        
        const removeButton = previewDiv.querySelector('.remove-image');
        removeButton.addEventListener('click', () => {
            const index = Array.from(imagePreviewContainer.children).indexOf(previewDiv);
            if (index !== -1) {
                uploadedImages.splice(index, 1);
                previewDiv.remove();
            }
        });
        
        imagePreviewContainer.appendChild(previewDiv);
    };
    reader.readAsDataURL(file);
}

// 发送消息
async function sendMessage() {
    const message = messageInput.value.trim();
    if (message === '' && uploadedImages.length === 0) return;
    
    // 禁用输入和发送按钮
    isLoading = true;
    messageInput.disabled = true;
    sendButton.disabled = true;
    
    // 添加用户消息到聊天区域
    addMessageToChat(message, true);
    
    // 清空输入框和图片预览
    messageInput.value = '';
    
    // 准备附件数组
    const attachments = uploadedImages.map(img => ({
        key: img.key,
        name: img.name,
        option: img.option
    }));
    
    // 清空上传的图片
    uploadedImages = [];
    imagePreviewContainer.innerHTML = '';
    
    try {
        // 添加AI正在输入的提示
        const loadingMessageId = addLoadingMessage();
        
        // 准备请求体
        const requestBody = {
            prompt: message,
            attachments: attachments,
            use_auto_cot: useAutoCotCheckbox.checked,
            use_deep_think: useDeepThinkCheckbox.checked,
            is_logged: isLoggedIn
        };
        
        // 只有在登录状态下且非新会话时才添加conversation_id和section_id
        if (isLoggedIn && currentConversationId !== null) {
            requestBody.conversation_id = currentConversationId;
            if (currentSectionId) {
                requestBody.section_id = currentSectionId;
            }
        }
        
        // 发送请求
        const response = await fetch('/api/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // 移除加载提示
            removeLoadingMessage(loadingMessageId);
            
            // 添加AI回复到聊天区域
            addMessageToChat(data.text, false, data.img_urls);
            
            // 如果是登录状态下的新会话，添加到会话列表
            if (isLoggedIn && currentConversationId === null && data.conversation_id) {
                const newConversation = {
                    id: data.conversation_id,
                    sectionId: data.section_id,
                    title: message.length > 20 ? message.substring(0, 20) + '...' : message
                };
                
                conversations.unshift(newConversation);
                saveConversations();
                renderConversationList();
                
                // 更新当前会话ID
                currentConversationId = data.conversation_id;
                currentSectionId = data.section_id;
                currentConversationTitle.textContent = newConversation.title;
            }
        } else {
            // 移除加载提示
            removeLoadingMessage(loadingMessageId);
            
            const errorData = await response.json();
            showError(`请求失败: ${errorData.detail}`);
        }
    } catch (error) {
        showError(`发送消息错误: ${error.message}`);
    } finally {
        // 恢复输入和发送按钮
        isLoading = false;
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// 添加消息到聊天区域
function addMessageToChat(content, isUser, images = []) {
    // 如果是第一条消息，清除欢迎信息
    if (chatContainer.querySelector('.welcome-message')) {
        chatContainer.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    let messageContent = `
        <div class="message-avatar">${isUser ? 'U' : 'AI'}</div>
        <div class="message-content">
            ${content.replace(/\n/g, '<br>')}
    `;
    
    // 如果有图片，添加图片
    if (images && images.length > 0) {
        messageContent += '<div class="message-images">';
        images.forEach(imageUrl => {
            messageContent += `<img src="${imageUrl}" alt="图片" class="message-image" onclick="window.open('${imageUrl}', '_blank')">`;
        });
        messageContent += '</div>';
    }
    
    messageContent += '</div>';
    messageDiv.innerHTML = messageContent;
    
    chatContainer.appendChild(messageDiv);
    
    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 添加加载中消息
function addLoadingMessage() {
    const loadingId = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message';
    loadingDiv.id = loadingId;
    loadingDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="loading"></div> AI正在思考...
        </div>
    `;
    
    chatContainer.appendChild(loadingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return loadingId;
}

// 移除加载中消息
function removeLoadingMessage(id) {
    const loadingMessage = document.getElementById(id);
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

// 显示错误消息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message bot-message error-message';
    errorDiv.innerHTML = `
        <div class="message-avatar">!</div>
        <div class="message-content" style="color: var(--danger-color);">
            错误: ${message}
        </div>
    `;
    
    chatContainer.appendChild(errorDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    console.error(message);
}

// 事件监听器
sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

fileUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // 添加图片预览
    addImagePreview(file);
    
    // 上传图片
    const uploadResult = await uploadImage(file);
    if (uploadResult) {
        uploadedImages.push(uploadResult);
    }
    
    // 清除文件输入，以便可以再次选择同一文件
    fileUpload.value = '';
});

newChatButton.addEventListener('click', createNewChat);
deleteChatButton.addEventListener('click', deleteCurrentChat);

// 登录状态切换
loginStatusToggle.addEventListener('change', () => {
    isLoggedIn = loginStatusToggle.checked;
    saveLoginStatus();
    updateLoginStatusText();
    
    // 如果切换到未登录状态，强制创建新会话
    if (!isLoggedIn) {
        createNewChat();
    }
});

// 自动调整输入框高度
messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = (messageInput.scrollHeight) + 'px';
});

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 加载设置
    loadSettings();
    
    // 如果有保存的当前会话ID，尝试恢复它
    const savedCurrentConversationId = localStorage.getItem('currentConversationId');
    const savedCurrentSectionId = localStorage.getItem('currentSectionId');
    
    if (isLoggedIn && savedCurrentConversationId && conversations.some(c => c.id === savedCurrentConversationId)) {
        // 找到保存的会话
        const conversation = conversations.find(c => c.id === savedCurrentConversationId);
        selectConversation(conversation.id, conversation.sectionId || savedCurrentSectionId, conversation.title);
    } else {
        // 没有保存的会话或会话不存在，创建新会话
        createNewChat();
    }
}); 