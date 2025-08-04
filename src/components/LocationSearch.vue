<script setup>
import { inject, ref, watch } from 'vue';
import mapboxgl from 'mapbox-gl';

const sceneRef = inject('scene');
const searchQuery = ref('');
let marker = null; // 避免重复创建 marker

function searchLocation() {
  const scene = sceneRef?.value;
  if (!scene || !scene.map) {
    console.warn('Scene is not available or not yet loaded');
    return;
  }

  const query = searchQuery.value.trim();
  if (!query) return;

  fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?language=zh&access_token=pk.eyJ1IjoieHpkbWFwZ2lzIiwiYSI6ImNtOWtxbXU3eTBwcGEya3BvYW9ubWZ6bWwifQ.bn8nv2PPHfWDeDWExmQamQ`)
    .then(res => res.json())
    .then(data => {
      if (data.features && data.features.length > 0) {
        const [lng, lat] = data.features[0].center;

        scene.map.flyTo({ center: [lng, lat], zoom: 14 });

        // 先清除旧 marker
        if (marker) marker.remove();

        // 添加新 marker
        marker = new mapboxgl.Marker({ color: '#FF0000' })
          .setLngLat([lng, lat])
          .addTo(scene.map);
      } else {
        alert('未找到相关地点');
      }
    });
}

// 等待 scene 加载成功
watch(
  () => sceneRef?.value,
  (scene) => {
    if (scene) {
      console.log('✅ Scene ready in search component');
    }
  },
  { immediate: true }
);
</script>

<template>
  <div class="search-container">
    <input v-model="searchQuery" placeholder="请输入地点" />
    <button @click="searchLocation">搜索</button>
  </div>
</template>

<style scoped>

.search-container {
  position: absolute; /* 确保它能浮动在地图上 */
  top: 3cm;           /* 距离顶部 20px，可根据需要调整 */
  left: 20px;          /* 靠左边距 20px */
  display: flex;
  gap: 8px;
  background: white;
  padding: 10px 12px;
  border-radius: 6px;
  /* box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15); */
  z-index: 10; /* 确保它盖在地图上 */
  width: 520px; /* 控制整体宽度，适当变大 */
}

input {
  padding: 6px 10px;
  border: 2px solid #ccc;
  flex: 1;
  font-size: 14px;
  border-radius: 10px;
  height:40px;
  width: 150px;

}

button {
  padding: 6px 14px;
  background: rgb(235, 239, 226);
  color: rgb(97, 144, 38);
  border: none;
  cursor: pointer;
  border-radius: 4px;
  font-weight: bold;
  font-size: 20px;
}
button:hover {
  background: rgba(235, 239, 226, 0.685);
} 
</style>
