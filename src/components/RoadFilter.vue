<!-- 无用，可暂时忽略 -->
<template>
    <div class="road-filter-box">
      <h3 class="text-base font-bold mb-2">筛选道路</h3>
      <button @click="filterByScore" class="filter-btn">可慢跑性得分 > 2</button>
      <button @click="filterByNDVI" class="filter-btn">NDVI > 60</button>
      <button @click="clearFilter" class="filter-btn">清除筛选</button>
    </div>
  </template>
  
  <script setup>
  const emit = defineEmits(["filter"]);
  
  function filterByScore() {
    emit("filter", { field: "score", operator: ">", value: 2 });
  }
  
  function filterByNDVI() {
    emit("filter", { field: "ndvi", operator: ">", value: 60 });
  }
  
  function clearFilter() {
    emit("filter", null);
  }
  </script>
  
  <style scoped>
  .road-filter-box {
    position: absolute;
    top: 3cm;
    right: 20px;
    background: white;
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }
  .filter-btn {
    display: block;
    margin-bottom: 8px;
    padding: 6px 10px;
    background: #0078d7;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .filter-btn:hover {
    background: #005a9e;
  }
  </style>
  