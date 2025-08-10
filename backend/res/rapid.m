%% 改进的慢跑路径优化算法（基于Dijkstra和BFS的中间节点路径筛选）
clear; clc; close all;

%% 控制台参数设置
% 基础数据
data = readtable('outputroad_clean.csv');
%==============================================================================
% 模式选择（1-4）
% 1=有终点，距离约束（Dijkstra）
% 2=有终点，路段数约束（BFS）
% 3=无终点，距离约束（Dijkstra）
% 4=无终点，路段数约束（BFS）

constraintMode = 1; %设置模式

%==============================================================================

%-------------------------- 通用参数（所有模式共享）--------------------------
startNode = 2903; % 起点（所有模式均需设置）
w1 = 1;          % Total的权重（建议1）
w2 = 0;          % 长度权重（w2>0时用长度计算比值，w2越大生成的路线越偏向于短距离（在约束范围内的短距离），同时每米可慢跑持续性下降，w2=1时每米可慢跑持续性最高）
w3 = 1;          % 路段数权重（w3>0时用路段数计算比值，w3越大生成的路线越偏向于短路段（在约束范围内的短路段），同时每段可慢跑持续性下降，w3=1时每段可慢跑持续性最高）
%------------------------------------------------------------------------------

%---------------------- 有终点模式（1/2）专用参数 ----------------------
if constraintMode == 1 || constraintMode == 2
    endNode = 1104;       % 终点（仅模式1/2需要）

    % 距离约束参数（模式1）
    PathLength_1 = 5000;   % 基准长度（真实值）
    PathTolerance_1 = 400; % 容差

    % 路段数约束参数（模式2）
    PathSegments_2 = 40;   % 基准路段数
    PathSegTolerance_2 = 5;% 容差
%----------------------------------------------------------------------

%---------------------- 无终点模式（3/4）专用参数 ----------------------
elseif constraintMode == 3 || constraintMode == 4
    endNode = [];% 模式3/4无需终点，自动忽略endNode

    % 距离约束参数（模式3）
    PathLength_3 = 5000;   % 基准长度（真实值）
    PathTolerance_3 = 400; % 容差

    % 路段数约束参数（模式4）
    PathSegments_4 = 40;   % 基准路段数
    PathSegTolerance_4 = 5;% 容差
end
%----------------------------------------------------------------------

%% 权重与参数合法性检测
fprintf("*****************************************************\n")
% 权重合法性
if w1 < 0
    error("w1必须为非负数");
end
if ~((w2 > 0 && w3 == 0) || (w2 == 0 && w3 > 0))
    error("w2和w3必须一正一零（w2>0用长度，w3>0用路段数）");
end
% 模式合法性
if ~ismember(constraintMode, [1,2,3,4])
    error("constraintMode必须为1-4（1/2有终点，3/4无终点）");
end
% 模式提示信息
if constraintMode == 1
    fprintf('当前模式：1（有终点，距离约束）\n');
    fprintf('起点: %d, 终点: %d\n', startNode, endNode);
    minPathLength = PathLength_1 - PathTolerance_1;
    maxPathLength = PathLength_1 + PathTolerance_1;
    fprintf('距离约束范围：%d-%d米\n', minPathLength, maxPathLength);
elseif constraintMode == 2
    fprintf('当前模式：2（有终点，路段数约束）\n');
    fprintf('起点: %d, 终点: %d\n', startNode, endNode);
    minPathSegments = PathSegments_2 - PathSegTolerance_2;
    maxPathSegments = PathSegments_2 + PathSegTolerance_2;
    fprintf('路段数约束范围：%d-%d段\n', minPathSegments, maxPathSegments);
elseif constraintMode == 3
    fprintf('当前模式：3（无终点，距离约束）\n');
    fprintf('起点: %d（无终点）\n', startNode);
    minPathLength = PathLength_3 - PathTolerance_3;
    maxPathLength = PathLength_3 + PathTolerance_3;
    fprintf('距离约束范围：%d-%d米\n', minPathLength, maxPathLength);
elseif constraintMode == 4
    fprintf('当前模式：4（无终点，路段数约束）\n');
    fprintf('起点: %d（无终点）\n', startNode);
    minPathSegments = PathSegments_4 - PathSegTolerance_4;
    maxPathSegments = PathSegments_4 + PathSegTolerance_4;
    fprintf('路段数约束范围：%d-%d段\n', minPathSegments, maxPathSegments);
end

% 提取路网基础信息
startX = data.startX;
startY = data.startY;
endX = data.endX;
endY = data.endY;
Distance = data.distance;    % 标准化距离（用于比值计算）
Distancereal = data.dis_ori; % 真实距离（仅用于约束和输出）
Score = data.Score;          % 道路得分
Total = data.Total;          % 标准化综合评价（用于比值计算）
Totalreal = data.toatl_ori1; % 真实综合评价（仅用于输出）

% 构建节点列表与邻接矩阵
allNodes = [startX, startY; endX, endY];
uniqueNodes = unique(allNodes, 'rows'); % 去重节点坐标
numNodes = size(uniqueNodes, 1);

% 初始化矩阵（存储距离、得分、综合评价等）
adjMat = zeros(numNodes);          % 标准化距离邻接矩阵（用于比值计算）
adjMatreal = zeros(numNodes);      % 真实距离邻接矩阵（用于约束）
scoreMat = zeros(numNodes);        % 得分矩阵
totalMat = zeros(numNodes);        % 标准化综合评价矩阵（用于比值计算）
totalMatreal = zeros(numNodes);    % 真实综合评价矩阵（用于输出）

% 填充矩阵（双向道路）
for i = 1:size(data, 1)
    % 找到节点坐标对应的索引
    startIdx = find(ismember(uniqueNodes, [startX(i), startY(i)], 'rows'));
    endIdx = find(ismember(uniqueNodes, [endX(i), endY(i)], 'rows'));
    % 双向赋值（无向图）
    adjMat(startIdx, endIdx) = Distance(i);
    adjMat(endIdx, startIdx) = Distance(i);
    adjMatreal(startIdx, endIdx) = Distancereal(i);
    adjMatreal(endIdx, startIdx) = Distancereal(i);
    scoreMat(startIdx, endIdx) = Score(i);
    scoreMat(endIdx, startIdx) = Score(i);
    totalMat(startIdx, endIdx) = Total(i);
    totalMat(endIdx, startIdx) = Total(i);
    totalMatreal(startIdx, endIdx) = Totalreal(i);
    totalMatreal(endIdx, startIdx) = Totalreal(i);
end

% 构建距离矩阵（不可达设为Inf）
distMat = adjMat;          % 标准化距离（用于比值计算）
distMat(distMat == 0) = Inf;
distMatreal = adjMatreal;  % 真实距离（用于约束和输出）
distMatreal(distMatreal == 0) = Inf;

% 确保起点终点不同
while endNode == startNode
    endNode = randi(numNodes);
end
fprintf('起点: 节点 %d, 终点: 节点 %d\n', startNode, endNode);


%% 基于约束筛选有效节点（距离约束或路段数约束）
if constraintMode == 1
    % 模式1：距离约束（用真实距离筛选）
    fprintf('基于距离约束筛选节点（%d-%d米）...\n', minPathLength, maxPathLength);
    % 计算起点/终点到所有节点的最短真实距离（用于约束）
    [startToAllDist, startPrev] = dijkstra_single_source(distMatreal, startNode);
    [endToAllDist, endPrev] = dijkstra_single_source(distMatreal, endNode);
    
    % 筛选满足总距离约束的节点（起点到节点+节点到终点的总真实距离在范围内）
    validNodeMask = (startToAllDist + endToAllDist) <= maxPathLength;
    validNodeMask(startNode) = true;
    validNodeMask(endNode) = true;
    validNodes = find(validNodeMask);
    
elseif constraintMode == 2
    % 模式2：路段数约束（用BFS筛选）
    fprintf('基于路段数约束筛选节点（%d-%d段）...\n', minPathSegments, maxPathSegments);
    % 计算起点/终点到所有节点的最少路段数（用于约束）
    startToAllPathWords = bfs_all_pathwords(adjMatreal, startNode);
    endToAllPathWords = bfs_all_pathwords(adjMatreal, endNode);
       
    % 筛选满足总路段数约束的节点
    validNodeMask = (startToAllPathWords + endToAllPathWords) <= maxPathSegments;
    validNodeMask(startNode) = true;
    validNodeMask(endNode) = true;
    validNodes = find(validNodeMask);

elseif constraintMode == 3
    % 模式3：无终点，距离约束（Dijkstra）
    fprintf('基于起点距离约束筛选节点（%d-%d米）...\n', minPathLength, maxPathLength);
    [startToAllDist, startPrev] = dijkstra_single_source(distMatreal, startNode);

    % 筛选：起点到节点的真实距离在范围内，且排除起点本身
    validNodeMask = startToAllDist <= maxPathLength;
    validNodeMask(startNode) = true;
    validNodes = find(validNodeMask);
    
elseif constraintMode == 4
    % 模式4：无终点，路段数约束（BFS）
    fprintf('基于起点路段数约束筛选节点（%d-%d段）...\n', minPathSegments, maxPathSegments);
    startToAllPathWords = bfs_all_pathwords(adjMatreal, startNode);

    % 筛选：起点到节点的路段数在范围内，且排除起点本身
    validNodeMask = startToAllPathWords <= maxPathSegments;
    validNodeMask(startNode) = true;
    validNodes = find(validNodeMask);
end

% 若没有有效节点则报错
if isempty(validNodes)
    error('没有满足约束条件的节点，请调整约束范围');
end
fprintf('约束筛选完成，剩余 %d 个有效节点\n', length(validNodes));

startCoord = uniqueNodes(startNode, :);
endCoord = uniqueNodes(endNode, :);

% 更新路网为有效节点子路网
uniqueNodes = uniqueNodes(validNodes, :);
adjMat = adjMat(validNodes, validNodes);
adjMatreal = adjMatreal(validNodes, validNodes);
scoreMat = scoreMat(validNodes, validNodes);
totalMat = totalMat(validNodes, validNodes);
totalMatreal = totalMatreal(validNodes, validNodes);
distMat = distMat(validNodes, validNodes);       % 标准化距离（用于比值计算）
distMatreal = distMatreal(validNodes, validNodes); % 真实距离（用于输出）
numNodes = size(uniqueNodes, 1);

startNode = find(ismember(uniqueNodes, startCoord, 'rows'));
endNode = find(ismember(uniqueNodes, endCoord, 'rows'));
if constraintMode == 1 || constraintMode == 2
    if isempty(startNode) || isempty(endNode)
        error('起点或终点被剔除了，无法继续路径计算。');
    end
else constraintMode == 3 || constraintMode == 4
    if isempty(startNode)
        error('起点被剔除了，无法继续路径计算。');
    end
end

fprintf('成功构建满足路径距离约束的子路网\n');

%% 计算各有效节点的中间路径指标（核心逻辑：预计算优化版）
% 预定义矩阵列索引常量
NODE_COL = 1;
TOTAL_COL = 2;          % 标准化综合评价（用于比值）
DIST_COL = 3;           % 标准化距离（用于比值）
SEGMENTS_COL = 4;       % 总路段数
TOTAL_REAL_COL = 5;     % 真实综合评价（输出）
DIST_REAL_COL = 6;      % 真实距离（输出）
RATIO_COL = 7;          % 原综合评价比值
SCORE_COL = 8;          % 总道路得分
SCORE_RATIO_LENGTH_COL = 9; 
SCORE_RATIO_SEGMENTS_COL = 10; 

% 初始化存储矩阵（扩展列数）
maxNodes = length(validNodes);
metricsMatrix = zeros(maxNodes + 1, 10);
rowIndex = 1;

%% 根据模式选择算法计算指标
if constraintMode == 1
    % 模式1：使用Dijkstra算法（距离优先）
    [startDist_std, startDist_real, startSegments, startTotal_std, startTotal_real, startScore, startPrev] = ...
        dijkstra_enhanced_dual(distMat, distMatreal, totalMat, totalMatreal, scoreMat, adjMat, startNode);

    [endDist_std, endDist_real, endSegments, endTotal_std, endTotal_real, endScore, endPrev] = ...
        dijkstra_enhanced_dual(distMat, distMatreal, totalMat, totalMatreal, scoreMat, adjMat, endNode);

elseif constraintMode == 2
    % 模式2：使用BFS算法（路段数优先）
    [startDist_std, startDist_real, startSegments, startTotal_std, startTotal_real, startScore, startPrev] = ...
        bfs_enhanced_dual(distMat, distMatreal, totalMat, totalMatreal, scoreMat, adjMat, startNode);

    [endDist_std, endDist_real, endSegments, endTotal_std, endTotal_real, endScore, endPrev] = ...
        bfs_enhanced_dual(distMat, distMatreal, totalMat, totalMatreal, scoreMat, adjMat, endNode);

elseif constraintMode == 3
    % 模式3：无终点，Dijkstra（仅起点指标）
    [startDist_std, startDist_real, startSegments, startTotal_std, startTotal_real, startScore, ~] = ...
        dijkstra_enhanced_dual(distMat, distMatreal, totalMat, totalMatreal, scoreMat, adjMat, startNode);

elseif constraintMode == 4
    % 模式4：无终点，BFS（仅起点指标）
    [startDist_std, startDist_real, startSegments, startTotal_std, startTotal_real, startScore, ~] = ...
        bfs_enhanced_dual(distMat, distMatreal, totalMat, totalMatreal, scoreMat, adjMat, startNode);
end

%% 遍历有效节点（新增得分及相关比值计算）
if constraintMode == 1 || constraintMode == 2
    for i = 1:length(validNodes)
        midNode = i;
        if midNode == startNode || midNode == endNode
            fprintf('跳过节点 %d（起点或终点）\n', midNode);
            continue;
        end
        
        % 提取基础指标（同上，略）
        startToMidDist_std = startDist_std(midNode);
        midToEndDist_std = endDist_std(midNode);
        startToMidTotal_std = startTotal_std(midNode);
        midToEndTotal_std = endTotal_std(midNode);
        startToMidDist_real = startDist_real(midNode);
        midToEndDist_real = endDist_real(midNode);
        startToMidTotal_real = startTotal_real(midNode);
        midToEndTotal_real = endTotal_real(midNode);
        startToMidSegments = startSegments(midNode);
        midToEndSegments = endSegments(midNode);
        
        % 新增：提取路径总得分（起点到中间节点+中间节点到终点）
        startToMidScore = startScore(midNode);       % 起点到中间节点的总得分
        midToEndScore = endScore(midNode);           % 中间节点到终点的总得分
        totalScore = startToMidScore + midToEndScore; % 完整路径总得分
        
        % 检查路径有效性（同上，略）
        if startToMidDist_std == Inf || midToEndDist_std == Inf
            fprintf('节点 %d：路径不可达，跳过\n', midNode);
            continue;
        end
        
        % 合并指标
        totalTotal_std = startToMidTotal_std + midToEndTotal_std; % 标准化综合评价总和（用于比值）
        totalDist_std = startToMidDist_std + midToEndDist_std;     % 标准化距离总和（用于比值）
        totalSegments = startToMidSegments + midToEndSegments;
        totalTotal_real = startToMidTotal_real + midToEndTotal_real; % 真实综合评价总和（输出）
        totalDist_real = startToMidDist_real + midToEndDist_real;     % 真实距离总和（输出）
        
        % -------------------- 新增约束检查（模式1/2）--------------------
        % 模式1：严格检查真实总距离在[minPathLength, maxPathLength]
        if constraintMode == 1
            if totalDist_real < minPathLength || totalDist_real > maxPathLength
                fprintf('节点 %d：真实总距离（%.2f米）超出约束范围（%d-%d米），跳过\n', ...
                    midNode, totalDist_real, minPathLength, maxPathLength);
                continue;
            end
        % 模式2：严格检查总路段数在[minPathSegments, maxPathSegments]
        elseif constraintMode == 2
            if totalSegments < minPathSegments || totalSegments > maxPathSegments
                fprintf('节点 %d：总路段数（%d）超出约束范围（%d-%d段），跳过\n', ...
                    midNode, totalSegments, minPathSegments, maxPathSegments);
                continue;
            end
        end
        % ------------------------------------------------------
        
        % 计算比值
        if w2 > 0 && totalDist_std > 0
            ratio = (totalTotal_std^w1) / (totalDist_std^w2);
        elseif w3 > 0 && totalSegments > 0
            ratio = (totalTotal_std^w1) / (totalSegments^w3);
        else
            fprintf('节点 %d：比值计算失败（分母为0），跳过\n', midNode);
            continue;
        end
    
        % 计算得分相关比值
        if totalDist_std > 0
            score_ratio_length = totalTotal_std / totalDist_std;
        else
            score_ratio_length = 0;
        end
        if totalSegments > 0
            score_ratio_segments = totalTotal_std / totalSegments;
        else
            score_ratio_segments = 0;
        end
        
        % 存储指标
        metricsMatrix(rowIndex, :) = [midNode, totalTotal_std, totalDist_std, ...
            totalSegments, totalTotal_real, totalDist_real, ratio, ...
            totalScore, score_ratio_length, score_ratio_segments];
        fprintf('节点 %d：记录成功（综合比值=%.4f，得分/长度=%.4f，得分/路段=%.4f）\n', ...
            midNode, ratio, score_ratio_length, score_ratio_segments);
        rowIndex = rowIndex + 1;

        % 补充直接路径（新增得分计算）
        directDist_std = startDist_std(endNode);
        directDist_real = startDist_real(endNode);
        directSegments = startSegments(endNode);
        directTotal_std = startTotal_std(endNode);
        directTotal_real = startTotal_real(endNode);
        directScore = startScore(endNode); % 直接路径总得分
        
        % 直接路径的约束检查
        if directDist_std < Inf && directSegments == 1
            % 模式1：检查直接路径距离是否在约束范围内
            if constraintMode == 1
                if directDist_real < minPathLength || directDist_real > maxPathLength
                    fprintf('直接路径：真实距离（%.2f米）超出约束范围（%d-%d米），跳过\n', ...
                        directDist_real, minPathLength, maxPathLength);
                    % 不记录该路径，直接跳过
                    continue;
                end
            % 模式2：检查直接路径路段数是否在约束范围内
            elseif constraintMode == 2
                if directSegments < minPathSegments || directSegments > maxPathSegments
                    fprintf('直接路径：路段数（%d）超出约束范围（%d-%d段），跳过\n', ...
                        directSegments, minPathSegments, maxPathSegments);
                    % 不记录该路径，直接跳过
                    continue;
                end
            end
            
            % 计算比值（通过约束检查后才计算）
            if w2 > 0 && directDist_std > 0
                directRatio = (directTotal_std^w1) / (directDist_std^w2);
            else
                directRatio = (directTotal_std^w1) / (directSegments^w3);
            end
            % 计算得分相关比值
            direct_score_ratio_length = directTotal_std / directDist_std;
            direct_score_ratio_segments = directTotal_std / directSegments;
            
            metricsMatrix(rowIndex, :) = [-1, directTotal_std, directDist_std, ...
                directSegments, directTotal_real, directDist_real, directRatio, ...
                directScore, direct_score_ratio_length, direct_score_ratio_segments];
            fprintf('直接路径：记录成功（综合比值=%.4f，每米可慢跑持续性=%.4f，每段可慢跑持续性=%.4f）\n', ...
                directRatio, direct_score_ratio_length, direct_score_ratio_segments);
            rowIndex = rowIndex + 1;
        end
    end

else
    for i = 1:length(validNodes)
        midNode = i; % 当前节点
        if midNode == startNode
            fprintf('跳过节点 %d（起点）\n', midNode);
            continue;
        end
        
        % 提取基础指标
        startToMidDist_std = startDist_std(midNode);
        startToMidTotal_std = startTotal_std(midNode);
        startToMidDist_real = startDist_real(midNode);  % 真实距离
        startToMidTotal_real = startTotal_real(midNode);
        startToMidSegments = startSegments(midNode);    % 路段数
        startToMidScore = startScore(midNode);
        totalScore = startToMidScore;
        
        % 检查路径可达性
        if startToMidDist_std == Inf 
            fprintf('节点 %d：路径不可达，跳过\n', midNode);
            continue;
        end
        
        % 合并指标（模式3/4的路径是"起点→当前节点"，无需合并）
        totalTotal_std = startToMidTotal_std;
        totalDist_std = startToMidDist_std;
        totalSegments = startToMidSegments;
        totalTotal_real = startToMidTotal_real;
        totalDist_real = startToMidDist_real;  % 真实总距离
        
        % -------------------- 约束检查 --------------------
        % 模式3：严格检查真实距离在[minPathLength, maxPathLength]
        if constraintMode == 3
            if totalDist_real < minPathLength || totalDist_real > maxPathLength
                fprintf('节点 %d：真实距离（%.2f米）超出约束范围（%d-%d米），跳过\n', ...
                    midNode, totalDist_real, minPathLength, maxPathLength);
                continue;
            end
        % 模式4：严格检查路段数在[minPathSegments, maxPathSegments]
        elseif constraintMode == 4
            if totalSegments < minPathSegments || totalSegments > maxPathSegments
                fprintf('节点 %d：路段数（%d）超出约束范围（%d-%d段），跳过\n', ...
                    midNode, totalSegments, minPathSegments, maxPathSegments);
                continue;
            end
        end
        % ------------------------------------------------------
        
        % 计算比值
        if w2 > 0 && totalDist_std > 0
            ratio = (totalTotal_std^w1) / (totalDist_std^w2);
        elseif w3 > 0 && totalSegments > 0
            ratio = (totalTotal_std^w1) / (totalSegments^w3);
        else
            fprintf('节点 %d：比值计算失败（分母为0），跳过\n', midNode);
            continue;
        end
    
        % 计算得分相关比值
        if totalDist_std > 0
            score_ratio_length = totalTotal_std / totalDist_std;
        else
            score_ratio_length = 0;
        end
        if totalSegments > 0
            score_ratio_segments = totalTotal_std / totalSegments;
        else
            score_ratio_segments = 0;
        end
        
        % 存储指标
        metricsMatrix(rowIndex, :) = [midNode, totalTotal_std, totalDist_std, ...
            totalSegments, totalTotal_real, totalDist_real, ratio, ...
            totalScore, score_ratio_length, score_ratio_segments];
        fprintf('节点 %d：记录成功（综合比值=%.4f，得分/长度=%.4f，得分/路段=%.4f）\n', ...
            midNode, ratio, score_ratio_length, score_ratio_segments);
        rowIndex = rowIndex + 1;
    end

end

% 去除未使用的行
metricsMatrix = metricsMatrix(1:rowIndex-1, :);

% 调试：输出最终矩阵行数
fprintf('有效路径总数：%d\n', size(metricsMatrix, 1));
if size(metricsMatrix, 1) == 0
    error('没有有效路径，请放松约束或检查路网数据');
end

%% 筛选最优路径（比值最大的路径）
if isempty(metricsMatrix) || size(metricsMatrix, 1) == 0
    error('没有找到有效路径，请调整约束参数');
end

%% 筛选最优路径（含得分相关指标）
[maxRatio, bestIdx] = max(metricsMatrix(:, RATIO_COL));
bestRow = metricsMatrix(bestIdx, :);

% 提取最优路径的所有指标（新增得分相关）
bestNode = bestRow(NODE_COL);
bestTotal_std = bestRow(TOTAL_COL);
bestDist_std = bestRow(DIST_COL);
bestSegments = bestRow(SEGMENTS_COL);
bestTotal_real = bestRow(TOTAL_REAL_COL);
bestDist_real = bestRow(DIST_REAL_COL);
bestRatio = bestRow(RATIO_COL);
bestScore = bestRow(SCORE_COL); % 总得分
bestScoreRatioLength = bestRow(SCORE_RATIO_LENGTH_COL); 
bestScoreRatioSegments = bestRow(SCORE_RATIO_SEGMENTS_COL); 

%% 重构最优路径
if constraintMode == 1 || constraintMode == 2
    % 有终点模式：重构起点-中间节点-终点或直接路径
    if bestNode == -1
        % 直接路径
        [~, bestPath] = dijkstra(distMatreal, startNode, endNode);
    else
        [~, startToMidPath] = dijkstra(distMatreal, startNode, bestNode);
        [~, midToEndPath] = dijkstra(distMatreal, bestNode, endNode);
        bestPath = [startToMidPath, midToEndPath(2:end)];
    end
else
    % 无终点模式：重构起点到最优节点的路径
    [~, bestPath] = dijkstra(distMatreal, startNode, bestNode);
end


%% 输出最优路径结果（新增得分相关输出）
fprintf("\n========= 最优慢跑路径结果 =========\n");
fprintf('1. 综合评价最优比值 (标准化Total^w1 / 标准化距离^w2/^w3)：%.4f\n', bestRatio);
fprintf('2. 总道路得分：%.2f\n', bestScore);
fprintf('3. 每米可慢跑持续性：%.4f\n', bestScoreRatioLength);
fprintf('4. 每段可慢跑持续性：%.4f\n', bestScoreRatioSegments);
fprintf('-------------------------------------\n');
fprintf('总综合评价（标准化）：%.2f，总综合评价（真实）：%.2f\n', bestTotal_std, bestTotal_real);
fprintf('总长度（标准化）：%.2f，总长度（真实）：%.2f 米\n', bestDist_std, bestDist_real);
fprintf('总路段数：%d\n', bestSegments);
fprintf('路径节点序列：');
fprintf('%d ', bestPath);
fprintf('\n');

%% 绘制初始路网与起终点
figure;
gplot(adjMat, uniqueNodes, 'k:');  % 用虚线绘制初始路网
hold on;

% 绘制所有节点（小蓝点）
plot(uniqueNodes(:,1), uniqueNodes(:,2), 'o', 'MarkerSize', 1, ...
     'MarkerFaceColor', 'b', 'MarkerEdgeColor', 'k');

% 标记起终点
scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled', 'DisplayName', '起点');
scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled', 'DisplayName', '终点');

title('起点和终点在路网中的位置', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('X 坐标', 'FontSize', 12);
ylabel('Y 坐标', 'FontSize', 12);
legend;
axis tight;
set(gca, 'FontSize', 12);
hold off;

%% 约束筛选后的路网绘图
figure;
gplot(adjMat, uniqueNodes, 'k:');  % 用虚线绘制约束筛选后的路网
hold on;

% 绘制所有节点
plot(uniqueNodes(:,1), uniqueNodes(:,2), 'o', 'MarkerSize', 1, ...
     'MarkerFaceColor', 'b', 'MarkerEdgeColor', 'k');

% 标记起终点
scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled', 'DisplayName', '起点');
scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled', 'DisplayName', '终点');

title('约束筛选后的路网与起终点', 'FontSize', 14, 'FontWeight', 'bold');
xlabel('X 坐标', 'FontSize', 12);
ylabel('Y 坐标', 'FontSize', 12);
legend;
axis tight;
set(gca, 'FontSize', 12);
hold off;

%% 可视化最优路径
figure;
gplot(adjMat, uniqueNodes, 'k:'); hold on;
% 绘制所有节点
plot(uniqueNodes(:,1), uniqueNodes(:,2), 'o', 'MarkerSize', 1, ...
     'MarkerFaceColor', 'b', 'MarkerEdgeColor', 'k');
% 绘制最优路径
for i = 1:length(bestPath)-1
    x = [uniqueNodes(bestPath(i),1), uniqueNodes(bestPath(i+1),1)];
    y = [uniqueNodes(bestPath(i),2), uniqueNodes(bestPath(i+1),2)];
    plot(x, y, 'r-', 'LineWidth', 2);
end
% 标记起点（模式3/4无终点）
scatter(uniqueNodes(startNode,1), uniqueNodes(startNode,2), 100, 'g', 'filled', 'DisplayName', '起点');
if constraintMode == 1 || constraintMode == 2
    scatter(uniqueNodes(endNode,1), uniqueNodes(endNode,2), 100, 'r', 'filled', 'DisplayName', '终点');
end
title(sprintf('最优路径（模式%d，比值=%.4f）', constraintMode, bestRatio), 'FontSize', 14);
xlabel('X 坐标'); ylabel('Y 坐标');
axis tight; hold off;

%% 增强版Dijkstra函数（新增scoreMat处理）
function [dist_std, dist_real, segments, total_std, total_real, score, prev] = dijkstra_enhanced_dual(...
    distMat_std, distMat_real, totalMat_std, totalMat_real, scoreMat, adjMat, startNode)
    numNodes = size(distMat_std, 1);
    dist_std = Inf(1, numNodes);   % 标准化距离
    dist_real = Inf(1, numNodes);  % 真实距离
    segments = zeros(1, numNodes); % 路段数
    total_std = zeros(1, numNodes);% 标准化综合评价
    total_real = zeros(1, numNodes);% 真实综合评价
    score = zeros(1, numNodes);    % 总道路得分（新增）
    prev = zeros(1, numNodes);     % 前驱节点
    visited = false(1, numNodes);
    
    % 初始化起点
    dist_std(startNode) = 0;
    dist_real(startNode) = 0;
    visited(startNode) = true;
    
    % 优先队列
    queue = startNode;
    
    while ~isempty(queue)
        [~, idx] = min(dist_std(queue));
        u = queue(idx);
        queue(idx) = [];
        
        % 遍历邻接节点
        neighbors = find(adjMat(u, :) > 0);
        for v = neighbors
            if ~visited(v) || dist_std(u) + distMat_std(u, v) < dist_std(v)
                % 更新距离、综合评价（同上，略）
                dist_std(v) = dist_std(u) + distMat_std(u, v);
                dist_real(v) = dist_real(u) + distMat_real(u, v);
                segments(v) = segments(u) + 1;
                total_std(v) = total_std(u) + totalMat_std(u, v);
                total_real(v) = total_real(u) + totalMat_real(u, v);
                
                % 新增：累加道路得分
                score(v) = score(u) + scoreMat(u, v);
                
                prev(v) = u;
                if ~visited(v)
                    visited(v) = true;
                    queue = [queue, v];
                end
            end
        end
    end
end

%% 修改后的BFS增强版函数（输出真实标准化距离，独立存储路段数）
function [dist_std, dist_real, segments, total_std, total_real, score, prev] = bfs_enhanced_dual(...
    distMat_std, distMat_real, totalMat_std, totalMat_real, scoreMat, adjMat, startNode)
    numNodes = size(adjMat, 1);
    dist_std = Inf(1, numNodes);   % 真实标准化距离（不再用路段数替代）
    dist_real = Inf(1, numNodes);  % 累计真实距离
    segments = Inf(1, numNodes);   % 独立存储路段数（核心指标）
    total_std = zeros(1, numNodes);% 累计标准化综合评价
    total_real = zeros(1, numNodes);% 累计真实综合评价
    score = zeros(1, numNodes);    % 累计道路得分
    prev = zeros(1, numNodes);     % 前驱节点
    visited = false(1, numNodes);
    
    % 初始化起点
    dist_std(startNode) = 0;       % 标准化距离初始化为0
    dist_real(startNode) = 0;      % 真实距离初始化为0
    segments(startNode) = 0;       % 路段数初始化为0
    visited(startNode) = true;
    queue = startNode;             % BFS队列（FIFO）
    
    while ~isempty(queue)
        u = queue(1);              % 取出队首节点（保持BFS特性）
        queue(1) = [];             % 移除已处理节点
        
        % 遍历邻接节点
        neighbors = find(adjMat(u, :) > 0);
        for v = neighbors
            if ~visited(v)         % BFS只访问未访问节点（保证最少路段数）
                % 关键修改：累计真实标准化距离（不再用路段数替代）
                dist_std(v) = dist_std(u) + distMat_std(u, v);
                % 累计真实距离
                dist_real(v) = dist_real(u) + distMat_real(u, v);
                % 独立累计路段数（与距离计算分离）
                segments(v) = segments(u) + 1;
                % 累计其他指标
                total_std(v) = total_std(u) + totalMat_std(u, v);
                total_real(v) = total_real(u) + totalMat_real(u, v);
                score(v) = score(u) + scoreMat(u, v);
                % 记录前驱
                prev(v) = u;
                visited(v) = true;
                queue = [queue, v];  % 加入队尾
            end
        end
    end
end

%% Dijkstra单源函数（用于约束筛选和路径重构）
function [dist, prev] = dijkstra_single_source(distMat, startNode)
    numNodes = size(distMat, 1);
    dist = Inf(1, numNodes);
    prev = zeros(1, numNodes); % 前驱节点
    visited = false(1, numNodes);
    dist(startNode) = 0;
    
    for i = 1:numNodes
        % 找未访问的最短距离节点
        minDist = Inf;
        u = -1;
        for j = 1:numNodes
            if ~visited(j) && dist(j) < minDist
                minDist = dist(j);
                u = j;
            end
        end
        if u == -1 || minDist == Inf, break; end % 无可达节点
        visited(u) = true;
        
        % 更新邻接节点距离
        for v = 1:numNodes
            if ~visited(v) && distMat(u, v) < Inf && distMat(u, v) > 0
                if dist(u) + distMat(u, v) < dist(v)
                    dist(v) = dist(u) + distMat(u, v);
                    prev(v) = u;
                end
            end
        end
    end
end

% 两点路径函数（用于路径重构）
function [dist, path] = dijkstra(distMat, startNode, endNode)
    [dist, prev] = dijkstra_single_source(distMat, startNode);
    if dist(endNode) == Inf || isempty(prev)
        dist = Inf;
        path = [];
        return;
    end
    % 重构路径
    path = endNode;
    while path(1) ~= startNode
        if prev(path(1)) == 0, path = []; return; end % 路径断裂
        path = [prev(path(1)), path];
    end
end

%% BFS单源最少路段数（用于约束筛选）
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