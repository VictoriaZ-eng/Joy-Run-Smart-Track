import {
    Fullscreen,
    Logo,
    Scale,
    Zoom,
    GeoLocate,
    MouseLocation,
    MapTheme,
  } from '@antv/l7';
  import mapboxgl from 'mapbox-gl'; // 确保 mapboxgl 正确导入
  
  export const useControl = (scene) => {
    // 确保 scene 已经正确传递
    if (!scene) {
      console.error('scene is not provided');
      return;
    }
  
    const controlObj = {
      fullScreen: new Fullscreen({
        position: 'topright',
      }),
      zoom: new Zoom({
        position: 'topleft',
        showZoom: true,
      }),
      logo: new Logo({
        position: 'bottomleft',
        img: 'http://www.x-zd.com/themes/simpleboot3_web/public/web/images/image/logo_03.png',
        href: 'http://www.x-zd.com',
      }),
      scale: new Scale({}),
      geolocate: new GeoLocate({}),
      mouseLocation: new MouseLocation({
        transform: (p) => {
          return [`经度: ${p[0].toFixed(4)}`, `纬度: ${p[1].toFixed(4)}`];
        },
        position: 'bottomright',
      }),
      mapTheme: new MapTheme({
        options: [
          {
            text: 'navigation-day-v1',
            value: 'mapbox://styles/mapbox/navigation-day-v1',
            img: '/src/assets/themes/navigation-day-v1.png',
          },
          {
            text: 'navigation-night-v1',
            value: 'mapbox://styles/mapbox/navigation-night-v1',
            img: '/src/assets/themes/navigation-night-v1.png',
          },
          {
            text: 'satellite-streets-v12',
            value: 'mapbox://styles/mapbox/satellite-streets-v12',
            img: '/src/assets/themes/satellite-streets-v12.png',
          },
          {
            text: 'satellite-v9',
            value: 'mapbox://styles/mapbox/satellite-v9',
            img: '/src/assets/themes/satellite-v9.png',
          },
          {
            text: 'standard',
            value: 'mapbox://styles/mapbox/standard',
            img: '/src/assets/themes/standard.png',
          },
        ],
      }),
    };
  
    // 添加 AntV L7 控件
    for (let key in controlObj) {
      scene.addControl(controlObj[key]);
    }
  
    // 添加 Mapbox GL JS 的 ScaleControl
    try {
      scene.map.addControl(new mapboxgl.ScaleControl(), 'bottom-left');
    } catch (error) {
      console.error('Failed to add ScaleControl:', error);
    }
  };

  