<!-- 测试代码，无用可忽略 -->
<template>
    <div class="route-stats">
      <h3>📊路线统计</h3>
  
      <!-- 平均值文字 -->
      <div v-if="avgValues">
        <h4>平均路段特征</h4>
        <ul>
          <li>平均坡度 (slope): {{ avgValues.slope?.toFixed(2) ?? 'N/A' }}</li>
          <li>平均绿视率 (gvi): {{ avgValues.gvi?.toFixed(2) ?? 'N/A' }}</li>
          <li>平均光照 (light): {{ avgValues.light?.toFixed(2) ?? 'N/A' }}</li>
          <li>平均兴趣点密度 (poi): {{ avgValues.poi?.toFixed(2) ?? 'N/A' }}</li>
          <li>平均视觉体验指数 (vei): {{ avgValues.vei?.toFixed(2) ?? 'N/A' }}</li>
        </ul>
      </div>
  
      <!-- 图表容器 -->
      <div ref="chart" class="chart" v-if="avgValues"></div>
    </div>
  </template>
  
  <script setup>
  import { ref, watch, onMounted } from 'vue';
  import Papa from 'papaparse';
  import * as echarts from 'echarts';
  
  const props = defineProps({
    routeResult: Object // 父组件传入的 geojson
  });
  
  // CSV 数据存储
  const edgeFeatures = ref({});
  
  // 平均值
  const avgValues = ref(null);
  const chart = ref(null);
  let myChart = null;
  
  // 加载 CSV
  async function loadCSV() {
    try {
      const res = await fetch("/res/road_modified-2.csv"); // 放到 public/res/
      const text = await res.text();
      const parsed = Papa.parse(text, { header: true });
      parsed.data.forEach(row => {
        const fidKey = row.FID ?? row.fid;
        if (fidKey !== undefined) edgeFeatures.value[fidKey] = row;
      });
      console.log("CSV 加载完成", edgeFeatures.value);
    } catch (err) {
      console.error("CSV 加载失败:", err);
    }
  }
  
  // 计算平均值
  function computeAverages() {
    if (!props.routeResult || !props.routeResult.features) return;
  
    const features = props.routeResult.features;
    const matchedEdges = features
      .map(f => edgeFeatures.value[f.properties.fid])
      .filter(Boolean);
  
    if (matchedEdges.length === 0) {
      console.warn("没有匹配到 CSV 数据的路段");
      avgValues.value = null;
      return;
    }
  
    const sumFields = ['slope','gvi','light','poi','vei'];
    const sums = {};
    sumFields.forEach(f => sums[f] = 0);
  
    matchedEdges.forEach(edge => {
      sumFields.forEach(f => {
        sums[f] += parseFloat(edge[f]) || 0;
      });
    });
  
    const n = matchedEdges.length;
    avgValues.value = {};
    sumFields.forEach(f => {
      avgValues.value[f] = sums[f]/n;
    });
  
    console.log("平均值计算完成", avgValues.value);
    initChart();
  }
  
  // 初始化 ECharts
  function initChart() {
    if (!avgValues.value) return;
    if (!chart.value) return;
  
    if (!myChart) myChart = echarts.init(chart.value);
  
    const option = {
      title: { text: '平均路段特征' },
      tooltip: {},
      xAxis: { type: 'category', data: ['slope','gvi','light','poi','vei'] },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: ['slope','gvi','light','poi','vei'].map(k => avgValues.value[k] ?? 0),
        itemStyle: { color: '#A80000' }
      }]
    };
  
    myChart.setOption(option);
  }
  
  // watch geojson
  watch(() => props.routeResult, () => {
    console.log("routeResult 变化，开始计算平均值");
    computeAverages();
  }, { immediate: true });
  
  // mounted 时加载 CSV
  onMounted(async () => {
    await loadCSV();
    computeAverages();
  });
  </script>
  
  <style scoped>
  .route-stats {
    position: absolute;
    right: 50px; /* 离右边 50px */
    top: 100px;
    background: #fff;
    padding: 10px;
    border-radius: 8px;
    box-shadow: 0 0 8px rgba(0,0,0,0.2);
    z-index: 999;
  }
  .chart {
    width: 300px;
    height: 200px;
    margin-top: 10px;
  }
  </style>
  