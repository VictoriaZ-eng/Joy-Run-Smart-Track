<template>
    <!-- 建成环境变量数据卡片（左侧） -->
    <div class="built-env-card" v-show="showBuiltEnv">
      <button class="close-btn" @click="closeAllCards">
        <span class="close-text">收起所有</span>×
      </button>
      <h1>建成环境变量指标</h1>
      <p class="build-description">该慢跑环境配套设施完善：POI多样性极高方便补给，设施密度适中兼具便利与清净，建筑面积占比合理避免压抑感，但道路曲折度和照明条件较差，需注意夜间跑步的安全性与路线规划。</p>
      <div ref="builtEnvChart" class="chart"></div>
    </div>
    
    <!-- 主观感知数据卡片（左侧） -->
    <div class="perception-card" v-show="showPerception">
      <button class="close-btn" @click="showPerception = false">×</button>
      <h1>主观感知指标</h1>
      <p class="perception-description">该慢跑环境视觉体验良好：道路视野最佳（0.219）利于保持节奏，绿化丰富（0.206）舒缓疲劳，天空开阔度适中（0.150）兼顾遮阳与通透感。</p>
      <div ref="perceptionChart" class="chart"></div>
    </div>
    
    <!-- 自然环境数据卡片（右侧） -->
    <div class="natural-env-card" v-show="showNaturalEnv">
      <button class="close-btn" @click="showNaturalEnv = false">×</button>
      <h1>自然环境指标</h1>
      <p class="natrual-description">高水域距离适中，植被覆盖良好，坡度平缓，为慢跑提供了舒适安全的自然环境，利于持久运动。</p>
      <div ref="naturalEnvChart" class="chart"></div>
    </div>
  </template>

  <script setup>
  import { ref, onMounted, onBeforeUnmount } from 'vue'
  import * as echarts from 'echarts'

  // 控制卡片显示状态
  const showBuiltEnv = ref(true)
  const showPerception = ref(true)
  const showNaturalEnv = ref(true)

  // 图表DOM引用
  const builtEnvChart = ref(null)
  const perceptionChart = ref(null)
  const naturalEnvChart = ref(null)
  
  // 图表实例
  let builtEnvChartInstance = null
  let perceptionChartInstance = null
  let naturalEnvChartInstance = null
  
  // 数据
  const perceptionData = {
    categories: ['绿化视图指数', '天空景观指数', '视觉步行能力'],
    values: [0.205507435365803, 0.149530692287085, 0.219399264398429]
  }
  
  const naturalEnvData = {
    categories: ['坡度(°)', '归一化植被指数NDVI', '离水域的平均距离(m)'],
    values: [4.9, 63.4, 201.7]
  }
  
  // 初始化所有图表
  const initCharts = () => {
    // 销毁已有实例
    disposeCharts()
    
    // 初始化建成环境图表
    if (showBuiltEnv.value && builtEnvChart.value) {
      builtEnvChartInstance = echarts.init(builtEnvChart.value)
      builtEnvChartInstance.setOption(getBuiltEnvOption())
    }
    
    // 初始化主观感知图表
    if (showPerception.value && perceptionChart.value) {
      perceptionChartInstance = echarts.init(perceptionChart.value)
      perceptionChartInstance.setOption(getPerceptionOption())
    }
    
    // 初始化自然环境图表
    if (showNaturalEnv.value && naturalEnvChart.value) {
      naturalEnvChartInstance = echarts.init(naturalEnvChart.value)
      naturalEnvChartInstance.setOption(getNaturalEnvOption())
    }
  }
  
  // 销毁所有图表实例
  const disposeCharts = () => {
    builtEnvChartInstance?.dispose()
    perceptionChartInstance?.dispose()
    naturalEnvChartInstance?.dispose()
  }
  
  // 关闭所有卡片
  const closeAllCards = () => {
    showBuiltEnv.value = false
    showPerception.value = false
    showNaturalEnv.value = false
  }

  // 获取建成环境雷达图配置
  const getBuiltEnvOption = () => {
    const builtEnvData = {
      categories: ['建筑面积', 'POI多样性', 'POI设施密度', '道路曲折度', '街道照明情况'],
      values: [0.20,  0.73, 0.31, 0.09, 0.10] 
    };

    return {
      tooltip: {
        trigger: 'item'
      },
      radar: {
        indicator: builtEnvData.categories.map((name) => ({
          name: name,
          max: 1,
          min: -1
        })),
        radius: '70%',
        splitNumber: 4,
        axisName: {
          color: '#333',
          fontSize: 12
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(255, 255, 255, 0.5)']
          }
        }
      },
      series: [{
        type: 'radar',
        data: [{
          value: builtEnvData.values, 
          name: '建成环境指标（数据标准化后）',
          areaStyle: {
            color: 'rgba(97, 144, 38,0.8)'
          },
          lineStyle: {
            width: 2,
            color: 'rgba(97, 144, 38,0.6)'
          },
          symbolSize: 6,
          label: {
            show: true,
            formatter: function(params) {
              return params.value.toFixed(1);
            }
          }
        }]
      }]
    };
  }
  
  // 获取主观感知图表配置
  const getPerceptionOption = () => {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: params => 
          `${params[0].name}: ${params[0].value}`
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: perceptionData.categories,
        axisLabel: {
          rotate: 30,
          fontSize: 12
        }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 0.3,
        axisLabel: {
          formatter: '{value}'
        }
      },
      series: [{
        type: 'bar',
        data: perceptionData.values.map((value, index) => ({
          value,
          itemStyle: {
            color: ['#91CC75', '#5470C6', '#EE6666'][index]
          }
        })),
        barWidth: '40%',
        label: {
          show: false,
          position: 'top',
          formatter: '{c}'
        }
      }]
    };
  }
  
  // 获取自然环境图表配置
  const getNaturalEnvOption = () => {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '15%',
        right: '5%',
        top: '20%',
        bottom: '10%'
      },
      xAxis: {
        type: 'value',
        name: '数值',
        axisLabel: {
          formatter: '{value}'
        }
      },
      yAxis: {
        type: 'category',
        data: naturalEnvData.categories,
        axisLine: { show: true },
        axisTick: { show: false }
      },
      series: [
        {
          name: '自然环境指标',
          type: 'bar',
          offset: [10, 0],
          padding: [2, 5],
          data: naturalEnvData.values,
          itemStyle: {
            color: function(params) {
              const colorList = ['#5470C6', '#91CC75', '#EE6666'];
              return colorList[params.dataIndex];
            }
          },
          label: {
            show: true,
            position: 'right',
            formatter: '{c}'
          },
          barWidth: '40%'
        }
      ]
    };
  }
  
  // 窗口大小变化时重绘图表
  const handleResize = () => {
    if (showBuiltEnv.value) builtEnvChartInstance?.resize()
    if (showPerception.value) perceptionChartInstance?.resize()
    if (showNaturalEnv.value) naturalEnvChartInstance?.resize()
  }
  
  onMounted(() => {
    initCharts()
    window.addEventListener('resize', handleResize)
  })
  
  onBeforeUnmount(() => {
    disposeCharts()
    window.removeEventListener('resize', handleResize)
  })
  </script>
  
  <style scoped>
  .close-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #999;
    width: auto;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1001;
    padding: 0 8px;
  }

  .close-btn:hover {
    color: #333;
  }

  .close-text {
    font-size: 12px;
    margin-right: 4px;
  }

  /* 左侧两张卡片 */
  .built-env-card,
  .perception-card {
    position: absolute;
    left: 50px;
    width: 380px;
    background: rgba(235, 239, 226, 0.85);
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 16px;
    z-index: 1000;
  }

  .built-env-card {
    top: 110px;
    height: 380px;
  }

  .perception-card {
    top: 495px; 
    height: 320px;
  }

  /* 右侧自然环境卡片 */
  .natural-env-card {
    position: absolute;
    top: 520px;
    right: 5px;
    width: 360px;
    height: 260px;
    padding: 12px 16px;
    background: rgba(235, 239, 226, 0.85);
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    z-index: 1000;
  }

  h1 {
    margin: 0 0 8px 0;
    font-size: 18px;
    text-align: center;
    color: #333;
    margin-top: 4px; 
  }

  .build-description,
  .perception-description,
  .natrual-description {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #666;
    line-height: 1.4;
    text-align: left;
    padding: 0 10px;
  }

  .built-env-card .chart {
    width: 350px;
    height: 250px;
  }

  .perception-card .chart {
    width: 100%;
    height: calc(100% - 90px);
  }

  .natural-env-card .chart {
    height: calc(100% - 95px);
    width: 100%;
    margin-top: 4px;
  }

  /* 响应式调整 */
  @media (max-width: 1200px) {
    .built-env-card,
    .perception-card,
    .natural-env-card {
      width: 300px;
    }
  }
  </style>