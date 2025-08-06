<template>
    <div ref="chartContainer" class="route-chart"></div>
  </template>
  
  <script setup>
  import { ref, onMounted, watch } from 'vue';
  import { Bar } from '@antv/g2plot';
  import { routeCharts, barConfig } from '@/data/routeCharts';
  
  // 定义11个指标的颜色（可根据需要调整）
  const metricColors = {
    '建筑密度': '#8dd3c7',
    'POI多样性': '#ffffb3',
    'POI密度': '#bebada',
    '道路曲折度': '#fb8072',
    '街道照明情况': '#80b1d3',
    '天空景观指数': '#fdb462',
    '绿化视图指数': '#b3de69',
    '视觉步行能力': '#fccde5',
    '归一化植被指数': '#d9d9d9',
    '坡度': '#bc80bd',
    '离水域的平均距离': '#ccebc5'
  };
  
  const props = defineProps({
    routeId: String,
    metricValues: Object
  });
  
  const chartContainer = ref(null);
  let chartInstance = null;
  
  const renderChart = () => {
    if (!props.routeId || !chartContainer.value) return;
  
    // 获取当前路线的图表配置
    const config = routeCharts[props.routeId] || {
      metrics: Object.entries(props.metricValues || {}).map(([name, value]) => ({
        name: name.replace('SUM_C_', '').replace('_', ''),
        value: value,
        max: 1
      })),
      highlightColor: '#888888'
    };
  
    // 准备图表数据
    const data = config.metrics.map(item => ({
      ...item,
      percent: Math.round((item.value / item.max) * 100),
      // 添加颜色字段
      color: metricColors[item.name] || config.highlightColor
    }));
  
    if (chartInstance) {
      chartInstance.destroy();
    }
  
    // 创建条形图实例
    chartInstance = new Bar(chartContainer.value, {
      data,
      xField: 'value',
      yField: 'name',
      seriesField: 'name', // 关键：按指标名称区分颜色
      color: ({ name }) => {
        return metricColors[name] || config.highlightColor;
      },
      meta: {
        value: {
          alias: '得分',
          formatter: (v) => `${v.toFixed(2)}`
        }
      },
      ...barConfig,
      barStyle: {
        lineWidth: 0,
        radius: [4, 4, 0, 0] // 顶部圆角
      },
      yAxis: {
        label: {
          style: {
            fontSize: 11
          },
          formatter: (name) => name.length > 8 ? `${name.slice(0,8)}...` : name
        }
      },
      tooltip: {
        showTitle: false,
        fields: ['name', 'value', 'max'],
        formatter: (datum) => {
          return {
            name: datum.name,
            value: `${datum.value.toFixed(2)} / ${datum.max}`
          };
        }
      },
      label: {
        position: 'middle',
        style: {
          fill: 'black',
          fontSize: 10,
          shadowBlur: 2,
          shadowColor: 'rgba(0,0,0,0.3)'
        },
        formatter: (item) => `${(item.value * 100).toFixed(0)}%`
      }
    });
  
    chartInstance.render();
  };
  
  onMounted(renderChart);
  watch(() => props.routeId, renderChart);
  </script>
  
  <style scoped>
  .route-chart {
    width: 100%;
    height: 500px; /* 增加高度适应11个指标 */
    margin-top: 16px;
    background: transparent; /* 确保背景透明 */
    left:500px;
  }
  </style>