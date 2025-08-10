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

def init_database():
    """初始化数据库，创建必要的扩展和索引"""
    
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
        
        # 3. 检查表是否存在，如果不存在则创建
        logger.info("检查和创建数据表...")
        
        # 创建边表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS edgesmodified (
            id SERIAL PRIMARY KEY,
            fid INTEGER,
            water DOUBLE PRECISION,
            bh INTEGER,
            shape_leng DOUBLE PRECISION,
            frequency INTEGER,
            slope DOUBLE PRECISION,
            buildng DOUBLE PRECISION,
            ndvi DOUBLE PRECISION,
            winding INTEGER,
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
            geom geometry(LineString, 4326)
        );
        """)

        # 导入边表数据（如有CSV）
        cursor.execute("""
            COPY edgesmodified(
            fid, water, bh, shape_leng, frequency, slope, buildng, ndvi, winding, sport, life, education, finance, traffic, public, scenery, food, poi, svi, gvi, vw, vei, light, poiden, origlen, bh_1, frequenc_1, sum_c_intr, sum_c_buil, sum_c_ndvi, sum_c_poi, sum_c_wind, sum_c_slop, sum_c_wate, sum_c_svi, sum_c_gvi, sum_c_vw, sum_c_ligh, sum_c_poid, score, startx, starty, endx, endy, total, dij_w1, distance, score_ori, dis_ori, toatl_ori1, toatl_ori2
        ) FROM 'G:/gh_repo/Joy-Run-Smart-Track/backend/res/road_modified.csv' WITH CSV HEADER;
        """)

        # 自动生成nodesmodified表
        logger.info("自动生成nodesmodified表（唯一节点集）...")
        cursor.execute("DROP TABLE IF EXISTS nodesmodified;")
        cursor.execute("""
        CREATE TABLE nodesmodified AS
        SELECT row_number() OVER () AS id, x, y, NULL::geometry(Point,4326) as geom
        FROM (
            SELECT DISTINCT startx AS x, starty AS y FROM edgesmodified
            UNION
            SELECT DISTINCT endx AS x, endy AS y FROM edgesmodified
        ) AS allnodes;
        """)
        cursor.execute("ALTER TABLE nodesmodified ADD PRIMARY KEY (id);")
        cursor.execute("ALTER TABLE nodesmodified ALTER COLUMN id SET NOT NULL;")
        cursor.execute("ALTER TABLE nodesmodified ALTER COLUMN x SET NOT NULL;")
        cursor.execute("ALTER TABLE nodesmodified ALTER COLUMN y SET NOT NULL;")
        cursor.execute("ALTER TABLE nodesmodified ALTER COLUMN geom TYPE geometry(Point,4326) USING geom;")
        
        
        # 4. 创建空间索引
        logger.info("创建空间索引...")
        
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
        
        # 5. 创建路径规划相关的索引
        logger.info("创建路径规划索引...")
        
        # 起点终点索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edgesmodified_startx 
        ON edgesmodified (startx);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edgesmodified_endx 
        ON edgesmodified (endx);
        """)
        
        # 距离和权重索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edgesmodified_dis_ori 
        ON edgesmodified (dis_ori);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edgesmodified_distance 
        ON edgesmodified (distance);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edgesmodified_total 
        ON edgesmodified (total);
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edgesmodified_score 
        ON edgesmodified (score);
        """)
        
        # 6. 更新节点表的几何字段（如果x,y坐标存在但geom为空）
        logger.info("更新节点几何字段...")
        cursor.execute("""
        UPDATE nodesmodified 
        SET geom = ST_SetSRID(ST_MakePoint(x, y), 4326)
        WHERE geom IS NULL AND x IS NOT NULL AND y IS NOT NULL;
        """)
        
        # 7. 更新边表的几何字段（如果起终点坐标存在但geom为空）
        logger.info("更新边几何字段...")
        cursor.execute("""
        UPDATE edgesmodified 
        SET geom = ST_SetSRID(ST_MakeLine(ST_MakePoint(startx, starty), ST_MakePoint(endx, endy)), 4326)
        WHERE geom IS NULL AND startx IS NOT NULL AND starty IS NOT NULL 
              AND endx IS NOT NULL AND endy IS NOT NULL;
        """)

        # 7.1 添加 source/target 字段
        cursor.execute("ALTER TABLE edgesmodified ADD COLUMN IF NOT EXISTS source integer;")
        cursor.execute("ALTER TABLE edgesmodified ADD COLUMN IF NOT EXISTS target integer;")

        # 7.2 用 nodesmodified 的 id 填充 source/target
        cursor.execute("""
            UPDATE edgesmodified e
            SET source = n1.id
            FROM nodesmodified n1
            WHERE e.startx = n1.x AND e.starty = n1.y;
        """)
        cursor.execute("""
            UPDATE edgesmodified e
            SET target = n2.id
            FROM nodesmodified n2
            WHERE e.endx = n2.x AND e.endy = n2.y;
        """)

        # 7.3 可选：为 source/target 建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edgesmodified_source ON edgesmodified(source);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edgesmodified_target ON edgesmodified(target);")
        
        # 8. 创建一些有用的视图
        logger.info("创建辅助视图...")
        
        # 路网统计视图
        cursor.execute("""
        CREATE OR REPLACE VIEW network_stats AS
        SELECT 
            COUNT(*) as total_nodes,
            (SELECT COUNT(*) FROM edgesmodified) as total_edges,
            (SELECT AVG(dis_ori) FROM edgesmodified WHERE dis_ori > 0) as avg_edge_length,
            (SELECT AVG(score) FROM edgesmodified WHERE score > 0) as avg_edge_score,
            ST_Extent(geom) as network_bounds
        FROM nodesmodified;
        """)
        
        # 高质量路段视图（得分前25%）
        cursor.execute("""
        CREATE OR REPLACE VIEW high_quality_edges AS
        SELECT *
        FROM edgesmodified
        WHERE score >= (
            SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY score)
            FROM edgesmodified 
            WHERE score > 0
        );
        """)
        
        logger.info("数据库初始化完成！")
        
        # 显示一些统计信息
        cursor.execute("SELECT * FROM network_stats;")
        stats = cursor.fetchone()
        if stats:
            logger.info(f"路网统计 - 节点数: {stats[0]}, 边数: {stats[1]}")
            logger.info(f"平均边长: {stats[2]:.2f}米, 平均得分: {stats[3]:.2f}")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_database_status():
    """检查数据库状态"""
    
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
        
        # 检查索引
        cursor.execute("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename IN ('nodesmodified', 'edgesmodified')
        AND indexname LIKE 'idx_%';
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        print(f"\n空间索引: {len(indexes)} 个")
        for idx in indexes:
            print(f"  ✓ {idx}")
        
    except Exception as e:
        print(f"检查数据库状态失败: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== 数据库初始化脚本 ===")
    
    choice = input("选择操作:\n1. 初始化数据库\n2. 检查数据库状态\n请输入选择 (1/2): ")
    
    if choice == "1":
        confirm = input("确定要初始化数据库吗？这可能会创建新的表和索引。(y/N): ")
        if confirm.lower() in ['y', 'yes']:
            init_database()
        else:
            print("操作已取消")
    elif choice == "2":
        check_database_status()
    else:
        print("无效选择")
