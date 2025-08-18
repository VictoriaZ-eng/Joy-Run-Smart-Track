<template>
  <top @filter-change="applyRoadFilter"/>
  <div class="app-container">
    <Sidebar :routes="routes" @select="onRouteSelect" @show-detail="showDetailCard"/>
    <div id="map" class="map-container"></div>
    <router-view />
    <div 
      v-if="activeDetailCard" 
      class="floating-card"
      :style="cardStyle"
    >
      <button class="close-btn" @click="closeDetailCard">×</button>
      <!-- 顶部信息区 -->
      <div class="card-header">
        <h3>{{ activeDetailCard.name }}</h3>
        <div class="score-badge">可慢跑性得分：{{ activeDetailCard.point }}</div>
      </div>
      <!-- 图表区 -->
      <div class="chart-area">
        <RouteChart :route-id="activeDetailCard.id" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import top from '@/components/Top.vue';
import Sidebar from '@/components/Sidebar.vue';
import route1Image from '@/assets/images/r1老德胜桥.png'
import route2Image from '@/assets/images/r2时光公园.png'
import route3Image from '@/assets/images/r3城北体育公园.png'
import RouteChart from '@/components/RouteChart.vue';
import Map from '@geoscene/core/Map.js';
import MapView from '@geoscene/core/views/MapView.js';
import GraphicsLayer from '@geoscene/core/layers/GraphicsLayer.js';
import Graphic from '@geoscene/core/Graphic.js';
import Polyline from '@geoscene/core/geometry/Polyline.js';
import Point from '@geoscene/core/geometry/Point.js';
import FeatureLayer from '@geoscene/core/layers/FeatureLayer.js';

// ------------------
// 全局变量，保存 MapView 实例
// ------------------
let sceneView = null;

// ------------------
// 初始化地图
// ------------------
onMounted(() => initMap());

function initMap() {
  try {
    const map = new Map({ basemap: "tianditu-vector" });
    const view = new MapView({
      container: "map",
      map: map,
      center: [120.18, 30.31],
      zoom: 13
    });

    sceneView = view; // 保存实例，避免 Vue Proxy 拦截

    view.when(() => {
      initLayers(view);
    }).catch(console.error);

    const roadLayer = new FeatureLayer({
      url: "https://www.geosceneonline.cn/server/rest/services/Hosted/roadrecommand/FeatureServer",
      title: "路网图层",
      renderer: {
        type: "unique-value",
        field: "hotspot",
        symbol: { type: "simple-line", color: [180, 180, 180, 0.7], width: 2 },
        uniqueValueInfos: [
          { value: -3, symbol: { type:"simple-line", color: "#4575B5", width: 1.2 } },
          { value: -2, symbol: { type:"simple-line", color: "#849EBA", width: 1.2 } },
          { value: -1, symbol: { type:"simple-line", color: "#C0CCBE", width: 1.2 } },
          { value: 0, symbol: { type:"simple-line", color: "#9C9C9C", width: 1.2 } },
          { value: 1, symbol: { type:"simple-line", color: "#FAB984", width: 1.2 } },
          { value: 2, symbol: { type:"simple-line", color: "#ED7551", width: 1.2 } },
          { value: 3, symbol: { type:"simple-line", color: "#D62F27", width: 1.2 } },
        ]
      },
    });
    map.add(roadLayer);
  } catch (error) {
    console.error('地图初始化失败:', error);
  }
}

// ------------------
// 路线/地标数据
// ------------------
const routeFiles = [
  '/src/GIS-data/推荐路线2/01.json',
  '/src/GIS-data/推荐路线2/02.json',
  '/src/GIS-data/推荐路线2/03.json',
];
const dibiaoFiles = [
  '/src/GIS-data/推荐路线2/01地标1.json',
  '/src/GIS-data/推荐路线2/02地标1.json',
  '/src/GIS-data/推荐路线2/03地标1.json',
];

// ------------------
// 图层存储
// ------------------
const routeLayers = [null, null, null];
const dibiaoLayers = [null, null, null];

// ------------------
// 获取 JSON 数据
// ------------------
async function fetchJson(url) {
  const res = await fetch(url);
  return await res.json();
}

// ------------------
// 初始化图层
// ------------------
async function initLayers(view) {
  for (let i = 0; i < 3; i++) {
    const rLayer = await createRouteLayer(i);
    rLayer.visible = false;
    view.map.add(rLayer);
    routeLayers[i] = rLayer;

    const dLayer = await createDibiaoLayer(i);
    dLayer.visible = false;
    view.map.add(dLayer);
    dibiaoLayers[i] = dLayer;
  }
}

async function createRouteLayer(idx) {
  const colorArr = ["#e0c060", "#305070", "#FA3380"];
  const data = await fetchJson(routeFiles[idx]);
  const layer = new GraphicsLayer({ title: `推荐路线${idx + 1}` });
  if (!data?.features) return layer;
  data.features.forEach(f => {
    if (f.geometry.type === 'LineString') {
      const polyline = new Polyline({ paths: [f.geometry.coordinates] });
      layer.add(new Graphic({
        geometry: polyline,
        symbol: { type: "simple-line", color: colorArr[idx], width: idx === 0 ? 6 : 3 }
      }));
    }
  });
  return layer;
}

async function createDibiaoLayer(idx) {
  const colorArr = ["#f8e088", "#88a0c0", "#c86080"];
  const data = await fetchJson(dibiaoFiles[idx]);
  const layer = new GraphicsLayer({ title: `路线${idx + 1}地标` });
  if (!data?.features) return layer;
  data.features.forEach(f => {
    if (f.geometry.type === 'Point') {
      layer.add(new Graphic({
        geometry: new Point({ longitude: f.geometry.coordinates[0], latitude: f.geometry.coordinates[1] }),
        symbol: { type: "simple-marker", color: colorArr[idx], size: 10, outline: { color: "white", width: 1 } },
        attributes: f.properties,
        popupTemplate: { title: f.properties?.地标名 || '未知地标', content: `<p>${f.properties?.地标名 || '暂无描述'}</p>` }
      }));
    }
  });
  return layer;
}

// ------------------
// 路线元数据
// ------------------
const routes = ref([
  { id: 'route1', type:'3km短途进阶中距离', name: '运河文脉漫行线', description: '老德胜桥 → 潮王桥 → 京杭运河 → 朝晖桥 → 西湖文化广场 → 创意图书馆', length:'总长度：2997.5m', image: route1Image, point:127.4, center: [120.15, 30.28] },
  { id: 'route2', type:'2.5km环形', name: '石桥时光闭环跑道', description: '华盛达中心 → 时光公园 → 石桥河 → 石桥河绿道 ', length:'总长度：2578.5m', image:route2Image, point:109.2, center: [120.17, 30.33] },
  { id: 'route3', type:'2.5km标准短途', name: '阅跑城北公园绿道', description: '杭州图书馆 → 体育公园绿道 → 城北体育公园', length:'总长度：2484.84m', image: route3Image, point:145.0, center: [120.15, 30.31] }
]);

// ------------------
// 悬浮卡片
// ------------------
const activeDetailCard = ref(null);
const showDetailCard = (routeId) => activeDetailCard.value = routes.value.find(r => r.id === routeId);
const closeDetailCard = () => activeDetailCard.value = null;

// ------------------
// 点击聚焦地图并显示路线
// ------------------
const onRouteSelect = async (routeId) => {
  const idx = routes.value.findIndex(r => r.id === routeId);
  if (idx === -1 || !sceneView) return;

  // 只显示当前路线/地标
  routeLayers.forEach((layer, i) => { if(layer) layer.visible = i === idx; });
  dibiaoLayers.forEach((layer, i) => { if(layer) layer.visible = i === idx; });

  // 聚焦地图中心
  sceneView.goTo({ center: routes.value[idx].center, zoom: 15 });
};
</script>

<style scoped>
.app-container { display: flex; height: 86vh; margin-bottom:0vh; }
.map-container { flex: 1; width: 100vw; height: 100vh; }
.marker-popup { font-weight: bold; background: white; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.floating-card { position: absolute; width: 420px; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 16px; z-index: 500; user-select: none; left:500px; padding-bottom: 20px; }
.floating-card h3 { margin: 0 0 12px 0; font-size: 18px; color: #333; }
.card-content { font-size: 14px; color: #555; max-height:60vh; overflow-y:auto; }
.card-content p { margin: 8px 0; }
.close-btn { position: absolute; top: 8px; right: 8px; background: none; border: none; font-size: 20px; cursor: pointer; color: #999; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { color: #333; height: 100%; min-height: 0; overflow: hidden; }
.map { flex: 1; height: 100%; min-height: 0; overflow: hidden; }
</style>
