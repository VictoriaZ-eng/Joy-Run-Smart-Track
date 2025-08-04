<template>
  <top></top>
  <div id="map"></div>
    <router-view />
</template>

<script setup>
import { ref, provide, onMounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { Scene, Mapbox } from '@antv/l7';
import { useControl } from '@/assets/hook/useControl';
import top from '@/components/Top.vue';
import { useRoute } from 'vue-router'
// 加入以下两行代码是为了用mapbox插件实现地点查询
const sceneRef = ref(null);  // ✅ 只在这里声明一次
provide('scene', sceneRef);  // ✅ 共享这个 ref，子组件能动态获取到 scene 对象

onMounted(() => {
  mapboxgl.accessToken = `pk.eyJ1IjoieHpkbWFwZ2lzIiwiYSI6ImNtOWtxbXU3eTBwcGEya3BvYW9ubWZ6bWwifQ.bn8nv2PPHfWDeDWExmQamQ`;

  const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [120.2, 30.25],
    zoom: 12,
    attributionControl: false,
  });

  const scene = new Scene({
    id: 'map',
    map: new Mapbox({ mapInstance: map }),
    logoVisible: false,
  });

  scene.on('loaded', () => {
    console.log('Scene loaded successfully');
    sceneRef.value = scene;  // ✅ 动态赋值，触发响应
    useControl(scene);
  });
});
</script>

<style scoped>
/* 确保地图容器有明确的高度 */
#map {
  width: 100wh;
  height: 100vh; /* 全屏高度，可以根据需要调整 */
}

:deep(.l7-control-container .l7-top) {
  top: 80px;
}

:deep(.l7-control-container .l7-bottom) {
  bottom: 30px;
}

:deep(.mapboxgl-ctrl-bottom-left) {
  bottom: 50px;
}

</style>