#!/usr/bin/env python3
"""
快速数据库状态检查脚本
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.schema.routeplanning_db_init import check_database_status

if __name__ == "__main__":
    print("=== 快速数据库状态检查 ===")
    check_database_status()
