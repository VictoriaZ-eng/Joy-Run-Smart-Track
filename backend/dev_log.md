# 开发日志

## 20250803

1. 优化了matlab内的function分布，位于脚本的末端以正确运行
2. 优化了csv表头，全英文以解决兼容性问题
3. 初步创建了后端flask
   1. 运行setup_env.sh脚本，初始化conda环境以及安装依赖
   <!-- 2. 运行start.sh脚本，启动后端服务 -->
4. 数据库postgresql
   1. 打开pgadmin（注意需要安装postgis），运行create_road.sql，会执行以下流程
      1. 使用文件夹res下的outputroad.csv进行路网的创建，注意设置路径
      2. 创建节点表
      3. 创建路段表
      4. 导入csv到表
      5. 生成空间字段（geom）
      6. 检查结果
