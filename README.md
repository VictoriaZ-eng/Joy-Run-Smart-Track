# JoyRun_SmartTrack

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```
### 注意：
```sh
1.components文件夹放组件代码
2.views文件夹放具体功能实现代码
3.目前构思是APP.vue作为首页直接放慢跑推荐路线
4.前端参考布局：https://www.komoot.com/discover/Current_location/@23.1628080,113.5054540/tours?sport=hike&map=true&max_distance=30000&pageNumber=1
5.研究区域为杭州市拱墅区的部分区域（原为下城区）
6.依赖mapbox与L7
```
### 2025.8.4
```sh
1.加入了基本地图控件，加入了LocationSearch.vue组件实现地点搜索
2.发现Top.vue写死了地图，地图会一直出现，懒得把地图封装提出（怕报错），遂决定将跳转路由的内容改成css卡片形式展示
3.完成了marathon的路由注册，其他还没有注册路由，写到再注册
4.上传了一些赛事服务相关的图片到images文件夹里面

```
