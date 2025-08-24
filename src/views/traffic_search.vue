<!-- 交通查询功能 -->
<template>
<div class="traffic-panel">
  <h2>交通查询</h2>
  <p>您可以使用右侧工具栏直接圈选查询范围，
或草绘慢跑终点位置并设置缓冲距离（如1000米范围），
系统将自动显示该区域内的公交和地铁站点信息。</p>
  
  <label for="bufferRadius">您期望的缓冲距离（米）：</label>
  <input id="bufferRadius" type="number" v-model.number="bufferRadius" min="100" step="100" />
</div>
</template>

<script setup>
import { inject, onMounted, onBeforeUnmount, ref, watch } from "vue";
import { useRoute } from "vue-router";
import FeatureLayer from "@geoscene/core/layers/FeatureLayer.js";
import GraphicsLayer from "@geoscene/core/layers/GraphicsLayer.js";
import Sketch from "@geoscene/core/widgets/Sketch.js";
import * as geometryEngine from "@geoscene/core/geometry/geometryEngine.js";

const bufferRadius = ref(1000);
const view = inject("view");
const route = useRoute();

let sketchLayer = null;
let sketch = null;
let resultLayer = null;

// 草图工具栏只显示一次
function addSketchUI() {
  if (sketch && view) {
    view.ui.add(sketch, "top-right");
  }
}

// 草图工具栏移除
function removeSketchUI() {
  if (sketch && view) {
    view.ui.remove(sketch);
  }
}

onMounted(() => {
  if (!view) return;

  if (!sketchLayer) {
    sketchLayer = new GraphicsLayer();
    view.map.add(sketchLayer);
  }

  if (!resultLayer) {
    resultLayer = new GraphicsLayer({ title: "交通结果" });
    view.map.add(resultLayer);
  }

  const busLayer = new FeatureLayer({
    url: "https://www.geosceneonline.cn/server/rest/services/Hosted/拱墅公交站/FeatureServer",
    title: "公交站点",
    outFields: ["*"],
    visible: false
  });

  const subwayLayer = new FeatureLayer({
    url: "https://www.geosceneonline.cn/server/rest/services/Hosted/拱墅地铁站/FeatureServer",
    title: "地铁站点",
    outFields: ["*"],
    visible: false
  });

  view.map.addMany([busLayer, subwayLayer]);

  if (!sketch) {
    sketch = new Sketch({
      layer: sketchLayer,
      view,
      creationMode: "update"
    });

    sketch.on("create", async (event) => {
      if (event.state !== "complete") return;
      let geometry = event.graphic.geometry;

      if (geometry.type === "point") {
        const buffer = geometryEngine.buffer(geometry, bufferRadius.value, "meters");
        geometry = buffer;

        sketchLayer.add({
          geometry: buffer,
          symbol: {
            type: "simple-fill",
            color: [0, 0, 0, 0.1],
            outline: { color: [0, 0, 0, 0.8], width: 1 }
          }
        });
      }

      resultLayer.removeAll();

      const queryAndShow = async (layer, geometry, symbol) => {
        const query = layer.createQuery();
        query.geometry = geometry;
        query.spatialRelationship = "intersects";
        query.returnGeometry = true;
        query.outFields = ["*"];
        const results = await layer.queryFeatures(query);

        return results.features.map(f => ({
          geometry: f.geometry,
          attributes: f.attributes,
          symbol,
          popupTemplate: layer.title === "公交站点"
            ? { title: "{sname}", content: "相关线路: {rname}" }
            : { title: "{name}", content: "地铁线路: {address}" }
        }));
      };

      const busGraphics = await queryAndShow(busLayer, geometry, {
        type: "simple-marker", style: "circle", color: "#00C5FF", size: 8, outline: { color: "grey", width: 1 }
      });

      const subwayGraphics = await queryAndShow(subwayLayer, geometry, {
        type: "simple-marker", style: "circle", color: "#c86080", size: 10, outline: { color: "grey", width: 1 }
      });

      resultLayer.addMany(busGraphics.concat(subwayGraphics));
    });
  }

  // 初次进入路由显示 Sketch
  if (route.name === "Traffic_search") addSketchUI();

  // 监听路由变化
  watch(() => route.fullPath, (newPath) => {
    if (route.name === "Traffic_search") addSketchUI();
    else removeSketchUI();
  });
});

onBeforeUnmount(() => {
  removeSketchUI();
});
</script>


<style scoped>
.traffic-panel {
  position: absolute;
  top: 120px;
  left: 50px;
  background: rgb(235, 239, 226);
  padding: 12px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 2000;
  color:rgb(31, 52, 6);
  width:390px;
}

</style>
