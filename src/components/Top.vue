<template>
  <div class="top-container">
    <!-- 头部导航栏 -->
    <el-header class="header">
      <el-row :gutter="20" class="header-row">
        <!-- 左侧：Logo 和 导航菜单 -->
        <el-col :span="16" class="left-section">
          <div class="logo">
            <img src="/src/assets/images/logo1.png" alt="Logo" />
          </div>
          <!-- 导航菜单项 -->
          <div class="nav-items">
            <el-button
              v-for="item in list"
              :key="item.name"
              :class="{ 'active': activeItem === item.name }"
              @click="handleClick(item)"
              class="nav-button"
            >
              <i :class="['iconfont', item.icon]"></i>
              <span class="button-text">{{ item.name }}</span>
            </el-button>
          </div>
        </el-col>

 
       
      </el-row>
    </el-header>

    <!-- 中间区域：地图控件集合块和右侧按钮 -->
    <el-main class="main-content">
      <el-row :gutter="20" class="main-row">
        <!-- 中间：地图控件集合块 -->
        <el-col :span="16" class="map-controls">
          <div class="map-controls-container">
            <LocationSearch   />
            <div class="login">
              <el-button>登录</el-button>
            </div>
          </div>
        </el-col>

        <!-- 右侧：实时天气查询按钮 -->
        <!-- <div class="weather">
          <el-button>实时天气查询</el-button>
        </div> -->
        <div class="weather">
          <WeatherView />
        </div>
   
        <div class="clockicon">
          <img src="/src/assets/images/shizhong.png" alt="" />
        </div>
        <div class="time">
          <p class="clock">{{ clock }}</p>
          <p class="date">{{ date }}</p>
        </div>


      </el-row>
    </el-main>
  </div>
</template>

<script setup>
import "@/assets/iconfont/iconfont.css";
import { ref } from "vue";
import WeatherView from '@/components/WeatherView.vue';
import LocationSearch from '@/components/LocationSearch.vue';
import { useRouter } from 'vue-router';

const router = useRouter(); // 获取路由实例
const activeItem = ref('');
const list = [
  { name: "慢跑路径规划", icon: "icon-lujingguihua", path: "/routeplan" },
  { name: "交通服务查询", icon: "icon-gongjiao", path: "/traffic_search" },
  { name: "赛事服务查询", icon: "icon-paobuxuanzhong", path: "/marathon" },
  { name: "AI健康助手", icon: "icon-wuguan", path: "/AI_search" },
];

const handleClick = (item) => {
  activeItem.value = item.name;
  router.push(item.path); // Vue Router 路由跳转
};

// 时间
const date = ref();
const clock = ref();

// 每秒更新时间
setInterval(updateTime, 1000);

// 更新时间和日期的函数
function updateTime() {
  const now = new Date();
  const year = now.getFullYear();
  const month = format(now.getMonth() + 1);
  const day = format(now.getDate());
  const hours = format(now.getHours());
  const minutes = format(now.getMinutes());
  const seconds = format(now.getSeconds());

  date.value = `${year}-${month}-${day}`;
  clock.value = `${hours}:${minutes}:${seconds}`;
}

// 格式化数字的辅助函数
function format(t) {
  if (t >= 10) {
    return t;
  } else if (t > 0) {
    return "0" + t;
  } else {
    return t;
  }
}
</script>

<style scoped>
/* 整体容器 */
.top-container {
  width: 100%;
  height: 100%;
}

/* 头部导航栏 */
.header {
  background-color: #f5f7fa;
  padding: 10px 20px;
}

/* Logo 样式 */
.logo img {
  width: 210px;
  height: 60px;
  vertical-align: middle;
}

/* 左侧：Logo 和 导航菜单 */
.left-section {
  display: flex;
  align-items: center;
}

/* 导航菜单项容器 */
.nav-items {
  display: flex;
  margin-left: 20px;
}

/* 每个导航按钮 */
.nav-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: 1px solid #fff;
  border-radius: 10px;
  background-color: rgb(235, 239, 226);
  color: rgb(97, 144, 38);
  font-size: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-right: 30px;
  font-weight: bold;
}

/* 图标样式 */
.nav-button .iconfont {
  font-size: 30px;
  margin-right: 10px;
}

/* 文字样式 */
.button-text {
  font-weight: bold;
}

/* 登录按钮 */
.login,
.weather {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: 1px solid #fff;
  border-radius: 10px;
  background-color: rgb(235, 239, 226);
  color: rgb(97, 144, 38);
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
}

.login {
  top: 20px;
  right: 1%;
  font-size: 30px;
}

.weather {
  top: 120px;
  right: 50px;
  font-size: 20px;
  height:60px;
}

/* 共享的悬停样式 */
.nav-button:hover,
.login:hover,
.weather:hover,
.nav-button.active,
.login.active,
.weather.active {
  background-color: rgb(235, 239, 226);
  color: rgb(48, 83, 6);
}

/* 选中状态增强（保持原色） */
.nav-button.active,
.login.active,
.weather.active {
  background-color: #addfc2;
  color: rgb(48, 83, 6);
}

/* 图标定位 */
.clockicon {
  position: absolute;
  top: 30px;
  right: 15%;
}

/* 时间显示 */
.time {
  position: absolute;
  right: 8%;
  top: 30px;
  font-weight: bold;
  font-size: 20px;
  font-family: Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;
  color: rgb(97, 144, 38);
}

.clock {
  text-align: center;
}



/* 中间内容区域 */
.main-content {
  margin-top: 10px;
  background-color: #fff;
}

/* 地图控件集合块 */
.map-controls-container {
  border-top: 2px solid #ccc;
  border-bottom: 1px solid #ccc;
  height: 65px;
  width:100%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 -4px 5px rgba(0, 0, 0, 0.1); 
}



</style>