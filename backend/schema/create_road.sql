-- Database: joy_run_db

-- DROP DATABASE IF EXISTS joy_run_db;

-- 创建数据库
-- CREATE DATABASE joy_run_db
--     WITH
--     OWNER = postgres
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'English_United States.936'
--     LC_CTYPE = 'English_United States.936'
--     LOCALE_PROVIDER = 'libc'
--     TABLESPACE = pg_default
--     CONNECTION LIMIT = -1
--     IS_TEMPLATE = False;

-- 激活postgis和pgrouting扩展
-- CREATE EXTENSION postgis;
-- CREATE EXTENSION pgrouting;

-- 创建表
CREATE TABLE nodesmodified (
	id SERIAL PRIMARY KEY,
	x DOUBLE PRECISION,
	y DOUBLE PRECISION,
	geom geometry(Point, 4326)
);

CREATE TABLE edgesmodified (
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

-- 导入 edges 数据
-- 注意修改你的路径
COPY edgesmodified(
	fid, water, bh, shape_leng, frequency, slope, buildng, ndvi, winding, sport, life, education, finance, traffic, public, scenery, food, poi, svi, gvi, vw, vei, light, poiden, origlen, bh_1, frequenc_1, sum_c_intr, sum_c_buil, sum_c_ndvi, sum_c_poi, sum_c_wind, sum_c_slop, sum_c_wate, sum_c_svi, sum_c_gvi, sum_c_vw, sum_c_ligh, sum_c_poid, score, startx, starty, endx, endy, total, dij_w1, distance, score_ori, dis_ori, toatl_ori1, toatl_ori2
) FROM 'G:/gh_repo/Joy-Run-Smart-Track/backend/res/road_modified.csv' WITH CSV HEADER;

-- 生成空间字段
UPDATE edgesmodified
SET geom = ST_MakeLine(
	ST_SetSRID(ST_MakePoint(startx, starty), 4326),
	ST_SetSRID(ST_MakePoint(endx, endy), 4326)
);

-- 自动插入所有唯一节点
INSERT INTO nodesmodified(x, y, geom)
SELECT DISTINCT startx, starty, ST_SetSRID(ST_MakePoint(startx, starty), 4326) FROM edgesmodified
UNION
SELECT DISTINCT endx, endy, ST_SetSRID(ST_MakePoint(endx, endy), 4326) FROM edgesmodified;

-- 增加 source/target 字段
ALTER TABLE edgesmodified ADD COLUMN source INTEGER;
ALTER TABLE edgesmodified ADD COLUMN target INTEGER;

-- 用坐标匹配节点ID
UPDATE edgesmodified
SET source = nodesmodified.id
FROM nodesmodified
WHERE edgesmodified.startx = nodesmodified.x AND edgesmodified.starty = nodesmodified.y;

UPDATE edgesmodified
SET target = nodesmodified.id
FROM nodesmodified
WHERE edgesmodified.endx = nodesmodified.x AND edgesmodified.endy = nodesmodified.y;

-- 检查数据
SELECT * FROM edgesmodified LIMIT 10000;

-- 测试路径规划（可选）
SELECT 
    e.*, 
    p.seq, 
    p.path_seq, 
    p.node, 
    p.edge, 
    p.cost, 
    e.geom
FROM 
    pgr_dijkstra(
        'SELECT id, source, target, distance AS cost FROM edgesmodified',
        1, 5000
    ) AS p
JOIN edgesmodified e ON p.edge = e.id
ORDER BY p.seq;