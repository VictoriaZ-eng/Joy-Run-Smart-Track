<template>
  <top />
  <div class="app-container">
    <Sidebar :routes="routes" @select="onRouteSelect" />
    <div id="map" class="map-container"></div>
    <router-view />
  </div>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { Scene, Mapbox, LineLayer, PointLayer } from '@antv/l7';
import { useControl } from '@/assets/hook/useControl';
import top from '@/components/Top.vue';
import Sidebar from '@/components/Sidebar.vue'; // 新组件
import request from '@/util/request';

const sceneRef = ref(null);
provide('scene', sceneRef);

onMounted(() => {
  mapboxgl.accessToken = `pk.eyJ1IjoieHpkbWFwZ2lzIiwiYSI6ImNtOWtxbXU3eTBwcGEya3BvYW9ubWZ6bWwifQ.bn8nv2PPHfWDeDWExmQamQ`;

  const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [120.2, 30.30],
    zoom: 12,
    attributionControl: false,
  });

  const scene = new Scene({
    id: 'map',
    map: new Mapbox({ mapInstance: map }),
    logoVisible: false,
  });

  scene.on('loaded', async () => {
    console.log('Scene loaded successfully');
    sceneRef.value = scene;
    useControl(scene);
    
    // ✅ 正确初始化图层
    await initLayers(scene);
  });
});


async function initLayers(scene) {
  try {
    const [route1, dibiao1,route2, dibiao2,route3, dibiao3] = await Promise.all([
      request.getroute1(),
      request.getdibiao1(),
      request.getroute2(),
      request.getdibiao2(),
      request.getroute3(),
      request.getdibiao3()
    ]);

    // 路线图层
    const route1Layer = new LineLayer({ name: "推荐路线1" })
      .source(route1)
      .color("#ff6b34")
      .size(3)
      .style({
        lineType: "solid",
        opacity: 0.8
      });
      const route2Layer = new LineLayer({ name: "推荐路线2" })
      .source(route2)
      .color("#ff6b34")
      .size(3)
      .style({
        lineType: "solid",
        opacity: 0.8
      });
      const route3Layer = new LineLayer({ name: "推荐路线3" })
      .source(route3)
      .color("#ff6b34")
      .size(3)
      .style({
        lineType: "solid",
        opacity: 0.8
      });


    // 地标图层
    const dibiao1Layer = new PointLayer({ name: "路线1地标" })
      .source(dibiao1)
      .shape("circle")
      .color("#ffed11")
      .size(10)
      .style({
        opacity: 0.9
      });
      const dibiao2Layer = new PointLayer({ name: "路线2地标" })
      .source(dibiao2)
      .shape("circle")
      .color("#ffed11")
      .size(10)
      .style({
        opacity: 0.9
      });
      const dibiao3Layer = new PointLayer({ name: "路线3地标" })
      .source(dibiao3)
      .shape("circle")
      .color("#ffed11")
      .size(10)
      .style({
        opacity: 0.9
      });

    scene.addLayer(route1Layer);
    scene.addLayer(route2Layer);
    scene.addLayer(route3Layer);
    scene.addLayer(dibiao1Layer);
    scene.addLayer(dibiao2Layer);
    scene.addLayer(dibiao3Layer);
    
    
  } catch (error) {
    console.error('图层加载失败:', error);
  }
}
// 路线元数据（用于传给 Sidebar）
const routes = ref([
  {
    id: 'route1',
    name: '推荐路线 1',
    description: '凤起路 → 城站 → 钱江新城',
    center: [120.17, 30.25]
  },
  {
    id: 'route2',
    name: '推荐路线 2',
    description: '黄龙 → 武林 → 河坊街',
    center: [120.14, 30.27]
  },
  {
    id: 'route3',
    name: '推荐路线 3',
    description: '西湖边 → 灵隐寺 → 西溪湿地',
    center: [120.12, 30.26]
  }
]);
// 点击聚焦地图
const onRouteSelect = (routeId) => {
  const selected = routes.value.find(r => r.id === routeId);
  if (selected && sceneRef.value) {
    const map = sceneRef.value.getMapService().map;
    map.flyTo({
      center: selected.center,
      zoom: 13,
      speed: 0.8
    });
  }
};
</script>

<style scoped>
/* #map {
  width: 100vw;
  height: 100vh;
  position: absolute;
}



:deep(.l7-control-container .l7-top) {
  top: 80px;
}

:deep(.l7-control-container .l7-bottom) {
  bottom: 30px;
}

:deep(.mapboxgl-ctrl-bottom-left) {
  bottom: 50px;
} */
.app-container {
  display: flex;
  height: 100vh;
}
.map-container {
  flex: 1;
}
</style>