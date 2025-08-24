// 推荐路线图表数据
// 为每条路线定义图表数据
export const routeCharts = {
  route1: {
    metrics: [
    { name: '建筑密度', value: 0.25, max: 1 },
    {name: 'POI多样性', value: 0.81, max: 1 },
    { name: 'POI密度', value: 0.49, max: 1 },
    { name: '道路曲折度', value: 0.37, max: 1 },
    { name: '街道照明情况', value: 0.41, max: 1 },
    { name: '天空景观指数', value:0.67 , max: 1 },
    { name: '绿化视图指数', value:0.63 , max: 1 },
    { name: '视觉步行能力', value: 0.59, max: 1 },
    { name: '归一化植被指数', value: 0.65, max: 1 },
    { name: '坡度', value: 0.73, max: 1 },
    { name: '离水域的平均距离', value: 0.13, max: 1 },

    ],

  },
  route2: {
    metrics: [
      { name: '建筑密度', value: 0.67, max: 1 },
      { name: 'POI多样性', value: 0.83, max: 1 },
      { name: 'POI密度', value: 0.51, max: 1 },
      { name: '道路曲折度', value: 0.45, max: 1 },
      { name: '街道照明情况', value: 0.37, max: 1 },
      { name: '天空景观指数', value:0.74 , max: 1 },
      { name: '绿化视图指数', value:0.45 , max: 1 },
      { name: '视觉步行能力', value: 0.59, max: 1 },
      { name: '归一化植被指数', value: 0.43, max: 1 },
      { name: '坡度', value: 0.75, max: 1 },
      { name: '离水域的平均距离', value: 0.38, max: 1 },
    ],
  },
  route3: {
    metrics: [
      { name: '建筑密度', value: 0.46, max: 1 },
      { name: 'POI多样性', value: 0.78, max: 1 },
      { name: 'POI密度', value: 0.45, max: 1 },
      { name: '道路曲折度', value: 0.34, max: 1 },
      { name: '街道照明情况', value: 0.56, max: 1 },
      { name: '天空景观指数', value:0.81 , max: 1 },
      { name: '绿化视图指数', value:0.72 , max: 1 },
      { name: '视觉步行能力', value: 0.49, max: 1 },
      { name: '归一化植被指数', value: 0.71, max: 1 },
      { name: '坡度', value: 0.80, max: 1 },
      { name: '离水域的平均距离', value: 0.39, max: 1 },
    ],

  }  

};

// 通用条形图配置
export const barConfig = {
  padding: [40, 20, 50, 100], // 上右下左
  legend: false,
  interactions: [{ type: 'active-region' }]
};
