%% 改进的蚁群算法慢行路径优化问题（线状路线）
clear; clc; close all;

%% 控制台
%基础数据
data = readtable('outputroad.csv');
startNode = 2903; %起点     outputroad建议组合（2852、1664）、smallroad建议组合（165、63）
endNode = 1104;   %终点

%蚁群参数设置
numAnts = 20;  % 蚂蚁数量
maxIter = 80; % 最大迭代次数
alpha = NaN;     % 信息素重要程度，设为NaN是因为模式不一样，信息素的重要程度有区别
beta = 1;      % 启发因子重要程度
rho = 0.3;
lambda = 0.98;
rho_min = 0.05;

%慢跑路线模式设置
w0=0;          %模式设置：（w0=0）分子为“道路得分*道路长度”累加（默认）
               %         （w0=1）分子为“道路得分”累加（不考虑得分的持续性）【新版可能失效】
               %         （w0=2）先前的“道路长度”的分母部分替换为为“道路得分取反”，分子变为1/【新版可能失效】
      
% ======
%偏好权重设置（w1只能为0或1，w2和w3不能同时大于0或等于0）
w1=1;          %（w1=0）控制“道路得分*道路长度”的偏好，即慢跑可持续性
               %（w1=1）分子为1，变成单纯求最短路径或最少路段数的情况（根据w2和w3来确定）

w2=0;          %（w2＞0）控制“道路长度”的偏好，权重越大说明其更偏向于短距离的路线，但同时也会导致慢跑可持续性在下降

w3=1;          %（w1＞0）控制“路段数”的偏好，权重越大说明其更偏向于路段少的路线，但同时也会导致慢跑可持续性在下降

%路线长度约束检测（使用 dijstra 查找最短路径）======
dij = 0;                   %（dij=0）不开启距离约束，（dij=1）开启距离约束，开启后会先进行迪杰斯特拉计算，若最短路径长度比迪杰斯特拉结果还小就会报错
minPathLength = 10000;      % 允许的最小路径长度（真实距离）
maxPathLength = 11000;     % 允许最大路径长度（真实距离）

% ====== 路段数约束检测（使用 BFS 查找最少路段数）======
BFS = 0;                   %（BFS=0）不开启路段数约束，（BFS=1）开启路段数约束，开启后会先进行BFS搜索，若最少路段数比BFS搜索结果还小就会报错
minPathWord = 50;          % 允许的最小路段数
maxPathWord = 60;          % 允许的最大路段数

%若出现可能的最优解，是否提前结束迭代（可能会导致还没出现全局最优解就结束了，但也可能减少不必要的迭代，提升运行速度）
limit = 0;     %(limitm=0)不开启，(limitm=1)开启
maxtime =30;   %当前最优解持续的回合数，若当前最优解持续maxtime回合仍保持不变，则提前结束迭代

%% 权重约束检测
fprintf("*****************************************************\n")
if w1 ~= 1 && w1 ~= 0
    error("w1 要大于等于0");
end

if (w2 == 0 && w3 == 0) || (w2 ~= 0 && w3 ~= 0)
    error("w2 和 w3 必须有一个为零，另一个为非零");
end

% 信息素权重调整
if w2 ~= 0 && w3 == 0 && w1 == 1
    alpha =6.5;
elseif w3 ~= 0 && w2 == 0 && w1 == 1
    alpha = 2.5;
elseif w1 == 0
    alpha = 2.5;
    rho = 0.1;
end
pathWord = 0; % 初始化最少路段数


%% 读取CSV文件并构建路网
startX = data.startX;
startY = data.startY;
endX = data.endX;
endY = data.endY;

if w0==1 || w0==0
   Distance = data.distance;    
elseif w0==2
   Distance = data.dij_W1;
   fprintf('先前的“道路长度”的分母部分替换为为“道路得分取反”\n')
end
Score = data.Score;  
if w0==1
   Total = data.Score;     
   fprintf('分子为“道路得分”\n')
elseif w0==0
    if w1 ==1 
    Total = data.Total;
        if w2==0
            c = 'b';
            fprintf('模式b\n') 
        elseif w3==0
            c = 'a';
            fprintf('模式a\n')
        end
    elseif w1==0
        %Total = data.Total;
        if w2==0
            Total = 1 * ones(size(data.Total));
            fprintf('模式d\n')
        elseif w3==0
            Total = 1 ./ data.distance;
            fprintf('模式c\n')
        end
    end
elseif w0==2
   Total = data.Total;
   fprintf('分子默认为1\n')
end

Distancereal = data.dis_ori;
Totalreal = data.toatl_ori1;

[numRows, numCols] = size(data);
fprintf("*****************************************************\n")

% 构建节点列表和邻接矩阵
allNodes = [startX, startY; endX, endY];
uniqueNodes = unique(allNodes, 'rows');
numNodes = size(uniqueNodes, 1);
adjMat = zeros(numNodes);
scoreMat = zeros(numNodes);  % 得分矩阵
totalMat = zeros(numNodes);  % Total矩阵
adjMatreal = zeros(numNodes);
totalMatreal = zeros(numNodes);
totalMean = mean(Total);  
disMean = mean(Distance);

for i = 1:size(data, 1)
    startIdx = find(ismember(uniqueNodes, [startX(i), startY(i)], 'rows'));
    endIdx = find(ismember(uniqueNodes, [endX(i), endY(i)], 'rows'));
    adjMat(startIdx, endIdx) = Distance(i);
    adjMat(endIdx, startIdx) = Distance(i); % 双向道路
    adjMatreal(startIdx, endIdx) = Distancereal(i);
    adjMatreal(endIdx, startIdx) = Distancereal(i); % 双向道路
    scoreMat(startIdx, endIdx) = Score(i);  % 记录得分
    scoreMat(endIdx, startIdx) = Score(i);  % 双向道路得分相同
    totalMat(startIdx, endIdx) = Total(i);  % 记录Total
    totalMat(endIdx, startIdx) = Total(i);  % 双向道路Total相同
    totalMatreal(startIdx, endIdx) = Totalreal(i);  % 记录Total
    totalMatreal(endIdx, startIdx) = Totalreal(i);  % 双向道路Total相同
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
    adjMatreal = adjMatreal(remainingNodes, remainingNodes);
    totalMatreal = totalMatreal(remainingNodes, remainingNodes);
    numNodes = size(uniqueNodes, 1);
end

% 计算有效距离矩阵
distMat = adjMat;          % 直接使用邻接矩阵作为距离矩阵
distMat(~adjMat) = Inf;    % 无直接连接设为无穷大
distMat(distMat == 0) = eps; % 避免除以零

distMatreal = adjMatreal;          % 直接使用邻接矩阵作为距离矩阵
distMatreal(~adjMatreal) = Inf;    % 无直接连接设为无穷大
distMatreal(distMatreal == 0) = eps; % 避免除以零

while endNode == startNode
    endNode = randi(numNodes); % 确保终点与起点不同
end

fprintf('起点: 节点 %d, 终点: 节点 %d\n', startNode, endNode);
    %% 运行前绘制起点和终点在路网中的位置
    figure;
    hold on;
    gplot(adjMat, uniqueNodes, '-k'); % 绘制路网，使用 uniqueNodes 作为节点坐标
    scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled'); % 起点
    scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled'); % 终点
    title('起点和终点在路网中的位置');
    xlabel('X 坐标');
    ylabel('Y 坐标');
    hold off;
    pause(2); % 暂停2秒，确保图像展示

%% 如果有距离约束则先执行迪杰斯特拉算法 
if dij==1
    % % 找到对应的 dis_ori
    % idx_distance_10 = data.distance == 10;
    % idx_distance_1  = data.distance == 1;
    % dis_ori_10 = data.dis_ori(idx_distance_10);
    % dis_ori_1  = data.dis_ori(idx_distance_1);
    % fprintf('当 distance = 10 时，对应的 dis_ori 值为：%.4f\n',dis_ori_10 );
    % fprintf('当 distance = 1 时，对应的 dis_ori 值为：%.4f\n',dis_ori_1);
    
    % 线性映射到标准距离量纲
    % minPathLength_real = minPathLength;
    % maxPathLength_real = maxPathLength;
    % minPathLength_std = ( (minPathLength_real - dis_ori_1) / (dis_ori_10 - dis_ori_1) ) * (10 - 1) + 1;
    % maxPathLength_std = ( (maxPathLength_real - dis_ori_1) / (dis_ori_10 - dis_ori_1) ) * (10 - 1) + 1;
    % minPathLength = minPathLength_std;
    % maxPathLength = maxPathLength_std;
    % fprintf('标准化后的 minPathLength = %.4f\n', minPathLength);
    % fprintf('标准化后的 maxPathLength = %.4f\n', maxPathLength);

    %% 步骤1：根据路径长度约束，筛选合法节点
    fprintf('正在使用dijkstra计算路段数约束...\n');

    % 保存原始起点终点坐标
    startCoord = uniqueNodes(startNode, :);
    endCoord = uniqueNodes(endNode, :);

    % 单源 Dijkstra（一次性获取到所有点）
    [startToAllDist,~] = dijkstra_single_source(distMatreal, startNode);
    [endToAllDist,~]   = dijkstra_single_source(distMatreal, endNode);

    % 节点筛选
    validNodeMask = (startToAllDist + endToAllDist) <= maxPathLength;

    % 强制保留起点和终点
    validNodeMask(startNode) = true;
    validNodeMask(endNode) = true;

    remainingNodes = find(validNodeMask);

    % 更新所有矩阵
    uniqueNodes = uniqueNodes(remainingNodes, :);
    adjMat = adjMat(remainingNodes, remainingNodes);
    scoreMat = scoreMat(remainingNodes, remainingNodes);
    totalMat = totalMat(remainingNodes, remainingNodes);
    distMat = distMat(remainingNodes, remainingNodes);
    distMatreal = distMatreal(remainingNodes, remainingNodes);
    adjMatreal = adjMatreal(remainingNodes, remainingNodes);
    totalMatreal = totalMatreal(remainingNodes, remainingNodes);
    numNodes = size(uniqueNodes, 1);

    fprintf('已剔除不满足路径距离约束的节点，剩余 %d 个节点。\n', numNodes);

    % 重新定位新的起点和终点编号
    startNode = find(ismember(uniqueNodes, startCoord, 'rows'));
    endNode = find(ismember(uniqueNodes, endCoord, 'rows'));

    if isempty(startNode) || isempty(endNode)
        error('起点或终点被剔除了，无法继续路径计算。');
    end

    fprintf('成功构建满足路径距离约束的子路网\n');

    %% 可视化起终点
    figure;
    hold on;
    gplot(adjMat, uniqueNodes, '-k');
    scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled');
    scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled');
    title('起点和终点在路网中的位置');
    xlabel('X 坐标');
    ylabel('Y 坐标');
    hold off;
    pause(1);

    % 最短路径（点对）
    [shortestPath, minDist] = dijkstra(distMatreal, startNode, endNode);
    %% 计算Total相关指标
    TotalSum = 0;
    realdist = 0;
    Totalreal = 0;
    numSegments = length(shortestPath) - 1; % 路径段数 = 节点数-1
    for i = 1:numSegments
        TotalSum = TotalSum + totalMat(shortestPath(i), shortestPath(i+1));
        realdist = realdist + adjMatreal(shortestPath(i), shortestPath(i+1));
        Totalreal = Totalreal + totalMatreal(shortestPath(i), shortestPath(i+1));
    end
    scoreRatio = TotalSum / numSegments;
    scoreRatioreal = Totalreal / numSegments;

    %% 结果输出
    fprintf('\n========= 路径分析结果 =========\n');
    fprintf('最短路径距离（标准化后）: %.2f 米，最短路径距离（标准化前）: %.2f 米，\n', minDist, realdist);
    fprintf('路径总Total值（标准化后）: %.2f，路径总Total值（标准化前）: %.2f\n', TotalSum, Totalreal);
    fprintf('路径包含路段数: %d\n', numSegments);
    fprintf('Total/路段数比值（标准化后）: %.2f，Total/路段数比值（标准化前）: %.2f\n', scoreRatio, scoreRatioreal);
    fprintf('路径节点序列: ');
    fprintf('%d ', shortestPath);
    fprintf('\n');
    if minPathLength < minDist
        error('设置的距离范围下限小于最短距离');
    else
        fprintf('设置的距离范围下限大于最短距离，可执行蚁群算法\n')
    end

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
    pause(1); % 暂停1秒，确保图像展示
end



%% BFS 方式找最小路段数

if BFS==1
    if BFS == 1
    %% 步骤1：根据路段数约束，筛选合法节点
    fprintf('正在使用 BFS 计算路段数约束...\n');

    % 保存原始起点终点坐标
    startCoord = uniqueNodes(startNode, :);
    endCoord = uniqueNodes(endNode, :);
    
    % 一次性 BFS
    startToAllPathWords = bfs_all_pathwords(adjMatreal, startNode);
    endToAllPathWords = bfs_all_pathwords(adjMatreal, endNode);
    
    % 路段数约束判断
    validNodeMask = (startToAllPathWords + endToAllPathWords) <= maxPathWord;
    
    remainingNodes = find(validNodeMask);

    % 更新所有矩阵
    uniqueNodes = uniqueNodes(remainingNodes, :);
    adjMat = adjMat(remainingNodes, remainingNodes);
    scoreMat = scoreMat(remainingNodes, remainingNodes);
    totalMat = totalMat(remainingNodes, remainingNodes);
    distMat = distMat(remainingNodes, remainingNodes); % 可选保留一致性
    distMatreal = distMatreal(remainingNodes, remainingNodes);
    adjMatreal = adjMatreal(remainingNodes, remainingNodes);
    totalMatreal = totalMatreal(remainingNodes, remainingNodes);
    numNodes = size(uniqueNodes, 1);

    fprintf('已剔除不满足路段数约束的节点，剩余 %d 个节点。\n', numNodes);

    % 重新定位新的起点和终点编号
    startNode = find(ismember(uniqueNodes, startCoord, 'rows'));
    endNode = find(ismember(uniqueNodes, endCoord, 'rows'));

    if isempty(startNode) || isempty(endNode)
        error('起点或终点被剔除了，无法继续路径计算。');
    end

    fprintf('成功构建满足路段数约束的子路网\n');
    %% 可视化起终点
    figure;
    hold on;
    gplot(adjMat, uniqueNodes, '-k');
    scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled');
    scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled');
    title('起点和终点在路网中的位置');
    xlabel('X 坐标');
    ylabel('Y 坐标');
    hold off;
    pause(1);
end
    %% 使用 BFS 辅助函数找最小路段数
    % === 使用 BFS 找最小路段数 ===
    [pathWord, shortestPath] = bfs_pathword(adjMat, startNode, endNode);
    
    if isempty(shortestPath)
        error('未找到可达路径，检查路网是否连通');
    end
    
    fprintf('最小可达路段数为 %d\n', pathWord);
    
    if pathWord < minPathWord
        fprintf('最小路段数小于允许下限，可继续执行蚁群算法。\n');
    elseif pathWord > maxPathWord
        error('最小路段数大于允许上限，无法继续');
    else
        fprintf('路段数在允许范围内，可继续执行蚁群算法。\n');
    end
    
    % === 路径相关指标 ===
    TotalSum = 0;
    realdist = 0;
    Totalreal = 0;
    numSegments = length(shortestPath) - 1; % 路径段数 = 节点数-1
    for i = 1:numSegments
        TotalSum = TotalSum + totalMat(shortestPath(i), shortestPath(i+1));
        realdist = realdist + adjMatreal(shortestPath(i), shortestPath(i+1));
        Totalreal = Totalreal + totalMatreal(shortestPath(i), shortestPath(i+1));
    end
    scoreRatio = TotalSum / numSegments;
    scoreRatioreal = Totalreal / numSegments;

    % === 结果输出 ===
    fprintf('\n========= BFS 路段数分析 =========\n');
    fprintf('最短路径距离（标准化前）: %.2f 米，\n',  realdist);
    fprintf('路径总Total值（标准化后）: %.2f，路径总Total值（标准化前）: %.2f\n', TotalSum, Totalreal);
    fprintf('路径包含路段数: %d\n', pathWord);
    fprintf('Total/路段数比值（标准化后）: %.2f，Total/路段数比值（标准化前）: %.2f\n', scoreRatio, scoreRatioreal);
    fprintf('路径节点序列: ');
    fprintf('%d ', shortestPath);
    fprintf('\n');
    
    % === 可视化 ===
    figure;
    hold on;
    gplot(adjMat, uniqueNodes, '-k'); % 路网骨架
    
    % 绘制路径
    for i = 1:numSegments
        x = [uniqueNodes(shortestPath(i),1), uniqueNodes(shortestPath(i+1),1)];
        y = [uniqueNodes(shortestPath(i),2), uniqueNodes(shortestPath(i+1),2)];
        plot(x, y, 'b-', 'LineWidth', 2);
    end
    
    % 标记起终点
    scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled');
    scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled');
    title(sprintf('最少路段数路径: %d | Total/路段数=%.2f', pathWord, scoreRatio));
    xlabel('X坐标'); ylabel('Y坐标');
    axis equal;
    hold off;
    pause(1); % 暂停1秒，确保图像展示
end

%% 初始化信息素矩阵（仅在有效路径上初始化）
pheromone = zeros(numNodes); % 初始化一个全零矩阵
for i = 1:numNodes
    for j = 1:numNodes
        if adjMat(i, j) > 0 % 如果存在路径
            pheromone(i, j) = 1; % 将信息素初始化
        end
    end
end

%% 算法初始化
bestPath = [];
bestcorePathRatio = -Inf;
iterBestcorePathRatio = zeros(maxIter, 1);
iterBestDist = zeros(maxIter, 1);
iterBestScores = zeros(maxIter, 1);
iterBestTotal = zeros(maxIter, 1);
iterBestpathword = zeros(maxIter, 1);
iteravrpathscore= zeros(maxIter, 1);
allBestDist = zeros(maxIter, 1);
allBestScores = zeros(maxIter, 1);
allBestcorePathRatio = zeros(maxIter, 1);
allBestTotal = zeros(maxIter, 1);
allBestpathword = zeros(maxIter, 1);
allavrpathscore= zeros(maxIter, 1);
allavrdisscore = zeros(maxIter, 1);
allBestDistreal = zeros(maxIter, 1);
noImproveCount = 0;       % 新增：连续未改进次数计数器
earlyStopFlag = false;    % 新增：早停标志位
% 在路网初始化时计算最大值
sumScore = sum(Score);
sumTotal = sum(Total);        % antsTotal(k)的最大值
sumDist = sum(Distance);      % antsDist(k)的最大值
sumPathword = numRows;  % pathword(k)的最大值

%% 启动并行池
% if isempty(gcp('nocreate'))
%     parpool; % 启动默认并行池
% end

%% 主循环
for iter = 1:maxIter
    rho = max(lambda*rho, rho_min); % 全程动态降低 rho
    antsPaths = cell(numAnts, 1);
    antsDist = Inf(numAnts, 1);
    antsScores = zeros(numAnts, 1);  % 记录每只蚂蚁的总得分
    antsTotal = zeros(numAnts, 1);
    pathword = zeros(numAnts, 1);
    totaldividepath = zeros(numAnts, 1); % 预分配
    avrpathscore = zeros(numAnts, 1);
    avrdisscore = zeros(numAnts, 1);
    antsTotalreal = zeros(numAnts, 1);
    antsDistreal = Inf(numAnts, 1);
    avrdisscorereal = zeros(numAnts, 1);
    avrpathscorereal = zeros(numAnts, 1);
    iteravrdisscore = zeros(numAnts, 1);
    iterBestDistreal = zeros(numAnts, 1);
    
    fprintf('\n------ 第 %d 次迭代 ------\n', iter);
    validPathCount = 0;  % 记录符合路径长度约束的蚂蚁数量
    
    % 使用 for 并行化每只蚂蚁的路径选择
    for k = 1:numAnts
        validPath = false;
        while ~validPath
            try
                currentNode = startNode;
                visited = currentNode;
                path = [currentNode];
                tempBarriers = [];
                backoffSteps = 0;
                maxBackoff = 50; % 允许更大回退层数
                totalScore = 0;
                totalTotal = 0;
                totalDist = 0;
                pathcalcul = 0;
                totalTotalreal = 0;
                totalDistreal = 0;
    
                while currentNode ~= endNode
                    neighbors = find(adjMat(currentNode, :) > 0);
                    reachable = setdiff(neighbors, [visited, tempBarriers]);
    
                    if isempty(reachable)
                        if length(path) == 1 || backoffSteps > maxBackoff
                            error('无法回退，重新构建路径');
                        end
                        % 回退：当前节点设为临时障碍
                        tempBarriers = [tempBarriers, currentNode];
                        prevNode = path(end-1);
                        % 扣除路径累计值
                        totalScore = totalScore - scoreMat(prevNode, currentNode);
                        totalTotal = totalTotal - totalMat(prevNode, currentNode);
                        totalDist = totalDist - distMat(prevNode, currentNode);
                        totalTotalreal = totalTotalreal - totalMatreal(prevNode, currentNode);
                        totalDistreal = totalDistreal - distMatreal(prevNode, currentNode);
                        pathcalcul = pathcalcul - 1;
    
                        path(end) = [];
                        currentNode = prevNode;
                        backoffSteps = backoffSteps + 1;
    
                        continue; % 重新选别的邻居
                    end
    
                    % 正常转移
                    if length(reachable) == 1
                        nextNode = reachable;
                    else
                        probabilities = (pheromone(currentNode, reachable).^alpha) .* (totalMat(currentNode, reachable).^beta);
                        probabilities = probabilities / sum(probabilities);
                        nextNode = randsample(reachable, 1, true, probabilities);
                    end
    
                    % 记录
                    prevNode = currentNode;
                    path = [path, nextNode];
                    visited = [visited, nextNode];
                    totalScore = totalScore + scoreMat(prevNode, nextNode);
                    totalTotal = totalTotal + totalMat(prevNode, nextNode);
                    totalDist = totalDist + distMat(prevNode, nextNode);
                    totalTotalreal = totalTotalreal + totalMatreal(prevNode, nextNode);
                    totalDistreal = totalDistreal + distMatreal(prevNode, nextNode);
                    pathcalcul = pathcalcul + 1;
    
                    % --- 核心：走一步就判断约束 ---
                    if dij == 1
                        if totalDistreal > maxPathLength || totalDistreal < minPathLength && nextNode == endNode
                            % 超了就回退 & 标记
                            tempBarriers = [tempBarriers, nextNode];
                            totalScore = totalScore - scoreMat(prevNode, nextNode);
                            totalTotal = totalTotal - totalMat(prevNode, nextNode);
                            totalDist = totalDist - distMat(prevNode, nextNode);
                            totalTotalreal = totalTotalreal - totalMatreal(prevNode, nextNode);
                            totalDistreal = totalDistreal - distMatreal(prevNode, nextNode);
                            pathcalcul = pathcalcul - 1;
    
                            path(end) = [];
                            currentNode = prevNode;
                            backoffSteps = backoffSteps + 1;
                            continue;
                        end
                    elseif BFS == 1
                        if pathcalcul > maxPathWord || (pathcalcul < minPathWord && nextNode == endNode)
                            tempBarriers = [tempBarriers, nextNode];
                            totalScore = totalScore - scoreMat(prevNode, nextNode);
                            totalTotal = totalTotal - totalMat(prevNode, nextNode);
                            totalDist = totalDist - distMat(prevNode, nextNode);
                            totalTotalreal = totalTotalreal - totalMatreal(prevNode, nextNode);
                            totalDistreal = totalDistreal - distMatreal(prevNode, nextNode);
                            pathcalcul = pathcalcul - 1;
    
                            path(end) = [];
                            currentNode = prevNode;
                            backoffSteps = backoffSteps + 1;
                            continue;
                        end
                    end
    
                    % 正常前进
                    currentNode = nextNode;
                    backoffSteps = 0; % 成功前进就重置
                end
    
                % 到终点了，额外校验是否满足下限
                if dij == 1
                    if totalDistreal >= minPathLength && totalDistreal <= maxPathLength
                        validPath = true;
                    else
                        error('路径长度不符合约束');
                    end
                elseif BFS == 1
                    if pathcalcul >= minPathWord && pathcalcul <= maxPathWord
                        validPath = true;
                    else
                        error('路段数不符合约束');
                    end
                else
                    validPath = true;
                end
    
            catch
                continue; % 整只蚂蚁重新尝试
            end
        end
    
        % 记录
        antsPaths{k} = path;
        antsDist(k) = totalDist;
        antsScores(k) = totalScore;
        antsTotal(k) = totalTotal;
        pathword(k) = pathcalcul;
        antsTotalreal(k) = totalTotalreal;
        antsDistreal(k) = totalDistreal
    
        avrdisscore(k) = antsTotal(k) / antsDist(k);
        avrpathscore(k) = antsTotal(k) / pathword(k);
        avrdisscorereal(k) = antsTotalreal(k) / antsDistreal(k);
        avrpathscorereal(k) = antsTotalreal(k) / pathword(k);
    
        if w1 == 0
            if w2 > 0  
                totaldividepath(k) = 1/antsDist(k);
            else
                totaldividepath(k) = 1/pathword(k);
            end
        else % w1 > 1
            if w2 > 0 
                totaldividepath(k) = (antsTotal(k)^w1)/(antsDist(k)^w2);
            else
                totaldividepath(k) = (antsTotal(k)^w1)/(pathword(k)^w3);
            end
        end
        fprintf('蚂蚁 %d: 路径长度（标准化后） = %.2f, 路径长度（标准化前） = %.2f, 总得分 = %.2f, 慢跑可持续性（标准化后） = %.2f, 慢跑可持续性（标准化前） = %.2f, 总路段数 = %.2f,  joggability= %.2f\n', k, antsDist(k), antsDistreal(k) , antsScores(k), antsTotal(k), antsTotalreal(k), pathword(k), totaldividepath(k)); 
    end
    
    %% 更新最优路径
    % 计算每只蚂蚁的得分与道路数量的比值
    totaldividepath_1 = totaldividepath';
    antsScorePathRatio = totaldividepath_1;
    
    % 找到得分与道路数量比值最大的蚂蚁
    [maxScorePathRatio, idx] = max(antsScorePathRatio);
    iterBestcorePathRatio(iter) = antsScorePathRatio(idx);
    iterBestScores(iter) = antsScores(idx);
    iterBestDist(iter) = antsDist(idx);
    iterBestTotal(iter) = antsTotal(idx);
    iterBestpathword(iter) = pathword(idx);
    iterbestPath = antsPaths{idx};
    iteravrpathscore(iter) = avrpathscore(idx);
    iteravrdisscore(iter) = avrdisscore(idx);
    iterBestDistreal(iter) = antsDistreal(idx);

    fprintf('迭代 %3d: 当前迭代最优joggability = %.4f, 最优路径的得分 = %.2f, 最优路径的长度 = %.2f, 最优路径的Total = %.2f, 最优路径的路段数 = %.2f, 平均道路得分 = %.2f,平均每米得分 = %.2f\n', iter, maxScorePathRatio, iterBestScores(iter), iterBestDist(iter), iterBestTotal(iter), iterBestpathword(iter), iteravrpathscore(iter),iteravrdisscore(iter));
    
    % 更新最优路径
    if maxScorePathRatio > bestcorePathRatio  % 这里将bestDist用作存储最优的得分与道路数量比值
        bestcorePathRatio = maxScorePathRatio;
        bestPath = antsPaths{idx};
        bestScores = antsScores(idx);
        BestDist = antsDist(idx);
        BestTotal = antsTotal(idx);
        Bestpathword = pathword(idx);
        bestavrpathscore = avrpathscore(idx);
        bestavrdisscore = avrdisscore(idx);
        BestDistreal = antsDistreal(idx);
    end
    allBestcorePathRatio(iter) = bestcorePathRatio;  % 这里记录的是最优的得分与道路数量比值
    allBestScores(iter) = bestScores; % 记录最优路径的得分
    allBestDist(iter) = BestDist;
    allBestTotal(iter) = BestTotal;
    allBestpathword(iter) = Bestpathword;
    allavrpathscore(iter) = bestavrpathscore;
    allavrdisscore(iter) = bestavrdisscore;
    allBestDistreal(iter) = BestDistreal;

    %% 信息素更新 (所有路段)
    pheromone = (1 - rho) * pheromone;
    
    % 先记录 iterbestPath 路段（方便后面判别）
    pathEdges = false(size(pheromone)); % 与邻接矩阵相同大小
    
    for i = 1:length(bestPath)-1
        from = bestPath(i);
        to = bestPath(i+1);
        pathEdges(from, to) = true; % 标记属于最优路径的边
    end

    % 先更新 iterbestPath 上的路段
    for i = 1:length(bestPath)-1
        from = bestPath(i);
        to = bestPath(i+1);
        origin(from, to) = pheromone(from, to);
        if w2 == 0
            if w1 == 1
                delta = allavrpathscore(iter) / totalMean;
                pheromone(from, to) = pheromone(from, to) + delta;
                fprintf('1信息素增加%.4f，该道路原始信息素为%.4f，更新后为%.4f\n', delta, origin(from, to), pheromone(from, to))
            elseif w1 == 0
                delta = 1* allBestcorePathRatio(iter);
                pheromone(from, to) = pheromone(from, to) + delta;
                fprintf('2信息素增加%.4f，该道路原始信息素为%.4f，更新后为%.4f\n', delta, origin(from, to), pheromone(from, to))
            end
        elseif w3 == 0
            if w1 == 1
                delta = (disMean * allavrdisscore(iter)) / totalMean;
                pheromone(from, to) = pheromone(from, to) + delta;
                fprintf('3信息素增加%.4f，该道路原始信息素为%.4f，更新后为%.4f\n', delta, origin(from, to), pheromone(from, to))
            elseif w1 == 0
                delta = 1* allBestcorePathRatio(iter);
                pheromone(from, to) = pheromone(from, to) + delta;
                fprintf('4信息素增加%.4f，该道路原始信息素为%.4f，更新后为%.4f\n', delta, origin(from, to), pheromone(from, to))
            end
        end
    end

    if w1 == 1
        % 再对不在 iterbestPath 上的路段增加 +1
        for from = 1:size(pheromone, 1)
            for to = 1:size(pheromone, 2)
                if ~pathEdges(from, to) && pheromone(from, to) > 0  % 如果该路段存在且不在 iterbestPath
                    pheromone(from, to) = pheromone(from, to) + 1;
                    %fprintf('非路径信息素+1: from %d to %d, 更新后 %.4f\n', from, to, pheromone(from, to));
                end
            end
        end
    end

    %pheromone(pheromone < 1 & pheromone > 0) = 1;
  
    %% 记录当前迭代的最优路径得分
    fprintf('迭代 %3d: 信息素范围 = [%.5f, %.5f],total范围 = [%.5f, %.5f],toatl平均值= %.2f,distanc平均值= %.2f,此时rho= %.2f,此时alpha=%.2f\n', iter, min(pheromone(pheromone>0)), max(pheromone(:)),min(totalMat(totalMat>0)), max(totalMat(:)),totalMean,disMean,rho,alpha);
    fprintf('===================================================================================\n');
    fprintf('迭代 %3d: 全局平均每段道路可慢跑持续性 = %.4f,全局平均每米可慢跑持续性 = %.4f,当前全局joggability = %.6f, 全局最优路径的总得分 = %.4f, \n 全局最优路径的总长度（标准化后） = %.4f, 全局最优路径的总长度（标准化前） = %.4f, 全局最优路径的总可慢跑持续得分 = %.4f, 全局最优路径的总路段数 = %.2f\n', iter, allavrpathscore(iter), allavrdisscore(iter),allBestcorePathRatio(iter), allBestScores(iter), allBestDist(iter), allBestDistreal(iter), allBestTotal(iter), allBestpathword(iter));


    %% 新增：早停条件判断（添加在信息素更新之后）
    if limit==1
        if iter >= 2
            % 检查当前最优值是否与前一次相同（允许微小浮点误差）
            if abs(allBestcorePathRatio(iter) - allBestcorePathRatio(iter-1)) < 1e-6
                noImproveCount = noImproveCount + 1;
            else
                noImproveCount = 0; % 重置计数器
            end
    
            if noImproveCount >= maxtime
                fprintf('连续%次迭代未改进最优值，提前终止迭代！\n',maxtime);
                earlyStopFlag = true;
                break; % 跳出主循环
            end
        end
    end
end

%% 可视化输出
figure;
gplot(adjMat, uniqueNodes, 'k:'); hold on;

% 绘制全局最优路径
for i = 1:length(bestPath)-1
    x = [uniqueNodes(bestPath(i),1), uniqueNodes(bestPath(i+1),1)];
    y = [uniqueNodes(bestPath(i),2), uniqueNodes(bestPath(i+1),2)];
    plot(x, y, 'r-', 'LineWidth', 2);  % 使用红色加粗路径
end

% 绘制节点（隐藏节点标签）
plot(uniqueNodes(:,1), uniqueNodes(:,2), 'o', 'MarkerSize', 1, 'MarkerFaceColor', 'b', 'MarkerEdgeColor', 'k');

title(['全局的bestcorePathRatio： ' num2str(bestcorePathRatio)], 'FontSize', 14, 'FontWeight', 'bold');
xlabel('X坐标', 'FontSize', 12); ylabel('Y坐标', 'FontSize', 12);
axis tight;
axis off;  % 隐藏坐标轴
set(gca, 'FontSize', 12);
% logFileName = sprintf('D:/资料/论文/新建文件夹 (2)/数据/蚁群算法代码改进1/输出结果/a模式/a模式路段数约束/高路段数/路线图/BestPath_%s_%.2f.xlsx', c, w2);
% saveas(gcf, [logFileName '.fig']);
% 
% %导出excel
% x = (1:maxIter)';
% y = iterBestcorePathRatio(:);  % 保证是列向量
% T = table(x, y, 'VariableNames', {'Iteration', 'BestPathScore'});
% logFileName1 = sprintf('D:/资料/论文/新建文件夹 (2)/数据/蚁群算法代码改进1/输出结果/a模式/a模式路段数约束/高路段数/画图数据/tablet_run_%s_%.2f.xlsx', c, w2);
% writetable(T, logFileName1);
% fprintf('已将迭代曲线数据导出\n');
% 
% %导出日志
% logFileName2 = sprintf('D:/资料/论文/新建文件夹 (2)/数据/蚁群算法代码改进1/输出结果/a模式/a模式路段数约束/高路段数/详细记录/log_run_%s_%.2f.txt', c, w2);
% fid = fopen(logFileName2, 'w');
% fprintf(fid, '迭代 %3d: 全局平均每段道路可慢跑持续性 = %.4f,全局平均每米可慢跑持续性 = %.4f,当前全局joggability = %.6f, 全局最优路径的总得分 = %.4f, \n 全局最优路径的总长度（标准化后） = %.4f, 全局最优路径的总长度（标准化前） = %.4f, 全局最优路径的总可慢跑持续得分 = %.4f, 全局最优路径的总路段数 = %.2f\n', iter, allavrpathscore(iter), allavrdisscore(iter),allBestcorePathRatio(iter), allBestScores(iter), allBestDist(iter), allBestDistreal(iter), allBestTotal(iter), allBestpathword(iter));
% fprintf('已将日志数据导出\n');

figure;
gplot(adjMat, uniqueNodes, 'k:'); hold on;

% 绘制收敛最优路径
for i = 1:length(iterbestPath)-1
    x = [uniqueNodes(iterbestPath(i),1), uniqueNodes(iterbestPath(i+1),1)];
    y = [uniqueNodes(iterbestPath(i),2), uniqueNodes(iterbestPath(i+1),2)];
    plot(x, y, 'r-', 'LineWidth', 2);  % 使用红色加粗路径
end

% 绘制节点（隐藏节点标签）
plot(uniqueNodes(:,1), uniqueNodes(:,2), 'o', 'MarkerSize', 1, 'MarkerFaceColor', 'b', 'MarkerEdgeColor', 'k');

title(['收敛的bestcorePathRatio： ' num2str(maxScorePathRatio)], 'FontSize', 14, 'FontWeight', 'bold');
xlabel('X坐标', 'FontSize', 12); ylabel('Y坐标', 'FontSize', 12);
axis tight;
axis off;  % 隐藏坐标轴
set(gca, 'FontSize', 12);


% 收敛曲线图
figure;
plot(allBestcorePathRatio, 'b-', 'LineWidth', 1.5);
title('收敛曲线', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('迭代次数', 'FontSize', 12); ylabel('allBestcorePathRatio的变化情况', 'FontSize', 12);
grid on;

% 迭代完成后绘制最优路径得分曲线
figure;
plot(1:maxIter, iterBestcorePathRatio, '-o', 'LineWidth', 2);
xlabel('迭代次数');
ylabel('最优路径得分');
title('iterBestcorePathRatio的变化情况');
grid on;

fprintf('\n========= 最终结果 =========\n');
fprintf('最优得分/道路数量比值 : %.2f\n', maxScorePathRatio);
fprintf('全局最优路径顺序: ');
fprintf('%d ', bestPath);
fprintf('\n');
fprintf('收敛最优路径顺序: ');
fprintf('%d ', iterbestPath);
fprintf('\n');



%% 单源最短路函数（带前驱prev，用于路径重构）
function [dist, prev] = dijkstra_single_source(distMat, startNode)
    numNodes = size(distMat, 1);
    dist = Inf(1, numNodes);
    prev = zeros(1, numNodes);  % 前驱节点初始化
    visited = false(1, numNodes);

    dist(startNode) = 0;

    for i = 1:numNodes
        % 找最小未访问节点
        minDist = Inf;
        u = -1;
        for j = 1:numNodes
            if ~visited(j) && dist(j) < minDist
                minDist = dist(j);
                u = j;
            end
        end

        if u == -1
            break; % 所有连通点都找完了
        end

        visited(u) = true;

        for v = 1:numNodes
            if distMat(u, v) < Inf && ~visited(v)
                alt = dist(u) + distMat(u,v);
                if alt < dist(v)
                    dist(v) = alt;
                    prev(v) = u;  % 记录前驱
                end
            end
        end
    end
end

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

function [pathWord, shortestPath] = bfs_pathword(adjMat, startNode, endNode)
    % BFS 求起点到终点的最小路段数，并返回路径
    % adjMat: 邻接矩阵
    % startNode, endNode: 起点终点索引
    % 返回:
    %   pathWord: 最小路段数 (不可达为 Inf)
    %   shortestPath: 节点序列
    
    numNodes = size(adjMat,1);
    pathWord = Inf(1,numNodes);
    prev = zeros(1,numNodes);  % 前驱节点，用于回溯路径
    visited = false(1,numNodes);
    
    queue = [startNode];
    pathWord(startNode) = 0;
    visited(startNode) = true;
    
    while ~isempty(queue)
        currentNode = queue(1);
        queue(1) = [];
    
        if currentNode == endNode
            break; % 已找到终点
        end
    
        neighbors = find(adjMat(currentNode,:) > 0);
        for i = 1:length(neighbors)
            neighbor = neighbors(i);
            if ~visited(neighbor)
                pathWord(neighbor) = pathWord(currentNode) + 1;
                prev(neighbor) = currentNode; % 记录前驱
                visited(neighbor) = true;
                queue(end+1) = neighbor;
            end
        end
    end
    
    if pathWord(endNode) == Inf
        shortestPath = [];
    else
        % 回溯路径
        shortestPath = endNode;
        while shortestPath(1) ~= startNode
            shortestPath = [prev(shortestPath(1)), shortestPath];
        end
        pathWord = pathWord(endNode);
    end
    end
    
    
function pathWords = bfs_all_pathwords(adjMat, startNode)
% BFS 求单源到所有节点的最小路段数
% adjMat: 邻接矩阵
% startNode: 起点索引
% 返回: 1*numNodes，包含 startNode 到所有点的最小路段数（不可达为 Inf）

numNodes = size(adjMat,1);
pathWords = Inf(1,numNodes);
visited = false(1,numNodes);

queue = [startNode];
pathWords(startNode) = 0;
visited(startNode) = true;

while ~isempty(queue)
    currentNode = queue(1);
    queue(1) = [];

    neighbors = find(adjMat(currentNode,:) > 0);
    for i = 1:length(neighbors)
        neighbor = neighbors(i);
        if ~visited(neighbor)
            pathWords(neighbor) = pathWords(currentNode) + 1;
            visited(neighbor) = true;
            queue(end+1) = neighbor;
        end
    end
end
end