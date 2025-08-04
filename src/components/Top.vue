<template>
  <div class="top-container">
    <!-- 头部导航栏 -->
    <el-header class="header">
      <el-row :gutter="0" class="header-row">
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
        <!-- 让左右间隔 -->
        <el-col :span="1" class="space"></el-col>
        <!-- 右侧：时钟、登录和天气按钮 -->
        <el-col :span="8" class="right-section">
          <!-- 按钮组（从右往左排列） -->
          <div class="buttons-group">
            <!-- 时钟容器（最右） -->
            <div class="clock-container control-button">
              <div class="clockicon">
                <img src="/src/assets/images/shizhong.png" alt="" />
              </div>
              
              <div class="time">
                <p class="clock">{{ clock }}</p>
                <p class="date">{{ date }}</p>
              </div>
            </div>
            
            <!-- 登录按钮（中间） -->
            <div class="login control-button">
              <el-button>登录</el-button>
            </div>
            
            <!-- 天气组件（最左） -->
            <div class="weather control-button">
              <WeatherView />
            </div>
          </div>
        </el-col>
      </el-row>
    </el-header>

    <!-- 中间区域：地图控件集合块 -->
    <el-main class="main-content">
      <el-row :gutter="20" class="main-row">
        <!-- 中间：地图控件集合块 -->
        <el-col :span="24" class="map-controls">
          <div class="map-controls-container">
            <LocationSearch />
          </div>
        </el-col>
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
  padding: 0.5vh 2vw;
  height: 6vh; /* 减小整体高度 */
}

/* 修改头部行样式，确保没有右侧边距 */
.header-row {
  height: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  margin: 0; /*移除所有外边距*/
  padding: 0; /* 移除所有内边距 */
}

/* Logo 样式 */
.logo img {
  width: 10vw;
  max-width: 180px;
  height: auto;
  max-height: 5vh;
  vertical-align: middle;
}

/* 修改列宽分配 */
.left-section {
  /* 将左侧内容区域从span="16"对应调整为更精确的宽度 */
  display: flex;
  align-items: center;
  height: 100%;
  max-width: calc(100% - 28vw); /* 给右侧按钮和间隔留出足够空间 */
}


/* 导航菜单项容器 */
.nav-items {
  display: flex;
  margin-left: 2vw;
  flex-wrap: wrap; /* 允许在小屏幕上换行 */
  /* margin-right: 10; */
}

/* 每个导航按钮 */
.nav-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.4vh 0.8vw;
  height: 5vh; /* 统一高度 */
  border: 1px solid #fff;
  border-radius: 0.5rem;
  background-color: rgb(235, 239, 226);
  color: rgb(97, 144, 38);
  font-size: clamp(0.8rem, 1.2vw, 1.1rem);
  cursor: pointer;
  transition: all 0.3s ease;
  margin-right: 1.5vw;
  margin-bottom: 0.5vh;
  font-weight: bold;
  white-space: nowrap; /* 防止文本换行 */
}

/* 修改右侧区域样式 */
.right-section {
  /* 确保右侧按钮区域固定宽度 */
  display: flex;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  min-width: 26vw; /* 确保按钮有足够空间 */
  padding-right: 0;
  margin-right: 0;
}

/* 按钮组 - 从右往左排列 */
.buttons-group {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-direction: row-reverse; /* 从右往左排列 */
  width: 100%;
}

/* 控制按钮共享样式 */
.control-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.4vh 0.8vw;
  height: 5vh; /* 与导航按钮相同高度 */
  border: 1px solid #fff;
  border-radius: 0.5rem;
  background-color: rgb(235, 239, 226);
  color: rgb(97, 144, 38);
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: bold;
  margin-left: 1vw; /* 从右往左的间距 */
}

/* 时钟容器 */
.clock-container {
  display: flex;
  align-items: center;
  width: 10vw; /* 固定宽度 */
  padding: 0.4vh 1vw;
  margin-left: 0; /* 最右边的元素，不需要左边距 */
}

/* 时钟图标 */
.clockicon {
  height: 3vh;
  display: flex;
  align-items: center;
  margin-right: 0.5vw;
}

.clockicon img {
  height: 3vh;
  width: auto;
}

/* 时间显示 */
.time {
  font-size: clamp(0.7rem, 1vw, 0.9rem);
  font-weight: bold;
  font-family: Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;
  color: rgb(97, 144, 38);
}

.clock {
  text-align: center;
  margin: 0;
}

.date {
  margin: 0;
}

/* 登录按钮 */
.login {
  width: 8vw; /* 加宽登录按钮 */
  max-width: 100px;
  font-size: clamp(0.8rem, 1.2vw, 1rem);
}

.login :deep(.el-button) {
  font-size: clamp(0.8rem, 1.2vw, 1rem);
  padding: 0.2vh 0.6vw;
  height: auto;
  width: 100%;
}

/* 天气按钮 */
.weather {
  width: 10vw; /* 加宽天气按钮 */
  max-width: 120px;
  font-size: clamp(0.7rem, 1vw, 0.9rem);
}

/* 确保WeatherView组件样式一致 */
.weather :deep(.el-button),
.weather :deep(.weather-info) {
  font-size: clamp(0.7rem, 1vw, 0.9rem);
  padding: 0.2vh 0.6vw;
  height: auto;
  white-space: nowrap;
  width: 100%;
}

/* 共享的悬停样式 */
.control-button:hover,
.nav-button:hover,
.control-button.active,
.nav-button.active {
  background-color: rgb(235, 239, 226);
  color: rgb(48, 83, 6);
}

/* 选中状态增强（保持原色） */
.control-button.active,
.nav-button.active {
  background-color: #addfc2;
  color: rgb(48, 83, 6);
}

/* 响应式媒体查询 */
@media (max-width: 1200px) {
  .nav-button {
    padding: 0.4vh 0.8vw;
    margin-right: 1vw;
  }
  
  .login {
    width: 10vw;
  }
  
  .weather {
    width: 12vw;
  }
  
  .clock-container {
    width: 7vw;
  }
}

@media (max-width: 768px) {
  .header {
    height: auto;
    padding: 0.5vh 1vw;
  }
  
  .buttons-group {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .control-button {
    margin: 0.5vh 1vw;
    width: 25vw;
  }
  
  .clock-container {
    width: 25vw;
  }
}

/* 中间空白间隔样式 */
.space {
  height: 100%;
  width: 15vw; /* 确保间隔宽度 */
  background-color: transparent; /* 完全透明 */
}

/* 重置Element Plus默认样式，确保没有额外边距 */
:deep(.el-row) {
  margin-left: 0 !important;
  margin-right: 0 !important;
}

:deep(.el-col) {
  padding-left: 0 !important;
  padding-right: 0 !important;
}

</style>