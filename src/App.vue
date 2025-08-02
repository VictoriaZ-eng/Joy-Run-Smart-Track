<template>
  <top></top>
  <div id="map"></div>
  <router-view></router-view>
</template>

<script setup>
import mapboxgl from 'mapbox-gl';
import { Scene, Mapbox } from '@antv/l7';
import { onMounted } from 'vue';
import top from '@/components/Top.vue';
import { useControl } from '@/assets/hook/useControl';


// 创建场景
let scene;

onMounted(async () => {
  // 设置 Mapbox 访问令牌
  mapboxgl.accessToken = `pk.eyJ1IjoieHpkbWFwZ2lzIiwiYSI6ImNtOWtxbXU3eTBwcGEya3BvYW9ubWZ6bWwifQ.bn8nv2PPHfWDeDWExmQamQ`;

  // 创建 Mapbox 地图实例
  const map = new mapboxgl.Map({
    container: 'map', // 必须与 DOM 中的 id 匹配
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [120.2, 30.25], // 杭州市拱墅区的部分区域
    zoom: 12,
    attributionControl: false,
    locale: {
      'ScaleControl.Meters': '米',
      'ScaleControl.Kilometers': '千米',
    },
  });

  // 创建 AntV L7 场景
  scene = new Scene({
    id: 'map',
    map: new Mapbox({
      mapInstance: map,
    }),
    logoVisible: false,
  });

  // 等待场景加载完成
  await scene.on('loaded', () => {
    console.log('Scene loaded successfully');
  });

  // 提供 scene 实例给全局
  app.provide('scene', scene);
  // 调用 useControl 来添加自定义控件
  useControl(scene);
  scene.map.on("move",setFog);
});

// 动态雾效函数
function setFog() {
  const lng = Math.abs(scene.map.getCenter().lng);
  scene.map.setFog({
    color: `hsl(0,0,${lng / 360})`,
    'high-color': `hsl(0,0,${lng / 360})`,
  });
}
</script>


<style scoped>
/* 确保地图容器有明确的高度 */
#map {
  width: 100%;
  height: 100vh; /* 全屏高度，可以根据需要调整 */
}

/* 调整 Mapbox 控件的位置 */
:deep(.mapboxgl-ctrl) {
  z-index: 1000;
}

:deep(.l7-control) {
  z-index: 1000;
}
</style>