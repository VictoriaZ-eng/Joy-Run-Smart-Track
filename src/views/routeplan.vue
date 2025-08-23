<template>
    <div class="route-form">
      <h2>🏃‍♀️个性化慢跑路径规划🏃</h2>
  
      <!-- 起点坐标 -->
      <div class="form-group">
        <div class="label-row">
          <label>🚩起点坐标：</label>
          <button class="btn" @click="selectStartPoint">选择起点</button>
          <button 
            class="btn danger" 
            @click="removeStartPoint"
            :disabled="!form.start_lat"
          >
            移除起点
          </button>
        </div>
        <input
          class="input"
          :value="form.start_lat && form.start_lon 
            ? `${form.start_lat.toFixed(6)}, ${form.start_lon.toFixed(6)}` 
            : ''"
          type="text"
          readonly
          placeholder="请在地图上选择起点"
        />
      </div>
  
      <!-- 终点坐标 -->
      <div class="form-group">
        <div class="label-row">
          <label>🎯终点坐标：</label>
          <button class="btn" @click="selectEndPoint">选择终点</button>
          <button 
            class="btn danger" 
            @click="removeEndPoint"
            :disabled="!form.end_lat"
          >
            移除终点
          </button>
        </div>
        <input
          class="input"
          :value="form.end_lat && form.end_lon 
            ? `${form.end_lat.toFixed(6)}, ${form.end_lon.toFixed(6)}` 
            : ''"
          type="text"
          readonly
          placeholder="请在地图上选择终点"
        />
      </div>
  
      <!-- 约束模式 -->
      <div class="form-group">
        <label>⚙️路径约束模式：</label>
        <select v-model="form.constraint_mode" class="select">
          <option
            v-for="(label, value) in constraintOptions"
            :key="value"
            :value="Number(value)"
          >
            {{ value }} - {{ label }}
          </option>
        </select>
      </div>
  
      <!-- 偏好模式 -->
      <div class="form-group">
        <label>💕路径偏好模式：</label>
        <select v-model="form.preference_mode" class="select">
          <option
            v-for="(label, value) in preferenceOptions"
            :key="value"
            :value="Number(value)"
          >
            {{ value }} - {{ label }}
          </option>
        </select>
      </div>
  
      <!-- 目标距离 -->
      <div class="form-group">
        <label>📏目标距离 (米)：</label>
        <input v-model.number="form.target_distance" type="number" class="input" />
      </div>
  
      <!-- 提交按钮 -->
      <div class="button-group">
        <button class="btn primary" @click="getRoute">✅规划路线</button>
        <button class="btn danger" @click="removeRoute">❌移除路线</button>
        <button class="btn info" @click="showHelp = !showHelp">❓帮助文档</button>
      </div>
        <!-- 左侧弹出卡片 -->
        <!-- 左侧弹出卡片 -->
<div v-if="showHelp" class="help-card">
  <h3>可慢跑性得分说明</h3>
  
  <p>
    1、通过多尺度地理加权回归（MGWR）模型分析慢跑行为与城市环境因素（如绿化、灯光、设施、坡度、视野、滨水等）的关系。<br>
    2、模型解释力达91.1%，表明能有效捕捉环境对慢跑偏好的影响。<br>
    3、每条道路会根据其环境特征计算出一个综合得分，用于衡量慢跑适宜性。
  </p>

  <h4>约束模式说明</h4>
  <table class="help-table">
    <thead>
      <tr>
        <th>模式</th>
        <th>名称</th>
        <th>说明</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>有终点，距离约束</td><td>指定起点和终点，路线总长度不超过设定值</td></tr>
      <tr><td>2</td><td>有终点，路段数约束</td><td>指定起点和终点，路线包含的路段数不超过设定值</td></tr>
      <tr><td>3</td><td>无终点，距离约束</td><td>仅指定起点，路线总长度不超过设定值</td></tr>
      <tr><td>4</td><td>无终点，路段数约束</td><td>仅指定起点，路线包含的路段数不超过设定值</td></tr>
      <tr><td>5</td><td>有终点，最短距离</td><td>指定起点和终点，优先选择最短路径</td></tr>
      <tr><td>6</td><td>有终点，最少路段数</td><td>指定起点和终点，优先选择转弯最少、最直接的路径</td></tr>
    </tbody>
  </table>

  <h4>偏好模式说明</h4>
  <table class="help-table">
    <thead>
      <tr>
        <th>模式</th>
        <th>名称</th>
        <th>说明</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>综合得分</td><td>基于MGWR和蚁群算法计算的综合考虑所有自变量的可慢跑性得分</td></tr>
      <tr><td>2</td><td>滨水路线</td><td>重点考虑自变量Water，优先选择沿河的道路</td></tr>
      <tr><td>3</td><td>绿化路线</td><td>重点考虑自变量GVI，优先选择绿化率高、公园附近的道路</td></tr>
      <tr><td>4</td><td>视野开阔路线</td><td>重点考虑自变量SVI，优先选择开阔、少遮挡的道路</td></tr>
      <tr><td>5</td><td>夜间灯光充足路线</td><td>重点考虑自变量Light，优先选择路灯覆盖好、夜间明亮的道路</td></tr>
      <tr><td>6</td><td>设施便利路线</td><td>重点考虑自变量POI，优先选择附近有便利店、厕所、休息设施的道路</td></tr>
      <tr><td>7</td><td>坡度平缓路线</td><td>重点考虑自变量Slope，优先选择坡度小、平坦的道路</td></tr>
    </tbody>
  </table>

  <button class="btn danger" @click="showHelp = false">关闭</button>
</div>

      <!-- 结果展示 -->
      <div v-if="routeResult" class="result">
        <h3>📊路线结果</h3>
        <p>总距离(米): {{ routeResult.route_info.total_distance}}</p>
        <p>总路段: {{ routeResult.route_info.total_segments }}</p>
        <p>全路径可慢跑性得分: {{totalScore}}</p>
      </div>
  
      <div v-if="errorMessage" class="error">
        ⚠️路径规划失败: 请检查参数配置，一般是因为没有满足约束条件的节点，请调整约束范围（目标距离），或切换约束模式，可借助右侧测量工具确定距离。
      </div>
    </div>
    <!-- <RouteStats v-if="routeResult" :routeResult="routeResult" /> -->
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted, computed } from "vue";
  import axios from "axios";
  import GeoJSONLayer from "@geoscene/core/layers/GeoJSONLayer.js";
  import Graphic from "@geoscene/core/Graphic.js";
  import SimpleMarkerSymbol from "@geoscene/core/symbols/SimpleMarkerSymbol.js";
  import DistanceMeasurement2D from '@geoscene/core/widgets/DistanceMeasurement2D.js';
  import GraphicsLayer from "@geoscene/core/layers/GraphicsLayer.js";
//   import RouteStats from './RouteStats.vue'

  const showHelp = ref(false);


  // 测量距离辅助工具
  let distanceMeasurement2D = null;
  onMounted(() => {
    if (!distanceMeasurement2D) {
      distanceMeasurement2D = new DistanceMeasurement2D({
        view: view,
        unit: 'kilometers',
        unitOptions: ["kilometers", "meters", "miles", "feet"],
        iconClass: 'esri-icon-measure-line'
      });
    }
    if (!view.ui.components.includes(distanceMeasurement2D)) {
      view.ui.add(distanceMeasurement2D, { position: 'bottom-left', index: 0 });
    }
  });
  onUnmounted(() => {
    if (distanceMeasurement2D) {
      view.ui.remove(distanceMeasurement2D);
    }
  });
  
  // 表单数据
  const form = ref({
    start_lat: null,
    start_lon: null,
    end_lat: null,
    end_lon: null,
    constraint_mode: 1,
    preference_mode: 1,
    target_distance: 5000
  });
  
  // 响应式变量
  const routeResult = ref(null);
  const errorMessage = ref(null);
  const totalScore = computed(() => {
    if (!routeResult.value?.route_info) return 0;
    return (
      routeResult.value.route_info.total_distance * 
      routeResult.value.route_info.score_per_meter
    ).toFixed(2);
  });
  
  // 普通变量保存地图图层/临时点
  let routeLayer = null;
  let startGraphic = null;
  let endGraphic = null;
  let tempGraphicLayer = null;
  let selectMode = null; // "start" 或 "end"
  
  // 模式选项
  const constraintOptions = {
    1: "固定起点终点（距离约束）",
    2: "固定起点终点（路段数约束）",
    3: "无终点（距离约束）",
    4: "无终点（路段数约束）",
    5: "固定起点终点，最短距离（无约束）",
    6: "固定起点到终点，最少路段数（无约束）"
  };
  const preferenceOptions = {
    1: "👍综合高可慢跑性得分路线",
    2: "🏞️滨水路线",
    3: "🌿高绿化（遮荫）路线",
    4: "🏞视野开阔路线",
    5: "🌆夜间灯光充足路线",
    6: "🏪设施便利路线",
    7: "🟩坡度平缓路线"
  };
  
  // 获取 MapView
  const view = window.sceneView;
  
  // 地图点击选择点
  onMounted(() => {
    view.on("click", (evt) => {
      if (!selectMode) return;
      const mapPoint = evt.mapPoint;
      if (!mapPoint) return;
  
      let lonLat;
      if (view.spatialReference?.isWebMercator) {
        const x = mapPoint.x;
        const y = mapPoint.y;
        lonLat = { x: (x / 20037508.34) * 180, y: (y / 20037508.34) * 180 };
        lonLat.y = 180 / Math.PI * (2 * Math.atan(Math.exp(lonLat.y * Math.PI / 180)) - Math.PI / 2);
      } else {
        lonLat = { x: mapPoint.x, y: mapPoint.y };
      }
  
      if (!tempGraphicLayer) {
        tempGraphicLayer = new GraphicsLayer();
        view.map.add(tempGraphicLayer);
      }
  
      if (selectMode === "start") {
        form.value.start_lon = lonLat.x;
        form.value.start_lat = lonLat.y;
        if (startGraphic) tempGraphicLayer.remove(startGraphic);
        startGraphic = new Graphic({
          geometry: mapPoint,
          symbol: new SimpleMarkerSymbol({ color: "green", size: 12, outline: { color: "#fff", width: 2 } })
        });
        tempGraphicLayer.add(startGraphic);
      } else if (selectMode === "end") {
        form.value.end_lon = lonLat.x;
        form.value.end_lat = lonLat.y;
        if (endGraphic) tempGraphicLayer.remove(endGraphic);
        endGraphic = new Graphic({
          geometry: mapPoint,
          symbol: new SimpleMarkerSymbol({ color: "blue", size: 12, outline: { color: "#fff", width: 2 } })
        });
        tempGraphicLayer.add(endGraphic);
      }
  
      selectMode = null;
    });
  });
  
  // 选择起点/终点
  function selectStartPoint() { selectMode = "start"; alert("点击地图选择起点"); }
  function selectEndPoint() { selectMode = "end"; alert("点击地图选择终点"); }
  
  // 移除起点/终点
  function removeStartPoint() {
    form.value.start_lat = null;
    form.value.start_lon = null;
    if (startGraphic && tempGraphicLayer) { tempGraphicLayer.remove(startGraphic); startGraphic = null; }
  }
  function removeEndPoint() {
    form.value.end_lat = null;
    form.value.end_lon = null;
    if (endGraphic && tempGraphicLayer) { tempGraphicLayer.remove(endGraphic); endGraphic = null; }
  }

  // 获取路线
  async function getRoute() {
    try {
      routeResult.value = null;
      const res = await axios.post("/api/get_routes", form.value);
  
      if (res.data.success) {
        errorMessage.value = null;
        routeResult.value = res.data;
        if (routeLayer) { view.map.remove(routeLayer); routeLayer = null; }
        if (res.data.geojson) {
          routeLayer = new GeoJSONLayer({
            url: URL.createObjectURL(new Blob([JSON.stringify(res.data.geojson)], { type: "application/json" })),
            renderer: { type: "simple", symbol: { type: "simple-line", color:'#A80000', width: 3 } },
          });
          view.map.add(routeLayer);
          await routeLayer.when();
          const extent = await routeLayer.queryExtent();
          view.goTo(extent.extent.expand(1.2));
        }
      } else { errorMessage.value = res.data.error; }
    } catch (err) { errorMessage.value = err.message; }
  }
 

  // 移除路线
  function removeRoute() {
    if (routeLayer) { view.map.remove(routeLayer); routeLayer = null; }
    routeResult.value = null;
  }
  </script>
  
  <style scoped>
  .route-form {
    color:rgb(31, 52, 6);
    padding: 1rem;
    border: 0.5px solid #ccc;
    border-radius: 8px;
    width: 350px;
    background: rgb(242, 244, 238);
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    z-index: 10;
    height:700px;
  }
  .route-form div { margin-bottom: 10px; }
  .result {
    margin-top: 1rem;
    padding: 0.5rem;
    background: #e9f7ef;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    height:160px;
  }
  .error { margin-top: 1rem; color: red; }
  .form-group { margin-bottom: 18px; }
  .label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
  .input, .select {
    width: 100%;
    padding: 10px 12px;
    font-size: 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    background: #fff;
    box-sizing: border-box;
  }
  .select { appearance: none; }
  .btn {
    padding: 6px 12px;
    background: #fff;
    border: 1px solid #ccc;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }
  .btn:hover { background: #f0f0f0; }
  .button-group { display: flex; gap: 12px; }
  .btn.primary { background: #457847; color: #fff; border: none; }
  .btn.primary:hover { background: #45a049; }
  .btn.danger { background: #bd453c; color: #fff; border: none; }
  .btn.danger:hover { background: #da190b; }
  .btn.info{background:#6ab1e3; color: #fff; border: none; }
  .btn.info:hover{background:#2d95df;}
  .help-card {
  position: fixed;
  top: 100px;
  left: 50px;
  width: 400px;
  max-height: 80vh;
  overflow-y: auto;
  background: #f9f9f9;
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 2px 2px 12px rgba(0,0,0,0.2);
  z-index: 2000;
}
.help-card h3 {
  margin-top: 0;
  font-size: 16px;
  color: #2c3e50;
}
.help-card h4 {
  margin-top: 12px;
  font-size: 14px;
  color: #34495e;
}
.help-card p {
  font-size: 13px;
  line-height: 1.5;
}
.help-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  margin-bottom: 12px;
}
.help-table th, .help-table td {
  border: 1px solid #ccc;
  padding: 6px 8px;
  font-size: 12px;
  text-align: left;
}
.help-table th {
  background-color: #e3f2fd;
}
.chart-card {
  margin-top: 16px;
  padding: 12px;
  background: #fefefe;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.15);
}


  </style>
  