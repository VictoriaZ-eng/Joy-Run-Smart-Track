%% 传统的迪杰斯特拉算法（含Total/路段数指标）
clear; clc; close all;

%% 读取CSV文件并构建路网
data = readtable('outputroad.csv');
startX = data.startX;
startY = data.startY;
endX = data.endX;
endY = data.endY;
Distance = data.dis_ori;
Score = data.Score;   % 读取每条道路的得分
Total = data.Total;     % 读取每条道路的Total值

% 构建节点列表和邻接矩阵
allNodes = [startX, startY; endX, endY];
uniqueNodes = unique(allNodes, 'rows');
numNodes = size(uniqueNodes, 1);
adjMat = zeros(numNodes);
scoreMat = zeros(numNodes);  % 得分矩阵
totalMat = zeros(numNodes);  % Total矩阵

for i = 1:size(data, 1)
    startIdx = find(ismember(uniqueNodes, [startX(i), startY(i)], 'rows'));
    endIdx = find(ismember(uniqueNodes, [endX(i), endY(i)], 'rows'));
    adjMat(startIdx, endIdx) = Distance(i);
    adjMat(endIdx, startIdx) = Distance(i); % 双向道路
    scoreMat(startIdx, endIdx) = Score(i);  % 记录得分
    scoreMat(endIdx, startIdx) = Score(i);  % 双向道路得分相同
    totalMat(startIdx, endIdx) = Total(i);  % 记录Total
    totalMat(endIdx, startIdx) = Total(i);  % 双向道路Total相同
end

%% --- 新增迭代剔除逻辑 ---
hasNodesToRemove = true;  % 循环标志位
iteration = 0;            % 迭代计数器
while hasNodesToRemove
    % 计算节点度数
    degree = sum(adjMat ~= 0, 2);  
    nodesToRemove = find(degree == 1);
    
    % 判断是否继续迭代
    if isempty(nodesToRemove)
        hasNodesToRemove = false;
        fprintf('迭代完成，共执行 %d 次剔除\n', iteration);
        break;
    else
        iteration = iteration + 1;
        fprintf('第%d次迭代：发现%d个度数为1的节点\n', iteration, length(nodesToRemove));
    end

    % 更新保留节点索引
    remainingNodes = setdiff(1:size(uniqueNodes,1), nodesToRemove);

    % 动态更新所有矩阵
    uniqueNodes = uniqueNodes(remainingNodes, :);
    adjMat = adjMat(remainingNodes, remainingNodes);
    scoreMat = scoreMat(remainingNodes, remainingNodes);
    totalMat = totalMat(remainingNodes, remainingNodes);
    numNodes = size(uniqueNodes, 1);
end

% 计算有效距离矩阵
distMat = adjMat;          % 直接使用邻接矩阵作为距离矩阵
distMat(~adjMat) = Inf;    % 无直接连接设为无穷大
distMat(distMat == 0) = eps; % 避免除以零

% 随机选择起点和终点
startNode = 2903; %起点     outputroad建议组合（2852、1664）、smallroad建议组合（165、63）
endNode = 1104;   %终点
while endNode == startNode
    endNode = randi(numNodes); % 确保终点与起点不同
end

fprintf('起点: 节点 %d, 终点: 节点 %d\n', startNode, endNode);

%% 执行迪杰斯特拉算法
[shortestPath, minDist] = dijkstra(distMat, startNode, endNode);

%% 计算Total相关指标
TotalSum = 0;
numSegments = length(shortestPath) - 1; % 路径段数 = 节点数-1
for i = 1:numSegments
    TotalSum = TotalSum + totalMat(shortestPath(i), shortestPath(i+1));
end
scoreRatio = TotalSum / numSegments;

%% 结果输出
fprintf('\n========= 路径分析结果 =========\n');
fprintf('最短路径距离: %.2f 米\n', minDist);
fprintf('路径总Total值: %.2f\n', TotalSum);
fprintf('路径包含路段数: %d\n', numSegments);
fprintf('Total/路段数比值: %.2f\n', scoreRatio);
fprintf('路径节点序列: ');
fprintf('%d ', shortestPath);
fprintf('\n');

%% 可视化展示
figure;
hold on;
gplot(adjMat, uniqueNodes, '-k'); % 路网骨架

% 绘制最优路径
for i = 1:numSegments
    x = [uniqueNodes(shortestPath(i),1), uniqueNodes(shortestPath(i+1),1)];
    y = [uniqueNodes(shortestPath(i),2), uniqueNodes(shortestPath(i+1),2)];
    plot(x, y, 'r-', 'LineWidth', 2);
end

% 标记起终点
scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled');
scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled');
title(sprintf('最短路径: %.1f米 | Total/路段数=%.2f', minDist, scoreRatio));
xlabel('X坐标'); ylabel('Y坐标');
axis equal;
hold off;

%% 迪杰斯特拉算法函数
function [shortestPath, minDist] = dijkstra(distMat, startNode, endNode)
    numNodes = size(distMat,1);
    dist = Inf(1,numNodes);
    prev = zeros(1,numNodes);
    visited = false(1,numNodes);

    dist(startNode) = 0;

    for i=1:numNodes
        minDist = Inf;
        u = -1;
        for j=1:numNodes
            if ~visited(j) && dist(j)<minDist
                minDist = dist(j);
                u = j;
            end
        end
        if u==-1 || u==endNode
            break;
        end
        visited(u) = true;
        for v=1:numNodes
            if distMat(u,v) < Inf && ~visited(v) % 注意这里不排除0权重
                alt = dist(u) + distMat(u,v);
                if alt < dist(v)
                    dist(v) = alt;
                    prev(v) = u;
                end
            end
        end
    end

    if dist(endNode)==Inf
        error('终点不可达');
    end

    shortestPath = endNode;
    while shortestPath(1) ~= startNode
        shortestPath = [prev(shortestPath(1)) shortestPath];
    end
    minDist = dist(endNode);
end
