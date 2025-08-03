%% 传统的蚁群算法（含Total/路段数指标）
clear; clc; close all;

%% 参数设置
numAnts = 30;       % 蚂蚁数量
maxIter = 100;      % 最大迭代次数
alpha = 1;         % 信息素重要程度
beta = 2;          % 启发因子重要程度
rho = 0.1;         % 信息素挥发系数
Q = 1;             % 信息素强度常数

%% 并行池初始化
if isempty(gcp('nocreate'))
    parpool;       % 启动并行池
end

%% 读取CSV文件并构建路网（新增Total处理）
data = readtable('outputroad.csv');
startX = data.startX;
startY = data.startY;
endX = data.endX;
endY = data.endY;
Distance = data.dis_ori;
Total = data.Total;  % 新增Total读取
Score = data.Score; 

% 构建节点列表和邻接矩阵
allNodes = [startX, startY; endX, endY];
uniqueNodes = unique(allNodes, 'rows');
numNodes = size(uniqueNodes, 1);
adjMat = zeros(numNodes);
totalMat = zeros(numNodes);  % 新增Total矩阵
scoreMat = zeros(numNodes);  % 得分矩阵
bestDist = Inf;

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
distMat = adjMat;         
distMat(~adjMat) = Inf;   
distMat(distMat == 0) = eps; 

% 固定测试起点和终点
startNode = 2903; %起点     outputroad建议组合（2852、1664）、smallroad建议组合（165、63）
endNode = 1104;   %终点
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

%% 初始化信息素矩阵
pheromone = ones(numNodes) * 0.1; 
pheromone(adjMat == 0) = 0;       

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
noImproveCount = 0;       % 新增：连续未改进次数计数器
earlyStopFlag = false;    % 新增：早停标志位

%% 主循环（新增指标计算）
for iter = 1:maxIter
    antsPaths = cell(numAnts, 1);
    antsDist = Inf(numAnts, 1);
    antsScores = zeros(numAnts, 1);  % 记录每只蚂蚁的总得分
    antsTotal = zeros(numAnts, 1);
    pathword = zeros(numAnts, 1);
    totaldividepath = zeros(numAnts, 1); % 预分配
    avrpathscore = zeros(numAnts, 1);
    
    fprintf('\n------ 第 %d 次迭代 ------\n', iter);
    validPathCount = 0;  % 记录符合路径长度约束的蚂蚁数量
    
    % 并行生成蚂蚁路径（新增指标采集）
    parfor k = 1:numAnts
        validPath = false;
        while ~validPath
            try
                currentNode = startNode;
                visited = currentNode;
                path = [currentNode]; % 当前路径记录
                tempBarriers = [];     % 当前蚂蚁的临时障碍
                backoffSteps = 0;     % 回退计数器
                maxBackoff = 20;       % 最大允许回退次数
                totalScore = 0;  % 初始化总得分
                totalTotal = 0;
                
                % 路径搜索循环
                while currentNode ~= endNode
                       % 获取可达节点（排除已访问路径节点和临时障碍）
                    neighbors = find(adjMat(currentNode, :) > 0);
                    reachable = setdiff(neighbors, [path, tempBarriers]);

                    if isempty(reachable)
                        if length(path) == 1 || backoffSteps > maxBackoff
                           error('无法回退，重新构建路径');
                        end
                        % 回退逻辑：移除当前节点并标记为临时障碍
                        tempBarriers = [tempBarriers, currentNode];
                        prevNode = path(end-1);
                        % 扣除从prevNode到currentNode的分数和Total值
                        totalScore = totalScore - scoreMat(prevNode, currentNode); % 新增回退扣除
                        totalTotal = totalTotal - totalMat(prevNode, currentNode); % 新增回退扣除
                        path(end) = []; % 回退到上一节点
                        currentNode = prevNode;
                        backoffSteps = backoffSteps + 1;
                        continue;
                    end

                    % 计算转移概率
                    if length(reachable) == 1
                        nextNode = reachable;
                    else
                        % 计算转移概率
                        pheromoneVec = pheromone(currentNode, reachable).^alpha;
                        heuristicVec = (1./distMat(currentNode, reachable)).^beta;
                        probabilities = pheromoneVec .* heuristicVec;
                        probabilities = probabilities / sum(probabilities);
                        
                        % 选择下一个节点
                        nextNode = randsample(reachable, 1, true, probabilities);
                    end
                    
                    path = [path nextNode];
                    visited = [visited nextNode];
                    totalScore = totalScore + scoreMat(currentNode, nextNode);  % 累加得分
                    totalTotal = totalTotal + totalMat(currentNode, nextNode);  % 累加Total
                    currentNode = nextNode;
                    backoffSteps = 0; % 重置回退计数器
                end
                
                    totalDist = sum(distMat(sub2ind(size(distMat),...
                        path(1:end-1), path(2:end)))); 
                    validPath = true;
            catch
                continue;
            end
        end
        
        % 存储结果
        antsPaths{k} = path;
        antsDist(k) = totalDist;
        antsScores(k) = totalScore;  % 记录总得分
        antsTotal(k) = totalTotal;   % 记录Total值
        pathword(k) = (length(antsPaths{k}) - 1)
        avrpathscore(k) = antsTotal(k)/pathword(k);
        fprintf('蚂蚁 %d: 路径长度 = %.2f, 总得分 = %.2f, Total = %.2f, 总路段数 = %.2f, 平均道路得分 = %.2f\n', k, antsDist(k), antsScores(k), antsTotal(k), pathword(k), avrpathscore(k)); 
      
    end
    
    %% 更新最优路径（新增比值计算）
    [minIterDist, idx] = min(antsDist);
    iterBestDist(iter) = minIterDist;
    
    if minIterDist < bestDist
        bestDist = minIterDist;
        BestTotal = antsTotal(idx);
        Bestpathword = pathword(idx);
        bestavrpathscore = avrpathscore(idx);
        bestPath = antsPaths{idx};
        bestScores = antsScores(idx);
    end
    allBestScores(iter) = bestScores; % 记录最优路径的得分
    allBestDist(iter) = bestDist;
    allBestTotal(iter) = BestTotal;
    allBestpathword(iter) = Bestpathword;
    allavrpathscore(iter) = bestavrpathscore;
    
    %% 信息素更新（保持核心逻辑）
    pheromone = (1 - rho) * pheromone;
    delta_pheromone = Q / bestDist;
    for i = 1:length(bestPath)-1
        from = bestPath(i);
        to = bestPath(i+1);
        pheromone(from, to) = pheromone(from, to) + delta_pheromone;
        pheromone(to, from) = pheromone(from, to) + delta_pheromone; 
    end
    
    fprintf('迭代 %3d: 当前最优=%.2f | 全局最优=%.2f | 得分比=%.2f |  路段数=%.2f| 总得分=%.2f\n',...
           iter, minIterDist, bestDist, allavrpathscore(iter),allBestpathword(iter), allBestScores(iter));
end

%% 增强可视化（新增比值显示）
figure;
subplot(2,1,1);
hold on;
gplot(adjMat, uniqueNodes, '-k');
scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled');
scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled');

% 绘制最优路径
pathX = uniqueNodes(bestPath,1);
pathY = uniqueNodes(bestPath,2);
plot(pathX, pathY, 'r-', 'LineWidth', 2);
title(sprintf('最优路径: %.1f米 | Total/路段=%.1f', bestDist, allavrpathscore(end)));
xlabel('X 坐标'); ylabel('Y 坐标');
axis equal;

% 双指标收敛曲线
subplot(2,1,2);
yyaxis left
plot(allBestDist, 'b-', 'LineWidth', 1.5);
ylabel('路径长度');
yyaxis right
plot(allavrpathscore, 'r--', 'LineWidth', 1.5);
ylabel('Total/路段数');
title('双指标收敛曲线');
xlabel('迭代次数');
grid on;

%% 增强结果输出
fprintf('\n========= 最终优化结果 =========\n');
fprintf('路径总长: %.2f米\n', bestDist);
fprintf('累计Total值: %.2f\n', allBestTotal(end));
fprintf('使用路段数: %d段\n', allBestpathword(end));
fprintf('Total/路段数: %.2f\n', allavrpathscore(end));
fprintf('路径节点序列:\n');
disp(bestPath);