<template>
  <top />
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
import { ref, provide, onMounted } from 'vue';
import top from '@/components/Top.vue';
import Sidebar from '@/components/Sidebar.vue';
// import request from '@/util/request';
import route1Image from '@/assets/images/r1老德胜桥.png'
import route2Image from '@/assets/images/r2时光公园.png'
import route3Image from '@/assets/images/r3城北体育公园.png'
import RouteChart from '@/components/RouteChart.vue';

// 使用 ES Module 方式导入 GeoScene 模块
import Map from '@geoscene/core/Map.js';
import MapView from '@geoscene/core/views/MapView.js';
import GraphicsLayer from '@geoscene/core/layers/GraphicsLayer.js';
import Graphic from '@geoscene/core/Graphic.js';
import Polyline from '@geoscene/core/geometry/Polyline.js';
import Point from '@geoscene/core/geometry/Point.js';
import SpatialReference from '@geoscene/core/geometry/SpatialReference.js';
import FeatureLayer from '@geoscene/core/layers/FeatureLayer.js';
import TileInfo from '@geoscene/core/layers/support/TileInfo.js';
import BasemapGallery from '@geoscene/core/widgets/BasemapGallery.js';

const sceneRef = ref(null);
provide('scene', sceneRef);

onMounted(() => {
  // 直接使用导入的模块初始化地图
  initMap();
});

// 使用 ES Module 导入的组件初始化地图
function initMap() {
  try {
    console.log('开始初始化地图...');
    
    // 创建地图
    const map = new Map({
      basemap: "tianditu-vector" // 使用天地图底图
    });

    // 创建地图视图
    const view = new MapView({
      container: "map",
      map: map,
      center: [120.17, 30.30], // 杭州坐标
      zoom: 12
    });

    sceneRef.value = view;
    
    // 等待视图准备就绪后初始化图层
    view.when(() => {
      console.log('地图视图准备就绪');
      initLayers(view);
    }).catch(error => {
      console.error('地图视图初始化失败:', error);
    });
    
  } catch (error) {
    console.error('地图初始化失败:', error);
  }
}

// 使用导入的模块初始化图层
// 路线和地标文件路径
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

// 存储图层，便于后续清除和切换
const routeLayers = [null, null, null];
const dibiaoLayers = [null, null, null];

async function fetchJson(url) {
  // Vite dev 环境下 fetch 需要以 public/ 或 /src/ 开头
  const res = await fetch(url);
  return await res.json();
}

async function initLayers(view) {
  // 默认加载全部路线和地标
  for (let i = 0; i < 3; i++) {
    await showRouteOnMap(i, view);
    await showDibiaoOnMap(i, view);
  }
}

async function showRouteOnMap(idx, view) {
  // 清除旧图层
  if (routeLayers[idx]) {
    view.map.remove(routeLayers[idx]);
    routeLayers[idx] = null;
  }
  const colorArr = ["#e0c060", "#305070", "#e098a8"];
  const url = routeFiles[idx];
  const data = await fetchJson(url);
  if (!data || !data.features) return;
  const layer = new GraphicsLayer({ title: `推荐路线${idx + 1}` });
  data.features.forEach(f => {
    if (f.geometry.type === 'LineString') {
      const polyline = new Polyline({ paths: [f.geometry.coordinates] });
      const graphic = new Graphic({
        geometry: polyline,
        symbol: {
          type: "simple-line",
          color: colorArr[idx],
          width: idx === 0 ? 6 : 3,
        }
      });
      layer.add(graphic);
    }
  });
  view.map.add(layer);
  routeLayers[idx] = layer;
}

async function showDibiaoOnMap(idx, view) {
  if (dibiaoLayers[idx]) {
    view.map.remove(dibiaoLayers[idx]);
    dibiaoLayers[idx] = null;
  }
  const colorArr = ["#f8e088", "#88a0c0", "#c86080"];
  const url = dibiaoFiles[idx];
  const data = await fetchJson(url);
  if (!data || !data.features) return;
  const layer = new GraphicsLayer({ title: `路线${idx + 1}地标` });
  data.features.forEach(f => {
    if (f.geometry.type === 'Point') {
      const point = new Point({
        longitude: f.geometry.coordinates[0],
        latitude: f.geometry.coordinates[1]
      });
      const graphic = new Graphic({
        geometry: point,
        symbol: {
          type: "simple-marker",
          color: colorArr[idx],
          size: 10,
          outline: { color: "white", width: 1 }
        },
        attributes: f.properties,
        popupTemplate: {
          title: f.properties?.地标名 || '未知地标',
          content: `<p>${f.properties?.地标名 || '暂无描述'}</p>`,
        }
      });
      layer.add(graphic);
    }
  });
  view.map.add(layer);
  dibiaoLayers[idx] = layer;
}
// 路线元数据（用于传给 Sidebar）
const routes = ref([
  {
    id: 'route1',
    type:'3km短途进阶中距离',
    name: '运河文脉漫行线',
    description: '老德胜桥 → 潮王桥 → 京杭运河 → 朝晖桥 → 西湖文化广场 → 创意图书馆',
    length:'总长度：2997.5m',
    image: route1Image ,
    point:127.4,
    center: [120.15, 30.28],
    
  },
  {
    id: 'route2',
    type:'2.5km环形',
    name: '石桥时光闭环跑道',
    description: '华盛达中心 → 时光公园 → 石桥河 → 石桥河绿道 ',
    length:'总长度：2578.5m',
    image:route2Image,
    point:109.2,
    center: [120.17, 30.33],
  },
  {
    id: 'route3',
    type:'2.5km标准短途',
    name: '阅跑城北公园绿道',
    description: '杭州图书馆 → 体育公园绿道 → 城北体育公园',
    length:'总长度：2484.84m',
    image: route3Image ,
    point:145.0,
    center: [120.15, 30.31],

  }
]);

// 新增状态管理
const activeDetailCard = ref(null);

// 新增方法
const showDetailCard = (routeId) => {
  activeDetailCard.value = routes.value.find(r => r.id === routeId);
};

const closeDetailCard = () => {
  activeDetailCard.value = null;
};


// 点击聚焦地图并只显示对应路线和地标
const onRouteSelect = async (routeId) => {
  console.log('点击路线:', routeId);
  const selected = routes.value.find(r => r.id === routeId);
  if (selected && sceneRef.value) {
    const idx = routes.value.findIndex(r => r.id === routeId);
    console.log('路线索引:', idx);
    
    try {
      // 先隐藏其他路线
      for (let i = 0; i < 3; i++) {
        if (i !== idx) {
          if (routeLayers[i]) {
            routeLayers[i].visible = false;
          }
          if (dibiaoLayers[i]) {
            dibiaoLayers[i].visible = false;
          }
        } else {
          // 显示当前路线
          if (routeLayers[i]) {
            routeLayers[i].visible = true;
          }
          if (dibiaoLayers[i]) {
            dibiaoLayers[i].visible = true;
          }
        }
      }
      
      // 使用延时来确保图层状态更新完成
      setTimeout(async () => {
        try {
          // 读取路线数据计算包络框
          const url = routeFiles[idx];
          const data = await fetchJson(url);

          if (data && data.features && data.features.length > 0) {
            let coords = [];
            data.features.forEach(f => {
              if (f.geometry.type === 'LineString') {
                coords = coords.concat(f.geometry.coordinates);
              }
            });
            
            if (coords.length > 0) {
              let minX = coords[0][0], maxX = coords[0][0], minY = coords[0][1], maxY = coords[0][1];
              coords.forEach(([x, y]) => {
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
              });
              
              // 创建 Extent 对象
              const extent = {
                xmin: minX,
                ymin: minY,
                xmax: maxX,
                ymax: maxY,
                spatialReference: { wkid: 4326 }
              };
              
              console.log('计算的范围:', extent);
              
              // 使用 goTo 方法，添加一些选项
              sceneRef.value.goTo(extent, {
                duration: 1000,
                easing: 'ease-in-out'
              }).then(() => {
                console.log('地图缩放完成');
              }).catch(error => {
                console.error('goTo 失败:', error);
                // fallback 到简单的中心点缩放
                sceneRef.value.goTo({
                  center: selected.center,
                  zoom: 15
                });
              });
              return;
            }
          }
          
          // fallback
          console.log('使用预设中心点缩放');
          sceneRef.value.goTo({
            center: selected.center,
            zoom: 15
          });
          
        } catch (error) {
          console.error('延时执行失败:', error);
          // 最终 fallback
          sceneRef.value.goTo({
            center: selected.center,
            zoom: 15
          });
        }
      }, 300);
      
    } catch (error) {
      console.error('路线选择失败:', error);
      // 直接 fallback
      sceneRef.value.goTo({
        center: selected.center,
        zoom: 15
      });
    }
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
  top: 80px !important;
  z-index: 10 !important;
}

:deep(.l7-control-container .l7-left) {
  z-index: 10 !important;
}

:deep(.l7-control-container .l7-bottom) {
  bottom: 30px;
}

:deep(.mapboxgl-ctrl-bottom-left) {
  bottom: 50px;
} */

:deep(.l7-control-container .l7-top) {
  /* top: 80px !important; */
  z-index: 10 !important;
}

:deep(.l7-control-container .l7-left) {
  z-index: 10 !important;
}

.app-container {
  display: flex;
  height: 86vh;
  margin-bottom:0vh; /* 确保顶部导航栏不覆盖地图 */
}
.map-container {
  flex: 1;
  width: 100vw;
  height: 100vh;
}
.marker-popup {
  font-weight: bold;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
/* 新增悬浮卡片样式 */
.floating-card {
  position: absolute;
  width: 420px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 16px;
  z-index: 500;
  user-select: none;
  left:500px;
  padding-bottom: 20px;
}

.floating-card h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #333;
}

.card-content {
  font-size: 14px;
  color: #555;
  max-height:60vh;
  overflow-y:auto;
}

.card-content p {
  margin: 8px 0;
}

.close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}
</style>

<style>
/* L7地图控件样式覆盖 - 全局样式 */
.l7-control-container .l7-top {
  top: 80px !important;
  z-index: 10 !important;
}

.l7-control-container .l7-left {
  z-index: 10 !important;
}

.l7-control-container .l7-bottom {
  bottom: 30px !important;
  z-index: 10 !important;
}

.mapboxgl-ctrl-bottom-left {
  bottom: 50px !important;
  z-index: 10 !important;
}
</style>