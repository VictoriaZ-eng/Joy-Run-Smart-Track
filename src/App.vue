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
import mapboxgl from 'mapbox-gl';
import { Scene, Mapbox, LineLayer, PointLayer,Popup } from '@antv/l7';
import { useControl } from '@/assets/hook/useControl';
import top from '@/components/Top.vue';
import Sidebar from '@/components/Sidebar.vue'; // 侧边栏组件
import request from '@/util/request';
import route1Image from '@/assets/images/r1老德胜桥.png'
import route2Image from '@/assets/images/r2时光公园.png'
import route3Image from '@/assets/images/r3城北体育公园.png'
import RouteChart from '@/components/RouteChart.vue';


const sceneRef = ref(null);
provide('scene', sceneRef);

onMounted(() => {
  mapboxgl.accessToken = `pk.eyJ1IjoieHpkbWFwZ2lzIiwiYSI6ImNtOWtxbXU3eTBwcGEya3BvYW9ubWZ6bWwifQ.bn8nv2PPHfWDeDWExmQamQ`;

  const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [120.17, 30.30],
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
      .color("#e0c060")
      .size(6)
      .style({
        lineType: "solid",
        opacity: 1
      })
      .animate({
    enable: true,
    interval: 1, // 间隔
    trailLength: 2, // 流线长度
    duration: 3 // 持续时间
  });
    
      const route2Layer = new LineLayer({ name: "推荐路线2" })
      .source(route2)
      .color("#305070")
      .size(3)
      .style({
        lineType: "solid",
        opacity: 1
      })
      .animate({
    enable: true,
    interval: 1, // 间隔
    trailLength: 2, // 流线长度
    duration: 3 // 持续时间
  });
      const route3Layer = new LineLayer({ name: "推荐路线3" })
      .source(route3)
      .color("#e098a8")
      .size(3)
      .style({
        lineType: "solid",
        opacity: 1
      })
      .animate({
    enable: true,
    interval: 1, // 间隔
    trailLength: 2, // 流线长度
    duration: 3 // 持续时间
  });

    // 地标图层
    const dibiao1Layer = new PointLayer({ name: "路线1地标" })
      .source(dibiao1)
      .shape("circle")
      .color("#f8e088")
      .size(10)
      .style({
        opacity: 1
      });
      const dibiao2Layer = new PointLayer({ name: "路线2地标" })
      .source(dibiao2)
      .shape("circle")
      .color("#88a0c0")
      .size(10)
      .style({
        opacity: 1
      });
      const dibiao3Layer = new PointLayer({ name: "路线3地标" })
      .source(dibiao3)
      .shape("circle")
      .color("#c86080")
      .size(10)
      .style({
        opacity: 0.9
      });

// 创建全局 Popup
let hoverPopup = null;

// 封装悬停事件绑定函数
function bindHoverPopup(layer) {
  layer.on('mousemove', (e) => {
    if (hoverPopup) hoverPopup.remove();

    // 防止数据缺失
    const props = e.feature?.properties || {};
    const name = props.地标名 || '未知地标';

    hoverPopup = new Popup({
      offsets: [0, -20],
      closeButton: false,
      closeOnClick: false,
      className: 'marker-popup'
    })
      .setLnglat(e.lngLat)
      .setHTML(`<div style="padding: 4px; font-size: 12px;">${name}</div>`)
      .addTo(scene);
  });

  layer.on('mouseout', () => {
    if (hoverPopup) {
      hoverPopup.remove();
      hoverPopup = null;
    }
  });
}

// 绑定所有图层悬停事件
[dibiao1Layer, dibiao2Layer, dibiao3Layer].forEach(bindHoverPopup);

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


// 点击聚焦地图
const onRouteSelect = (routeId) => {
  const selected = routes.value.find(r => r.id === routeId);
  if (selected && sceneRef.value) {
    const map = sceneRef.value.getMapService().map;
    map.flyTo({
      center: selected.center,
      zoom: 15,
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