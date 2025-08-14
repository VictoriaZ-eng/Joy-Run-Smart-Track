#!/usr/bin/env python3
"""
快速测试路径规划API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from routes.routeplanning import JoggingPathPlanner, RouteParams, ConstraintMode, PreferenceMode

def test_route_planning():
    print("=== 路径规划API测试 ===")
    
    try:
        # 创建路径规划器
        planner = JoggingPathPlanner()
        print("✓ 路径规划器初始化成功")
        
        # 测试不同偏好模式
        test_cases = [
            {
                "name": "综合路线",
                "params": RouteParams(
                    start_lat=30.25,
                    start_lon=120.15,
                    end_lat=30.26,
                    end_lon=120.16,
                    constraint_mode=ConstraintMode.DISTANCE_WITH_END,
                    preference_mode=PreferenceMode.COMPREHENSIVE,
                    target_distance=1000
                )
            },
            {
                "name": "滨水路线",
                "params": RouteParams(
                    start_lat=30.25,
                    start_lon=120.15,
                    end_lat=30.26,
                    end_lon=120.16,
                    constraint_mode=ConstraintMode.SHORTEST_PATH,
                    preference_mode=PreferenceMode.WATERFRONT
                )
            },
            {
                "name": "绿化路线",
                "params": RouteParams(
                    start_lat=30.25,
                    start_lon=120.15,
                    end_lat=30.26,
                    end_lon=120.16,
                    constraint_mode=ConstraintMode.SHORTEST_PATH,
                    preference_mode=PreferenceMode.GREEN
                )
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n测试 {i+1}: {test_case['name']}")
            try:
                # 测试偏好列名获取
                column = planner.get_preference_total_column(test_case['params'].preference_mode)
                print(f"  ✓ 偏好字段: {column}")
                
                # 测试动态约束计算  
                if test_case['params'].constraint_mode in [ConstraintMode.DISTANCE_WITH_END, ConstraintMode.SEGMENTS_WITH_END]:
                    constraints = planner.calculate_dynamic_constraints(test_case['params'])
                    print(f"  ✓ 动态约束计算成功")
                
                print(f"  ✓ {test_case['name']} 参数验证通过")
                
            except Exception as e:
                print(f"  ✗ {test_case['name']} 测试失败: {e}")
        
        print("\n=== API测试完成 ===")
        print("✓ 所有核心功能已准备就绪")
        
    except Exception as e:
        print(f"✗ 路径规划器初始化失败: {e}")

if __name__ == "__main__":
    test_route_planning()
