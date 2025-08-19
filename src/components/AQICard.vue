<template>
    <div v-if="visible" class="aqi-card">
      <button class="close-btn" @click="closeCard">×</button>
      <h1 class="title">实时空气质量</h1>
  
      <div v-if="error" class="error">
        获取失败：{{ error }}
      </div>
  
      <div v-else-if="loading">
        加载中...
      </div>
  
      <div v-else class="content">
        <p><strong>AQI空气质量指数：</strong>{{ data.air.aqi }}</p>
        <p><strong>等级：</strong>{{ data.air.category }}</p>
        <p><small>更新时间：{{ data.updateTime }}</small></p>
  
        <div ref="chartRef" class="chart-container"></div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, nextTick, watch } from "vue";
  import axios from "axios";
  import * as echarts from "echarts";
  
  const data = ref(null);
  const loading = ref(true);
  const error = ref(null);
  const chartRef = ref(null);
  const visible = ref(true); // 新增可见性控制
  let chart = null;
  
  const pollutants = [
    { key: "co", name: "一氧化碳", color: "#5470C6", scale: 50 },
    { key: "no2", name: "二氧化氮", color: "#91CC75", scale: 2 },
    { key: "o3", name: "臭氧", color: "#FAC858", scale: 1 },
    { key: "pm10", name: "可吸入颗粒物PM10", color: "#EE6666", scale: 1 },
    { key: "pm25", name: "细颗粒物PM2.5", color: "#73C0DE", scale: 1 },
    { key: "so2", name: "二氧化硫", color: "#3BA272", scale: 10 }
  ];
  
  // 获取 AQI 数据
  async function fetchAQI() {
    loading.value = true;
    error.value = null;
    try {
      const res = await axios.get("/api/qweather/now");
      data.value = res.data;
    } catch (err) {
      error.value = err.message;
      console.error(err);
    } finally {
      loading.value = false;
    }
  }
  
  // 初始化 chart
  function initChart() {
    if (chartRef.value && !chart) {
      chart = echarts.init(chartRef.value);
    }
  }
  
  // 更新环形饼图（下方统一图例）
  function updateChart() {
    if (!chart || !data.value || !data.value.air) return;
  
    const seriesData = pollutants.map((p) => {
      const rawVal = Number(data.value.air[p.key]);
      const displayVal = isNaN(rawVal) ? 0 : rawVal;
      const scaledVal = displayVal * p.scale;
      return {
        value: scaledVal,
        name: p.name,
        raw: displayVal,
        itemStyle: { color: p.color }
      };
    });
  
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: (params) => `${params.name}: ${params.data.raw}`
      },
      legend: {
        orient: 'horizontal',
        bottom: 10,
        left: 'center',
        itemWidth: 14,
        itemHeight: 14,
        formatter: name => {
          const p = seriesData.find(s => s.name === name)
          return `${name}`
        }
      },
      series: [{
        name: '污染物浓度',
        type: 'pie',
        radius: ['40%', '70%'], // 环形
        center: ['50%', '35%'],
        avoidLabelOverlap: true,
        label: { show: false }, // 不显示外部文字
        data: seriesData
      }]
    };
  
    chart.setOption(option);
    chart.resize();
  }
  
  // watch chartRef
  watch(chartRef, async (el) => {
    if (el) {
      await nextTick();
      initChart();
      updateChart();
    }
  });
  
  // watch 数据变化
  watch(data, () => {
    if (chart) updateChart();
  });
  
  // 页面挂载
  onMounted(() => {
    fetchAQI();
    setInterval(fetchAQI, 5 * 60 * 1000);
  });
  
  // 窗口自适应
  window.addEventListener('resize', () => {
    if (chart) chart.resize();
  });
  
  const closeCard = () => {
    visible.value = false;
  }
  </script>
  
  <style scoped>
  .aqi-card {
    width: 360px;
    padding: 16px;
    border-radius: 12px;
    background: rgba(235, 239, 226, 0.674);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    font-family: sans-serif;
    height: 400px;
    position: relative; /* 为关闭按钮定位提供上下文 */
  }
  .title {
    font-size: 18px;
    margin-bottom: 12px;
    text-align: center;
  }
  .error {
    color: red;
  }
  .content p {
    margin: 6px 0;
  }
  .chart-container {
    width: 350px;
    height: 250px;
  }
  .close-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #999;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1; /* 确保按钮在最上层 */
  }
  
  .close-btn:hover {
    color: #333;
  }
  </style>