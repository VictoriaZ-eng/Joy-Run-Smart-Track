<template>
  <div class="sidebar" :class="{ collapsed }">
    <button class="toggle" @click="collapsed = !collapsed">
      {{ collapsed ? '▶' : '◀' }}
    </button>
    <div v-if="!collapsed" class="content">
      <div
        v-for="route in routes"
        :key="route.id"
        class="route-block"
        @click="selectRoute(route.id)"
        @dblclick="emit('show-detail', route.id)" 
      >
 <!-- 左侧文本区 -->
 <div class="text-content">
          <div class="type-tag" :style="getTagStyle(route.type)">
            {{ route.type }}
          </div>
          <h3 class="route-name">{{ route.name }}</h3>
          <p class="route-description">{{ route.description }}</p>
          <p class="route-length">{{ route.length }}</p>
        </div>
<!-- 右侧图片区 -->
<div class="image-content">
          <img 
            v-if="route.image" 
            :src="route.image" 
            :alt="route.name"
            class="route-image"
            @error="handleImageError"
          >
          <div v-else class="image-placeholder">
            <span>暂无图片</span>
          </div>
        </div>
      </div>
    </div>
  
  </div>
</template>
  
  <script setup>
  import { ref } from 'vue';
  const getTagStyle = (type) => {
  const colorMap = {
    '3km短途进阶中距离': '#e0c060', 
    '2.5km标准短途': '#b87078' ,     
    '2.5km环形': '#6090b0',
  };
  return {
    backgroundColor: colorMap[type]
  };
};
  defineProps({
    routes: Array
  });
  const emit = defineEmits(['select']);
  
  const collapsed = ref(false);
  const selectRoute = (id) => {
    emit('select', id);
  };



  </script>
  
  <style scoped>
  .sidebar {
  width: 400px;
  background-color: white;
  border-right: 1px solid #ccc;
  position: relative; /* 为绝对定位的按钮提供参考 */
  transition: width 0.3s ease;
  height: 100%; /* 确保侧边栏有高度 */
  display: flex;
  flex-direction: column;
}

.sidebar.collapsed {
  width: 30px;
}

.toggle {
  position: absolute;
  right: -15px; /* 向右移动一半到侧边栏外 */
  top: 40%; /* 距离顶部距离 */
  width: 30px;
  height: 30px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle:hover {
  background: #f0f0f0;
}

.route-block {
  display: flex;
  gap: 16px;
  padding: 16px;
  margin-bottom: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  height:220px;
}

.route-block:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 左侧文本区 */
.text-content {
  flex: 1;
  min-width: 0; /* 防止文本溢出 */
}

.type-tag {
  display: inline-block;
  padding: 4px 8px;
  background: #555;
  color: white;
  font-size: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.route-name {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #333;
}

.route-description {
  margin: 0;
  font-size: 16px;
  color: #666;
  line-height: 1.5;
  font-weight:bold;
}
.route-length{
  margin: 0;
  font-size: 15px;
  color: #666;
  line-height: 1.5;
}

/* 右侧图片区 */
.image-content {
  width: 120px;
  height: 120px;
  flex-shrink: 0;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f5f5;
}

.route-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #999;
  font-size: 12px;
}

  </style>
  