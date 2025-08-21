<template>
    <div class="route-form">
      <h2>路线查询</h2>
  
      <!-- 起点坐标 -->
      <div>
        <label>起点纬度：</label>
        <input v-model.number="form.start_lat" type="number" step="0.000001" />
        <button @click="selectStartPoint">在地图上选择起点</button>
        <span v-if="form.start_lat && form.start_lon">
          已选起点：{{ form.start_lat.toFixed(6) }}, {{ form.start_lon.toFixed(6) }}
        </span>
      </div>
  
      <!-- 终点坐标（部分模式必填） -->
      <div>
        <label>终点纬度：</label>
        <input v-model.number="form.end_lat" type="number" step="0.000001" />
        <button @click="selectEndPoint">在地图上选择终点</button>
        <span v-if="form.end_lat && form.end_lon">
          已选终点：{{ form.end_lat.toFixed(6) }}, {{ form.end_lon.toFixed(6) }}
        </span>
      </div>
  
      <!-- 约束模式 -->
      <div>
        <label>约束模式：</label>
        <select v-model="form.constraint_mode">
          <option v-for="(label, value) in constraintOptions" :key="value" :value="Number(value)">
            {{ value }} - {{ label }}
          </option>
        </select>
      </div>
  
      <!-- 偏好模式 -->
      <div>
        <label>偏好模式：</label>
        <select v-model="form.preference_mode">
          <option v-for="(label, value) in preferenceOptions" :key="value" :value="Number(value)">
            {{ value }} - {{ label }}
          </option>
        </select>
      </div>
  
      <!-- 目标距离 -->
      <div>
        <label>目标距离 (米)：</label>
        <input v-model.number="form.target_distance" type="number" />
      </div>
  
      <!-- 提交按钮 -->
      <button @click="getRoute">获取路线</button>
      <button @click="removeRoute">移除路线</button>
  
      <!-- 结果展示 -->
      <div v-if="routeResult" class="result">
        <h3>路线结果</h3>
        <p>文件名: {{ routeResult.filename }}</p>
        <p>总距离: {{ routeResult.route_info.total_distance }}</p>
        <p>总路段: {{ routeResult.route_info.total_segments }}</p>
        <p>得分/米: {{ routeResult.route_info.score_per_meter }}</p>
      </div>
  
      <div v-if="errorMessage" class="error">
        错误: {{ errorMessage }}
      </div>
    </div>
  </template>
  
  <script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import GeoJSONLayer from "@geoscene/core/layers/GeoJSONLayer.js";
import Point from "@geoscene/core/geometry/Point.js";
import Graphic from "@geoscene/core/Graphic.js";
import SimpleMarkerSymbol from "@geoscene/core/symbols/SimpleMarkerSymbol.js";

// 表单数据
const form = ref({
  start_lat: 30.3210982,
  start_lon: 120.1788077,
  end_lat: 30.313572,
  end_lon: 120.1776803,
  constraint_mode: 1,
  preference_mode: 1,
  target_distance: 5000
});

// 响应式变量
const routeResult = ref(null);
const errorMessage = ref(null);

// 普通变量保存地图图层/临时点，避免 Vue Proxy 冲突
let routeLayer = null;
let tempGraphic = null;
let selectMode = null; // "start" 或 "end"

// 模式选项
const constraintOptions = {
  1: "固定起点终点",
  2: "起点到终点（无环）",
  3: "起点回路（Round-trip）",
  4: "随机回路",
  5: "起点到终点（约束优化）",
  6: "起点到终点（高级优化）"
};

const preferenceOptions = {
  1: "最短路线",
  2: "滨水路线",
  3: "高绿化路线",
  4: "景点优先",
  5: "运动设施优先",
  6: "人流活跃",
  7: "自定义"
};

// 获取 MapView
const view = window.sceneView;

// 地图点击选择点
onMounted(() => {
  view.on("click", (evt) => {
    if (!selectMode) return;

    const mapPoint = evt.mapPoint;
    if (!mapPoint) return;

    // 投影 -> 经纬度
    let lonLat;
    if (view.spatialReference?.isWebMercator) {
      const x = mapPoint.x;
      const y = mapPoint.y;
      lonLat = {
        x: (x / 20037508.34) * 180,
        y: (y / 20037508.34) * 180,
      };
      lonLat.y = 180 / Math.PI * (2 * Math.atan(Math.exp(lonLat.y * Math.PI / 180)) - Math.PI / 2);
    } else {
      lonLat = { x: mapPoint.x, y: mapPoint.y };
    }

    if (selectMode === "start") {
      form.value.start_lon = lonLat.x;
      form.value.start_lat = lonLat.y;
    } else if (selectMode === "end") {
      form.value.end_lon = lonLat.x;
      form.value.end_lat = lonLat.y;
    }

    // 移除旧临时点
    if (tempGraphic) {
      view.map.remove(tempGraphic);
    }

// 用原始 mapPoint（投影坐标）创建临时点
tempGraphic = new Graphic({
  geometry: new Point({ x: mapPoint.x, y: mapPoint.y }),
  symbol: new SimpleMarkerSymbol({
    color: selectMode === "start" ? "green" : "blue",
    size: 12,       // 点稍微大一点方便看
    outline: {      // 给点加个边框，更明显
      color: "#fff",
      width: 2
    }
  })
});

// 添加到地图
view.map.add(tempGraphic);
    selectMode = null;
  });
});

// 选择起点/终点
function selectStartPoint() {
  selectMode = "start";
  alert("点击地图选择起点");
}

function selectEndPoint() {
  selectMode = "end";
  alert("点击地图选择终点");
}

// 获取路线
async function getRoute() {
  try {
    errorMessage.value = null;
    routeResult.value = null;

    const res = await axios.post("/api/get_routes", form.value);

    if (res.data.success) {
      routeResult.value = res.data;

      // 移除旧路线
      if (routeLayer) {
        view.map.remove(routeLayer);
        routeLayer = null;
      }

      // 渲染新路线
      if (res.data.geojson) {
        routeLayer = new GeoJSONLayer({
          url: URL.createObjectURL(
            new Blob([JSON.stringify(res.data.geojson)], { type: "application/json" })
          ),
          renderer: {
            type: "simple",
            symbol: {
              type: "simple-line",
              color: [255, 0, 0, 0.8],
              width: 3
            }
          }
        });

        view.map.add(routeLayer);
        await routeLayer.when();
        const extent = await routeLayer.queryExtent();
        view.goTo(extent.extent.expand(1.2));
      }
    } else {
      errorMessage.value = res.data.error;
    }
  } catch (err) {
    errorMessage.value = err.message;
  }
}

// 移除路线
function removeRoute() {
  if (routeLayer) {
    view.map.remove(routeLayer);
    routeLayer = null;
  }
  routeResult.value = null;
}
</script>

  
  
  <style scoped>
  .route-form {
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    width: 320px;
    background: #fafafa;
    z-index: 1000;
  }
  .route-form div {
    margin-bottom: 10px;
  }
  .result {
    margin-top: 1rem;
    padding: 0.5rem;
    background: #e9f7ef;
  }
  .error {
    margin-top: 1rem;
    color: red;
  }
  </style>
  