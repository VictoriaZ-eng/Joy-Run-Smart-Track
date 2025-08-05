<template>
    <div class="sidebar" :class="{ collapsed }">
      <button class="toggle" @click="collapsed = !collapsed">
        {{ collapsed ? '▶' : '◀' }}
      </button>
      <div v-if="!collapsed">
        <div
          v-for="route in routes"
          :key="route.id"
          class="route-block"
          @click="selectRoute(route.id)"
        >
          <h3>{{ route.name }}</h3>
          <p>{{ route.description }}</p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  defineProps({
    routes: Array
  });
  const emit = defineEmits(['select']);
  
  const collapsed = ref(false);
  const selectRoute = (id) => {
    emit('select', id);
  };
  </script>
  
  <style scoped>
  .sidebar {
    width: 250px;
    background-color: white;
    border-right: 1px solid #ccc;
    padding: 10px;
    overflow-y: auto;
    transition: width 0.3s ease;
  }
  .sidebar.collapsed {
    width: 30px;
    overflow: hidden;
  }
  .toggle {
    position: absolute;
    left: 150px;
    top: 10px;
    z-index: 10;
    background: #eee;
    border: none;
    cursor: pointer;
    
  }
  .sidebar.collapsed .toggle {
    bottom:50px;
    left: 30px;
  }
  .route-block {
    margin-bottom: 12px;
    cursor: pointer;
    border: 1px solid #ccc;
    padding: 8px;
    border-radius: 6px;
    transition: background-color 0.2s;
  }
  .route-block:hover {
    background-color: #f3f3f3;
  }
  </style>
  