CREATE TABLE race (
    raceId INTEGER PRIMARY KEY,
    raceName VARCHAR(255) NOT NULL,
    province VARCHAR(50),
    city VARCHAR(50),
    area VARCHAR(50),
    shortAddress VARCHAR(255),
    startTime TIMESTAMP,
    showSignEndTime TIMESTAMP,
    coverImage TEXT,
    raceType INTEGER
);

