from flask import Blueprint, jsonify, request, send_file
import psycopg2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io
import random
import os
import time
from scipy.sparse import csr_matrix
from collections import deque
import matplotlib.patches as mpatches
import matplotlib
import yaml
import json
from datetime import datetime

routeplanning_bp = Blueprint('routeplanning', __name__)
# 设置matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
matplotlib.use('Agg')

# 加载配置
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {"route_planning_temp_folder": "./temp"}

# 确保临时文件夹存在
def ensure_temp_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'joy_run_db',
    'user': 'postgres',
    'password': 'postgres1'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def fetch_road_network():
    """从数据库获取路网数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取边数据
    cursor.execute("""
        SELECT id, startx, starty, endx, endy, distance, score, total, dis_ori, 
               toatl_ori1, source, target
        FROM edges
    """)
    edges_data = cursor.fetchall()
    
    # 获取节点数据
    cursor.execute("SELECT id, x, y FROM nodes")
    nodes_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # 转换为DataFrame
    edges_df = pd.DataFrame(edges_data, columns=[
        'id', 'startx', 'starty', 'endx', 'endy', 'distance', 'score', 
        'total', 'dis_ori', 'toatl_ori1', 'source', 'target'
    ])
    
    nodes_df = pd.DataFrame(nodes_data, columns=['id', 'x', 'y'])
    
    return edges_df, nodes_df

def dijkstra_single_source(dist_mat, start_node):
    """单源Dijkstra算法"""
    num_nodes = dist_mat.shape[0]
    dist = np.full(num_nodes, np.inf)
    prev = np.zeros(num_nodes, dtype=int)
    visited = np.zeros(num_nodes, dtype=bool)
    
    dist[start_node] = 0
    
    for _ in range(num_nodes):
        # 找最小未访问节点
        min_dist = np.inf
        u = -1
        for j in range(num_nodes):
            if not visited[j] and dist[j] < min_dist:
                min_dist = dist[j]
                u = j
        
        if u == -1:
            break  # 所有连通点都找完了
        
        visited[u] = True
        
        for v in range(num_nodes):
            if dist_mat[u, v] < np.inf and not visited[v]:
                alt = dist[u] + dist_mat[u, v]
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
    
    return dist, prev

def dijkstra(dist_mat, start_node, end_node):
    """优化的Dijkstra算法（使用优先队列）"""
    import heapq
    
    num_nodes = dist_mat.shape[0]
    dist = np.full(num_nodes, np.inf)
    prev = np.zeros(num_nodes, dtype=int)
    dist[start_node] = 0
    
    # 优先队列存储(距离,节点)对
    pq = [(0, start_node)]
    
    while pq:
        d, u = heapq.heappop(pq)
        
        # 如果已找到终点或者弹出的距离大于已知距离，跳过
        if u == end_node or d > dist[u]:
            continue
        
        # 只检查有边相连的节点，而不是所有节点
        neighbors = np.where(dist_mat[u, :] < np.inf)[0]
        for v in neighbors:
            alt = dist[u] + dist_mat[u, v]
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                heapq.heappush(pq, (alt, v))
    
    if dist[end_node] == np.inf:
        raise ValueError('终点不可达')
    
    shortest_path = [end_node]
    while shortest_path[0] != start_node:
        shortest_path.insert(0, prev[shortest_path[0]])
    
    return shortest_path, dist[end_node]

def bfs_pathword(adj_mat, start_node, end_node):
    """BFS求起点到终点的最小路段数"""
    num_nodes = adj_mat.shape[0]
    path_word = np.full(num_nodes, np.inf)
    prev = np.zeros(num_nodes, dtype=int)
    visited = np.zeros(num_nodes, dtype=bool)
    
    queue = deque([start_node])
    path_word[start_node] = 0
    visited[start_node] = True
    
    while queue:
        current_node = queue.popleft()
        
        if current_node == end_node:
            break
        
        neighbors = np.where(adj_mat[current_node, :] > 0)[0]
        for neighbor in neighbors:
            if not visited[neighbor]:
                path_word[neighbor] = path_word[current_node] + 1
                prev[neighbor] = current_node
                visited[neighbor] = True
                queue.append(neighbor)
    
    if path_word[end_node] == np.inf:
        return np.inf, []
    
    # 回溯路径
    shortest_path = [end_node]
    while shortest_path[0] != start_node:
        shortest_path.insert(0, prev[shortest_path[0]])
    
    return path_word[end_node], shortest_path

def bfs_all_pathwords(adj_mat, start_node):
    """BFS求单源到所有节点的最小路段数"""
    num_nodes = adj_mat.shape[0]
    path_words = np.full(num_nodes, np.inf)
    visited = np.zeros(num_nodes, dtype=bool)
    
    queue = deque([start_node])
    path_words[start_node] = 0
    visited[start_node] = True
    
    while queue:
        current_node = queue.popleft()
        
        neighbors = np.where(adj_mat[current_node, :] > 0)[0]
        for neighbor in neighbors:
            if not visited[neighbor]:
                path_words[neighbor] = path_words[current_node] + 1
                visited[neighbor] = True
                queue.append(neighbor)
    
    return path_words

def ant_colony_optimization(start_node, end_node, num_ants=20, max_iter=80, 
                            min_path_length=10000, max_path_length=11000,
                            min_path_word=50, max_path_word=60, w0=0, w1=1, w2=0, w3=1,
                            dij=0, bfs=0, limit=0, max_time=30):
    """蚁群算法主函数"""
    # 获取路网数据
    data, _ = fetch_road_network()
    
    # 参数设置
    alpha = None  # 信息素重要程度
    beta = 1      # 启发因子重要程度
    rho = 0.3     # 信息素挥发率
    lambda_val = 0.98
    rho_min = 0.05
    
    # 权重检查和调整
    if w1 != 1 and w1 != 0:
        raise ValueError("w1 要等于0或1")
    
    if (w2 == 0 and w3 == 0) or (w2 != 0 and w3 != 0):
        raise ValueError("w2 和 w3 必须有一个为零，另一个为非零")
    
    # 信息素权重调整
    if w2 != 0 and w3 == 0 and w1 == 1:
        alpha = 6.5
    elif w3 != 0 and w2 == 0 and w1 == 1:
        alpha = 2.5
    elif w1 == 0:
        alpha = 2.5
        rho = 0.1
    
    # 提取数据
    start_x = data['startx'].values
    start_y = data['starty'].values
    end_x = data['endx'].values
    end_y = data['endy'].values
    
    if w0 == 1 or w0 == 0:
        distance = data['distance'].values
    elif w0 == 2:
        distance = data['dij_w1'].values
        print('先前的"道路长度"的分母部分替换为为"道路得分取反"')
    
    score = data['score'].values
    
    if w0 == 1:
        total = data['score'].values
        print('分子为"道路得分"')
    elif w0 == 0:
        if w1 == 1:
            total = data['total'].values
            if w2 == 0:
                c = 'b'
                print('模式b')
            elif w3 == 0:
                c = 'a'
                print('模式a')
        elif w1 == 0:
            if w2 == 0:
                total = np.ones_like(data['total'].values)
                print('模式d')
            elif w3 == 0:
                total = 1.0 / data['distance'].values
                print('模式c')
    elif w0 == 2:
        total = data['total'].values
        print('分子默认为1')
    
    distance_real = data['dis_ori'].values
    total_real = data['toatl_ori1'].values
    
    # 构建节点列表和邻接矩阵
    all_nodes = np.vstack((np.column_stack((start_x, start_y)), np.column_stack((end_x, end_y))))
    unique_nodes, inverse = np.unique(all_nodes, axis=0, return_inverse=True)
    num_nodes = len(unique_nodes)
    
    adj_mat = np.zeros((num_nodes, num_nodes))
    score_mat = np.zeros((num_nodes, num_nodes))
    total_mat = np.zeros((num_nodes, num_nodes))
    adj_mat_real = np.zeros((num_nodes, num_nodes))
    total_mat_real = np.zeros((num_nodes, num_nodes))
    
    for i in range(len(data)):
        start_idx = np.where(np.all(unique_nodes == [start_x[i], start_y[i]], axis=1))[0][0]
        end_idx = np.where(np.all(unique_nodes == [end_x[i], end_y[i]], axis=1))[0][0]
        
        adj_mat[start_idx, end_idx] = distance[i]
        adj_mat[end_idx, start_idx] = distance[i]  # 双向道路
        
        adj_mat_real[start_idx, end_idx] = distance_real[i]
        adj_mat_real[end_idx, start_idx] = distance_real[i]
        
        score_mat[start_idx, end_idx] = score[i]
        score_mat[end_idx, start_idx] = score[i]
        
        total_mat[start_idx, end_idx] = total[i]
        total_mat[end_idx, start_idx] = total[i]
        
        total_mat_real[start_idx, end_idx] = total_real[i]
        total_mat_real[end_idx, start_idx] = total_real[i]
    
    # 计算平均值
    total_mean = np.mean(total)
    dis_mean = np.mean(distance)
    
    # 迭代剔除度为1的节点
    has_nodes_to_remove = True
    iteration = 0
    
    while has_nodes_to_remove:
        # 计算节点度数
        degree = np.sum(adj_mat != 0, axis=1)
        nodes_to_remove = np.where(degree == 1)[0]
        
        if len(nodes_to_remove) == 0:
            has_nodes_to_remove = False
            print(f'迭代完成，共执行 {iteration} 次剔除')
            break
        else:
            iteration += 1
            print(f'第{iteration}次迭代：发现{len(nodes_to_remove)}个度数为1的节点')
        
        # 更新保留节点索引
        remaining_nodes = np.setdiff1d(np.arange(unique_nodes.shape[0]), nodes_to_remove)
        
        # 动态更新所有矩阵
        unique_nodes = unique_nodes[remaining_nodes]
        adj_mat = adj_mat[np.ix_(remaining_nodes, remaining_nodes)]
        score_mat = score_mat[np.ix_(remaining_nodes, remaining_nodes)]
        total_mat = total_mat[np.ix_(remaining_nodes, remaining_nodes)]
        adj_mat_real = adj_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        total_mat_real = total_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        num_nodes = len(unique_nodes)
    
    # 计算有效距离矩阵
    dist_mat = adj_mat.copy()
    dist_mat[adj_mat == 0] = np.inf
    dist_mat[dist_mat == 0] = np.finfo(float).eps  # 避免除以零
    
    dist_mat_real = adj_mat_real.copy()
    dist_mat_real[adj_mat_real == 0] = np.inf
    dist_mat_real[dist_mat_real == 0] = np.finfo(float).eps
    
    # 确保终点与起点不同
    while end_node == start_node:
        end_node = np.random.randint(0, num_nodes)
    
    print(f'起点: 节点 {start_node}, 终点: 节点 {end_node}')
    
    # 路径约束预处理
    if dij == 1:
        print('正在使用dijkstra计算路径长度约束...')
        
        # 保存原始起点终点坐标
        start_coord = unique_nodes[start_node]
        end_coord = unique_nodes[end_node]
        
        # 单源Dijkstra
        start_to_all_dist, _ = dijkstra_single_source(dist_mat_real, start_node)
        end_to_all_dist, _ = dijkstra_single_source(dist_mat_real, end_node)
        
        # 节点筛选
        valid_node_mask = (start_to_all_dist + end_to_all_dist) <= max_path_length
        
        # 强制保留起点和终点
        valid_node_mask[start_node] = True
        valid_node_mask[end_node] = True
        
        remaining_nodes = np.where(valid_node_mask)[0]
        
        # 更新所有矩阵
        unique_nodes = unique_nodes[remaining_nodes]
        adj_mat = adj_mat[np.ix_(remaining_nodes, remaining_nodes)]
        score_mat = score_mat[np.ix_(remaining_nodes, remaining_nodes)]
        total_mat = total_mat[np.ix_(remaining_nodes, remaining_nodes)]
        dist_mat = dist_mat[np.ix_(remaining_nodes, remaining_nodes)]
        dist_mat_real = dist_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        adj_mat_real = adj_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        total_mat_real = total_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        num_nodes = len(unique_nodes)
        
        # 重新定位起点和终点
        start_node = np.where(np.all(unique_nodes == start_coord, axis=1))[0][0]
        end_node = np.where(np.all(unique_nodes == end_coord, axis=1))[0][0]
        
        # 计算最短路径
        shortest_path, min_dist = dijkstra(dist_mat_real, start_node, end_node)
        
        # 检查最短路径是否满足约束
        if min_path_length < min_dist:
            raise ValueError('设置的距离范围下限小于最短距离')
    
    if bfs == 1:
        print('正在使用BFS计算路段数约束...')
        
        # 保存原始起点终点坐标
        start_coord = unique_nodes[start_node]
        end_coord = unique_nodes[end_node]
        
        # BFS计算
        start_to_all_path_words = bfs_all_pathwords(adj_mat_real, start_node)
        end_to_all_path_words = bfs_all_pathwords(adj_mat_real, end_node)
        
        # 路段数约束判断
        valid_node_mask = (start_to_all_path_words + end_to_all_path_words) <= max_path_word
        
        remaining_nodes = np.where(valid_node_mask)[0]
        
        # 更新所有矩阵
        unique_nodes = unique_nodes[remaining_nodes]
        adj_mat = adj_mat[np.ix_(remaining_nodes, remaining_nodes)]
        score_mat = score_mat[np.ix_(remaining_nodes, remaining_nodes)]
        total_mat = total_mat[np.ix_(remaining_nodes, remaining_nodes)]
        dist_mat = dist_mat[np.ix_(remaining_nodes, remaining_nodes)]
        dist_mat_real = dist_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        adj_mat_real = adj_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        total_mat_real = total_mat_real[np.ix_(remaining_nodes, remaining_nodes)]
        num_nodes = len(unique_nodes)
        
        # 重新定位起点和终点
        start_node = np.where(np.all(unique_nodes == start_coord, axis=1))[0][0]
        end_node = np.where(np.all(unique_nodes == end_coord, axis=1))[0][0]
        
        # 检查最小路段数
        path_word, shortest_path = bfs_pathword(adj_mat, start_node, end_node)
        
        if path_word > max_path_word:
            raise ValueError('最小路段数大于允许上限，无法继续')
    
    # 初始化信息素矩阵
    pheromone = np.zeros((num_nodes, num_nodes))
    for i in range(num_nodes):
        for j in range(num_nodes):
            if adj_mat[i, j] > 0:
                pheromone[i, j] = 1
    
    # 算法初始化
    best_path = []
    best_score_path_ratio = -np.inf
    iter_best_score_path_ratio = np.zeros(max_iter)
    iter_best_dist = np.zeros(max_iter)
    iter_best_scores = np.zeros(max_iter)
    iter_best_total = np.zeros(max_iter)
    iter_best_pathword = np.zeros(max_iter)
    iter_avr_pathscore = np.zeros(max_iter)
    all_best_dist = np.zeros(max_iter)
    all_best_scores = np.zeros(max_iter)
    all_best_score_path_ratio = np.zeros(max_iter)
    all_best_total = np.zeros(max_iter)
    all_best_pathword = np.zeros(max_iter)
    all_avr_pathscore = np.zeros(max_iter)
    all_avr_disscore = np.zeros(max_iter)
    all_best_dist_real = np.zeros(max_iter)
    no_improve_count = 0
    early_stop_flag = False
    
    # 主循环
    for iter in range(max_iter):
        rho = max(lambda_val * rho, rho_min)  # 动态降低rho
        ants_paths = [None] * num_ants
        ants_dist = np.full(num_ants, np.inf)
        ants_scores = np.zeros(num_ants)
        ants_total = np.zeros(num_ants)
        pathword = np.zeros(num_ants)
        total_divide_path = np.zeros(num_ants)
        avr_pathscore = np.zeros(num_ants)
        avr_disscore = np.zeros(num_ants)
        ants_total_real = np.zeros(num_ants)
        ants_dist_real = np.full(num_ants, np.inf)
        
        print(f'\n------ 第 {iter+1} 次迭代 ------')
        
        # 每只蚂蚁的路径选择
        for k in range(num_ants):
            valid_path = False
            attempts = 0
            max_attempts = 100
            
            while not valid_path and attempts < max_attempts:
                try:
                    current_node = start_node
                    visited = [current_node]
                    path = [current_node]
                    temp_barriers = []
                    backoff_steps = 0
                    max_backoff = 50
                    total_score = 0
                    total_total = 0
                    total_dist = 0
                    path_calcul = 0
                    total_total_real = 0
                    total_dist_real = 0
                    
                    while current_node != end_node:
                        neighbors = np.where(adj_mat[current_node, :] > 0)[0]
                        reachable = np.setdiff1d(neighbors, np.concatenate((visited, temp_barriers)))
                        
                        if len(reachable) == 0:
                            if len(path) == 1 or backoff_steps > max_backoff:
                                raise ValueError('无法回退，重新构建路径')
                            
                            # 回退
                            temp_barriers.append(current_node)
                            prev_node = path[-2]
                            
                            # 扣除路径累计值
                            total_score -= score_mat[prev_node, current_node]
                            total_total -= total_mat[prev_node, current_node]
                            total_dist -= dist_mat[prev_node, current_node]
                            total_total_real -= total_mat_real[prev_node, current_node]
                            total_dist_real -= dist_mat_real[prev_node, current_node]
                            path_calcul -= 1
                            
                            path.pop()
                            current_node = prev_node
                            backoff_steps += 1
                            continue
                        
                        # 正常转移
                        if len(reachable) == 1:
                            next_node = reachable[0]
                        else:
                            probabilities = (pheromone[current_node, reachable]**alpha) * (total_mat[current_node, reachable]**beta)
                            probabilities = probabilities / np.sum(probabilities)
                            next_node = np.random.choice(reachable, p=probabilities)
                        
                        # 记录
                        prev_node = current_node
                        path.append(next_node)
                        visited.append(next_node)
                        total_score += score_mat[prev_node, next_node]
                        total_total += total_mat[prev_node, next_node]
                        total_dist += dist_mat[prev_node, next_node]
                        total_total_real += total_mat_real[prev_node, next_node]
                        total_dist_real += dist_mat_real[prev_node, next_node]
                        path_calcul += 1
                        
                        # 走一步就判断约束
                        if dij == 1:
                            if total_dist_real > max_path_length or (total_dist_real < min_path_length and next_node == end_node):
                                temp_barriers.append(next_node)
                                total_score -= score_mat[prev_node, next_node]
                                total_total -= total_mat[prev_node, next_node]
                                total_dist -= dist_mat[prev_node, next_node]
                                total_total_real -= total_mat_real[prev_node, next_node]
                                total_dist_real -= dist_mat_real[prev_node, next_node]
                                path_calcul -= 1
                                
                                path.pop()
                                current_node = prev_node
                                backoff_steps += 1
                                continue
                        elif bfs == 1:
                            if path_calcul > max_path_word or (path_calcul < min_path_word and next_node == end_node):
                                temp_barriers.append(next_node)
                                total_score -= score_mat[prev_node, next_node]
                                total_total -= total_mat[prev_node, next_node]
                                total_dist -= dist_mat[prev_node, next_node]
                                total_total_real -= total_mat_real[prev_node, next_node]
                                total_dist_real -= dist_mat_real[prev_node, next_node]
                                path_calcul -= 1
                                
                                path.pop()
                                current_node = prev_node
                                backoff_steps += 1
                                continue
                        
                        # 正常前进
                        current_node = next_node
                        backoff_steps = 0  # 成功前进就重置
                    
                    # 到终点后额外校验约束
                    if dij == 1:
                        if total_dist_real >= min_path_length and total_dist_real <= max_path_length:
                            valid_path = True
                        else:
                            raise ValueError('路径长度不符合约束')
                    elif bfs == 1:
                        if path_calcul >= min_path_word and path_calcul <= max_path_word:
                            valid_path = True
                        else:
                            raise ValueError('路段数不符合约束')
                    else:
                        valid_path = True
                
                except Exception as e:
                    attempts += 1
                    continue
            
            if not valid_path:
                print(f"蚂蚁 {k}: 在 {max_attempts} 次尝试后仍未找到有效路径")
                continue
            
            # 记录结果
            ants_paths[k] = path
            ants_dist[k] = total_dist
            ants_scores[k] = total_score
            ants_total[k] = total_total
            pathword[k] = path_calcul
            ants_total_real[k] = total_total_real
            ants_dist_real[k] = total_dist_real
            
            avr_disscore[k] = ants_total[k] / ants_dist[k]
            avr_pathscore[k] = ants_total[k] / pathword[k]
            
            if w1 == 0:
                if w2 > 0:
                    total_divide_path[k] = 1/ants_dist[k]
                else:
                    total_divide_path[k] = 1/pathword[k]
            else:  # w1 > 0
                if w2 > 0:
                    total_divide_path[k] = (ants_total[k]**w1)/(ants_dist[k]**w2)
                else:
                    total_divide_path[k] = (ants_total[k]**w1)/(pathword[k]**w3)
            
            print(f'蚂蚁 {k}: 路径长度（标准化后）= {ants_dist[k]:.2f}, 路径长度（标准化前）= {ants_dist_real[k]:.2f}, 总得分 = {ants_scores[k]:.2f}, 慢跑可持续性（标准化后）= {ants_total[k]:.2f}, 慢跑可持续性（标准化前）= {ants_total_real[k]:.2f}, 总路段数 = {pathword[k]:.2f}, joggability = {total_divide_path[k]:.2f}')
        
        # 更新最优路径
        valid_ants = np.where(~np.isinf(ants_dist))[0]
        if len(valid_ants) == 0:
            print("本次迭代没有找到有效路径，跳过更新")
            continue
            
        ants_score_path_ratio = total_divide_path[valid_ants]
        
        # 找到得分与道路数量比值最大的蚂蚁
        max_score_path_ratio_idx = np.argmax(ants_score_path_ratio)
        max_score_path_ratio = ants_score_path_ratio[max_score_path_ratio_idx]
        idx = valid_ants[max_score_path_ratio_idx]
        
        iter_best_score_path_ratio[iter] = max_score_path_ratio
        iter_best_scores[iter] = ants_scores[idx]
        iter_best_dist[iter] = ants_dist[idx]
        iter_best_total[iter] = ants_total[idx]
        iter_best_pathword[iter] = pathword[idx]
        iter_best_path = ants_paths[idx]
        iter_avr_pathscore[iter] = avr_pathscore[idx]
        
        print(f'迭代 {iter+1}: 当前迭代最优joggability = {max_score_path_ratio:.4f}, 最优路径的得分 = {iter_best_scores[iter]:.2f}, 最优路径的长度 = {iter_best_dist[iter]:.2f}, 最优路径的Total = {iter_best_total[iter]:.2f}, 最优路径的路段数 = {iter_best_pathword[iter]:.2f}, 平均道路得分 = {iter_avr_pathscore[iter]:.2f}')
        
        # 更新全局最优
        if max_score_path_ratio > best_score_path_ratio:
            best_score_path_ratio = max_score_path_ratio
            best_path = ants_paths[idx].copy()
            best_scores = ants_scores[idx]
            best_dist = ants_dist[idx]
            best_total = ants_total[idx]
            best_pathword = pathword[idx]
            best_avr_pathscore = avr_pathscore[idx]
            best_avr_disscore = avr_disscore[idx]
            best_dist_real = ants_dist_real[idx]
        
        all_best_score_path_ratio[iter] = best_score_path_ratio
        all_best_scores[iter] = best_scores
        all_best_dist[iter] = best_dist
        all_best_total[iter] = best_total
        all_best_pathword[iter] = best_pathword
        all_avr_pathscore[iter] = best_avr_pathscore
        all_avr_disscore[iter] = best_avr_disscore
        all_best_dist_real[iter] = best_dist_real
        
        # 信息素更新
        pheromone = (1 - rho) * pheromone
        
        # 标记最优路径的边
        path_edges = np.zeros_like(pheromone, dtype=bool)
        for i in range(len(best_path)-1):
            from_node = best_path[i]
            to_node = best_path[i+1]
            path_edges[from_node, to_node] = True
        
        # 更新最优路径上的信息素
        for i in range(len(best_path)-1):
            from_node = best_path[i]
            to_node = best_path[i+1]
            original = pheromone[from_node, to_node]
            
            if w2 == 0:
                if w1 == 1:
                    delta = all_avr_pathscore[iter] / total_mean
                    pheromone[from_node, to_node] += delta
                    print(f'1信息素增加{delta:.4f}，该道路原始信息素为{original:.4f}，更新后为{pheromone[from_node, to_node]:.4f}')
                elif w1 == 0:
                    delta = 1 * all_best_score_path_ratio[iter]
                    pheromone[from_node, to_node] += delta
                    print(f'2信息素增加{delta:.4f}，该道路原始信息素为{original:.4f}，更新后为{pheromone[from_node, to_node]:.4f}')
            elif w3 == 0:
                if w1 == 1:
                    delta = (dis_mean * all_avr_disscore[iter]) / total_mean
                    pheromone[from_node, to_node] += delta
                    print(f'3信息素增加{delta:.4f}，该道路原始信息素为{original:.4f}，更新后为{pheromone[from_node, to_node]:.4f}')
                elif w1 == 0:
                    delta = 1 * all_best_score_path_ratio[iter]
                    pheromone[from_node, to_node] += delta
                    print(f'4信息素增加{delta:.4f}，该道路原始信息素为{original:.4f}，更新后为{pheromone[from_node, to_node]:.4f}')
        
        if w1 == 1:
            # 对非最优路径上的路段增加基础信息素
            # for from_node in range(pheromone.shape[0]):
            #     for to_node in range(pheromone.shape[1]):
            #         if not path_edges[from_node, to_node] and pheromone[from_node, to_node] > 0:
            #             pheromone[from_node, to_node] += 1
            mask = (~path_edges) & (pheromone > 0)
            pheromone[mask] += 1
        
        # 状态输出
        print(f'迭代 {iter+1}: 信息素范围 = [{np.min(pheromone[pheromone>0]):.5f}, {np.max(pheromone):.5f}], total范围 = [{np.min(total_mat[total_mat>0]):.5f}, {np.max(total_mat):.5f}], total平均值 = {total_mean:.2f}, distance平均值 = {dis_mean:.2f}, 此时rho = {rho:.2f}, 此时alpha = {alpha:.2f}')
        print('===================================================================================')
        print(f'迭代 {iter+1}: 全局平均每段道路可慢跑持续性 = {all_avr_pathscore[iter]:.4f}, 全局平均每米可慢跑持续性 = {all_avr_disscore[iter]:.4f}, 当前全局joggability = {all_best_score_path_ratio[iter]:.6f}, 全局最优路径的总得分 = {all_best_scores[iter]:.4f}, \n 全局最优路径的总长度（标准化后）= {all_best_dist[iter]:.4f}, 全局最优路径的总长度（标准化前）= {all_best_dist_real[iter]:.4f}, 全局最优路径的总可慢跑持续得分 = {all_best_total[iter]:.4f}, 全局最优路径的总路段数 = {all_best_pathword[iter]:.2f}')
        
        # 早停条件判断
        if limit == 1 and iter >= 1:
            if abs(all_best_score_path_ratio[iter] - all_best_score_path_ratio[iter-1]) < 1e-6:
                no_improve_count += 1
            else:
                no_improve_count = 0
            
            if no_improve_count >= max_time:
                print(f'连续{max_time}次迭代未改进最优值，提前终止迭代！')
                early_stop_flag = True
                break
    
    # 绘制结果
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 绘制路网
    for i in range(num_nodes):
        for j in range(i+1, num_nodes):
            if adj_mat[i, j] > 0:
                ax.plot([unique_nodes[i, 0], unique_nodes[j, 0]], 
                        [unique_nodes[i, 1], unique_nodes[j, 1]], 'k-', alpha=0.2)
    
    # 绘制最优路径
    for i in range(len(best_path)-1):
        from_node = best_path[i]
        to_node = best_path[i+1]
        ax.plot([unique_nodes[from_node, 0], unique_nodes[to_node, 0]], 
                [unique_nodes[from_node, 1], unique_nodes[to_node, 1]], 'r-', linewidth=2)
    
    # 标记起点和终点
    ax.scatter(unique_nodes[start_node, 0], unique_nodes[start_node, 1], color='g', s=100, zorder=5)
    ax.scatter(unique_nodes[end_node, 0], unique_nodes[end_node, 1], color='r', s=100, zorder=5)
    
    # 添加图例
    start_patch = mpatches.Patch(color='g', label='起点')
    end_patch = mpatches.Patch(color='r', label='终点')
    path_patch = mpatches.Patch(color='r', label=f'最优路径 (joggability: {best_score_path_ratio:.4f})')
    
    ax.legend(handles=[start_patch, end_patch, path_patch], loc='upper right')
    
    # 设置标题和标签
    ax.set_title(f'蚁群算法优化路径 (总长度: {best_dist_real:.2f}m, 路段数: {best_pathword:.0f})', fontsize=14)
    ax.set_xlabel('X坐标', fontsize=12)
    ax.set_ylabel('Y坐标', fontsize=12)
    ax.set_aspect('equal')
    
    # 绘制收敛曲线
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    iterations = np.arange(1, iter+2)
    ax2.plot(iterations, all_best_score_path_ratio[:iter+1], 'b-', linewidth=1.5)
    ax2.set_title('收敛曲线', fontsize=14)
    ax2.set_xlabel('迭代次数', fontsize=12)
    ax2.set_ylabel('joggability', fontsize=12)
    ax2.grid(True)
    
    # 返回结果
    result = {
        'best_path': best_path,
        'best_score_path_ratio': best_score_path_ratio,
        'best_dist': best_dist,
        'best_dist_real': best_dist_real,
        'best_pathword': best_pathword,
        'best_total': best_total,
        'node_coords': unique_nodes,
        'convergence': all_best_score_path_ratio[:iter+1].tolist(),
        'figures': [fig, fig2],
        'adj_mat': adj_mat
    }
    
    return result

# 自定义JSON编码器处理NumPy类型
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

@routeplanning_bp.route('/plan_route', methods=['POST'])
def plan_route():
    """API接口：规划路线"""
    try:
        data = request.get_json()
        start_node = data.get('start_node', 2903)
        end_node = data.get('end_node', 1104)
        
        # 可选参数
        params = {
            'num_ants': data.get('num_ants', 20),
            'max_iter': data.get('max_iter', 80),
            'min_path_length': data.get('min_path_length', 10000),
            'max_path_length': data.get('max_path_length', 11000),
            'min_path_word': data.get('min_path_word', 50),
            'max_path_word': data.get('max_path_word', 60),
            'w0': data.get('w0', 0),
            'w1': data.get('w1', 1),
            'w2': data.get('w2', 0),
            'w3': data.get('w3', 1),
            'dij': data.get('dij', 0),
            'bfs': data.get('bfs', 0),
        }
        
        result = ant_colony_optimization(start_node, end_node, **params)
        
        # 加载配置获取临时文件夹路径
        config = load_config()
        temp_folder = config.get('route_planning_temp_folder', './temp')
        temp_folder = ensure_temp_folder(temp_folder)

        # 生成时间戳作为文件名的一部分
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存结果为JSON文件
        result_data = {
            'start_node': start_node,
            'end_node': end_node,
            'best_path': result['best_path'],
            'best_score': float(result['best_score_path_ratio']),
            'path_length': float(result['best_dist_real']),
            'path_segments': int(result['best_pathword']),
            'parameters': params
        }
        
        json_path = os.path.join(temp_folder, f'route_{start_node}_to_{end_node}_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(result_data, json_file, ensure_ascii=False, indent=4, cls=NumpyEncoder)
        
        print(f"路径规划结果已保存至: {json_path}")
        
        # 绘制路网图并保存
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 绘制路网
        for i in range(len(result['node_coords'])):
            for j in range(i+1, len(result['node_coords'])):
                if result['adj_mat'][i, j] > 0:  # 使用 result['adj_mat'] 而不是 adj_mat
                    ax.plot([result['node_coords'][i, 0], result['node_coords'][j, 0]], 
                            [result['node_coords'][i, 1], result['node_coords'][j, 1]], 'k-', alpha=0.2)
         # 绘制最优路径
        for i in range(len(result['best_path'])-1):
            from_node = result['best_path'][i]
            to_node = result['best_path'][i+1]
            ax.plot([result['node_coords'][from_node, 0], result['node_coords'][to_node, 0]], 
                    [result['node_coords'][from_node, 1], result['node_coords'][to_node, 1]], 'r-', linewidth=2)
        
        # 标记起点和终点
        ax.scatter(result['node_coords'][start_node, 0], result['node_coords'][start_node, 1], 
                   color='g', s=100, zorder=5)
        ax.scatter(result['node_coords'][end_node, 0], result['node_coords'][end_node, 1], 
                   color='r', s=100, zorder=5)
        
        # 添加图例（确保中文显示）
        start_patch = mpatches.Patch(color='g', label='起点')
        end_patch = mpatches.Patch(color='r', label='终点')
        path_patch = mpatches.Patch(color='r', label=f'最优路径 (joggability: {result["best_score_path_ratio"]:.4f})')
        
        ax.legend(handles=[start_patch, end_patch, path_patch], loc='upper right')
        
        # 设置标题和标签（中文）
        ax.set_title(f'蚁群算法优化路径 (总长度: {result["best_dist_real"]:.2f}m, 路段数: {result["best_pathword"]:.0f})', 
                    fontsize=14)
        ax.set_xlabel('X坐标 (经度)', fontsize=12)
        ax.set_ylabel('Y坐标 (纬度)', fontsize=12)
        ax.set_aspect('equal')
        
        # 保存图像到临时文件夹
        img_path = os.path.join(temp_folder, f'route_{start_node}_to_{end_node}_{timestamp}.png')
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        print(f"路径规划图像已保存至: {img_path}")
        
        # 绘制收敛曲线并保存
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        iterations = np.arange(1, len(result['convergence'])+1)
        ax2.plot(iterations, result['convergence'], 'b-', linewidth=1.5)
        ax2.set_title('收敛曲线', fontsize=14)

        ax2.set_xlabel('迭代次数', fontsize=12)
        ax2.set_ylabel('joggability', fontsize=12)
        ax2.grid(True)
        
        convergence_path = os.path.join(temp_folder, f'convergence_{start_node}_to_{end_node}_{timestamp}.png')
        fig2.savefig(convergence_path, dpi=300, bbox_inches='tight')
        print(f"收敛曲线图像已保存至: {convergence_path}")
        
        # 清理matplotlib资源
        plt.close(fig)
        plt.close(fig2)
        
        # 提取关键结果数据
        response_data = {
            'best_path': [int(node) for node in result['best_path']],  # 转换int64为Python int
            'best_score': float(result['best_score_path_ratio']),
            'path_length': float(result['best_dist_real']),
            'path_segments': int(result['best_pathword']),
            'node_coordinates': result['node_coords'].tolist(),  # 转换ndarray为list
            'convergence': result['convergence'],
            'json_file': json_path,
            'image_file': img_path,
            'convergence_file': convergence_path
        }
        
        return jsonify({
            'status': 'success',
            'data': response_data
        })
    except Exception as e:
        print(f"路径规划错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



@routeplanning_bp.route('/get_route_image/<int:start_node>/<int:end_node>', methods=['GET'])
def get_route_image(start_node, end_node):
    """返回路径规划图像"""
    try:
        # 执行路径规划
        params = {
            'num_ants': int(request.args.get('num_ants', 20)),
            'max_iter': int(request.args.get('max_iter', 30)),  # 减少迭代次数以加快响应
            'w1': int(request.args.get('w1', 1)),
            'w2': int(request.args.get('w2', 0)),
            'w3': int(request.args.get('w3', 1)),
        }
        
        result = ant_colony_optimization(start_node, end_node, **params)
        
        # 保存图像到内存
        img_buffer = io.BytesIO()
        result['figures'][0].savefig(img_buffer, format='png', dpi=300)
        img_buffer.seek(0)
        
        # 清理matplotlib资源
        for fig in result['figures']:
            plt.close(fig)
        
        return send_file(img_buffer, mimetype='image/png')
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500