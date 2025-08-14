"""
数据库初始化脚本 - 为智能慢跑路径规划设置PostGIS和pgRouting
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'joy_run_db',
    'user': 'postgres',
    'password': 'postgres1'
}

def init_database(drop_existing=False):
    """
    初始化数据库，创建必要的扩展和索引
    UPDATE: 支持新的偏好模式字段，兼容updated路径规划功能
    
    Args:
        drop_existing: 是否删除现有的路径规划表重新创建
    """
    
    conn = None
    cursor = None
    
    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("开始初始化数据库...")
        
        # 1. 启用PostGIS扩展
        logger.info("启用PostGIS扩展...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        
        # 2. 启用pgRouting扩展
        logger.info("启用pgRouting扩展...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgrouting;")
        
        # UPDATE: 3. 处理现有表格（新增删除重建选项）
        if drop_existing:
            logger.info("删除现有的路径规划表...")
            cursor.execute("DROP TABLE IF EXISTS edgesmodified CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS nodesmodified CASCADE;")
            cursor.execute("DROP VIEW IF EXISTS network_stats CASCADE;")
            cursor.execute("DROP VIEW IF EXISTS high_quality_edges CASCADE;")
            logger.info("现有表格已删除")
        
        # UPDATE: 4. 检查表是否存在，创建或更新edgesmodified表
        logger.info("检查和创建/更新数据表...")
        
        # 检查edgesmodified表是否存在
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'edgesmodified'
        );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists or drop_existing:
            # 创建新的edgesmodified表（包含原有字段和新增偏好模式字段）
            logger.info("创建edgesmodified表（包含新的偏好模式字段）...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS edgesmodified (
                id SERIAL PRIMARY KEY,
                -- 原有基础字段
                fid INTEGER,
                water DOUBLE PRECISION,
                bh INTEGER,
                shape_leng DOUBLE PRECISION,
                frequency INTEGER,
                slope DOUBLE PRECISION,
                buildng DOUBLE PRECISION,
                ndvi DOUBLE PRECISION,
                winding INTEGER,
                -- 原有运动和设施字段
                sport INTEGER,
                life INTEGER,
                education INTEGER,
                finance INTEGER,
                traffic INTEGER,
                public INTEGER,
                scenery INTEGER,
                food INTEGER,
                poi DOUBLE PRECISION,
                svi DOUBLE PRECISION,
                gvi DOUBLE PRECISION,
                vw DOUBLE PRECISION,
                vei DOUBLE PRECISION,
                light DOUBLE PRECISION,
                poiden DOUBLE PRECISION,
                origlen DOUBLE PRECISION,
                bh_1 INTEGER,
                frequenc_1 INTEGER,
                -- 原有综合评分字段
                sum_c_intr DOUBLE PRECISION,
                sum_c_buil DOUBLE PRECISION,
                sum_c_ndvi DOUBLE PRECISION,
                sum_c_poi DOUBLE PRECISION,
                sum_c_wind DOUBLE PRECISION,
                sum_c_slop DOUBLE PRECISION,
                sum_c_wate DOUBLE PRECISION,
                sum_c_svi DOUBLE PRECISION,
                sum_c_gvi DOUBLE PRECISION,
                sum_c_vw DOUBLE PRECISION,
                sum_c_ligh DOUBLE PRECISION,
                sum_c_poid DOUBLE PRECISION,
                score DOUBLE PRECISION,
                -- 原有坐标和权重字段
                startx DOUBLE PRECISION,
                starty DOUBLE PRECISION,
                endx DOUBLE PRECISION,
                endy DOUBLE PRECISION,
                total DOUBLE PRECISION,
                dij_w1 DOUBLE PRECISION,
                distance DOUBLE PRECISION,
                score_ori DOUBLE PRECISION,
                dis_ori DOUBLE PRECISION,
                toatl_ori1 DOUBLE PRECISION,
                toatl_ori2 DOUBLE PRECISION,
                
                -- UPDATE: 新增偏好模式相关字段（来自modified-3.m）
                -- 标准化偏好指标（M后缀表示标准化值）
                poi_m DOUBLE PRECISION,        -- 标准化POI得分
                svi_m DOUBLE PRECISION,        -- 标准化SVI得分
                gvi_m DOUBLE PRECISION,        -- 标准化GVI得分
                vw_m DOUBLE PRECISION,         -- 标准化VW得分
                vei_m DOUBLE PRECISION,        -- 标准化VEI得分
                light_m DOUBLE PRECISION,      -- 标准化灯光得分
                poiden_m DOUBLE PRECISION,     -- 标准化POI密度得分
                slope_m DOUBLE PRECISION,      -- 标准化坡度得分
                buildng_m DOUBLE PRECISION,    -- 标准化建筑得分
                ndvi_m DOUBLE PRECISION,       -- 标准化NDVI得分
                winding_m DOUBLE PRECISION,    -- 标准化蜿蜒度得分
                water_m DOUBLE PRECISION,      -- 标准化滨水得分
                
                -- 偏好模式综合评价（Mtotal后缀表示综合评价值）
                poi_mtotal DOUBLE PRECISION,      -- POI设施便利综合评价
                svi_mtotal DOUBLE PRECISION,      -- SVI视野开阔综合评价
                gvi_mtotal DOUBLE PRECISION,      -- GVI绿化综合评价
                vw_mtotal DOUBLE PRECISION,       -- VW综合评价
                vei_mtotal DOUBLE PRECISION,      -- VEI综合评价
                light_mtotal DOUBLE PRECISION,    -- 夜间灯光充足综合评价
                poiden_mtotal DOUBLE PRECISION,   -- POI密度综合评价
                slope_mtotal DOUBLE PRECISION,    -- 坡度平缓综合评价
                buildng_mtotal DOUBLE PRECISION,  -- 建筑视野综合评价
                ndvi_mtotal DOUBLE PRECISION,     -- NDVI绿化综合评价
                winding_mtotal DOUBLE PRECISION,  -- 蜿蜒度综合评价
                water_mtotal DOUBLE PRECISION,    -- 滨水路线综合评价
                
                -- 路由字段
                source INTEGER,                 -- pgRouting起点节点ID
                target INTEGER,                 -- pgRouting终点节点ID
                geom geometry(LineString, 4326) -- 几何字段
            );
            """)
        else:
            # UPDATE: 为现有表添加新的偏好模式字段
            logger.info("为现有edgesmodified表添加新的偏好模式字段...")
            
            # 检查并添加标准化字段
            new_m_fields = [
                'poi_m', 'svi_m', 'gvi_m', 'vw_m', 'vei_m', 'light_m', 
                'poiden_m', 'slope_m', 'buildng_m', 'ndvi_m', 'winding_m', 'water_m'
            ]
            
            for field in new_m_fields:
                cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'edgesmodified' AND column_name = '{field}';
                """)
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE edgesmodified ADD COLUMN {field} DOUBLE PRECISION;")
                    logger.info(f"添加字段: {field}")
            
            # 检查并添加综合评价字段
            new_mtotal_fields = [
                'poi_mtotal', 'svi_mtotal', 'gvi_mtotal', 'vw_mtotal', 'vei_mtotal', 
                'light_mtotal', 'poiden_mtotal', 'slope_mtotal', 'buildng_mtotal', 
                'ndvi_mtotal', 'winding_mtotal', 'water_mtotal'
            ]
            
            for field in new_mtotal_fields:
                cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'edgesmodified' AND column_name = '{field}';
                """)
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE edgesmodified ADD COLUMN {field} DOUBLE PRECISION;")
                    logger.info(f"添加字段: {field}")
            
            # 检查并添加source/target字段
            for field in ['source', 'target']:
                cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'edgesmodified' AND column_name = '{field}';
                """)
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE edgesmodified ADD COLUMN {field} INTEGER;")
                    logger.info(f"添加字段: {field}")

        # UPDATE: 5. 数据导入选项（如果表刚创建或用户选择重新导入）
        if not table_exists or drop_existing:
            csv_path = r'G:\gh_repo\Joy-Run-Smart-Track\backend\res\road_modified-2.csv'
            if csv_path and csv_path != "":
                logger.info(f"从CSV文件导入数据: {csv_path}")
                try:
                    cursor.execute(f"""
                    COPY edgesmodified(
                        fid, water, bh, shape_leng, frequency, slope, buildng, ndvi, winding, 
                        sport, life, education, finance, traffic, public, scenery, food, poi, svi, gvi, vw, vei, light, poiden, origlen, bh_1, frequenc_1, 
                        sum_c_intr, sum_c_buil, sum_c_ndvi, sum_c_poi, sum_c_wind, sum_c_slop, sum_c_wate, sum_c_svi, sum_c_gvi, sum_c_vw, sum_c_ligh, sum_c_poid, 
                        score, startx, starty, endx, endy, total, dij_w1, distance, score_ori, dis_ori, toatl_ori1, toatl_ori2,
                        poi_m, svi_m, gvi_m, vw_m, vei_m, light_m, poiden_m, slope_m, buildng_m, ndvi_m, winding_m, water_m,
                        poi_mtotal, svi_mtotal, gvi_mtotal, vw_mtotal, vei_mtotal, light_mtotal, poiden_mtotal, slope_mtotal, buildng_mtotal, ndvi_mtotal, winding_mtotal, water_mtotal
                    ) FROM '{csv_path}' WITH CSV HEADER;
                    """)
                    logger.info("CSV数据导入成功")
                except Exception as e:
                    logger.warning(f"CSV数据导入失败: {e}")
                    logger.info("跳过数据导入，继续创建表结构...")
            else:
                logger.info("跳过CSV数据导入")

        # UPDATE: 6. 自动生成/更新nodesmodified表
        logger.info("自动生成/更新nodesmodified表（唯一节点集）...")
        
        # 检查nodesmodified表是否存在
        cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'nodesmodified'
        );
        """)
        nodes_table_exists = cursor.fetchone()[0]
        
        if not nodes_table_exists or drop_existing:
            cursor.execute("DROP TABLE IF EXISTS nodesmodified;")
            cursor.execute("""
            CREATE TABLE nodesmodified AS
            SELECT row_number() OVER () AS id, x, y, ST_SetSRID(ST_MakePoint(x, y), 4326) as geom
            FROM (
                SELECT DISTINCT startx AS x, starty AS y FROM edgesmodified WHERE startx IS NOT NULL AND starty IS NOT NULL
                UNION
                SELECT DISTINCT endx AS x, endy AS y FROM edgesmodified WHERE endx IS NOT NULL AND endy IS NOT NULL
            ) AS allnodes;
            """)
            cursor.execute("ALTER TABLE nodesmodified ADD PRIMARY KEY (id);")
            cursor.execute("ALTER TABLE nodesmodified ALTER COLUMN id SET NOT NULL;")
            cursor.execute("ALTER TABLE nodesmodified ALTER COLUMN x SET NOT NULL;")
            cursor.execute("ALTER TABLE nodesmodified ALTER COLUMN y SET NOT NULL;")
            logger.info("nodesmodified表创建完成")
        else:
            logger.info("nodesmodified表已存在，跳过创建")
        
        
        # UPDATE: 7. 创建空间索引（包含新字段的索引）
        logger.info("创建空间索引和偏好字段索引...")
        
        # 节点表的空间索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_nodesmodified_geom 
        ON nodesmodified USING GIST (geom);
        """)
        
        # 边表的空间索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edgesmodified_geom 
        ON edgesmodified USING GIST (geom);
        """)
        
        # UPDATE: 8. 创建路径规划相关的索引（包含新偏好字段）
        logger.info("创建路径规划索引（包含偏好模式字段）...")
        
        # 基本路径规划索引
        basic_indexes = [
            ('idx_edgesmodified_startx', 'startx'),
            ('idx_edgesmodified_endx', 'endx'),
            ('idx_edgesmodified_dis_ori', 'dis_ori'),
            ('idx_edgesmodified_distance', 'distance'),
            ('idx_edgesmodified_total', 'total'),
            ('idx_edgesmodified_score', 'score'),
            ('idx_edgesmodified_source', 'source'),
            ('idx_edgesmodified_target', 'target')
        ]
        
        for idx_name, column in basic_indexes:
            cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {idx_name} 
            ON edgesmodified ({column});
            """)
        
        # UPDATE: 偏好模式字段索引（加速偏好计算）
        preference_indexes = [
            ('idx_edgesmodified_water_mtotal', 'water_mtotal'),      # 滨水路线索引
            ('idx_edgesmodified_ndvi_mtotal', 'ndvi_mtotal'),        # NDVI绿化索引
            ('idx_edgesmodified_gvi_mtotal', 'gvi_mtotal'),          # GVI绿化索引
            ('idx_edgesmodified_svi_mtotal', 'svi_mtotal'),          # SVI视野索引
            ('idx_edgesmodified_buildng_mtotal', 'buildng_mtotal'),  # 建筑视野索引
            ('idx_edgesmodified_light_mtotal', 'light_mtotal'),      # 灯光索引
            ('idx_edgesmodified_poi_mtotal', 'poi_mtotal'),          # POI设施索引
            ('idx_edgesmodified_slope_mtotal', 'slope_mtotal')       # 坡度索引
        ]
        
        for idx_name, column in preference_indexes:
            cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {idx_name} 
            ON edgesmodified ({column});
            """)
            
        logger.info("偏好模式索引创建完成")
        
        # UPDATE: 9. 更新几何字段和source/target关联
        logger.info("更新几何字段和路由关联...")
        
        # 更新节点表的几何字段（如果需要）
        cursor.execute("""
        UPDATE nodesmodified 
        SET geom = ST_SetSRID(ST_MakePoint(x, y), 4326)
        WHERE geom IS NULL AND x IS NOT NULL AND y IS NOT NULL;
        """)
        
        # 更新边表的几何字段（如果需要）
        cursor.execute("""
        UPDATE edgesmodified 
        SET geom = ST_SetSRID(ST_MakeLine(ST_MakePoint(startx, starty), ST_MakePoint(endx, endy)), 4326)
        WHERE geom IS NULL AND startx IS NOT NULL AND starty IS NOT NULL 
              AND endx IS NOT NULL AND endy IS NOT NULL;
        """)

        # 更新source/target字段（关联nodesmodified的id）
        logger.info("更新source/target字段关联...")
        cursor.execute("""
            UPDATE edgesmodified e
            SET source = n1.id
            FROM nodesmodified n1
            WHERE e.startx = n1.x AND e.starty = n1.y AND e.source IS NULL;
        """)
        cursor.execute("""
            UPDATE edgesmodified e
            SET target = n2.id
            FROM nodesmodified n2
            WHERE e.endx = n2.x AND e.endy = n2.y AND e.target IS NULL;
        """)
        
        # UPDATE: 10. 创建增强的辅助视图（包含偏好模式支持）
        logger.info("创建增强的辅助视图...")
        
        # 路网统计视图（包含偏好模式统计）
        cursor.execute("""
        CREATE OR REPLACE VIEW network_stats AS
        SELECT 
            COUNT(*) as total_nodes,
            (SELECT COUNT(*) FROM edgesmodified) as total_edges,
            (SELECT AVG(dis_ori) FROM edgesmodified WHERE dis_ori > 0) as avg_edge_length,
            (SELECT AVG(score) FROM edgesmodified WHERE score > 0) as avg_edge_score,
            -- UPDATE: 偏好模式统计
            (SELECT AVG(water_mtotal) FROM edgesmodified WHERE water_mtotal > 0) as avg_water_score,
            (SELECT AVG(ndvi_mtotal + gvi_mtotal) FROM edgesmodified WHERE ndvi_mtotal > 0 AND gvi_mtotal > 0) as avg_green_score,
            (SELECT AVG(svi_mtotal + buildng_mtotal) FROM edgesmodified WHERE svi_mtotal > 0 AND buildng_mtotal > 0) as avg_view_score,
            (SELECT AVG(light_mtotal) FROM edgesmodified WHERE light_mtotal > 0) as avg_light_score,
            (SELECT AVG(poi_mtotal) FROM edgesmodified WHERE poi_mtotal > 0) as avg_poi_score,
            (SELECT AVG(slope_mtotal) FROM edgesmodified WHERE slope_mtotal > 0) as avg_slope_score,
            ST_Extent(geom) as network_bounds
        FROM nodesmodified;
        """)
        
        # UPDATE: 高质量路段视图（按不同偏好分类）
        cursor.execute("""
        CREATE OR REPLACE VIEW high_quality_edges AS
        SELECT *,
            CASE 
                WHEN water_mtotal >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY water_mtotal) FROM edgesmodified WHERE water_mtotal > 0) THEN 'high_water'
                WHEN (ndvi_mtotal + gvi_mtotal) >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY (ndvi_mtotal + gvi_mtotal)) FROM edgesmodified WHERE ndvi_mtotal > 0 AND gvi_mtotal > 0) THEN 'high_green'
                WHEN (svi_mtotal + buildng_mtotal) >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY (svi_mtotal + buildng_mtotal)) FROM edgesmodified WHERE svi_mtotal > 0 AND buildng_mtotal > 0) THEN 'high_view'
                WHEN light_mtotal >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY light_mtotal) FROM edgesmodified WHERE light_mtotal > 0) THEN 'high_light'
                WHEN poi_mtotal >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY poi_mtotal) FROM edgesmodified WHERE poi_mtotal > 0) THEN 'high_poi'
                WHEN slope_mtotal >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY slope_mtotal) FROM edgesmodified WHERE slope_mtotal > 0) THEN 'high_gentle'
                ELSE 'standard'
            END as preference_category
        FROM edgesmodified
        WHERE score >= (
            SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY score)
            FROM edgesmodified 
            WHERE score > 0
        );
        """)
        
        # UPDATE: 偏好模式数据质量检查视图
        cursor.execute("""
        CREATE OR REPLACE VIEW preference_data_quality AS
        SELECT 
            'water_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(water_mtotal) as non_null_records,
            AVG(water_mtotal) as avg_value,
            MIN(water_mtotal) as min_value,
            MAX(water_mtotal) as max_value
        FROM edgesmodified
        UNION ALL
        SELECT 
            'ndvi_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(ndvi_mtotal) as non_null_records,
            AVG(ndvi_mtotal) as avg_value,
            MIN(ndvi_mtotal) as min_value,
            MAX(ndvi_mtotal) as max_value
        FROM edgesmodified
        UNION ALL
        SELECT 
            'gvi_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(gvi_mtotal) as non_null_records,
            AVG(gvi_mtotal) as avg_value,
            MIN(gvi_mtotal) as min_value,
            MAX(gvi_mtotal) as max_value
        FROM edgesmodified
        UNION ALL
        SELECT 
            'svi_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(svi_mtotal) as non_null_records,
            AVG(svi_mtotal) as avg_value,
            MIN(svi_mtotal) as min_value,
            MAX(svi_mtotal) as max_value
        FROM edgesmodified
        UNION ALL
        SELECT 
            'buildng_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(buildng_mtotal) as non_null_records,
            AVG(buildng_mtotal) as avg_value,
            MIN(buildng_mtotal) as min_value,
            MAX(buildng_mtotal) as max_value
        FROM edgesmodified
        UNION ALL
        SELECT 
            'light_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(light_mtotal) as non_null_records,
            AVG(light_mtotal) as avg_value,
            MIN(light_mtotal) as min_value,
            MAX(light_mtotal) as max_value
        FROM edgesmodified
        UNION ALL
        SELECT 
            'poi_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(poi_mtotal) as non_null_records,
            AVG(poi_mtotal) as avg_value,
            MIN(poi_mtotal) as min_value,
            MAX(poi_mtotal) as max_value
        FROM edgesmodified
        UNION ALL
        SELECT 
            'slope_mtotal' as field_name,
            COUNT(*) as total_records,
            COUNT(slope_mtotal) as non_null_records,
            AVG(slope_mtotal) as avg_value,
            MIN(slope_mtotal) as min_value,
            MAX(slope_mtotal) as max_value
        FROM edgesmodified;
        """)
        
        logger.info("数据库初始化完成！")
        
        # UPDATE: 显示增强的统计信息（包含偏好模式）
        cursor.execute("SELECT * FROM network_stats;")
        stats = cursor.fetchone()
        if stats:
            logger.info(f"路网统计 - 节点数: {stats[0]}, 边数: {stats[1]}")
            logger.info(f"平均边长: {stats[2]:.2f}米, 平均得分: {stats[3]:.2f}")
            # UPDATE: 偏好模式统计
            if len(stats) > 4:
                water_score = f"{stats[4]:.2f}" if stats[4] is not None else "N/A"
                green_score = f"{stats[5]:.2f}" if stats[5] is not None else "N/A"
                view_score = f"{stats[6]:.2f}" if stats[6] is not None else "N/A"
                light_score = f"{stats[7]:.2f}" if stats[7] is not None else "N/A"
                poi_score = f"{stats[8]:.2f}" if stats[8] is not None else "N/A"
                slope_score = f"{stats[9]:.2f}" if stats[9] is not None else "N/A"
                
                logger.info(f"平均滨水得分: {water_score}")
                logger.info(f"平均绿化得分: {green_score}")
                logger.info(f"平均视野得分: {view_score}")
                logger.info(f"平均灯光得分: {light_score}")
                logger.info(f"平均设施得分: {poi_score}")
                logger.info(f"平均坡度得分: {slope_score}")
        
        # UPDATE: 显示偏好数据质量报告
        cursor.execute("SELECT * FROM preference_data_quality;")
        quality_stats = cursor.fetchall()
        if quality_stats:
            logger.info("\n偏好数据质量报告:")
            for stat in quality_stats:
                field_name, total, non_null, avg_val, min_val, max_val = stat
                coverage = (non_null / total * 100) if total > 0 else 0
                avg_display = f"{avg_val:.2f}" if avg_val is not None else "N/A"
                logger.info(f"  {field_name}: 覆盖率 {coverage:.1f}% ({non_null}/{total}), 平均值 {avg_display}")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_database_status():
    """检查数据库状态 - UPDATE: 包含偏好模式字段检查"""
    
    conn = None
    cursor = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查扩展
        cursor.execute("""
        SELECT extname FROM pg_extension 
        WHERE extname IN ('postgis', 'pgrouting');
        """)
        extensions = [row[0] for row in cursor.fetchall()]
        
        print("已安装的扩展:")
        for ext in extensions:
            print(f"  ✓ {ext}")
        
        if 'postgis' not in extensions:
            print("  ✗ PostGIS 未安装")
        if 'pgrouting' not in extensions:
            print("  ✗ pgRouting 未安装")
        
        # 检查表
        cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('nodesmodified', 'edgesmodified');
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print("\n数据表状态:")
        for table in ['nodesmodified', 'edgesmodified']:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table}: {count} 条记录")
            else:
                print(f"  ✗ {table}: 表不存在")
        
        # UPDATE: 检查偏好模式字段
        if 'edgesmodified' in tables:
            print("\n偏好模式字段检查:")
            preference_fields = [
                'water_mtotal', 'ndvi_mtotal', 'gvi_mtotal', 'svi_mtotal', 
                'buildng_mtotal', 'light_mtotal', 'poi_mtotal', 'slope_mtotal'
            ]
            
            for field in preference_fields:
                cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'edgesmodified' AND column_name = '{field}';
                """)
                if cursor.fetchone():
                    # 检查数据完整性
                    cursor.execute(f"SELECT COUNT(*), COUNT({field}) FROM edgesmodified;")
                    total, non_null = cursor.fetchone()
                    coverage = (non_null / total * 100) if total > 0 else 0
                    print(f"  ✓ {field}: 覆盖率 {coverage:.1f}% ({non_null}/{total})")
                else:
                    print(f"  ✗ {field}: 字段不存在")
        
        # 检查索引
        cursor.execute("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename IN ('nodesmodified', 'edgesmodified')
        AND indexname LIKE 'idx_%';
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        print(f"\n空间和业务索引: {len(indexes)} 个")
        basic_indexes = [idx for idx in indexes if not any(pref in idx for pref in ['water', 'ndvi', 'gvi', 'svi', 'buildng', 'light', 'poi', 'slope'])]
        preference_indexes = [idx for idx in indexes if any(pref in idx for pref in ['water', 'ndvi', 'gvi', 'svi', 'buildng', 'light', 'poi', 'slope'])]
        
        print("  基础索引:")
        for idx in basic_indexes:
            print(f"    ✓ {idx}")
            
        # UPDATE: 偏好索引检查
        print("  偏好模式索引:")
        for idx in preference_indexes:
            print(f"    ✓ {idx}")
        
        # UPDATE: 检查视图
        cursor.execute("""
        SELECT viewname FROM pg_views 
        WHERE schemaname = 'public' 
        AND viewname IN ('network_stats', 'high_quality_edges', 'preference_data_quality');
        """)
        views = [row[0] for row in cursor.fetchall()]
        
        print(f"\n辅助视图: {len(views)} 个")
        for view in ['network_stats', 'high_quality_edges', 'preference_data_quality']:
            if view in views:
                print(f"  ✓ {view}")
            else:
                print(f"  ✗ {view}: 视图不存在")
        
        # UPDATE: 显示偏好数据质量摘要
        if 'preference_data_quality' in views:
            print("\n偏好数据质量摘要:")
            cursor.execute("SELECT * FROM preference_data_quality ORDER BY field_name;")
            for row in cursor.fetchall():
                field_name, total, non_null, avg_val, min_val, max_val = row
                coverage = (non_null / total * 100) if total > 0 else 0
                avg_display = f"{avg_val:.2f}" if avg_val is not None else "N/A"
                print(f"  {field_name}: {coverage:.1f}% 覆盖率, 平均值 {avg_display}")
        
    except Exception as e:
        print(f"检查数据库状态失败: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def migrate_preference_data():
    """
    UPDATE: 数据迁移辅助函数 - 为已有数据生成偏好模式字段的示例值
    这个函数可以帮助用户基于现有字段计算偏好模式字段
    """
    conn = None
    cursor = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("开始偏好数据迁移...")
        
        # 检查是否有现有数据
        cursor.execute("SELECT COUNT(*) FROM edgesmodified WHERE startx IS NOT NULL;")
        data_count = cursor.fetchone()[0]
        
        if data_count == 0:
            logger.warning("没有找到现有数据，请先导入基础路网数据")
            return
        
        logger.info(f"发现 {data_count} 条边数据，开始计算偏好字段...")
        
        # UPDATE: 基于现有字段计算偏好模式字段（示例逻辑）
        migration_queries = [
            # 基于原有字段计算标准化值（M字段）
            "UPDATE edgesmodified SET water_m = COALESCE(water / NULLIF((SELECT MAX(water) FROM edgesmodified), 0), 0) WHERE water_m IS NULL;",
            "UPDATE edgesmodified SET ndvi_m = COALESCE(ndvi / NULLIF((SELECT MAX(ndvi) FROM edgesmodified), 0), 0) WHERE ndvi_m IS NULL;",
            "UPDATE edgesmodified SET gvi_m = COALESCE(gvi / NULLIF((SELECT MAX(gvi) FROM edgesmodified), 0), 0) WHERE gvi_m IS NULL;", 
            "UPDATE edgesmodified SET svi_m = COALESCE(svi / NULLIF((SELECT MAX(svi) FROM edgesmodified), 0), 0) WHERE svi_m IS NULL;",
            "UPDATE edgesmodified SET buildng_m = COALESCE(buildng / NULLIF((SELECT MAX(buildng) FROM edgesmodified), 0), 0) WHERE buildng_m IS NULL;",
            "UPDATE edgesmodified SET light_m = COALESCE(light / NULLIF((SELECT MAX(light) FROM edgesmodified), 0), 0) WHERE light_m IS NULL;",
            "UPDATE edgesmodified SET poi_m = COALESCE(poi / NULLIF((SELECT MAX(poi) FROM edgesmodified), 0), 0) WHERE poi_m IS NULL;",
            "UPDATE edgesmodified SET slope_m = COALESCE((SELECT MAX(slope) FROM edgesmodified) - slope, 0) / NULLIF((SELECT MAX(slope) FROM edgesmodified), 0) WHERE slope_m IS NULL;",  # 坡度反向（越小越好）
            "UPDATE edgesmodified SET poiden_m = COALESCE(poiden / NULLIF((SELECT MAX(poiden) FROM edgesmodified), 0), 0) WHERE poiden_m IS NULL;",
            "UPDATE edgesmodified SET winding_m = COALESCE(winding / NULLIF((SELECT MAX(winding) FROM edgesmodified), 0), 0) WHERE winding_m IS NULL;",
            
            # 基于标准化值计算综合评价（Mtotal字段）
            "UPDATE edgesmodified SET water_mtotal = COALESCE(water_m * 100, 0) WHERE water_mtotal IS NULL;",
            "UPDATE edgesmodified SET ndvi_mtotal = COALESCE(ndvi_m * 100, 0) WHERE ndvi_mtotal IS NULL;",
            "UPDATE edgesmodified SET gvi_mtotal = COALESCE(gvi_m * 100, 0) WHERE gvi_mtotal IS NULL;",
            "UPDATE edgesmodified SET svi_mtotal = COALESCE(svi_m * 100, 0) WHERE svi_mtotal IS NULL;",
            "UPDATE edgesmodified SET buildng_mtotal = COALESCE(buildng_m * 100, 0) WHERE buildng_mtotal IS NULL;",
            "UPDATE edgesmodified SET light_mtotal = COALESCE(light_m * 100, 0) WHERE light_mtotal IS NULL;",
            "UPDATE edgesmodified SET poi_mtotal = COALESCE(poi_m * 100, 0) WHERE poi_mtotal IS NULL;",
            "UPDATE edgesmodified SET slope_mtotal = COALESCE(slope_m * 100, 0) WHERE slope_mtotal IS NULL;",
            "UPDATE edgesmodified SET poiden_mtotal = COALESCE(poiden_m * 100, 0) WHERE poiden_mtotal IS NULL;",
            "UPDATE edgesmodified SET winding_mtotal = COALESCE(winding_m * 100, 0) WHERE winding_mtotal IS NULL;",
            
            # 组合字段计算
            "UPDATE edgesmodified SET vw_m = COALESCE(vw / NULLIF((SELECT MAX(vw) FROM edgesmodified), 0), 0) WHERE vw_m IS NULL;",
            "UPDATE edgesmodified SET vei_m = COALESCE(vei / NULLIF((SELECT MAX(vei) FROM edgesmodified), 0), 0) WHERE vei_m IS NULL;",
            "UPDATE edgesmodified SET vw_mtotal = COALESCE(vw_m * 100, 0) WHERE vw_mtotal IS NULL;",
            "UPDATE edgesmodified SET vei_mtotal = COALESCE(vei_m * 100, 0) WHERE vei_mtotal IS NULL;"
        ]
        
        for i, query in enumerate(migration_queries):
            try:
                cursor.execute(query)
                logger.info(f"完成迁移步骤 {i+1}/{len(migration_queries)}")
            except Exception as e:
                logger.warning(f"迁移步骤 {i+1} 失败: {e}")
        
        # 验证迁移结果
        cursor.execute("SELECT COUNT(*) FROM edgesmodified WHERE water_mtotal IS NOT NULL;")
        migrated_count = cursor.fetchone()[0]
        
        logger.info(f"偏好数据迁移完成！{migrated_count} 条记录已更新偏好字段")
        
        # 显示迁移后的数据质量
        cursor.execute("SELECT * FROM preference_data_quality LIMIT 3;")
        quality_sample = cursor.fetchall()
        if quality_sample:
            logger.info("迁移后数据质量样本:")
            for row in quality_sample:
                field_name, total, non_null, avg_val, min_val, max_val = row
                coverage = (non_null / total * 100) if total > 0 else 0
                avg_display = f"{avg_val:.2f}" if avg_val is not None else "N/A"
                logger.info(f"  {field_name}: {coverage:.1f}% 覆盖率, 平均值 {avg_display}")
        
    except Exception as e:
        logger.error(f"偏好数据迁移失败: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    """
    UPDATE: 增强的数据库初始化主程序
    支持多种初始化模式和偏好数据迁移
    """
    logging.basicConfig(level=logging.INFO)
    
    print("=== Joy Run 智能慧跑路径规划数据库初始化脚本 ===")
    print("UPDATE: 支持新的偏好模式字段和6种约束模式")
    
    choice = input("""
选择操作:
1. 渐进式初始化（保留现有数据，添加新字段）
2. 完全重建数据库（删除现有表，完全重新创建）
3. 检查数据库状态
4. 仅执行偏好数据迁移
请输入选择 (1/2/3/4): """).strip()
    
    try:
        if choice == "1":
            print("\n=== 渐进式数据库初始化 ===")
            print("这将为现有表添加新的偏好字段，保留已有数据")
            confirm = input("确定要进行渐进式初始化吗？(y/N): ")
            if confirm.lower() in ['y', 'yes']:
                init_database(drop_existing=False)
                
                # 询问是否执行数据迁移
                migrate_confirm = input("是否执行偏好数据迁移（为现有数据计算偏好字段）？(y/N): ")
                if migrate_confirm.lower() in ['y', 'yes']:
                    migrate_preference_data()
            else:
                print("操作已取消")
                
        elif choice == "2":
            print("\n=== 危险操作：完全重建数据库 ===")
            print("这将删除所有现有的路径规划表和数据！")
            confirm = input("确定要重建数据库吗？请输入 'YES' 确认: ")
            if confirm == 'YES':
                init_database(drop_existing=True)
                print("数据库重建完成！")
                
                # 询问是否执行数据迁移
                migrate_confirm = input("是否执行偏好数据迁移？(y/N): ")
                if migrate_confirm.lower() in ['y', 'yes']:
                    migrate_preference_data()
            else:
                print("操作已取消")
                
        elif choice == "3":
            print("\n=== 数据库状态检查 ===")
            check_database_status()
            
        elif choice == "4":
            print("\n=== 偏好数据迁移 ===")
            print("为已有数据计算偏好模式字段的值")
            confirm = input("确定要执行偏好数据迁移吗？(y/N): ")
            if confirm.lower() in ['y', 'yes']:
                migrate_preference_data()
            else:
                print("操作已取消")
        else:
            print("无效选择")
            
    except Exception as e:
        logger.error(f"数据库操作失败: {e}")
        print("\n可尝试的解决方案:")
        print("1. 检查PostgreSQL服务是否运行")
        print("2. 检查数据库连接配置")
        print("3. 确认PostGIS扩展已安装")
        print("4. 使用选项2重建数据库")
        exit(1)
    
    print("\n=== 操作完成 ===")
    print("新增偏好模式说明:")
    print("1. 综合得分（原Total）")
    print("2. 滨水路线（water_mtotal）")
    print("3. 绿化路线（ndvi_mtotal + gvi_mtotal）")
    print("4. 视野开阔路线（svi_mtotal + buildng_mtotal）") 
    print("5. 夜间灯光充足路线（light_mtotal）")
    print("6. 设施便利路线（poi_mtotal）")
    print("7. 坡度平缓路线（slope_mtotal）")
    print("\n数据库已准备就绪，可以使用增强的路径规划API！")


