<template>
  <top/>
  <div class="app-container">
    <div class="weather-container" v-if="isHomePage && showAQICard">
      <AQICard/>
    </div>
    <div v-if="isHomePage && showDataCards">
      <DataCards />
    </div>
      <!-- 地标浮动弹窗 -->
      <div 
      v-if="activeLandmark" 
      class="landmark-popup"
      :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }"
    >
      <button class="close-btn" @click="activeLandmark = null">×</button>
      <p>{{ activeLandmark.name }}</p>
      <img 
        :src="activeLandmark.img" 
        alt="街景" 
        style="width:100%; max-height:200px;"
        @error="handleImageError"
      >
      <p v-if="imgError" style="color:red">图片加载失败</p>
    </div>
    
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
import { ref, onMounted,provide ,watch,computed} from 'vue';
import { useRoute } from 'vue-router';
import top from '@/components/Top.vue';
import Sidebar from '@/components/Sidebar.vue';
import AQICard from '@/components/AQICard.vue';
import DataCards from '@/components/DataVisible.vue'
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

// 计算属性判断当前是否是首页
const isHomePage = computed(() => route.path === '/');
//收起数据卡片
const showAQICard = ref(true);
const showDataCards = ref(true);
const route = useRoute();

// 当路由变化时，如果是首页则显示卡片，否则隐藏
watch(() => route.path, (newPath) => {
  if (newPath === '/') {
    showAQICard.value = true;
    showDataCards.value = true;
  } else {
    showAQICard.value = false;
    showDataCards.value = false;
  }
});



// 全局变量，保存 MapView 实例
let sceneView = null;


// 地标弹窗状态
const activeLandmark = ref(null);
const popupPosition = ref({ x: 0, y: 0 });
const imgError = ref(false);

const landmarkData = ref({
  1: { name: "杭州图书馆", image: "/streetviews/hz_library.jpg" },
  2: { name: "城北体育公园绿道", image: "/streetviews/cb_sports_park_trail.jpg" },
  3: { name: "汉宝堡水上乐园", image: "/streetviews/hanbao_waterpark.jpg" },
  4: { name: "城北体育公园", image: "/streetviews/cb_sports_park.jpg" },
  5: { name: "华盛达时代中心", image: "/streetviews/huashida_center.jpg" },
  6: { name: "时光公园", image: "/streetviews/time_park.jpg" },
  7: { name: "石桥河", image: "/streetviews/stone_bridge_river.jpg" },
  8: { name: "石桥河绿道", image: "/streetviews/stone_bridge_trail.jpg" },
  9: { name: "潮王桥", image: "/streetviews/chaowang_bridge.jpg" },
  10: { name: "京杭运河", image: "/streetviews/grand_canal.jpg" },
  11: { name: "老德胜桥", image: "/streetviews/laodesheng_bridge.jpg" },
  12: { name: "朝晖桥", image: "/streetviews/zhaohui_bridge.jpg" },
  13: { name: "蓝星球创意图书馆", image: "/streetviews/blue_planet_library.jpg" },
  14: { name: "西湖文化广场", image: "/streetviews/westlake_culture_square.jpg" },
  15: { name: "西湖六公园", image: "/streetviews/westlake_park6.jpg" },
  16: { name: "庆春门", image: "/streetviews/qingchun_gate.jpg" },
  17: { name: "浙江展览馆", image: "/streetviews/zhejiang_exhibition.jpg" },
  18: { name: "武林广场", image: "/streetviews/wulin_square.jpg" },
  19: { name: "杭州体育馆", image: "/streetviews/hz_gymnasium.jpg" },
  20: { name: "城东公园", image: "/streetviews/chengdong_park.jpg" },
  21: { name: "朝晖公园", image: "/streetviews/zhaohui_park.jpg" },
  22: { name: "北景园生态公园", image: "/streetviews/beijing_eco_park.jpg" },
  23: { name: "同心文化公园", image: "/streetviews/tongxin_culture_park.jpg" },
  24: { name: "武林之星博览中心", image: "/streetviews/wulin_expo.jpg" },
  25: { name: "浙江工业大学（朝晖校区）", image: "/streetviews/zjut_zhaohui.jpg" }
});
// 初始化地图
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
    window.sceneView = view;

    provide('view', sceneView);
    view.when(() => {
      initLayers(view);
      initLegend(view); 
    }).catch(console.error);

    const roadLayer = new FeatureLayer({
      url: "https://www.geosceneonline.cn/server/rest/services/Hosted/roadrecommand/FeatureServer",
      title: "路网图层",
      renderer: {
        type: "unique-value",
        field: "hotspot",
        visible: true,
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

    const pointLayer = new FeatureLayer({
      url: "https://www.geosceneonline.cn/server/rest/services/Hosted/地标街景/FeatureServer",
      title: "地标图层",
      visible: true, // 默认隐藏
      renderer: {
        type: "simple",
        symbol: {
          type: "simple-marker",
          color: "#FFFF00",
          size: "10px",
          outline: { color: "grey", width: 1 }
        }
      },
});

    map.add(roadLayer);
    map.add(pointLayer);

    //弹窗
    view.on("click", async (evt) => {
  const hit = await view.hitTest(evt);
  const graphic = hit.results.find(r => r.graphic.layer === pointLayer)?.graphic;
  
  if (graphic) {
    const fid = graphic.attributes.fid;
    const landmark = landmarkData.value[fid];
    
    if (landmark) {
      activeLandmark.value = {
        name: landmark.name,
        img: landmark.image
      };
      
      // 计算弹窗位置（避免超出视口）
      const containerRect = view.container.getBoundingClientRect();
      const maxX = window.innerWidth - 320; // 弹窗宽度320px
      const maxY = window.innerHeight - 300; // 弹窗高度约300px
      
      popupPosition.value = {
        x: Math.min(evt.screenPoint.x + containerRect.left, maxX),
        y: Math.min(evt.screenPoint.y + containerRect.top, maxY)
      };
      
      imgError.value = false;
    }
  } else {
    activeLandmark.value = null;
  }
});

  } catch (error) {
    console.error('地图初始化失败:', error);
  }
  function initLegend(view) {
  const legendDiv = document.createElement('div');
  legendDiv.id = "map-legend";
  legendDiv.style.position = "absolute";
  legendDiv.style.right = "390px";
  legendDiv.style.bottom = "20px";
  legendDiv.style.background = "rgba(255, 255, 255, 0.9)";
  legendDiv.style.padding = "8px";
  legendDiv.style.borderRadius = "6px";
  legendDiv.style.boxShadow = "0 0 10px rgba(0,0,0,0.2)";
  legendDiv.style.fontSize = "12px";
  legendDiv.style.maxWidth = "200px";

  // 标题 + 折叠按钮
  const header = document.createElement('div');
  header.style.display = "flex";
  header.style.justifyContent = "space-between";
  header.style.alignItems = "center";
  header.style.cursor = "pointer";

  const title = document.createElement('span');
  title.innerText = "图例";
  title.style.fontWeight = "bold";

  const toggleBtn = document.createElement('span');
  toggleBtn.innerText = "▼"; // 默认展开
  toggleBtn.style.marginLeft = "5px";

  header.appendChild(title);
  header.appendChild(toggleBtn);
  legendDiv.appendChild(header);

  // 内容区域
  const content = document.createElement('div');
  content.style.marginTop = "5px";
  content.innerHTML = `
    <div style="font-weight:bold; margin-bottom:3px;">路网图层</div>
    <div><span style="display:inline-block;width:20px;height:3px;background:#4575B5;margin-right:5px;"></span>置信度为99%的慢跑冷点</div>
    <div><span style="display:inline-block;width:20px;height:3px;background:#849EBA;margin-right:5px;"></span>置信度为95%的慢跑冷点</div>
    <div><span style="display:inline-block;width:20px;height:3px;background:#C0CCBE;margin-right:5px;"></span>置信度为90%的慢跑冷点</div>
    <div><span style="display:inline-block;width:20px;height:3px;background:#9C9C9C;margin-right:5px;"></span>不具有显著性</div>
    <div><span style="display:inline-block;width:20px;height:3px;background:#FAB984;margin-right:5px;"></span>置信度为90%的慢跑热点</div>
    <div><span style="display:inline-block;width:20px;height:3px;background:#ED7551;margin-right:5px;"></span>置信度为95%的慢跑热点</div>
    <div><span style="display:inline-block;width:20px;height:3px;background:#D62F27;margin-right:5px;"></span>置信度为99%的慢跑热点</div>

    <div style="font-weight:bold; margin:8px 0 3px;">地标图层</div>
    <div><span style="display:inline-block;width:10px;height:10px;background:#FFFF00;margin-right:5px;border:1px solid grey;"></span> 地标</div>
  `;
  legendDiv.appendChild(content);

  // 点击折叠/展开
  let collapsed = false;
  header.addEventListener('click', () => {
    collapsed = !collapsed;
    content.style.display = collapsed ? 'none' : 'block';
    toggleBtn.innerText = collapsed ? "▲" : "▼";
  });

  view.container.appendChild(legendDiv);
}

}
  




// 路线/地标数据
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


// 图层存储
const routeLayers = [null, null, null];
const dibiaoLayers = [null, null, null];


// 获取 JSON 数据
async function fetchJson(url) {
  const res = await fetch(url);
  return await res.json();
}


// 初始化图层
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
        // popupTemplate: { title: f.properties?.地标名 || '未知地标', content: `<p>${f.properties?.地标名 || '暂无描述'}</p>` }
      }));
    }
  });
  return layer;
}


// 路线元数据
const routes = ref([
  { id: 'route1', type:'3km短途进阶中距离', name: '运河文脉漫行线', description: '老德胜桥 → 潮王桥 → 京杭运河 → 朝晖桥 → 西湖文化广场 → 创意图书馆', length:'总长度：2997.5m', image: route1Image, point:127.4, center: [120.15, 30.28] },
  { id: 'route2', type:'2.5km环形', name: '石桥时光闭环跑道', description: '华盛达中心 → 时光公园 → 石桥河 → 石桥河绿道 ', length:'总长度：2578.5m', image:route2Image, point:109.2, center: [120.17, 30.33] },
  { id: 'route3', type:'2.5km标准短途', name: '阅跑城北公园绿道', description: '杭州图书馆 → 体育公园绿道 → 城北体育公园', length:'总长度：2484.84m', image: route3Image, point:145.0, center: [120.15, 30.31] }
]);


// 悬浮卡片
const activeDetailCard = ref(null);
const showDetailCard = (routeId) => activeDetailCard.value = routes.value.find(r => r.id === routeId);
const closeDetailCard = () => activeDetailCard.value = null;


// 点击聚焦地图并显示路线
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
.weather-container {position: absolute;top: 110px; right: 5px;z-index: 1000; /* 确保在地图上方 */}
.landmark-popup { 
  position: absolute; 
  background: white; 
  border: 1px solid #ccc; 
  padding: 8px; 
  z-index: 1000; 
  width: 320px; 
  border-radius: 6px; 
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.landmark-popup .close-btn {
  position: absolute; top: 4px; right: 4px; border: none; background: none; cursor: pointer; font-size: 16px;
}

</style>
