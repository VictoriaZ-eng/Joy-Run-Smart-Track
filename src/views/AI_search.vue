<template>
    <div class="ai-search-wrapper" :style="{ left: '500px' }">
      <div class="ai-search-container">
        <!-- 头部标题栏 -->
        <div class="panel-header">
          <h3>慢跑健康助手</h3>
          <div class="assistant-score" v-if="isTyping">思考中...</div>
        </div>
        
        <!-- 聊天消息区域 -->
        <div class="chat-messages">
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            :class="['message', msg.role]"
          >
            <div class="message-content">
              {{ msg.content }}
            </div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
  
        <!-- 输入区域 -->
        <div class="input-area">
          <input
            v-model="userInput"
            placeholder="咨询路线问题..."
            @keyup.enter="sendMessage"
            :disabled="isTyping"
          />
          <button @click="sendMessage" :disabled="isTyping || !userInput.trim()">
            <span v-if="!isTyping">发送</span>
            <span v-else class="loading-dots">···</span>
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  
  // 消息数据
  const messages = ref([
    { 
      role: 'bot', 
      content: '您好！我是慢跑健康助手，可以为您制定合适的慢跑计划。',
      time: getCurrentTime() 
    }
  ]);
  const userInput = ref('');
  const isTyping = ref(false);
  
  // 获取当前时间
  function getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  // 发送消息
  const sendMessage = async () => {
    if (!userInput.value.trim() || isTyping.value) return;
  
    // 添加用户消息
    const userMessage = userInput.value;
    messages.value.push({
      role: 'user',
      content: userMessage,
      time: getCurrentTime()
    });
    userInput.value = '';
    isTyping.value = true;
  
    try {
      // 调用后端API
      const response = await fetch('http://localhost:3000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage
        })
      });
  
      const data = await response.json();
      
      // 添加AI回复
      messages.value.push({
        role: 'bot',
        content: data.messages[0].content,
        time: getCurrentTime()
      });
    } catch (error) {
      messages.value.push({
        role: 'bot',
        content: 'oi出错了，请点击跳转链接访问更多：https://www.coze.cn/store/agent/7535143219005702186?bot_id=true',
        time: getCurrentTime()
      });
    } finally {
      isTyping.value = false;
      scrollToBottom();
    }
  };
  
  // 自动滚动到底部
  const scrollToBottom = () => {
    nextTick(() => {
      const container = document.querySelector('.chat-messages');
      container.scrollTop = container.scrollHeight;
    });
  };
  </script>
  
  <style scoped>
  /* 外层定位容器 */
  .ai-search-wrapper {
    position: absolute;
    left: 500px;
    top: 130px;
    width: 320px;
    z-index: 600;
  }
  
  /* 面板容器样式 */
  .ai-search-container {
    height: 500px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  /* 头部样式 */
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: linear-gradient(90deg, #b4dabf, #9cdf93);
    color: rgb(97, 144, 38);
  }
  
  .panel-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
  
  .assistant-score {
    font-size: 12px;
    color: rgba(97, 144, 38, 0.8);
  }
  
  /* 消息区域 */
  .chat-messages {
    flex: 1;
    padding: 16px;
    background: #f9f9f9;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .message {
    max-width: 80%;
    align-self: flex-start;
  }
  
  .message.user {
    align-self: flex-end;
  }
  
  .message-content {
    padding: 10px 14px;
    border-radius: 18px;
    line-height: 1.4;
    word-break: break-word;
  }
  
  .message.user .message-content {
    background: #b4dabf;
    color: #333;
    border-bottom-right-radius: 4px;
  }
  
  .message.bot .message-content {
    background: #f0f0f0;
    color: #333;
    border-bottom-left-radius: 4px;
  }
  
  .message-time {
    font-size: 10px;
    color: #999;
    margin-top: 4px;
    text-align: right;
  }
  
  .message.user .message-time {
    text-align: right;
  }
  
  /* 输入区域 */
  .input-area {
    padding: 12px;
    background: white;
    border-top: 1px solid #eee;
    display: flex;
    gap: 8px;
  }
  
  .input-area input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #ddd;
    border-radius: 20px;
    outline: none;
  }
  
  .input-area button {
    padding: 0 16px;
    min-width: 60px;
    height: 36px;
    background: #9cdf93;
    color: white;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .input-area button:disabled {
    background: #ddd;
    cursor: not-allowed;
  }
  
  .loading-dots {
    animation: blink 1.5s infinite;
  }
  
  @keyframes blink {
    0%, 100% { opacity: 0.2; }
    50% { opacity: 1; }
  }
  </style>