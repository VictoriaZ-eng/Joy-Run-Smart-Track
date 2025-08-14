import psycopg2
import numpy as np
from typing import Tuple, List, Dict, Optional, Union
import json
import logging
import yaml
import os
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'joy_run_db',
    'user': 'postgres',
    'password': 'postgres1'
}

class ConstraintMode(Enum):
    """约束模式枚举 - UPDATE: 扩展到6个模式（来自modified-3.m）"""
    DISTANCE_WITH_END = 1      # 有终点，距离约束
    SEGMENTS_WITH_END = 2      # 有终点，路段数约束  
    DISTANCE_NO_END = 3        # 无终点，距离约束
    SEGMENTS_NO_END = 4        # 无终点，路段数约束
    SHORTEST_PATH = 5          # 有终点，最短距离（无约束）
    MIN_SEGMENTS_PATH = 6      # 有终点，最少路段数（无约束）

class PreferenceMode(Enum):
    """偏好模式枚举 - UPDATE: 新增偏好系统（来自modified-3.m）"""
    COMPREHENSIVE = 1          # 综合得分（原Total）
    WATERFRONT = 2            # 滨水路线（Water_Mtotal）
    GREEN = 3                 # 高绿化路线（NDVI_Mtotal + GVI_Mtotal）
    OPEN_VIEW = 4             # 视野开阔路线（SVI_Mtotal + Buildng_Mtotal）
    WELL_LIT = 5              # 夜间灯光充足路线（light_Mtotal）
    FACILITIES = 6            # 设施便利路线（POI_Mtotal）
    GENTLE_SLOPE = 7          # 坡度平缓路线（slope_Mtotal）

@dataclass
class RouteParams:
    """路径规划参数 - UPDATE: 添加偏好模式支持（来自modified-3.m）"""
    start_lat: float
    start_lon: float
    end_lat: Optional[float] = None
    end_lon: Optional[float] = None
    constraint_mode: ConstraintMode = ConstraintMode.DISTANCE_WITH_END
    preference_mode: PreferenceMode = PreferenceMode.COMPREHENSIVE  # UPDATE: 新增偏好模式
    
    # 权重参数
    w1: float = 1.0    # Total的权重
    w2: float = 0.0    # 长度权重 (w2>0且w3=0时使用)
    w3: float = 1.0    # 路段数权重 (w3>0且w2=0时使用)
    
    # 距离约束参数
    target_distance: float = 5000  # 目标距离(米)
    distance_tolerance: float = 400 # 距离容差
    
    # 路段数约束参数
    target_segments: int = 40      # 目标路段数
    segments_tolerance: int = 5    # 路段数容差

@dataclass
class RouteResult:
    """路径规划结果 - UPDATE: 添加推荐约束范围信息（来自modified-3.m）"""
    path_nodes: List[int]
    path_coordinates: List[Tuple[float, float]]
    total_distance: float
    total_segments: int
    total_score: float
    optimization_ratio: float
    score_per_meter: float
    score_per_segment: float
    geojson: Dict
    # UPDATE: 新增字段
    recommended_distances: Optional[List[float]] = None   # 推荐距离范围
    recommended_segments: Optional[List[int]] = None      # 推荐路段数范围
    distance_range: Optional[Tuple[float, float]] = None # 有效距离范围
    segments_range: Optional[Tuple[int, int]] = None     # 有效路段数范围

class JoggingPathPlanner:
    def get_temp_folder(self):
        """读取config.yaml获取route_planning_temp_folder路径"""
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.yaml'))
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        temp_folder = config.get('route_planning_temp_folder')
        if not temp_folder:
            raise ValueError('config.yaml 未配置 route_planning_temp_folder')
        return temp_folder
    """智能慢跑路径规划器"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("数据库连接已断开")
    
    def find_nearest_node(self, lat: float, lon: float) -> Tuple[int, float, float]:
        """
        查找最近的路网节点，返回节点ID和坐标
        Args:
            lat: 纬度
            lon: 经度
        Returns:
            (节点ID, 节点纬度, 节点经度)
        """
        sql = """
        SELECT id, y, x
        FROM nodesmodified 
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        LIMIT 1;
        """
        self.cursor.execute(sql, (lon, lat))
        result = self.cursor.fetchone()
        if not result:
            raise ValueError(f"未找到任何路网节点，请检查nodesmodified表是否有数据")
        node_id, node_lat, node_lon = result
        return node_id, node_lat, node_lon
    
    def validate_params(self, params: RouteParams):
        """验证参数合法性 - UPDATE: 扩展到6个约束模式和7个偏好模式（来自modified-3.m）"""
        # 权重参数验证
        if params.w1 < 0:
            raise ValueError("w1必须为非负数")
        
        if not ((params.w2 > 0 and params.w3 == 0) or (params.w2 == 0 and params.w3 > 0)):
            raise ValueError("w2和w3必须一正一零（w2>0用长度，w3>0用路段数）")
        
        # UPDATE: 约束模式验证（扩展到1-6）
        if not isinstance(params.constraint_mode, ConstraintMode):
            raise ValueError("constraintMode必须为1-6")
        
        # UPDATE: 偏好模式验证（新增1-7）
        if not isinstance(params.preference_mode, PreferenceMode):
            raise ValueError("preferenceMode必须为1-7")
        
        # UPDATE: 终点验证（模式1,2,5,6需要终点）
        if params.constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.SEGMENTS_WITH_END, 
                                    ConstraintMode.SHORTEST_PATH, ConstraintMode.MIN_SEGMENTS_PATH]:
            if params.end_lat is None or params.end_lon is None:
                raise ValueError("模式1,2,5,6需要提供终点坐标")
    
    def get_preference_total_column(self, preference_mode: PreferenceMode) -> str:
        """根据偏好模式获取对应的Total列名 - UPDATE: 新增偏好系统（来自modified-3.m）"""
        column_mapping = {
            PreferenceMode.COMPREHENSIVE: "total",           # 综合得分（原Total）
            PreferenceMode.WATERFRONT: "water_mtotal",       # 滨水路线
            PreferenceMode.GREEN: "ndvi_mtotal + COALESCE(gvi_mtotal, 0)",  # UPDATE: 修复组合字段语法
            PreferenceMode.OPEN_VIEW: "svi_mtotal + COALESCE(buildng_mtotal, 0)", # UPDATE: 修复组合字段语法
            PreferenceMode.WELL_LIT: "light_mtotal",         # 夜间灯光充足路线
            PreferenceMode.FACILITIES: "poi_mtotal",         # 设施便利路线
            PreferenceMode.GENTLE_SLOPE: "slope_mtotal"      # 坡度平缓路线
        }
        return column_mapping[preference_mode]
    
    def calculate_dynamic_constraints(self, start_node: int, end_node: Optional[int], 
                                    constraint_mode: ConstraintMode) -> Dict:
        """动态计算约束范围并生成推荐值 - UPDATE: 新增动态约束计算（来自modified-3.m）"""
        if constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.DISTANCE_NO_END]:
            # 距离约束的动态计算
            if constraint_mode == ConstraintMode.DISTANCE_WITH_END and end_node is not None:
                # 有终点：计算起点+终点到所有节点的总距离
                sql = """
                WITH start_distances AS (
                    SELECT end_vid as node_id, sum(cost) as dist_from_start
                    FROM pgr_dijkstra(
                        'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                        %s, 
                        (SELECT array_agg(id) FROM nodesmodified),
                        directed := false
                    ) GROUP BY end_vid
                ),
                end_distances AS (
                    SELECT end_vid as node_id, sum(cost) as dist_to_end  
                    FROM pgr_dijkstra(
                        'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                        %s,
                        (SELECT array_agg(id) FROM nodesmodified), 
                        directed := false
                    ) GROUP BY end_vid
                )
                SELECT min(s.dist_from_start + e.dist_to_end) as min_dist, 
                       max(s.dist_from_start + e.dist_to_end) as max_dist
                FROM start_distances s
                JOIN end_distances e ON s.node_id = e.node_id;
                """
                self.cursor.execute(sql, (start_node, end_node))
            else:
                # 无终点：计算起点到所有节点的累积距离
                sql = """
                SELECT min(agg_cost), max(agg_cost)
                FROM pgr_dijkstra(
                    'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                    %s,
                    (SELECT array_agg(id) FROM nodesmodified WHERE id != %s),
                    directed := false
                ) WHERE agg_cost < 'Infinity'::float AND agg_cost > 0;
                """
                self.cursor.execute(sql, (start_node, start_node))
            
            result = self.cursor.fetchone()
            if not result or result[0] is None:
                raise ValueError("无法计算有效距离范围，请检查路网数据")
            
            min_dist, max_dist = result
            distance_step = 500  # 500米间隔
            
            # 生成推荐距离（向上取整到步长倍数）
            min_recommended = int(np.ceil(min_dist / distance_step) * distance_step)
            max_recommended = int(np.floor(max_dist / distance_step) * distance_step)
            
            if min_recommended > max_recommended:
                recommended_distances = [min_recommended]
            else:
                recommended_distances = list(range(min_recommended, max_recommended + 1, distance_step))
            
            return {
                'type': 'distance',
                'min_value': min_dist,
                'max_value': max_dist,
                'recommended_values': recommended_distances,
                'step': distance_step,
                'unit': 'meters'
            }
            
        else:  # 路段数约束
            if constraint_mode == ConstraintMode.SEGMENTS_WITH_END and end_node is not None:
                # 有终点：使用递归CTE计算路段数范围（简化版BFS）
                sql = """
                WITH RECURSIVE segments_calc AS (
                    SELECT source, target, 1 as segments
                    FROM edgesmodified
                    WHERE source = %s OR target = %s
                    UNION ALL
                    SELECT e.source, e.target, s.segments + 1
                    FROM segments_calc s
                    JOIN edgesmodified e ON (e.source = s.target OR e.target = s.source)
                    WHERE s.segments < 50  -- 限制递归深度
                )
                SELECT min(segments), max(segments)
                FROM segments_calc
                WHERE source = %s OR target = %s;
                """
                self.cursor.execute(sql, (start_node, start_node, end_node, end_node))
            else:
                # 无终点：单源路段数计算
                sql = """
                WITH RECURSIVE segments_calc AS (
                    SELECT target as node_id, 1 as segments
                    FROM edgesmodified
                    WHERE source = %s
                    UNION ALL
                    SELECT e.target, s.segments + 1
                    FROM segments_calc s
                    JOIN edgesmodified e ON e.source = s.node_id
                    WHERE s.segments < 50 AND s.node_id != %s
                )
                SELECT min(segments), max(segments)
                FROM segments_calc;
                """
                self.cursor.execute(sql, (start_node, start_node))
            
            result = self.cursor.fetchone()
            if not result or result[0] is None:
                raise ValueError("无法计算有效路段数范围，请检查路网数据")
            
            min_segments, max_segments = result
            segments_step = 5  # 5段间隔
            
            # 生成推荐路段数
            min_recommended = int(np.ceil(min_segments / segments_step) * segments_step)
            max_recommended = int(np.floor(max_segments / segments_step) * segments_step)
            
            if min_recommended > max_recommended:
                recommended_segments = [min_recommended]
            else:
                recommended_segments = list(range(min_recommended, max_recommended + 1, segments_step))
            
            return {
                'type': 'segments',
                'min_value': min_segments,
                'max_value': max_segments,
                'recommended_values': recommended_segments,
                'step': segments_step,
                'unit': 'segments'
            }
    
    def get_constraint_bounds(self, params: RouteParams) -> Tuple[float, float]:
        """获取约束范围"""
        if params.constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.DISTANCE_NO_END]:
            return (
                params.target_distance - params.distance_tolerance,
                params.target_distance + params.distance_tolerance
            )
        else:  # 路段数约束
            return (
                params.target_segments - params.segments_tolerance,
                params.target_segments + params.segments_tolerance
            )
    
    def filter_valid_nodes_by_distance(self, start_node: int, end_node: Optional[int], 
                                     min_dist: float, max_dist: float) -> List[int]:
        """
        基于距离约束筛选有效节点
        使用PostGIS的pgr_dijkstra进行高效计算
        """
        if end_node is not None:
            # 有终点模式：筛选满足起点到节点+节点到终点总距离在范围内的节点
            sql = """
            WITH start_distances AS (
                SELECT end_vid as node_id, sum(cost) as dist_from_start
                FROM pgr_dijkstra(
                    'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                    %s, 
                    (SELECT array_agg(id) FROM nodesmodified),
                    directed := false
                ) GROUP BY end_vid
            ),
            end_distances AS (
                SELECT end_vid as node_id, sum(cost) as dist_to_end  
                FROM pgr_dijkstra(
                    'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                    %s,
                    (SELECT array_agg(id) FROM nodesmodified), 
                    directed := false
                ) GROUP BY end_vid
            )
            SELECT s.node_id
            FROM start_distances s
            JOIN end_distances e ON s.node_id = e.node_id
            WHERE (s.dist_from_start + e.dist_to_end) BETWEEN %s AND %s;
            """
            self.cursor.execute(sql, (start_node, end_node, min_dist, max_dist))
        else:
            # 无终点模式：筛选起点到节点累积距离在范围内的节点
            sql = """
            SELECT end_vid as node_id
            FROM pgr_dijkstra(
                'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                %s,
                (SELECT array_agg(id) FROM nodesmodified WHERE id != %s),
                directed := false
            )
            WHERE agg_cost BETWEEN %s AND %s AND agg_cost > 0;
            """
            self.cursor.execute(sql, (start_node, start_node, min_dist, max_dist))
        
        return [row[0] for row in self.cursor.fetchall()]
    
    def filter_valid_nodes_by_segments(self, start_node: int, end_node: Optional[int],
                                     min_segments: int, max_segments: int) -> List[int]:
        """
        基于路段数约束筛选有效节点
        使用BFS思想，通过hop数限制实现
        """
        if end_node is not None:
            # 有终点模式：使用pgr_withPoints结合距离限制模拟路段数约束
            sql = """
            WITH RECURSIVE path_segments AS (
                -- 起点BFS
                SELECT %s as node_id, 0 as segments_from_start
                UNION ALL
                SELECT e.endx as node_id, p.segments_from_start + 1
                FROM path_segments p
                JOIN edgesmodified e ON e.startx = p.node_id
                WHERE p.segments_from_start < %s
            ),
            end_segments AS (
                -- 终点BFS  
                SELECT %s as node_id, 0 as segments_to_end
                UNION ALL
                SELECT e.startx as node_id, p.segments_to_end + 1
                FROM end_segments p
                JOIN edgesmodified e ON e.endx = p.node_id
                WHERE p.segments_to_end < %s
            )
            SELECT DISTINCT s.node_id
            FROM path_segments s
            JOIN end_segments e ON s.node_id = e.node_id
            WHERE (s.segments_from_start + e.segments_to_end) BETWEEN %s AND %s;
            """
            self.cursor.execute(sql, (start_node, max_segments, end_node, max_segments, min_segments, max_segments))
        else:
            # 无终点模式：单源BFS
            sql = """
            WITH RECURSIVE path_segments AS (
                SELECT %s as node_id, 0 as segments
                UNION ALL
                SELECT e.endx as node_id, p.segments + 1
                FROM path_segments p
                JOIN edgesmodified e ON e.startx = p.node_id
                WHERE p.segments < %s
            )
            SELECT DISTINCT node_id
            FROM path_segments
            WHERE segments BETWEEN %s AND %s;
            """
            self.cursor.execute(sql, (start_node, max_segments, min_segments, max_segments))
        
        return [row[0] for row in self.cursor.fetchall()]
    
    def calculate_shortest_path(self, start_node: int, end_node: int, 
                              constraint_mode: ConstraintMode, params: RouteParams) -> Dict:
        """计算最短路径（模式5）或最少路段数路径（模式6） - UPDATE: 新增模式5,6支持并修复偏好评分应用（来自modified-3.m）"""
        
        # UPDATE: 获取偏好模式对应的评分字段
        preference_column = self.get_preference_total_column(params.preference_mode)
        
        if constraint_mode == ConstraintMode.SHORTEST_PATH:
            # 模式5：最短距离路径 - 考虑偏好评分的权重
            cost_function = f"CASE WHEN {preference_column} > 0 THEN dis_ori / {preference_column} ELSE dis_ori * 10 END"
            
            sql = f"""
            SELECT 
                array_agg(node ORDER BY seq) as path_nodes,
                sum(cost) as total_distance,
                count(*) as total_segments
            FROM pgr_dijkstra(
                'SELECT id, source, target, {cost_function} as cost, {cost_function} as reverse_cost FROM edgesmodified',
                %s, %s, directed := false
            );
            """
            self.cursor.execute(sql, (start_node, end_node))
            
        elif constraint_mode == ConstraintMode.MIN_SEGMENTS_PATH:
            # 模式6：最少路段数路径 - 同时考虑偏好评分
            sql = f"""
            SELECT 
                array_agg(node ORDER BY seq) as path_nodes,
                count(*) as total_segments,
                sum(cost) as total_distance
            FROM pgr_dijkstra(
                'SELECT id, source, target, 1 as cost, 1 as reverse_cost FROM edgesmodified',
                %s, %s, directed := false
            ) a
            JOIN edgesmodified b ON a.edge = b.id;
            """
            self.cursor.execute(sql, (start_node, end_node))
        
        result = self.cursor.fetchone()
        if not result or not result[0]:
            raise ValueError("起点到终点无可达路径")
        
        path_nodes, segments_or_distance, distance_or_segments = result
        
        if constraint_mode == ConstraintMode.SHORTEST_PATH:
            total_distance = segments_or_distance
            total_segments = distance_or_segments
        else:  # MIN_SEGMENTS_PATH
            total_segments = segments_or_distance
            total_distance = distance_or_segments
            
        # UPDATE: 计算路径的偏好得分和综合评价
        edges_from_path = []
        for i in range(len(path_nodes) - 1):
            src_node = path_nodes[i]
            tgt_node = path_nodes[i + 1]
            edges_from_path.append(f"(source = {src_node} AND target = {tgt_node}) OR (source = {tgt_node} AND target = {src_node})")
        
        if edges_from_path:
            edges_condition = " OR ".join(edges_from_path)
            sql = f"""
            SELECT 
                sum(score) as total_score,
                sum({preference_column}) as total_preference_score,
                sum(dis_ori) as actual_distance
            FROM edgesmodified 
            WHERE {edges_condition};
            """
            self.cursor.execute(sql)
            score_result = self.cursor.fetchone()
            total_score = score_result[0] if score_result[0] else 0
            total_preference_score = score_result[1] if score_result[1] else 0
            actual_distance = score_result[2] if score_result[2] else total_distance
        else:
            total_score = 0
            total_preference_score = 0
            actual_distance = total_distance
        
        # UPDATE: 使用偏好评分计算优化比值
        if params.w2 > 0:  # 使用长度权重
            ratio = (total_preference_score ** params.w1) / (actual_distance ** params.w2) if actual_distance > 0 else 0
        else:  # 使用路段数权重
            ratio = (total_preference_score ** params.w1) / (total_segments ** params.w3) if total_segments > 0 else 0
        
        return {
            'node_id': -1,  # 标识为直接路径
            'path_nodes': path_nodes,
            'preference_total': total_preference_score,  # UPDATE: 添加偏好总分
            'dist_real': actual_distance,
            'segments': total_segments, 
            'score': total_score,
            'ratio': ratio,
            'score_per_meter': total_preference_score / actual_distance if actual_distance > 0 else 0,
            'score_per_segment': total_preference_score / total_segments if total_segments > 0 else 0
        }
    
    def calculate_path_metrics(self, start_node: int, end_node: Optional[int], 
                             valid_nodes: List[int], params: RouteParams) -> List[Dict]:
        """
        计算所有有效节点的路径指标 - UPDATE: 修复偏好模式在有终点约束时不生效的问题
        使用SQL批量计算提高效率，并正确应用偏好评分
        """
        metrics = []
        
        # UPDATE: 获取偏好模式对应的评分字段
        preference_column = self.get_preference_total_column(params.preference_mode)
        
        # 构建有效节点的WHERE子句
        valid_nodes_str = ','.join(map(str, valid_nodes))
        
        if params.constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.SEGMENTS_WITH_END]:
            # UPDATE: 有终点模式 - 修复偏好评分计算
            # 使用偏好评分作为路径权重，而不是固定的distance
            cost_function = f"CASE WHEN {preference_column} > 0 THEN dis_ori / {preference_column} ELSE dis_ori * 10 END"
            
            sql = f"""
            WITH start_paths AS (
                SELECT 
                    end_vid as mid_node,
                    sum(cost) as dist_std_to_mid,
                    sum(b.dis_ori) as dist_real_to_mid,
                    count(*) as segments_to_mid,
                    sum(b.{preference_column}) as preference_score_to_mid,
                    sum(b.total) as total_std_to_mid,
                    sum(b.score) as score_to_mid
                FROM pgr_dijkstra(
                    'SELECT id, source, target, {cost_function} as cost, {cost_function} as reverse_cost FROM edgesmodified', 
                    %s, 
                    ARRAY[{valid_nodes_str}], 
                    directed := false
                ) a
                JOIN edgesmodified b ON a.edge = b.id
                WHERE end_vid IN ({valid_nodes_str})
                GROUP BY end_vid
            ),
            end_paths AS (
                SELECT 
                    end_vid as mid_node,
                    sum(cost) as dist_std_from_mid, 
                    sum(b.dis_ori) as dist_real_from_mid,
                    count(*) as segments_from_mid,
                    sum(b.{preference_column}) as preference_score_from_mid,
                    sum(b.total) as total_std_from_mid,
                    sum(b.score) as score_from_mid
                FROM pgr_dijkstra(
                    'SELECT id, source, target, {cost_function} as cost, {cost_function} as reverse_cost FROM edgesmodified',
                    %s,
                    ARRAY[{valid_nodes_str}], 
                    directed := false
                ) a
                JOIN edgesmodified b ON a.edge = b.id  
                WHERE end_vid IN ({valid_nodes_str})
                GROUP BY end_vid
            )
            SELECT 
                s.mid_node,
                (s.preference_score_to_mid + e.preference_score_from_mid) as preference_total,
                (s.total_std_to_mid + e.total_std_from_mid) as total_std,
                (s.dist_std_to_mid + e.dist_std_from_mid) as dist_std, 
                (s.segments_to_mid + e.segments_from_mid) as segments,
                (s.dist_real_to_mid + e.dist_real_from_mid) as dist_real,
                (s.score_to_mid + e.score_from_mid) as score
            FROM start_paths s
            JOIN end_paths e ON s.mid_node = e.mid_node
            WHERE s.mid_node != %s AND s.mid_node != %s;
            """
            
            self.cursor.execute(sql, (start_node, end_node, start_node, end_node))
        else:
            # UPDATE: 无终点模式 - 修复偏好评分计算
            cost_function = f"CASE WHEN {preference_column} > 0 THEN dis_ori / {preference_column} ELSE dis_ori * 10 END"
            
            sql = f"""
            SELECT 
                end_vid as node_id,
                sum(b.{preference_column}) as preference_total,
                sum(b.total) as total_std,
                sum(cost) as dist_std,
                count(*) as segments, 
                sum(b.dis_ori) as dist_real,
                sum(b.score) as score
            FROM pgr_dijkstra(
                'SELECT id, source, target, {cost_function} as cost, {cost_function} as reverse_cost FROM edgesmodified',
                %s,
                ARRAY[{valid_nodes_str}],
                directed := false
            ) a
            JOIN edgesmodified b ON a.edge = b.id
            WHERE end_vid IN ({valid_nodes_str}) AND end_vid != %s
            GROUP BY end_vid;
            """
            
            self.cursor.execute(sql, (start_node, start_node))
        
        results = self.cursor.fetchall()
        
        # 计算约束范围
        min_constraint, max_constraint = self.get_constraint_bounds(params)
        
        for row in results:
            if params.constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.SEGMENTS_WITH_END]:
                node_id, preference_total, total_std, dist_std, segments, dist_real, score = row
            else:
                node_id, preference_total, total_std, dist_std, segments, dist_real, score = row
            
            # 约束检查
            constraint_value = dist_real if params.constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.DISTANCE_NO_END] else segments
            if not (min_constraint <= constraint_value <= max_constraint):
                continue
            
            # UPDATE: 使用偏好评分计算优化比值
            if params.w2 > 0 and dist_std > 0:
                ratio = (preference_total ** params.w1) / (dist_std ** params.w2)
            elif params.w3 > 0 and segments > 0:
                ratio = (preference_total ** params.w1) / (segments ** params.w3)
            else:
                continue
                
            # 计算得分比值
            score_per_meter = preference_total / dist_real if dist_real > 0 else 0
            score_per_segment = preference_total / segments if segments > 0 else 0
            
            metrics.append({
                'node_id': node_id,
                'preference_total': preference_total,  # UPDATE: 添加偏好总分
                'total_std': total_std,
                'dist_std': dist_std,
                'segments': segments,
                'dist_real': dist_real,
                'score': score,
                'ratio': ratio,
                'score_per_meter': score_per_meter,
                'score_per_segment': score_per_segment
            })
        
        return metrics
    
    def get_optimal_path(self, start_node: int, end_node: Optional[int], best_metric: Dict) -> Tuple[List[int], List[Tuple[float, float]], List[Dict]]:
        """
        获取最优路径的节点序列、坐标和路段详细信息
        """
        if best_metric['node_id'] == -1:  # 直接路径
            sql = """
            SELECT node, edge 
            FROM pgr_dijkstra(
                'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                %s, %s, directed := false
            ) ORDER BY seq;
            """
            self.cursor.execute(sql, (start_node, end_node))
            path_result = self.cursor.fetchall()
        elif end_node is not None:
            # 通过中间节点的路径
            mid_node = best_metric['node_id']
            
            # 起点到中间节点
            sql1 = """
            SELECT node, edge 
            FROM pgr_dijkstra(
                'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                %s, %s, directed := false
            ) ORDER BY seq;
            """
            self.cursor.execute(sql1, (start_node, mid_node))
            path1 = self.cursor.fetchall()
            
            # 中间节点到终点
            sql2 = """
            SELECT node, edge 
            FROM pgr_dijkstra(
                'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                %s, %s, directed := false
            ) ORDER BY seq;
            """
            self.cursor.execute(sql2, (mid_node, end_node))
            path2 = self.cursor.fetchall()
            
            # 合并路径（去除重复的中间节点）
            path_result = path1 + path2[1:]
        else:
            # 无终点模式：起点到最优节点
            sql = """
            SELECT node, edge 
            FROM pgr_dijkstra(
                'SELECT id, source, target, dis_ori as cost, dis_ori as reverse_cost FROM edgesmodified',
                %s, %s, directed := false
            ) ORDER BY seq;
            """
            self.cursor.execute(sql, (start_node, best_metric['node_id']))
            path_result = self.cursor.fetchall()
        
        # 提取节点和边
        path_nodes = [row[0] for row in path_result]
        path_edges = [row[1] for row in path_result if row[1] is not None]  # 去除None值（终点没有outgoing edge）
        
        # 获取路径坐标
        nodes_str = ','.join(map(str, path_nodes))
        sql = """
        SELECT x, y 
        FROM nodesmodified 
        WHERE id IN ({})
        ORDER BY array_position(ARRAY[{}], id);
        """.format(nodes_str, nodes_str)

        self.cursor.execute(sql)
        coordinates = [(row[0], row[1]) for row in self.cursor.fetchall()]  # (lon, lat)
        
        # 获取路段详细信息
        edge_details = []
        if path_edges:
            edges_str = ','.join(map(str, path_edges))
            sql = """
            SELECT id, fid, water, bh, shape_leng, frequency, slope, buildng, ndvi, winding,
                   sport, life, education, finance, traffic, public, scenery, food, poi, svi, gvi,
                   vw, vei, light, poiden, origlen, score, startx, starty, endx, endy, total,
                   dij_w1, distance, score_ori, dis_ori, toatl_ori1, toatl_ori2,
                   ST_AsGeoJSON(geom) as geometry
            FROM edgesmodified 
            WHERE id IN ({})
            ORDER BY array_position(ARRAY[{}], id);
            """.format(edges_str, edges_str)
            
            self.cursor.execute(sql)
            edge_results = self.cursor.fetchall()
            
            for edge in edge_results:
                edge_info = {
                    'edge_id': edge[0],
                    'fid': edge[1],
                    'water': edge[2],
                    'bh': edge[3],
                    'shape_leng': edge[4],
                    'frequency': edge[5],
                    'slope': edge[6],
                    'buildng': edge[7],
                    'ndvi': edge[8],
                    'winding': edge[9],
                    'sport': edge[10],
                    'life': edge[11],
                    'education': edge[12],
                    'finance': edge[13],
                    'traffic': edge[14],
                    'public': edge[15],
                    'scenery': edge[16],
                    'food': edge[17],
                    'poi': edge[18],
                    'svi': edge[19],
                    'gvi': edge[20],
                    'vw': edge[21],
                    'vei': edge[22],
                    'light': edge[23],
                    'poiden': edge[24],
                    'origlen': edge[25],
                    'score': edge[26],
                    'startx': edge[27],
                    'starty': edge[28],
                    'endx': edge[29],
                    'endy': edge[30],
                    'total': edge[31],
                    'dij_w1': edge[32],
                    'distance': edge[33],
                    'score_ori': edge[34],
                    'dis_ori': edge[35],
                    'toatl_ori1': edge[36],
                    'toatl_ori2': edge[37],
                    'geometry': json.loads(edge[38]) if edge[38] else None
                }
                edge_details.append(edge_info)

        return path_nodes, coordinates, edge_details
    
    def create_geojson(self, coordinates: List[Tuple[float, float]], properties: Dict, edge_details: List[Dict] = None) -> Dict:
        """创建GeoJSON格式的路径，包含边的详细信息"""
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": properties
        }
        
        # 添加边的详细信息
        if edge_details:
            geojson["properties"]["edge_details"] = edge_details
            
            # 添加统计信息
            total_score = sum(edge.get('score', 0) or 0 for edge in edge_details)
            total_distance = sum(edge.get('dis_ori', 0) or 0 for edge in edge_details)
            avg_score = total_score / len(edge_details) if edge_details else 0
            avg_distance = total_distance / len(edge_details) if edge_details else 0
            
            geojson["properties"]["edge_statistics"] = {
                "total_edges": len(edge_details),
                "total_score": total_score,
                "total_distance": total_distance,
                "avg_score_per_edge": avg_score,
                "avg_distance_per_edge": avg_distance
            }
        
        return geojson
    
    def plan_route(self, params: RouteParams) -> RouteResult:
        """
        主要路径规划方法 - UPDATE: 支持6种约束模式和7种偏好模式（来自modified-3.m）
        
        Args:
            params: 路径规划参数
            
        Returns:
            路径规划结果
        """
        logger.info(f"开始路径规划，约束模式: {params.constraint_mode.name}，偏好模式: {params.preference_mode.name}")
        
        # 验证参数
        self.validate_params(params)
        
        # 查找起终点最近的路网节点，并输出吸附信息
        start_node, start_node_lat, start_node_lon = self.find_nearest_node(params.start_lat, params.start_lon)
        end_node = None
        end_node_lat = end_node_lon = None
        
        # UPDATE: 根据约束模式决定是否需要终点
        if params.constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.SEGMENTS_WITH_END, 
                                    ConstraintMode.SHORTEST_PATH, ConstraintMode.MIN_SEGMENTS_PATH]:
            if params.end_lat is not None and params.end_lon is not None:
                end_node, end_node_lat, end_node_lon = self.find_nearest_node(params.end_lat, params.end_lon)
                logger.info(f"终点吸附到节点: {end_node} (lat={end_node_lat}, lon={end_node_lon})")
        
        logger.info(f"起点吸附到节点: {start_node} (lat={start_node_lat}, lon={start_node_lon})")
        
        # UPDATE: 处理最短路径模式（5和6）
        if params.constraint_mode in [ConstraintMode.SHORTEST_PATH, ConstraintMode.MIN_SEGMENTS_PATH]:
            if end_node is None:
                raise ValueError("模式5和6需要提供终点坐标")
            
            # 直接计算最短路径
            best_metric = self.calculate_shortest_path(start_node, end_node, params.constraint_mode, params)
            logger.info(f"最短路径计算完成，距离: {best_metric['dist_real']:.2f}米，路段数: {best_metric['segments']}")
            
            # 获取路径坐标
            path_nodes, coordinates, edge_details = self.get_optimal_path(start_node, end_node, best_metric)
            
        else:
            # UPDATE: 传统约束模式（1-4）- 支持动态约束计算
            # 首先计算动态约束范围
            try:
                constraint_info = self.calculate_dynamic_constraints(start_node, end_node, params.constraint_mode)
                logger.info(f"动态约束范围: {constraint_info['min_value']:.0f} - {constraint_info['max_value']:.0f} {constraint_info['unit']}")
                logger.info(f"推荐值: {constraint_info['recommended_values']}")
            except Exception as e:
                logger.warning(f"动态约束计算失败，使用固定约束: {e}")
                constraint_info = None
            
            # 获取约束范围
            min_constraint, max_constraint = self.get_constraint_bounds(params)
            logger.info(f"使用约束范围: {min_constraint} - {max_constraint}")
            
            # 筛选有效节点
            if params.constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.DISTANCE_NO_END]:
                valid_nodes = self.filter_valid_nodes_by_distance(start_node, end_node, min_constraint, max_constraint)
            else:
                valid_nodes = self.filter_valid_nodes_by_segments(start_node, end_node, min_constraint, max_constraint)
            
            if not valid_nodes:
                print("valid_nodes:", len(valid_nodes))
                raise ValueError("没有满足约束条件的节点，请调整约束范围")
            
            logger.info(f"有效节点数: {len(valid_nodes)}")
            
            # 计算路径指标
            metrics = self.calculate_path_metrics(start_node, end_node, valid_nodes, params)
            
            if not metrics:
                raise ValueError("没有找到有效路径，请调整约束参数")
            
            # 选择最优路径
            best_metric = max(metrics, key=lambda x: x['ratio'])
            logger.info(f"最优比值: {best_metric['ratio']:.4f}")
            
            # 获取最优路径
            path_nodes, coordinates, edge_details = self.get_optimal_path(start_node, end_node, best_metric)

        # UPDATE: 确保使用正确的偏好评分值
        preference_score = best_metric.get('preference_total', best_metric.get('score', 0))
        logger.info(f"偏好模式 {params.preference_mode.name} 总评分: {preference_score:.2f}")

        # 创建GeoJSON - UPDATE: 添加偏好模式信息和偏好评分
        geojson = self.create_geojson(coordinates, {
            'optimization_ratio': best_metric['ratio'],
            'total_score': best_metric['score'],
            'preference_score': preference_score,  # UPDATE: 新增偏好评分
            'total_distance': best_metric['dist_real'],
            'total_segments': best_metric['segments'],
            'score_per_meter': best_metric['score_per_meter'],
            'score_per_segment': best_metric['score_per_segment'],
            'constraint_mode': params.constraint_mode.name,
            'preference_mode': params.preference_mode.name  # UPDATE: 新增偏好模式信息
        }, edge_details)

        # 保存GeoJSON到指定临时目录
        try:
            temp_folder = self.get_temp_folder()
            os.makedirs(temp_folder, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'route_{start_node}_to_{end_node if end_node else "auto"}_{timestamp}.json'
            geojson_path = os.path.join(temp_folder, filename)
            with open(geojson_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            logger.info(f"GeoJSON 路径已保存到: {geojson_path}")
        except Exception as e:
            logger.error(f"保存GeoJSON失败: {e}")

        # UPDATE: 返回结果包含动态约束信息
        result = RouteResult(
            path_nodes=path_nodes,
            path_coordinates=coordinates,
            total_distance=best_metric['dist_real'],
            total_segments=best_metric['segments'],
            total_score=best_metric['score'],
            optimization_ratio=best_metric['ratio'],
            score_per_meter=best_metric['score_per_meter'],
            score_per_segment=best_metric['score_per_segment'],
            geojson=geojson
        )
        
        # UPDATE: 添加动态约束推荐信息（如果计算成功）
        if 'constraint_info' in locals() and constraint_info:
            if constraint_info['type'] == 'distance':
                result.recommended_distances = constraint_info['recommended_values']
                result.distance_range = (constraint_info['min_value'], constraint_info['max_value'])
            else:
                result.recommended_segments = constraint_info['recommended_values']
                result.segments_range = (constraint_info['min_value'], constraint_info['max_value'])
        
        return result

def plan_jogging_route(start_lat: float, start_lon: float, 
                      end_lat: Optional[float] = None, end_lon: Optional[float] = None,
                      constraint_mode: int = 1, preference_mode: int = 1,  # UPDATE: 新增偏好模式参数
                      target_distance: float = 5000, distance_tolerance: float = 400, 
                      target_segments: int = 40, segments_tolerance: int = 5, 
                      w1: float = 1.0, w2: float = 0.0, w3: float = 1.0) -> Dict:
    """
    便捷的路径规划函数 - UPDATE: 支持6种约束模式和7种偏好模式（来自modified-3.m）
    
    Args:
        start_lat: 起点纬度
        start_lon: 起点经度
        end_lat: 终点纬度（可选）
        end_lon: 终点经度（可选）
        constraint_mode: 约束模式 (1-6)，模式1：有终点，距离约束；模式2：有终点，路段数约束；模式3：无终点，距离约束；模式4：无终点，路段数约束；模式5：有终点，最短距离；模式6：有终点，最少路段数
        preference_mode: 偏好模式 (1-7)，模式1：综合得分；模式2：滨水路线；模式3：绿化路线；模式4：视野开阔路线；模式5：夜间灯光充足路线；模式6：设施便利路线；模式7：坡度平缓路线
        target_distance: 目标距离(米)
        distance_tolerance: 距离容差
        target_segments: 目标路段数
        segments_tolerance: 路段数容差
        w1: Total权重
        w2: 长度权重
        w3: 路段数权重
        
    Returns:
        包含路径信息的字典
    """
    # 参数设置 - UPDATE: 添加偏好模式
    params = RouteParams(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        constraint_mode=ConstraintMode(constraint_mode),
        preference_mode=PreferenceMode(preference_mode),  # UPDATE: 新增偏好模式
        target_distance=target_distance,
        distance_tolerance=distance_tolerance,
        target_segments=target_segments,
        segments_tolerance=segments_tolerance,
        w1=w1,
        w2=w2,
        w3=w3
    )
    
    # 执行路径规划
    planner = JoggingPathPlanner()
    try:
        planner.connect()
        result = planner.plan_route(params)
        
        return {
            'success': True,
            'path_nodes': result.path_nodes,
            'path_coordinates': result.path_coordinates,
            'total_distance': result.total_distance,
            'total_segments': result.total_segments,
            'total_score': result.total_score,
            'optimization_ratio': result.optimization_ratio,
            'score_per_meter': result.score_per_meter,
            'score_per_segment': result.score_per_segment,
            'geojson': result.geojson,
            # UPDATE: 新增动态约束推荐信息
            'recommended_distances': result.recommended_distances,
            'recommended_segments': result.recommended_segments,
            'distance_range': result.distance_range,
            'segments_range': result.segments_range
        }
    except Exception as e:
        logger.error(f"路径规划失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        planner.disconnect()

def test(test_mode: int = 1):
    """
    路径规划测试
    有3个modes，分别是：
    测试1：滨水路线偏好（偏好模式2）。
    测试2：最短路径模式（约束模式5）。
    测试3：绿化路线偏好，无终点模式（约束模式3，偏好模式3）
    """
    # UPDATE: 示例测试支持新的偏好模式（来自modified-3.m）
    if test_mode == 1:
        print("=== 测试1：路线偏好===")
        result1 = plan_jogging_route(
            start_lat=30.263982,  # 起点纬度
            start_lon=120.1588077, # 起点经度
            end_lat=30.341572,    # 终点纬度（可选）
            end_lon=120.1876803,   # 终点经度（可选）
            constraint_mode=1,    # 模式1：有终点，距离约束
            preference_mode=7,    # UPDATE: 偏好模式7：坡度平缓路线
            target_distance=10000,  # 目标距离10公里
            distance_tolerance=5000,  # 容差5000米
            w1=1.0,             # Total权重
            w2=0.0,             # 长度权重
            w3=1.0              # 路段数权重
        )
        
        if result1['success']:
            print("滨水路线规划成功！")
            print(f"总距离: {result1['total_distance']:.2f}米")
            print(f"总路段数: {result1['total_segments']}")
            print(f"优化比值: {result1['optimization_ratio']:.4f}")
            print(f"每米可慢跑性: {result1['score_per_meter']:.4f}")
            print(f"每段可慢跑性: {result1['score_per_segment']:.4f}")
            # UPDATE: 显示动态约束推荐信息
            if result1['recommended_distances']:
                print(f"推荐距离: {result1['recommended_distances']}")
            if result1['distance_range']:
                print(f"有效距离范围: {result1['distance_range'][0]:.0f} - {result1['distance_range'][1]:.0f}米")
        else:
            print(f"滨水路线规划失败: {result1['error']}")
    if test_mode == 2:
        print("\n=== 测试2：最短路径模式（约束模式5） ===")
        result2 = plan_jogging_route(
            start_lat=30.263982,
            start_lon=120.1588077,
            end_lat=30.341572,
            end_lon=120.1876803,
            constraint_mode=5,    # UPDATE: 模式5：最短距离路径
            preference_mode=3,    # 偏好模式1：综合得分
            w1=1.0,
            w2=0.0,
            w3=1.0
        )
        
        if result2['success']:
            print("最短路径规划成功！")
            print(f"总距离: {result2['total_distance']:.2f}米")
            print(f"总路段数: {result2['total_segments']}")
            print(f"优化比值: {result2['optimization_ratio']:.4f}")
        else:
            print(f"最短路径规划失败: {result2['error']}")
    
    if test_mode == 3:
        print("\n=== 测试3：绿化路线偏好，无终点模式（约束模式3，偏好模式3） ===")
        result3 = plan_jogging_route(
            start_lat=30.263982,
            start_lon=120.1588077,
            constraint_mode=3,    # 模式3：无终点，距离约束
            preference_mode=6,    # UPDATE: 偏好模式6：设施便利路线
            target_distance=7000,  # 目标距离8公里
            distance_tolerance=7000,
            w1=1.0,
            w2=0.0,
            w3=1.0
        )
        
        if result3['success']:
            print("绿化路线规划成功！")
            print(f"总距离: {result3['total_distance']:.2f}米")
            print(f"总路段数: {result3['total_segments']}")
            print(f"优化比值: {result3['optimization_ratio']:.4f}")
            if result3['recommended_distances']:
                print(f"推荐距离: {result3['recommended_distances']}")
        else:
            print(f"绿化路线规划失败: {result3['error']}")


# ================================
# Flask 蓝图 API 部分
# ================================

try:
    from flask import Blueprint, request, jsonify
    import glob
    import time
    
    # 创建蓝图
    route_planning_bp = Blueprint('route_planning', __name__)
    
    @route_planning_bp.route('/api/get_routes', methods=['POST'])
    def get_routes():
        """
        路径规划API端点 - UPDATE: 支持6种约束模式和7种偏好模式（来自modified-3.m）
        接受JSON格式的路径规划请求，返回生成的文件名
        
        请求格式:
        {
            "start_lat": 30.3210982,
            "start_lon": 120.1788077,
            "end_lat": 30.313572,          # 可选（模式1,2,5,6需要）
            "end_lon": 120.1776803,        # 可选（模式1,2,5,6需要）
            "constraint_mode": 1,          # 1-6, 默认1（UPDATE: 扩展到6个模式）
            "preference_mode": 1,          # 1-7, 默认1（UPDATE: 新增偏好模式）
            "target_distance": 6000,       # 目标距离(米), 默认5000
            "distance_tolerance": 500,     # 距离容差, 默认400
            "target_segments": 40,         # 目标路段数, 默认40
            "segments_tolerance": 5,       # 路段数容差, 默认5
            "w1": 1.0,                    # Total权重, 默认1.0
            "w2": 0.0,                    # 长度权重, 默认0.0
            "w3": 1.0                     # 路段数权重, 默认1.0
        }
        
        约束模式说明:
        1: 有终点，距离约束
        2: 有终点，路段数约束
        3: 无终点，距离约束
        4: 无终点，路段数约束
        5: 有终点，最短距离（无约束）
        6: 有终点，最少路段数（无约束）
        
        偏好模式说明:
        1: 综合得分（原Total）
        2: 滨水路线
        3: 绿化路线
        4: 视野开阔路线
        5: 夜间灯光充足路线
        6: 设施便利路线
        7: 坡度平缓路线
        
        响应格式:
        {
            "success": true,
            "filename": "route_2903_to_1104_20250810_152030.json",
            "filepath": "G:/gh_repo/Joy-Run-Smart-Track/backend/temp/route_2903_to_1104_20250810_152030.json",
            "route_info": {
                "total_distance": 6234.56,
                "total_segments": 42,
                "optimization_ratio": 1.2345,
                "score_per_meter": 0.0012,
                "score_per_segment": 15.67,
                "recommended_distances": [5000, 5500, 6000],  # UPDATE: 动态推荐值
                "distance_range": [3200, 8500]                # UPDATE: 有效范围
            }
            }
        }
        """
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': '请求体必须是JSON格式'
                }), 400
            
            # 验证必需参数
            required_params = ['start_lat', 'start_lon']
            for param in required_params:
                if param not in data:
                    return jsonify({
                        'success': False,
                        'error': f'缺少必需参数: {param}'
                    }), 400
            
            # 提取参数，设置默认值 - UPDATE: 添加偏好模式参数
            start_lat = float(data['start_lat'])
            start_lon = float(data['start_lon'])
            end_lat = data.get('end_lat')
            end_lon = data.get('end_lon')
            constraint_mode = int(data.get('constraint_mode', 1))
            preference_mode = int(data.get('preference_mode', 1))  # UPDATE: 新增偏好模式，默认为1
            target_distance = float(data.get('target_distance', 5000))
            distance_tolerance = float(data.get('distance_tolerance', 400))
            target_segments = int(data.get('target_segments', 40))
            segments_tolerance = int(data.get('segments_tolerance', 5))
            w1 = float(data.get('w1', 1.0))
            w2 = float(data.get('w2', 0.0))
            w3 = float(data.get('w3', 1.0))
            
            # 转换 end_lat 和 end_lon 为 float 或 None
            if end_lat is not None:
                end_lat = float(end_lat)
            if end_lon is not None:
                end_lon = float(end_lon)
            
            # UPDATE: 参数验证扩展到6种约束模式和7种偏好模式
            if constraint_mode not in range(1, 7):
                return jsonify({
                    'success': False,
                    'error': 'constraint_mode必须在1-6之间'
                }), 400
                
            if preference_mode not in range(1, 8):
                return jsonify({
                    'success': False,
                    'error': 'preference_mode必须在1-7之间'
                }), 400
            
            # 执行路径规划
            logger.info(f"API请求路径规划: start=({start_lat}, {start_lon}), end=({end_lat}, {end_lon}), constraint_mode={constraint_mode}, preference_mode={preference_mode}")
            
            result = plan_jogging_route(
                start_lat=start_lat,
                start_lon=start_lon,
                end_lat=end_lat,
                end_lon=end_lon,
                constraint_mode=constraint_mode,
                preference_mode=preference_mode,  # UPDATE: 添加偏好模式参数
                target_distance=target_distance,
                distance_tolerance=distance_tolerance,
                target_segments=target_segments,
                segments_tolerance=segments_tolerance,
                w1=w1,
                w2=w2,
                w3=w3
            )
            
            if result['success']:
                # 从temp目录获取最新生成的路径文件
                config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.yaml'))
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                temp_folder = config.get('route_planning_temp_folder', 'G:/gh_repo/Joy-Run-Smart-Track/backend/temp')
                
                # 获取最近5分钟内生成的路径文件
                current_time = time.time()
                pattern = os.path.join(temp_folder, 'route_*.json')
                recent_files = []
                
                for file in glob.glob(pattern):
                    if os.path.getctime(file) > current_time - 300:  # 5分钟内
                        recent_files.append(file)
                
                if recent_files:
                    # 获取最新的文件
                    latest_file = max(recent_files, key=os.path.getctime)
                    filename = os.path.basename(latest_file)
                    filepath = latest_file
                else:
                    # 如果没有找到最新文件，使用默认命名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'route_generated_{timestamp}.json'
                    filepath = os.path.join(temp_folder, filename)
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'filepath': filepath,
                    'route_info': {
                        'total_distance': result['total_distance'],
                        'total_segments': result['total_segments'],
                        'optimization_ratio': result['optimization_ratio'],
                        'score_per_meter': result['score_per_meter'],
                        'score_per_segment': result['score_per_segment']
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 500
                
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'参数格式错误: {str(e)}'
            }), 400
        except Exception as e:
            logger.error(f"API路径规划失败: {e}")
            return jsonify({
                'success': False,
                'error': f'服务器内部错误: {str(e)}'
            }), 500
    
    @route_planning_bp.route('/api/get_routes/health', methods=['GET'])
    def health_check():
        """健康检查端点"""
        return jsonify({
            'status': 'healthy',
            'service': 'route_planning',
            'timestamp': datetime.now().isoformat()
        })
    
    @route_planning_bp.route('/api/get_routes/help', methods=['GET'])
    def api_help():
        """API帮助文档"""
        return jsonify({
            'endpoint': '/api/get_routes',
            'method': 'POST',
            'description': '智能慢跑路径规划API',
            'required_parameters': {
                'start_lat': 'float - 起点纬度',
                'start_lon': 'float - 起点经度'
            },
            'optional_parameters': {
                'end_lat': 'float - 终点纬度（可选）',
                'end_lon': 'float - 终点经度（可选）',
                'constraint_mode': 'int - 约束模式 (1-4)，默认1',
                'target_distance': 'float - 目标距离(米)，默认5000',
                'distance_tolerance': 'float - 距离容差，默认400',
                'target_segments': 'int - 目标路段数，默认40',
                'segments_tolerance': 'int - 路段数容差，默认5',
                'w1': 'float - Total权重，默认1.0',
                'w2': 'float - 长度权重，默认0.0',
                'w3': 'float - 路段数权重，默认1.0'
            },
            'constraint_modes': {
                '1': '有终点，距离约束',
                '2': '有终点，路段数约束',
                '3': '无终点，距离约束',
                '4': '无终点，路段数约束'
            }
        })

except ImportError:
    # 如果没有安装Flask，定义一个虚拟的蓝图对象
    logger.info("Flask未安装，跳过API功能")
    route_planning_bp = None


# 使用示例
if __name__ == "__main__":
   test(3)