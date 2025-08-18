
CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    city VARCHAR(50),
    adcode VARCHAR(20),
    province VARCHAR(50),
    reporttime TIMESTAMP,
    date DATE,
    week VARCHAR(10),
    dayweather VARCHAR(20),
    nightweather VARCHAR(20),
    daytemp INTEGER,
    nighttemp INTEGER,
    daywind VARCHAR(10),
    nightwind VARCHAR(10),
    daypower VARCHAR(10),
    nightpower VARCHAR(10),
    daytemp_float FLOAT,
    nighttemp_float FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE gaode_api (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(64) NOT NULL
);

INSERT INTO gaode_api (api_key) VALUES ('e5ee167ec71db5cfb0458897af4f03a7');