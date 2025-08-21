# 智能慢跑路径规划系统文档

## 概述

本系统是一个基于PostgreSQL + PostGIS + pgRouting的智能慢跑路径规划系统，能够根据用户的起终点、距离约束、路段数约束等条件，生成最优的慢跑路径，并输出详细的GeoJSON格式数据。

## 核心特性

- **多种约束模式**：支持距离约束和路段数约束，有终点和无终点模式
- **智能优化算法**：基于路网质量评分进行路径优化
- **详细路段信息**：包含每个路段的地理、环境、设施等详细信息
- **GeoJSON输出**：标准地理数据格式，便于GIS工具和前端地图展示
- **双重功能**：既可独立测试，又可作为Flask API服务

## 系统架构

```text
routeplanning.py
├── 核心算法模块
│   ├── JoggingPathPlanner (主规划器类)
│   ├── RouteParams (参数数据类)
│   ├── RouteResult (结果数据类)
│   └── ConstraintMode (约束模式枚举)
├── 便捷接口函数
│   └── plan_jogging_route()
├── 独立测试模块
│   └── test()
└── Flask API模块
    ├── /api/get_routes (主要API端点)
    ├── /api/get_routes/health (健康检查)
    └── /api/get_routes/help (帮助文档)
```

## 约束模式说明

系统支持4种约束模式：

| 模式 | 名称 | 说明 |
|------|------|------|
| 1 | DISTANCE_WITH_END | 有终点，距离约束 - 指定起终点，控制总距离 |
| 2 | SEGMENTS_WITH_END | 有终点，路段数约束 - 指定起终点，控制路段数量 |
| 3 | DISTANCE_NO_END | 无终点，距离约束 - 只指定起点，按距离寻找最优终点 |
| 4 | SEGMENTS_NO_END | 无终点，路段数约束 - 只指定起点，按路段数寻找最优终点 |

## 核心类和方法

### JoggingPathPlanner 类

主要的路径规划器类，包含完整的规划算法。

#### 主要方法

1. **connect() / disconnect()**
   - 数据库连接管理

2. **find_nearest_node(lat, lon)**
   - 查找最近的路网节点
   - 使用PostGIS空间索引进行高效查询

3. **validate_params(params)**
   - 参数验证，确保权重设置合理

4. **filter_valid_nodes_by_distance/segments()**
   - 基于约束条件筛选有效节点
   - 使用pgr_dijkstra进行路径分析

5. **calculate_path_metrics()**
   - 计算所有候选路径的评分指标
   - 批量SQL计算提高效率

6. **get_optimal_path()**
   - 获取最优路径的详细信息
   - 包含节点序列、坐标和路段详情

7. **create_geojson()**
   - 生成标准GeoJSON格式输出
   - 包含路径几何和属性信息

### 权重参数说明

- **w1**: Total权重 - 控制路网质量评分的影响
- **w2**: 长度权重 - 当w2>0且w3=0时，优化距离效率
- **w3**: 路段数权重 - 当w3>0且w2=0时，优化路段数效率

## API接口文档

### 主要端点：POST /api/get_routes

#### 请求格式

```json
{
    "start_lat": 30.3210982,      // 必需：起点纬度
    "start_lon": 120.1788077,     // 必需：起点经度
    "end_lat": 30.313572,         // 可选：终点纬度
    "end_lon": 120.1776803,       // 可选：终点经度
    "constraint_mode": 1,         // 约束模式 (1-4)，默认1
    "target_distance": 6000,      // 目标距离(米)，默认5000
    "distance_tolerance": 500,    // 距离容差，默认400
    "target_segments": 40,        // 目标路段数，默认40
    "segments_tolerance": 5,      // 路段数容差，默认5
    "w1": 1.0,                   // Total权重，默认1.0
    "w2": 0.0,                   // 长度权重，默认0.0
    "w3": 1.0                    // 路段数权重，默认1.0
}
```

#### 响应格式

```json
{
    "success": true,
    "filename": "route_841_to_2212_20250810_181153.json",
    "filepath": "G:\\gh_repo\\Joy-Run-Smart-Track\\backend\\temp\\route_841_to_2212_20250810_181153.json",
    "route_info": {
        "total_distance": 6475.34,
        "total_segments": 55,
        "optimization_ratio": 7.0403,
        "score_per_meter": 3.8051,
        "score_per_segment": 7.0403
    }
}
```

### 辅助端点

- **GET /api/get_routes/health** - 健康检查
- **GET /api/get_routes/help** - API帮助文档

## 使用方法

### 1. 初始化数据库

- 使用schema中的routeplanning_db_init.py`进行路网表的初始化，代码中需要标注res中个人的road_modified.csv路径。

```sql
# 导入边表数据（如有CSV）
cursor.execute("""
    COPY edgesmodified(
    fid, water, bh, shape_leng, frequency, slope, buildng, ndvi, winding, sport, life, education, finance, traffic, public, scenery, food, poi, svi, gvi, vw, vei, light, poiden, origlen, bh_1, frequenc_1, sum_c_intr, sum_c_buil, sum_c_ndvi, sum_c_poi, sum_c_wind, sum_c_slop, sum_c_wate, sum_c_svi, sum_c_gvi, sum_c_vw, sum_c_ligh, sum_c_poid, score, startx, starty, endx, endy, total, dij_w1, distance, score_ori, dis_ori, toatl_ori1, toatl_ori2
) FROM 'your/csv/path' WITH CSV HEADER;
""")
```

- 注意，同时需要修改backend文件夹中的`config.yaml`，使其保存路径规划的临时文件路径是正确的。

### 2. 独立测试运行

```bash
# 直接运行Python文件进行测试
cd backend/routes
python routeplanning.py
```

测试会使用预设的杭州坐标进行路径规划演示。

### 3. 作为Flask API服务

```bash
# 启动Flask应用
cd backend
python app.py
```

然后通过HTTP请求调用API接口。

## 测试方法

### PowerShell API测试

以下是完整的API测试流程：

#### 1. 健康检查测试

```powershell
# 测试API服务状态
Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/get_routes/health" -Method GET
```

预期响应：

```json
{
  "service": "route_planning",
  "status": "healthy", 
  "timestamp": "2025-08-10T18:11:09.316542"
}
```

#### 2. 路径规划API测试

```powershell
# 构建请求数据
$body = @{
    start_lat = 30.3210982
    start_lon = 120.1788077
    end_lat = 30.313572
    end_lon = 120.1776803
    constraint_mode = 1
    target_distance = 6000
    distance_tolerance = 500
    w1 = 1.0
    w2 = 0.0
    w3 = 1.0
} | ConvertTo-Json

# 发送POST请求
$response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/get_routes" -Method POST -Body $body -ContentType "application/json"

# 查看响应内容
$response.Content
```

#### 3. 查看生成的文件

```powershell
# 检查最新生成的路径文件
Get-ChildItem "G:\gh_repo\Joy-Run-Smart-Track\backend\temp" -Filter "route_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 3
```

### Python测试脚本

```python
import requests
import json

# 测试健康检查
def test_health():
    response = requests.get('http://127.0.0.1:5000/api/get_routes/health')
    print('Health Check:', response.status_code)
    print('Response:', json.dumps(response.json(), indent=2))

# 测试路径规划
def test_route_planning():
    test_data = {
        'start_lat': 30.3210982,
        'start_lon': 120.1788077,
        'end_lat': 30.313572,
        'end_lon': 120.1776803,
        'constraint_mode': 1,
        'target_distance': 6000,
        'distance_tolerance': 500,
        'w1': 1.0,
        'w2': 0.0,
        'w3': 1.0
    }
    
    response = requests.post('http://127.0.0.1:5000/api/get_routes', 
                           json=test_data, 
                           headers={'Content-Type': 'application/json'})
    print('Route Planning Response:', response.status_code)
    if response.status_code == 200:
        print('Response:', json.dumps(response.json(), indent=2))
    else:
        print('Error:', response.text)

if __name__ == "__main__":
    test_health()
    test_route_planning()
```

## 输出文件格式

生成的GeoJSON文件包含以下信息：

### 基本结构

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[lon1, lat1], [lon2, lat2], ...]
  },
  "properties": {
    "optimization_ratio": 7.0403,
    "total_score": 387.15,
    "total_distance": 6475.34,
    "total_segments": 55,
    "score_per_meter": 3.8051,
    "score_per_segment": 7.0403,
    "edge_details": [...],
    "edge_statistics": {...}
  }
}
```

### 路段详细信息 (edge_details)

每个路段包含40+个属性字段：

- **几何信息**: geometry (GeoJSON几何)
- **基础属性**: edge_id, fid, shape_leng, distance, dis_ori
- **环境指标**: water, slope, buildng, ndvi, light
- **设施评分**: sport, life, education, finance, traffic, public
- **景观评分**: scenery, food, poi, svi, gvi, vw, vei
- **综合评分**: score, total, score_ori

## 数据库依赖

系统依赖以下数据库表：

- **nodesmodified**: 路网节点表
- **edgesmodified**: 路网边表（包含丰富的属性信息）

确保这些表已经正确配置了pgRouting的source/target字段。

## 配置文件

系统通过 `config.yaml` 配置临时文件存储路径：

```yaml
route_planning_temp_folder: "G:/gh_repo/Joy-Run-Smart-Track/backend/temp"
```

## 错误处理

系统包含完善的错误处理机制：

- 参数验证错误
- 数据库连接错误  
- 路径规划失败
- 文件保存错误

所有错误都会返回详细的错误信息，便于调试。

## 性能优化

- 使用PostGIS空间索引加速节点查找
- 批量SQL查询减少数据库交互
- pgRouting高效路径算法
- 智能文件命名避免冲突

## 扩展性

系统设计具有良好的扩展性：

- 可以轻松添加新的约束模式
- 支持自定义权重算法
- 可以扩展更多路段属性
- 支持不同的输出格式
