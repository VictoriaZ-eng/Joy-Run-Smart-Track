<!-- 赛事查询功能 -->
<template>
  <div class="marathon-card">
    <div class="marathon-content" ref="marathonContent">
      <!-- 标题区域 -->
      <header class="hero">
        <div
          class="hero-bg"
          :style="{
            filter: `blur(${heroBlur}px)`,
            backgroundImage: `url(${marathonBg})`
          }"
        ></div>
        <div class="hero-content">
          <h1>全国马拉松赛事</h1>
          <p>跑遍中华大地，感受体育精神！</p>
        </div>
      </header>

      <!-- 赛事网格区域 -->
      <section class="races-grid" ref="racesContainer">
        <div class="loading" v-if="loading && races.length === 0">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div class="grid-container" v-else>
          <div 
            class="race-card" 
            v-for="race in races" 
            :key="race.raceId"
            @click="openDetail(race)"
          >
            <div class="race-image">
              <img 
                :src="race.coverImage || '/src/assets/images/marathonbg.png'" 
                :alt="race.raceName"
                @error="handleImageError"
              />
            </div>
            <div class="race-info">
              <h3 class="race-name">{{ race.raceName }}</h3>
              <p class="race-date">{{ formatDate(race.startTime) }}</p>
              <p class="race-city">{{ race.city || race.province }}</p>
            </div>
          </div>
        </div>

        <!-- 底部加载提示 -->
        <div class="load-more" v-if="loading && races.length > 0">
          <div class="loading-spinner"></div>
          <p>加载更多...</p>
        </div>

        <div class="no-more" v-if="!hasMore && races.length > 0">
          <p>没有更多赛事了</p>
        </div>
      </section>
    </div>

    <!-- 赛事详情弹窗 -->
    <div class="detail-modal" v-if="showDetail" @click="closeDetail">
      <div class="detail-content" @click.stop>
        <button class="close-btn" @click="closeDetail">×</button>
        
        <div class="detail-image">
          <img 
            :src="selectedRace.coverImage || '/src/assets/images/marathonbg.png'" 
            :alt="selectedRace.raceName"
          />
        </div>
        
        <div class="detail-info">
          <h2>{{ selectedRace.raceName }}</h2>
          
          <div class="info-grid">
            <div class="info-item">
              <label>开始时间:</label>
              <span>{{ formatDate(selectedRace.startTime) }}</span>
            </div>
            <div class="info-item">
              <label>报名截止:</label>
              <span>{{ formatDate(selectedRace.showSignEndTime) }}</span>
            </div>
            <div class="info-item">
              <label>省份:</label>
              <span>{{ selectedRace.province || '暂无信息' }}</span>
            </div>
            <div class="info-item">
              <label>城市:</label>
              <span>{{ selectedRace.city || '暂无信息' }}</span>
            </div>
            <div class="info-item">
              <label>区域:</label>
              <span>{{ selectedRace.area || '暂无信息' }}</span>
            </div>
            <div class="info-item">
              <label>地址:</label>
              <span>{{ selectedRace.shortAddress || '暂无信息' }}</span>
            </div>
            <div class="info-item">
              <label>赛事类型:</label>
              <span>{{ getRaceTypeText(selectedRace.raceType) }}</span>
            </div>
            <div class="info-item">
              <label>赛事ID:</label>
              <span>{{ selectedRace.raceId }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
  
<script setup>
import { ref, onMounted, nextTick } from 'vue';
import marathonBg from '@/assets/images/marathonbg.png';
import axios from 'axios';
import { onUnmounted } from 'vue';

// 响应式数据
const races = ref([]);
const loading = ref(false);
const hasMore = ref(true);
const currentPage = ref(1);
const pageSize = 9; // 每页9个

const showDetail = ref(false);
const selectedRace = ref({});
const racesContainer = ref(null);
const marathonContent = ref(null);

const heroBlur = ref(0); // 模糊度
const maxBlur = 16; // 最大模糊像素
const blurScrollDistance = 200; // 滚动多少像素达到最大模糊
// 获取赛事数据
const fetchRaces = async (page = 1) => {
  if (loading.value || !hasMore.value) {
    console.log('跳过请求:', { loading: loading.value, hasMore: hasMore.value });
    return;
  }
  
  loading.value = true;
  
  try {
    const start = (page - 1) * pageSize + 1;
    const end = page * pageSize;
    const range = `${start}-${end}`;
    
    console.log(`正在请求第${page}页数据，范围: ${range}`);
    
    const response = await axios.get(`${import.meta.env.VITE_APP_API_URL}/get_races/api/get_races`, {
      params: { range }
    });
    
    console.log('API响应:', response.data);
    
    const data = response.data;
    if (data.code === 200) {
      const newRaces = data.data;
      
      console.log(`接收到 ${newRaces.length} 条新数据`);
      
      if (newRaces.length > 0) {
        races.value.push(...newRaces);
        currentPage.value = page;
        
        console.log(`当前总数据量: ${races.value.length}, 当前页: ${page}`);
        
        // 如果返回的数据少于请求的数量，说明没有更多数据了
        if (newRaces.length < pageSize) {
          hasMore.value = false;
          console.log('已加载所有数据，设置 hasMore 为 false');
        }
      } else {
        hasMore.value = false;
        console.log('没有更多数据，设置 hasMore 为 false');
      }
    } else {
      console.error('API返回错误:', data);
    }
  } catch (error) {
    console.error('获取赛事数据失败:', error);
    console.error('错误详情:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    });
    
    // 在控制台显示更详细的错误信息
    if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
      console.error('网络连接错误 - 请检查后端服务是否正在运行');
    }
  } finally {
    loading.value = false;
    console.log('请求完成，loading 设置为 false');
  }
};

// 滚动到底部检测
const handleScroll = () => {
  const container = marathonContent.value;
  if (!container) return;
  
  const scrollTop = container.scrollTop;
  const scrollHeight = container.scrollHeight;
  const clientHeight = container.clientHeight;
  
  console.log('滚动检测:', {
    scrollTop,
    scrollHeight,
    clientHeight,
    距离底部: scrollHeight - scrollTop - clientHeight,
    当前页: currentPage.value,
    是否加载中: loading.value,
    是否还有更多: hasMore.value
  });
  
  // 距离底部还有100px时就开始加载
  if (scrollHeight - scrollTop - clientHeight < 100 && !loading.value && hasMore.value) {
    console.log('触发加载下一页:', currentPage.value + 1);
    fetchRaces(currentPage.value + 1);
  }
};

// 打开详情弹窗
const openDetail = (race) => {
  selectedRace.value = race;
  showDetail.value = true;
  document.body.style.overflow = 'hidden'; // 禁止背景滚动
};

// 关闭详情弹窗
const closeDetail = () => {
  showDetail.value = false;
  selectedRace.value = {};
  document.body.style.overflow = 'auto'; // 恢复背景滚动
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '暂无信息';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

// 获取赛事类型文本
const getRaceTypeText = (type) => {
  const typeMap = {
    1: '全程马拉松',
    2: '半程马拉松',
    3: '10公里跑',
    4: '5公里跑',
    5: '其他'
  };
  return typeMap[type] || '未知类型';
};

// 图片加载错误处理
const handleImageError = (event) => {
  event.target.src = '/src/assets/images/marathonbg.png';
};

const handleHeroBlur = () => {
  const scrollTop = marathonContent.value?.scrollTop || 0;
  // 计算模糊度，最大不超过maxBlur
  heroBlur.value = Math.min((scrollTop / blurScrollDistance) * maxBlur, maxBlur);
};


// 生命周期
onMounted(async () => {
  await fetchRaces(1);
  await nextTick();
  if (marathonContent.value) {
    marathonContent.value.addEventListener('scroll', handleScroll);
    marathonContent.value.addEventListener('scroll', handleHeroBlur);
    handleHeroBlur(); // 初始化
  }
});

// 清理事件监听器
const cleanup = () => {
  if (marathonContent.value) {
    marathonContent.value.removeEventListener('scroll', handleScroll);
    marathonContent.value.removeEventListener('scroll', handleHeroBlur);
  }
};

// 组件卸载时清理
onUnmounted(cleanup);
</script>  <style scoped>
/* 主容器 */
.marathon-card {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  width: 90%;
  max-width: 1200px;
  height: 85vh;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

/* 滚动内容区域 */
.marathon-content {
  height: 100%;
  overflow-y: auto;
  font-family: 'Helvetica Neue', sans-serif;
  color: #333;
  line-height: 1.6;
  position: relative;
  z-index: 1000;
}

/* 自定义滚动条 */
.marathon-content::-webkit-scrollbar {
  width: 8px;
}
.marathon-content::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
}
.marathon-content::-webkit-scrollbar-track {
  background-color: rgba(0, 0, 0, 0.1);
}

/* 标题区域 */
hero {
  position: relative;
  height: 15vh;
  margin-bottom: 30px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-bg {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  width: 100%;
  height: 25vh;
  background-size: cover;
  background-position: center;
  transition: filter 0.3s;
  z-index: 1;
}
.hero-content {
  position: relative;
  z-index: 2;
  width: 100%;
  text-align: center;
  color: white;
  text-shadow: 0 2px 8px rgba(0,0,0,0.3);
  padding: 60px 20px;
}
.hero h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  font-weight: bold;
}

.hero p {
  font-size: 1.2rem;
  opacity: 0.9;
}

/* 赛事网格区域 */
.races-grid {
  padding: 0 30px 30px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

/* 赛事卡片 */
.race-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateY(0);
  animation: slideInUp 0.6s ease-out;
}

.race-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.15);
}

/* 卡片动画 */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 赛事图片 */
.race-image {
  width: 100%;
  height: 180px;
  overflow: hidden;
}

.race-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.race-card:hover .race-image img {
  transform: scale(1.05);
}

/* 赛事信息 */
.race-info {
  padding: 15px;
}

.race-name {
  font-size: 1.1rem;
  font-weight: bold;
  color: #333;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
}

.race-date {
  color: #666;
  font-size: 0.9rem;
  margin: 4px 0;
}

.race-city {
  color: #888;
  font-size: 0.85rem;
  margin: 4px 0 0 0;
}

/* 加载状态 */
.loading, .load-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-more {
  text-align: center;
  padding: 20px;
  color: #999;
  font-size: 0.9rem;
}

/* 详情弹窗 */
.detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1010;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.detail-content {
  background: white;
  border-radius: 16px;
  max-width: 600px;
  max-height: 80vh;
  width: 90%;
  overflow-y: auto;
  position: relative;
  animation: slideInScale 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideInScale {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 35px;
  height: 35px;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s ease;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.7);
}

.detail-image {
  width: 100%;
  height: 250px;
  overflow: hidden;
  border-radius: 16px 16px 0 0;
}

.detail-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-info {
  padding: 30px;
}

.detail-info h2 {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 20px;
  font-weight: bold;
}

.info-grid {
  display: grid;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item label {
  font-weight: bold;
  color: #555;
  min-width: 80px;
  margin-right: 15px;
}

.info-item span {
  color: #333;
  flex: 1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .marathon-card {
    width: 95%;
    height: 90vh;
  }
  
  .races-grid {
    padding: 0 15px 20px;
  }
  
  .grid-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .hero {
    height: 150px;
  }

  .hero-content {
    padding: 40px 10px;
  }

  .hero h1 {
    font-size: 2rem;
  }
  
  .detail-content {
    max-width: 95%;
    margin: 20px;
  }
  
  .detail-info {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .grid-container {
    grid-template-columns: 1fr;
  }
  
  .hero h1 {
    font-size: 1.8rem;
  }
  
  .race-image {
    height: 150px;
  }
}
</style>
  