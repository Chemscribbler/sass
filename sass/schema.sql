DROP TABLE IF EXISTS player;
DROP TABLE IF EXISTS match;
DROP TABLE IF EXISTS tournament;

-- PRAGMA encoding = 'UTF-8'
-- PRAGMA foreign_keys = ON

CREATE TABLE tournament (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    t_date TEXT DEFAULT (date('now')),
    current_rnd INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1    
);

CREATE TABLE player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tid INTEGER NOT NULL,
    p_name TEXT NOT NULL,
    corp_id TEXT,
    runner_id TEXT,
    score INTEGER DEFAULT 0,
    sos REAL DEFAULT 0.0,
    esos REAL DEFAULT 0.0,
    bias INTEGER DEFAULT 0,
    opponents TEXT,
    recivied_bye INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    FOREIGN KEY (tid) REFERENCES tournament (id)
);

CREATE TABLE match (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tid INTEGER NOT NULL,
    corp_id INTEGER NOT NULL,
    runner_id INTEGER NOT NULL,
    rnd INTEGER,
    corp_score INTEGER DEFAULT NULL,
    runner_score INTEGER DEFAULT NUll,
    FOREIGN KEY (tid) REFERENCES tournament (id),
    FOREIGN KEY (corp_id) REFERENCES player (id),
    FOREIGN KEY (runner_id) REFERENCES player (id)
);

INSERT INTO tournament (title) VALUES ("Earliest Test");

INSERT INTO player (tid, p_name, corp_id, runner_id)
VALUES (1, "Zsengrin", "Asa","MaxX"),
(1, "2ndmxma","CtM","Val"),
(1, "Goonkid","Outfit","Wu"),
(1, "EuroPantsu","Asa","Freedom"),
(1, "anotherLaura","Argus","419");