// backend.js
const express = require('express');
const axios = require('axios');
const app = express();

// 配置信息（替换为您的实际值）
const config = {
  COZE_API_KEY: "cztei_hecpGI2NPTyWDJ4q8SCJ1RECCHcDjQdYyYVcvO8sBIL29wcwKGzElHjtZAwZdV9pG",
  BOT_ID: "7535143219005702186"
};

// 新增状态查询接口
app.get('/api/bot-status', async (req, res) => {
  try {
    const response = await axios.get('https://api.coze.cn/v1/bot/get_online_info', {
      params: {
        bot_id: config.BOT_ID
      },
      headers: {
        'Authorization': `Bearer ${config.COZE_API_KEY}`,
        'Content-Type': 'application/json'
      },
      timeout: 5000
    });

    res.json(response.data);
  } catch (error) {
    console.error('状态查询失败:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    
    res.status(500).json({ 
      error: "状态查询失败",
      details: error.response?.data || error.message 
    });
  }
});

// 保留原有对话接口
app.post('/api/chat', async (req, res) => {
  // ...（保持原有实现不变）
});

// 启动服务
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`
  🚀 服务已启动
  ► 本地地址: http://localhost:${PORT}
  ► 状态查询: GET  http://localhost:${PORT}/api/bot-status
  ► 对话接口: POST http://localhost:${PORT}/api/chat
  `);
});