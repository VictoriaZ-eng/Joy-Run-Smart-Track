<!-- AI健康助手功能 -->
<template>

</template>

<script setup>
import { onMounted } from 'vue'
import axios from 'axios'

// 异步获取 token
const fetchToken = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:5000/coze/token') 
    return res.data.token
  } catch (e) {
    console.error('获取 Coze token 失败:', e)
    return null
  }
}

const initCozeChat = async () => {
  const token = await fetchToken()
  if (!token) return

  if (!window.CozeWebSDK) {
    const script = document.createElement('script')
    script.src = 'https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.10/libs/cn/index.js'
    script.onload = () => createChatWidget(token)
    document.head.appendChild(script)
  } else {
    createChatWidget(token)
  }
}

const createChatWidget = (token) => {
  new window.CozeWebSDK.WebChatClient({
    config: {
      bot_id: '7535143219005702186',
    },
    ui: {
      chatBot: {
        title: "慢跑健康助手",
        uploadable: true,
        width: 450,
      },
      base:{
        icon:"AI参考.png",
      },
      asstBtn:{
      isNeed:true,
    },
    },
    auth: {
      type: 'token',
      token,
      onRefreshToken: () => token // 这里直接复用已有 token
    }
  }).mount("#coze-chat-container")
}

onMounted(() => {
  setTimeout(initCozeChat, 300)
})
</script>
<style scoped>

</style>