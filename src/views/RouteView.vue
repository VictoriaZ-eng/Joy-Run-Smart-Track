<template>
  <!-- 输入了起点和终点之后,还没有摁查询路径的画面 -->
    <div class="lu-jing-gui-hua">
      <!-- 搜索框 -->
      <!-- 外层容器 -->
      <div class="search-containers">
        <!-- 交换的侧边栏 -->
        <div class="revert-containers">
          <div class="car"><img src='@/assets/image/map_icon/car.png'></div>
          <div class="swap-action">
            <!-- 绑定 swap 方法到点击事件 -->
            <button @click="swap" title="切换起终点">
              <img :src="require('@/assets/image/map_icon/revert_new_dark.png')" alt="" class="revert">
            </button>
          </div>
        </div>
        <!-- 搜索起点的容器 -->
        <div class="search-container start">
          <!-- 图片 -->
          <div class="search-icon-wrapper">
            <img src='@/assets/image/map_icon/pink-circle.png' alt="pink">
          </div>
          <!-- 输入框 -->
          <input type="text" v-model="searchQueryStart" @input="onSearchInputChange($event, true)" placeholder="请输入起点" class="search-box search-box-start"/>
          <!-- 搜索框内部的删除图片 -->
          <span class="search-box-img">
            <div class="delete" title="清空" @click="clc1">
              <img src='@/assets/image/map_icon/cancel.png' alt="delete1">
            </div>
          </span>
          <!-- 起点搜索结果展示 -->
          <div class="search-results" v-if="searchResults.length && searchQueryStart" ref="searchResultsStart">
      <ul>
        <li v-for="(result, index) in searchResults" :key="index" :class="{ 'highlighted': index === highlightedIndex }" @click="selectResult(result, true)">
          {{ result.name }}
        </li>
          </ul>
          </div>
      </div>
        <!-- 搜索终点的容器 -->
        <div class="search-container end">
          <!-- 图片容器 -->
          <div class="search-icon-wrapper">
            <img src='@/assets/image/map_icon/green-circle.png' alt="green">
          </div>
          <!-- 输入框 -->
          <input type="text" v-model="searchQueryEnd" @input="onSearchInputChange($event, false)" placeholder="请输入终点" class="search-box search-box-end"/>
          <!-- 搜索框内部的删除图片 -->
          <span class="search-box-img">
            <div class="delete" title="清空" @click="clc2">
              <img src='@/assets/image/map_icon/cancel.png' alt="delete1">
            </div>
          </span>
          <!-- 终点搜索结果展示 -->
          <div class="search-results" v-if="searchResultsEnd.length && searchQueryEnd" ref="searchResultsEnd">
      <ul>
        <li v-for="(result, index) in searchResultsEnd" :key="index" :class="{ 'highlighted': index === highlightedIndex }" @click="selectResult(result, false)">
          {{ result.name }}
        </li>
            </ul>
          </div>
        </div>
        <div class="search-action" @click="onSearch" title="搜索">
          <img :src="require('@/assets/image/map_icon/search.png')" alt="" class="search">
        </div>
      <!-- 新的覆盖层容器 -->
      <div v-if="isLoading" class="loader-overlay">
        <div class="loader">
        </div>
      </div>
      </div>
    </div>
    <!-- 地图展示 -->
    <div id="viewDiv"></div>
    <div v-if="ismaploading" class="maploader-overlay">
      <div class="maploader">
      </div>
    </div>
    <!-- 时间选择框和路径展示框 -->
    <div class="main-container">
      <!-- 时间选择框 -->
      <div class="choose-time">
        <div class="form-group">
          <label for="date-input">选择日期：</label>
          <input id="date-input" type="date" v-model="selectedDate" :min="minDate" :max="maxDate" :class="{ 'invalid-date': isDateDisabled(selectedDate) }" @change="handleDateChange">
          <label for="time-input">选择时间：</label>
          <input id="time-input" type="time" v-model="formattedTime" @input="onTimeInputChange" step="600"> <!-- 600秒 = 10分钟 -->
        </div>
      </div>
      <div>
    <!-- 路线展示 -->
    <transition name="fade">
        <div class="routelist" v-show="isRouteListVisible">
          <ul class="cardlist">
            <div class="route" data-index="1" @click="highlightRoute('noGlareRouteId')">
              <div class="introduction" :style="{ color: getColor(1) }">无眩光路径</div>
              <p class="intro">
                <span>用时：{{totalHours}}小时{{totalMinutes}}分钟</span> |
                <!-- <span></span> -->
                <span>路长：{{totalDistance}}</span>
                <!-- <span></span> -->
              </p>
              <p class="intro">
                <span>途径：{{totalPass }}</span>
                <!-- <span></span> -->
              </p>
            </div>
            <div class="route" data-index="0" @click="highlightRoute('defaultRouteId')">
              <div class="introduction" :style="{ color: getColor(0) }">常规路径</div>
              <p class="intro">
                <span>用时：{{noGlareTotalHours}}小时{{noGlareTotalMinutes}}分钟</span> |
                <!-- <span></span> -->
                <span>路长：{{noGlareTotalDistance}}</span>
                <!-- <span></span> -->
              </p>
              <p class="intro">
                <span>途径：{{noGlareTotalPass}}</span>
                <!-- <span></span> -->
              </p>
            </div>
          </ul>
          <span class="toggle-button" @click="toggleRouteList" title="隐藏">
            <img src='@/assets/image/map_icon/cancel.png' alt="delete1">
          </span>
        </div>
      </transition>
      <button v-if="!isRouteListVisible" @click="toggleRouteList" class="open-button">展开路线结果</button>
    </div>
  </div>
</template>

<script>
import Map from '@geoscene/core/Map.js'
import MapView from '@geoscene/core/views/MapView.js'
import Graphic from '@geoscene/core/Graphic'
import Point from '@geoscene/core/geometry/Point.js'
import GraphicsLayer from '@geoscene/core/layers/GraphicsLayer'
import FeatureLayer from '@geoscene/core/layers/FeatureLayer'
import Extent from '@geoscene/core/geometry/Extent'
import axios from 'axios'
import { markRaw } from 'vue'
import BasemapGallery from '@geoscene/core/widgets/BasemapGallery.js'
import Compass from '@geoscene/core/widgets/Compass.js'
import ScaleBar from '@geoscene/core/widgets/ScaleBar.js'
import DistanceMeasurement2D from '@geoscene/core/widgets/DistanceMeasurement2D.js'
import LayerList from '@geoscene/core/widgets/LayerList.js'
import { parseUrlParams, toggleRouteList, getColor, highlightRoute, selectResult, swap } from '@/assets/share_js/routeview_public'
import { handleKeydown, updateTime, clc1, clc2, isDateDisabled, handleDateChange, onTimeInputChange, onSearchInputChange } from '@/assets/share_js/routeplanning_all'

export default {
  name: 'RouteView',
  data () {
    return {
      searchQueryStart: '',
      searchQueryEnd: '',
      selectedResultStart: null,
      selectedResultEnd: null,
      searchResults: [],
      searchResultsEnd: [],
      isLoading: false,
      ismaploading: false,
      totalHours: 0,
      totalMinutes: 0,
      totalDistance: '0千米',
      selectedDate: '', // 用户选择的日期
      selectedTime: '', // 用户选择的时间
      noGlareTotalHours: 0, // 无眩光路径的总时长（小时）
      noGlareTotalMinutes: 0, // 无眩光路径的总时长（分钟）
      highlightedIndex: -1, // 高亮的搜索结果索引
      noGlareTotalDistance: '0千米', // 无眩光路径的总距离
      highlightedRouteId: null, // 当前高亮显示的路径ID
      routeLayers: {}, // 存储路径的FeatureLayer实例
      // 闪烁路径的相关数据
      blinkingTimers: {}, // 存储每条路径的闪烁定时器 ID
      highlightedColor: [0, 123, 255, 1], // 浅蓝色，完全不透明
      highlightedBlinkColor: [0, 123, 255, 0.2], // 浅蓝色，半透明
      noGlareColor: [244, 96, 108], // 无眩光路径为红色
      defaultColor: [25, 202, 173], // 常规路径为绿色
      noGlareRouteId: 'noGlareRouteId',
      defaultRouteId: 'defaultRouteId',
      isRouteListVisible: true, // 路线列表是否可见
      totalPass: '',
      noGlareTotalPass: '',
      BasemapName: null
    }
  },
  // 在组件挂载时初始化地图
  mounted () {
    // this.parseUrlParams()
    this.created()
    this.initMap()
    if (this.$route.query.start && this.$route.query.end) {
      this.selectedResultStart = JSON.parse(this.$route.query.start)
      this.selectedResultEnd = JSON.parse(this.$route.query.end)
    }
    parseUrlParams(this)
    // 设置定时器，每隔1分钟更新时间
    window.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount () {
    window.removeEventListener('keydown', this.handleKeydown)
  },
  computed: {
    minDate () {
      return '2024-01-01'
    },
    maxDate () {
      return '2024-12-31'
    },
    formattedTime () {
      // 格式化时间为10分钟间隔
      if (!this.selectedTime) return ''
      const [hours, minutes] = this.selectedTime.split(':').map(Number)
      const roundedMinutes = Math.floor(minutes / 10) * 10
      return `${String(hours).padStart(2, '0')}:${String(roundedMinutes).padStart(2, '0')}`
    }
  },
  methods: {
    toggleRouteList () {
      toggleRouteList(this)
    },
    getColor (index) {
      return getColor(index)
    },
    highlightRoute (routeId) {
      highlightRoute(this, routeId)
    },
    onTimeInputChange (event) {
      onTimeInputChange(this, event)
    },
    isDateDisabled (date) {
      return isDateDisabled(this, date)
    },
    handleDateChange (event) {
      handleDateChange(this, event)
    },
    handleKeydown (event) {
      handleKeydown(this, event)
    },
    updateTime () {
      updateTime(this)
    },
    clc1 () {
      clc1(this)
    },
    clc2 () {
      clc2(this)
    },
    swap () {
      swap(this)
    },
    onSearchInputChange (event, isStart) {
      onSearchInputChange(this, event, isStart)
    },
    selectResult (result, isStart = true) {
      selectResult(this, result, isStart)
    },
    onSearch () {
      return new Promise((resolve, reject) => {
        // 检查是否两个结果都已选择
        if (this.selectedResultStart && this.selectedResultEnd) {
          // 显示加载动画
          this.isLoading = true
          // 构造包含location属性的起点和终点对象
          const startWithLocation = {
            ...this.selectedResultStart,
            location: [this.selectedResultStart.wgs84_longitude, this.selectedResultStart.wgs84_latitude]
          }
          const endWithLocation = {
            ...this.selectedResultEnd,
            location: [this.selectedResultEnd.wgs84_longitude, this.selectedResultEnd.wgs84_latitude]
          }
          const formattedTime = this.selectedTime.length === 5 ? `${this.selectedTime}:00` : this.selectedTime
          console.log('Formatted Time:', formattedTime) // 打印时间参数
          // 发送请求到后端进行路径规划
          axios.post(`${process.env.VUE_APP_API_URL}/api/route/plan`, { start: startWithLocation, end: endWithLocation, date: this.selectedDate, time: formattedTime })
            .then(response => {
              // 后端返回的路径规划结果ID
              const defaultRoutePlanId = response.data.default_id
              const timeBasedRoutePlanId = response.data.time_based_id
              console.log('默认路径规划结果ID:', defaultRoutePlanId)
              console.log('基于时间的路径规划结果ID:', timeBasedRoutePlanId)
              console.log('路径规划成功，时间日期是:', this.selectedDate, this.selectedTime)
              // 隐藏加载动画
              this.isLoading = false
              // 使用Vue Router跳转到结果页面，并传递路径规划结果ID
              this.$router.push({
                path: '/lu-jing-gui-hua/routesw',
                query: {
                  start: JSON.stringify(startWithLocation),
                  end: JSON.stringify(endWithLocation),
                  default_id: defaultRoutePlanId,
                  time_based_id: timeBasedRoutePlanId,
                  date: this.selectedDate,
                  time: formattedTime,
                  BasemapLayer: this.BasemapName
                }
              })
              // 更新搜索框的值
              this.searchQueryStart = startWithLocation.name
              this.searchQueryEnd = endWithLocation.name
              resolve()
            })
            .catch(error => {
              console.error(error)
              // 隐藏加载动画
              this.isLoading = false
              // 错误处理，例如显示提示信息
              alert('路径规划失败，请稍后再试。')
              reject(error)
            })
        } else {
          // 如果起点或终点未选择，显示提示信息
          alert('请确保起点和终点都已选择。')
          reject(new Error('请确保起点和终点都已选择。'))
        }
      })
    },
    // 初始化地图
    initMap (basemapName) {
      const map = new Map({
        // basemap: 'tianditu-vector' // 使用适合的底图
        // basemap: this.BasemapName || 'tianditu-vector' // 使用适合的底图
        basemap: basemapName || this.BasemapName || 'tianditu-vector' // 使用适合的底图
      })
      this.map = map
      // console.log('当前底图名称:', this.BasemapName, basemapName)
      this.view = new MapView({
        container: 'viewDiv', // 使用正确的容器ID
        map: map,
        center: [114.3, 30.7], // 默认中心点坐标
        zoom: 4, // 默认缩放级别
        constraints: {
          geometry: {
            type: 'extent',
            xmin: 113.6,
            ymin: 29.9,
            xmax: 115.0,
            ymax: 31.3
          },
          minScale: 500,
          maxScale: 2000000,
          rotationEnabled: false,
          // 假设tileInfo.lods已经在某处定义，否则这里需要调整
          // lods: tileInfo.lods,
          snapToZoom: false
        }
      })
      // 创建 BasemapGallery 实例
      const basemapGallery = new BasemapGallery({
        view: this.view,
        source: {
          query: {
            title: '"Basemaps for Developers" AND owner:geoscenedev'
          }
        }
      })
      // 监听底图选择事件
      basemapGallery.watch('activeBasemap', (newBasemap) => {
        this.handleBasemapChange(newBasemap)
      })
      const compass = new Compass({
        view: this.view
      })
      // 创建 ScaleBar 实例
      const scaleBar = new ScaleBar({
        view: this.view,
        unit: 'metric', // 使用公制单位
        style: 'ruler' // 使用标尺样式
      })
      // 创建 DistanceMeasurement2D 实例
      const distanceMeasurement2D = new DistanceMeasurement2D({
        view: this.view,
        unit: 'metric',
        unitOptions: {
          metric: ['kilometers', 'meters'],
          nonMetric: ['miles', 'feet']
        },
        iconClass: 'esri-icon-measure-line' // 设置图标类
      })
      // 创建 LayerList 实例
      const layerList = new LayerList({
        view: this.view
      })
      // 将 DistanceMeasurement2D 添加到地图视图的左下角
      this.view.ui.add(distanceMeasurement2D, {
        position: 'bottom-leading',
        index: 0 // 确保它在最上面
      })
      // 将 BasemapGallery 添加到地图视图的右下角
      this.view.ui.add(basemapGallery, {
        position: 'bottom-right',
        index: 0
      })
      // 将 LayerList 添加到地图视图的右下角
      this.view.ui.add(layerList, {
        position: 'bottom-right',
        index: 1
      })
      // 移动缩放控件到左下角
      this.view.ui.move('zoom', {
        position: 'bottom-left',
        index: 1
      })
      // 将指南针添加到地图视图的左下角
      this.view.ui.add(compass, {
        position: 'bottom-left',
        index: 2
      })
      // 将 ScaleBar 添加到地图视图的左下角
      this.view.ui.add(scaleBar, {
        position: 'bottom-left',
        index: 3
      })

      // 创建一个新的GraphicsLayer实例，以便在地图上绘制点
      const graphicsLayer = new GraphicsLayer(
        {
          title: '起点与终点'
        }
      )
      map.add(graphicsLayer)

      // 创建 FeatureLayer 实例
      const featureLayer = new FeatureLayer({
        url: 'https://www.geosceneonline.cn/server/rest/services/Hosted/wuhan_village/FeatureServer',
        title: '武汉县区面', // 设置图层名称
        renderer: {
          type: 'simple', // 使用简单渲染器
          title: '县区边界',
          symbol: {
            type: 'simple-fill', // 使用简单填充符号
            color: [0, 0, 0, 0], // 填充颜色透明
            outline: {
              color: [0, 0, 0, 1], // 轮廓颜色红色
              width: 1
            }
          }
        },
        popupTemplate: {
          content: [{
            type: 'fields',
            fieldInfos: [{
              fieldName: '县区name',
              label: '县区名称'
            }]
          }]
        }
      })
      // 将 FeatureLayer 添加到地图
      map.add(featureLayer)
      map.add(graphicsLayer)

      this.view.when(() => {
        this.drawPoints(graphicsLayer)
        this.adjustView()
        this.drawRoutes(map)
      }).catch((err) => {
        console.error('MapView initialization error:', err)
      })
    },
    // 处理底图选择
    handleBasemapChange (basemap) {
      const basemapMapping = {
        '天地图-矢量（球面墨卡托投影）': 'tianditu-vector',
        '天地图-影像（球面墨卡托投影）': 'tianditu-image',
        '天地图-地形（球面墨卡托投影）': 'tianditu-topography'
      }
      // 检查 basemap.title 是否是中文
      if (basemapMapping[basemap.title]) {
        this.BasemapName = basemapMapping[basemap.title]
      } else {
        this.BasemapName = basemap.title
      }
      console.log('Basemap changed:', this.BasemapName)
      const urlParams = new URLSearchParams(window.location.search)
      urlParams.set('BasemapLayer', this.BasemapName)
      window.history.replaceState({}, '', `${window.location.pathname}?${urlParams}`)
    },
    created () {
      const BasemapLayer = this.$route.query.BasemapLayer
      const basemapMapping = {
        '天地图-矢量（球面墨卡托投影）': 'tianditu-vector',
        '天地图-影像（球面墨卡托投影）': 'tianditu-image',
        '天地图-地形（球面墨卡托投影）': 'tianditu-topography',
        '天地图-矢量（含注记）（球面墨卡托投影）': 'tianditu-vector'
      }

      // 如果有底图参数，进行解析
      if (BasemapLayer) {
        // 检查 BasemapLayer 是否是中文
        if (basemapMapping[BasemapLayer]) {
          this.BasemapName = basemapMapping[BasemapLayer]
        } else {
          this.BasemapName = BasemapLayer
        }
      }
      console.log('BasemapLayer is update', this.BasemapName)
    },
    // 调整视图以适应起点和终点
    adjustView () {
      if (this.selectedResultStart && this.selectedResultEnd) {
        const padding = 0.01 // 调整这个值以增加或减少边界的放宽程度
        const extent = new Extent({
          xmin: Math.min(this.selectedResultStart.location[0], this.selectedResultEnd.location[0]) - 10 * padding,
          ymin: Math.min(this.selectedResultStart.location[1], this.selectedResultEnd.location[1]) - 10 * padding,
          xmax: Math.max(this.selectedResultStart.location[0], this.selectedResultEnd.location[0]) + 10 * padding,
          ymax: Math.max(this.selectedResultStart.location[1], this.selectedResultEnd.location[1]) + 10 * padding
        })
        this.view.goTo(extent).catch((err) => {
          console.error('Error adjusting view:', err)
        })
      } else if (this.selectedResultStart) {
        this.view.goTo({
          center: [this.selectedResultStart.location[0], this.selectedResultStart.location[1]],
          zoom: 10
        }).catch((err) => {
          console.error('Error adjusting view:', err)
        })
      } else if (this.selectedResultEnd) {
        this.view.goTo({
          center: [this.selectedResultEnd.location[0], this.selectedResultEnd.location[1]],
          zoom: 10
        }).catch((err) => {
          console.error('Error adjusting view:', err)
        })
      }
    },
    drawPoints (graphicsLayer) {
      // 检查this.$route.query.start和this.$route.query.end是否定义
      if (!this.$route.query.start || !this.$route.query.end) {
        console.error('Start or end point is undefined.')
        return // 如果未定义，直接返回
      }
      const start = JSON.parse(this.$route.query.start)
      const end = JSON.parse(this.$route.query.end)
      // 检查start和end是否有location属性
      if (!start.location || !end.location) {
        console.error('Start or end point does not have a location.')
        return // 如果没有location属性，直接返回
      }
      // 创建起点和终点的Point对象
      const startPoint = new Point({
        longitude: start.location[0],
        latitude: start.location[1]
      })
      const endPoint = new Point({
        longitude: end.location[0],
        latitude: end.location[1]
      })
      const startGraphic = new Graphic({
        geometry: startPoint,
        title: '起点',
        symbol: {
          type: 'simple-marker', // autocasts as new SimpleMarkerSymbol()
          color: 'red',
          size: '20px'
        },
        // 添加popupTemplate
        popupTemplate: {
          title: '起点信息',
          content: [
            {
              type: 'fields',
              fieldInfos: [
                {
                  fieldName: 'address',
                  label: '地址'
                },
                {
                  fieldName: 'name',
                  label: '名称'
                },
                // 可以继续添加更多字段
                {
                  fieldName: 'wgs84_latitude',
                  label: 'WGS84纬度'
                },
                {
                  fieldName: 'wgs84_longitude',
                  label: 'WGS84经度'
                },
                {
                  fieldName: 'baidu_index',
                  label: '百度索引'
                },
                {
                  fieldName: 'baidu_latitude',
                  label: '百度纬度'
                },
                {
                  fieldName: 'baidu_longitude',
                  label: '百度经度'
                },
                {
                  fieldName: 'id',
                  label: 'ID'
                },
                {
                  fieldName: 'label',
                  label: '标签'
                }
              ]
            }
          ]
        },
        attributes: start
      })
      const endGraphic = new Graphic({
        geometry: endPoint,
        title: '终点',
        symbol: {
          type: 'simple-marker',
          color: 'green',
          size: '20px'
        },
        // 添加popupTemplate
        popupTemplate: {
          title: '终点信息',
          content: [
            {
              type: 'fields',
              fieldInfos: [
                {
                  fieldName: 'address',
                  label: '地址'
                },
                {
                  fieldName: 'name',
                  label: '名称'
                },
                // 可以继续添加更多字段
                {
                  fieldName: 'wgs84_latitude',
                  label: 'WGS84纬度'
                },
                {
                  fieldName: 'wgs84_longitude',
                  label: 'WGS84经度'
                },
                {
                  fieldName: 'baidu_index',
                  label: '百度索引'
                },
                {
                  fieldName: 'baidu_latitude',
                  label: '百度纬度'
                },
                {
                  fieldName: 'baidu_longitude',
                  label: '百度经度'
                },
                {
                  fieldName: 'id',
                  label: 'ID'
                },
                {
                  fieldName: 'label',
                  label: '标签'
                }
              ]
            }
          ]
        },
        attributes: end
      })
      graphicsLayer.addMany([startGraphic, endGraphic])
    },
    drawRoutes (map) {
      const defaultRouteId = this.$route.query.default_id // 从URL获取默认路线ID
      const timeBasedRouteId = this.$route.query.time_based_id // 从URL获取基于时间的路线ID

      if (!defaultRouteId && !timeBasedRouteId) {
        console.error('Route IDs are undefined.')
        return
      }
      if (defaultRouteId) {
        this.fetchAndDrawRoute(map, defaultRouteId, [25, 202, 173], true) // 绿色，耗时少路径
      }
      if (timeBasedRouteId) {
        this.fetchAndDrawRoute(map, timeBasedRouteId, [244, 96, 108]) // 红色，无眩光路径
      }
    },
    fetchAndDrawRoute (map, routeId, color, isNoGlareRoute = false) {
      const geojsonUrl = `${process.env.VUE_APP_API_URL}/api/get_geojson/${routeId}`
      fetch(geojsonUrl) // 使用fetch API获取GeoJSON文件
        .then(response => response.json()) // 将响应转换为JSON
        .then(data => {
          let totalLength = 0
          let totalCost = 0
          const roadLengths = {}

          const features = data.features.map((feature, index) => {
            if (feature.properties.cost !== 99999) {
              totalLength += feature.properties.length
              totalCost += feature.properties.cost
            }

            if (!feature.properties.name.includes('未知')) {
              if (!roadLengths[feature.properties.name]) {
                roadLengths[feature.properties.name] = { length: 0, order: index }
              }
              roadLengths[feature.properties.name].length += feature.properties.length
            }
            return {
              geometry: {
                type: 'polyline',
                paths: feature.geometry.coordinates
              },
              attributes: {
                ...feature.properties,
                id: index, // 为每个要素生成唯一的ID
                routeType: isNoGlareRoute ? '耗时少路径' : '无眩光路径' // 添加路线类型
              }
            }
          })

          const sortedRoads = Object.entries(roadLengths)
            .sort((a, b) => b[1].length - a[1].length || a[1].order - b[1].order)
          const topPassRoads = sortedRoads.slice(0, 3).map(road => road[0]).join('->')

          const geojsonLayer = new FeatureLayer({ // 创建FeatureLayer图层
            title: isNoGlareRoute ? '耗时少路径' : '无眩光路径',
            source: features,
            renderer: {
              type: 'simple', // 使用简单渲染器
              title: isNoGlareRoute ? '耗时少路径' : '无眩光路径',
              symbol: {
                type: 'simple-line', // 使用简单线符号
                color: color, // 使用传入的颜色
                width: isNoGlareRoute ? 4.5 : 3 // 根据是否为无眩光路径设置宽度
              }
            },
            objectIdField: 'id', // 必须指定一个唯一的字段作为ObjectId
            fields: [
              { name: 'id', type: 'oid' },
              { name: 'seq', type: 'integer' },
              { name: 'path_seq', type: 'integer' },
              { name: 'node', type: 'integer' },
              { name: 'edge', type: 'integer' },
              { name: 'cost', type: 'double' },
              { name: 'agg_cost', type: 'double' },
              { name: 'length', type: 'double' },
              { name: 'name', type: 'string' },
              { name: 'maxspeed', type: 'integer' },
              { name: 'routeType', type: 'string' } // 添加routeType字段
            ],
            popupTemplate: {
              title: '{routeType} - {name}', // 显示路线类型和路名
              content: [
                {
                  type: 'text',
                  text: `总距离: ${(totalLength / 1000).toFixed(2)} km<br>总耗时: ${(totalCost / 3600).toFixed(2)} 小时`
                },
                {
                  type: 'fields',
                  fieldInfos: [
                    {
                      fieldName: 'length',
                      label: '长度（米）'
                    },
                    {
                      fieldName: 'cost',
                      label: '耗时（秒）'
                    },
                    {
                      fieldName: 'maxspeed',
                      label: '最大速度'
                    },
                    {
                      fieldName: 'name',
                      label: '名称'
                    }
                  ]
                }
              ]
            }
          })
          const rawGeojsonLayer = markRaw(geojsonLayer)
          map.layers.add(rawGeojsonLayer)
          if (totalCost < 3600) {
            totalCost += 60
          }
          const hours = Math.floor(totalCost / 3600)
          const minutes = Math.floor((totalCost % 3600) / 60)
          let distance
          if (totalLength < 1000) {
            distance = `${totalLength.toFixed(2)}米`
          } else {
            distance = `${(totalLength / 1000).toFixed(2)}千米`
          }
          // 根据是否为无眩光路径来存储结果
          if (isNoGlareRoute) {
            this.noGlareTotalHours = hours
            console.log('Hours:', hours)
            this.noGlareTotalMinutes = minutes
            this.noGlareTotalDistance = distance
            this.noGlareTotalPass = topPassRoads
            this.routeLayers.noGlareRouteId = geojsonLayer
          } else {
            this.totalHours = hours
            this.totalMinutes = minutes
            this.totalDistance = distance
            this.totalPass = topPassRoads
            this.routeLayers.defaultRouteId = geojsonLayer
          }
        })
        .catch(error => console.error('Error loading the geojson file:', error))
    }
  }
}
</script>

<style src="@/assets/share_css/routeplanning.css">

</style>
