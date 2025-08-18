#!/usr/bin/env python3
"""
修复后的偏好模式测试脚本
验证相同起点终点和约束条件下，不同偏好模式是否能产生不同的路径结果
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from routes.routeplanning import plan_jogging_route, PreferenceMode, ConstraintMode

def test_preference_modes():
    """测试不同偏好模式在相同约束条件下的效果"""
    
    print("=== 偏好模式差异化测试 ===")
    print("相同起点、终点、约束条件，测试不同偏好模式的效果")
    
    # 固定的测试参数 - UPDATE: 根据动态约束结果调整
    start_lat = 30.263982
    start_lon = 120.1588077
    end_lat = 30.341572
    end_lon = 120.1876803
    target_distance = 15000  # 调整为15公里，在动态范围内
    distance_tolerance = 3000  # 增大容差
    
    # 测试不同偏好模式
    preference_modes = [
        (PreferenceMode.COMPREHENSIVE.value, "综合得分"),
        (PreferenceMode.WATERFRONT.value, "滨水路线"),
        (PreferenceMode.GREEN.value, "绿化路线"),
        (PreferenceMode.OPEN_VIEW.value, "视野开阔"),
        (PreferenceMode.WELL_LIT.value, "夜间灯光"),
        (PreferenceMode.FACILITIES.value, "设施便利"),
        (PreferenceMode.GENTLE_SLOPE.value, "坡度平缓")
    ]
    
    results = []
    
    for mode_value, mode_name in preference_modes:
        print(f"\n--- 测试偏好模式 {mode_value}: {mode_name} ---")
        
        result = plan_jogging_route(
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            constraint_mode=ConstraintMode.DISTANCE_WITH_END.value,  # 有终点距离约束
            preference_mode=mode_value,
            target_distance=target_distance,
            distance_tolerance=distance_tolerance,
            w1=1.0,
            w2=0.0,
            w3=1.0
        )
        
        if result['success']:
            print(f"✓ {mode_name} 规划成功")
            print(f"  总距离: {result['total_distance']:.2f}米")
            print(f"  总路段数: {result['total_segments']}")
            print(f"  优化比值: {result['optimization_ratio']:.6f}")
            print(f"  每米得分: {result['score_per_meter']:.6f}")
            print(f"  总得分: {result['total_score']:.2f}")
            
            # 如果GeoJSON中有偏好评分，显示它
            if 'preference_score' in result['geojson']['properties']:
                preference_score = result['geojson']['properties']['preference_score']
                print(f"  偏好评分: {preference_score:.2f}")
            
            results.append({
                'mode': mode_name,
                'mode_value': mode_value,
                'distance': result['total_distance'],
                'segments': result['total_segments'],
                'ratio': result['optimization_ratio'],
                'score_per_meter': result['score_per_meter'],
                'total_score': result['total_score'],
                'preference_score': result['geojson']['properties'].get('preference_score', 0)
            })
        else:
            print(f"✗ {mode_name} 规划失败: {result['error']}")
    
    # 分析结果差异
    print("\n=== 结果差异分析 ===")
    if len(results) >= 2:
        print("偏好模式对比:")
        print(f"{'模式':<10} {'距离(米)':<10} {'路段数':<8} {'优化比值':<12} {'偏好评分':<10}")
        print("-" * 60)
        
        for r in results:
            print(f"{r['mode']:<10} {r['distance']:<10.0f} {r['segments']:<8} {r['ratio']:<12.6f} {r['preference_score']:<10.2f}")
        
        # 检查是否有差异
        distances = [r['distance'] for r in results]
        ratios = [r['ratio'] for r in results]
        preference_scores = [r['preference_score'] for r in results]
        
        distance_diff = max(distances) - min(distances)
        ratio_diff = max(ratios) - min(ratios)
        preference_diff = max(preference_scores) - min(preference_scores)
        
        print(f"\n差异统计:")
        print(f"距离差异: {distance_diff:.2f}米")
        print(f"优化比值差异: {ratio_diff:.6f}")
        print(f"偏好评分差异: {preference_diff:.2f}")
        
        if distance_diff > 100 or ratio_diff > 0.001 or preference_diff > 1:
            print("✓ 偏好模式生效！不同偏好产生了不同的路径结果")
        else:
            print("✗ 偏好模式可能未生效，结果过于相似")
    else:
        print("测试结果不足，无法进行差异分析")

def test_no_endpoint_mode():
    """测试无终点模式的偏好效果"""
    
    print("\n\n=== 无终点模式偏好测试 ===")
    
    # 测试无终点距离约束模式 - UPDATE: 调整参数
    start_lat = 30.263982
    start_lon = 120.1588077
    target_distance = 5000  # 调整为5000米，在动态范围内
    distance_tolerance = target_distance * 0.1  # 调整容差，为目标距离的0.1
    
    preference_modes = [
        (PreferenceMode.COMPREHENSIVE.value, "综合得分"),
        (PreferenceMode.WATERFRONT.value, "滨水路线"),
        (PreferenceMode.GREEN.value, "绿化路线"),
        (PreferenceMode.OPEN_VIEW.value, "视野开阔"),
        (PreferenceMode.WELL_LIT.value, "夜间灯光"),
        (PreferenceMode.FACILITIES.value, "设施便利"),
        (PreferenceMode.GENTLE_SLOPE.value, "坡度平缓")

    ]
    
    for mode_value, mode_name in preference_modes:
        print(f"\n--- 无终点模式测试: {mode_name} ---")
        
        result = plan_jogging_route(
            start_lat=start_lat,
            start_lon=start_lon,
            constraint_mode=ConstraintMode.DISTANCE_NO_END.value,  # 无终点距离约束
            preference_mode=mode_value,
            target_distance=target_distance,
            distance_tolerance=distance_tolerance,
            w1=1.0,
            w2=0.0,
            w3=1.0
        )
        
        if result['success']:
            print(f"✓ {mode_name} 规划成功")
            print(f"  总距离: {result['total_distance']:.2f}米")
            print(f"  优化比值: {result['optimization_ratio']:.6f}")
            preference_score = result['geojson']['properties'].get('preference_score', 0)
            print(f"  偏好评分: {preference_score:.2f}")
        else:
            print(f"✗ {mode_name} 规划失败: {result['error']}")

if __name__ == "__main__":
    # test_preference_modes()
    test_no_endpoint_mode()
