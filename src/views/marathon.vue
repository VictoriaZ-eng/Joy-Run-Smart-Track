<template>
    <div class="marathon-card">
      <div class="marathon-content">
        <header class="hero">
          <h1>杭州马拉松 2025</h1>
          <p>跑进西子湖畔，遇见最美杭城！</p>
          <button @click="scrollToInfo">了解更多</button>
        </header>
  
        <section class="info" ref="infoSection">
  <div class="introduction">
    <h2>赛事介绍</h2>
    <p>
      杭州马拉松的前身是西湖桂花国际马拉松和国际友好西湖马拉松赛，始于1987年10月，是中国历史上第三悠久的马拉松赛事。
      仅次于1981年创办的北京马拉松和1987年创办的大连马拉松，是国际级赛事。
      2012-2014年升级为中国田协金牌赛事，2017-2019年又成为国际田联金标赛事。2021-2022年被评为精英标牌赛事。
      2024年赛事总人数达36000人。
    </p>
  </div>

  <div class="info-card">
    <h2>赛事信息</h2>
    <ul>
      <li><strong>比赛日期：</strong>2025年11月2日（星期日）</li>
      <li><strong>比赛地点：</strong>杭州黄龙体育中心（起点）</li>
      <li><strong>比赛项目：</strong>全程马拉松、半程马拉松、10公里欢乐跑</li>
      <li><strong>报名时间：</strong>2025年8月15日 - 9月30日</li>
    </ul>
  </div>
</section>

<section class="info-card route">
  <h2>往年路线示意</h2>
  <img src="@/assets/images/2024杭马路线.png" alt="杭州马拉松路线图" />
</section>

<section class="info-card signup">
  <h2>报名流程</h2>
  <img src="@/assets/images/报名流程.png" alt="报名流程图" />
  <p>点击下方按钮前往报名官网，了解更多信息！</p>
  <a href="https://www.hlsports.net/marathon" target="_blank" class="signup-btn">前往报名</a>
</section>

<footer class="info-card">
  <p>信息来源：https://www.baidu.com</p>
</footer>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  const infoSection = ref(null);
  const scrollToInfo = () => {
    infoSection.value?.scrollIntoView({ behavior: 'smooth' });
  };
  </script>
  
  <style scoped>
  .info-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-top: 20px;
  margin-left: 0; /* 保持与介绍左对齐 */
}

.info-card h2 {
  margin-top: 0;
  font-size: 1.5rem;
  color: rgb(48, 83, 6);
}

.info-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-card li {
  padding: 10px 0;
  border-bottom: 1px solid #eee;
  font-size: 1rem;
}

.info-card li:last-child {
  border-bottom: none;
}
.info-card img {
  width: 100%;
  border-radius: 8px;
  margin-top: 10px;
}

  .marathon-card {
    position: absolute;
    top: 80px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 20;
    width: 90%;
    max-width: 900px;
    height: 85vh;
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    overflow-y: auto;
    padding: 20px;
    box-sizing: border-box;
  }
  
  /* 让滚动条更优雅 */
  .marathon-card::-webkit-scrollbar {
    width: 8px;
  }
  .marathon-card::-webkit-scrollbar-thumb {
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 8px;
  }
  
  /* 内容样式 */
  .marathon-content {
    font-family: 'Helvetica Neue', sans-serif;
    color: #333;
    line-height: 1.6;
  }
  
  .hero {
    background: url("@/assets/images/marathonbg.png") center/cover no-repeat;
    color: rgb(48, 83, 6);
    text-align: center;
    padding: 100px 20px;
    border-radius: 12px;
    font-weight: bold;
  }
  
  .hero h1 {
    color: rgb(48, 83, 6);
    font-size: 3rem;
    margin-bottom: 10px;
  }
 
  .hero p {
    font-size: 1.5rem;
    margin-bottom: 10px;
  }
  .hero button {
    margin-top: 20px;
    padding: 10px 24px;
    font-size: 1rem;
    background-color: rgb(218, 239, 168);
    color: rgb(48, 83, 6);
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
  }
  
  section {
    padding: 30px 10px;
  }
  .introduction {
    border-left: 4px solid #4caf50;
    padding-left: 12px;
    margin-bottom: 20px;
  }
  .introduction h2{
    color:rgb(48, 83, 6);
  }
  .route img {
    max-width: 100%;
    border-radius: 8px;
  }
  
  .signup-btn {
    display: inline-block;
    margin-top: 20px;
    padding: 12px 24px;
    background-color:rgb(235, 239, 226);;
    color: rgb(97, 144, 38);
    text-decoration: none;
    border-radius: 4px;
    font-weight: bold;
    font-size: 2ch;
  }
  .signup-btn:hover {
    color: rgb(48, 83, 6);
}
  footer {
    text-align: center;
    padding: 20px;
    background: #f9f9f9;
    color: #777;
    font-size: 0.9rem;
    border-top: 1px solid #e0e0e0;
  }
  </style>
  