DROP TABLE IF EXISTS match;
DROP TABLE IF EXISTS player;
DROP TABLE IF EXISTS tournament;

CREATE TABLE tournament (
    id serial PRIMARY KEY,
    title TEXT UNIQUE NOT NULL,
    t_date TIMESTAMP NOT NULL,
    current_rnd INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true    
);

CREATE TABLE player (
    id serial PRIMARY KEY,
    tid INTEGER NOT NULL,
    p_name TEXT NOT NULL,
    corp_id TEXT,
    runner_id TEXT,
    score INTEGER DEFAULT 0,
    sos REAL DEFAULT 0.0,
    esos REAL DEFAULT 0.0,
    bias INTEGER DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    received_bye BOOLEAN DEFAULT false,
    is_bye BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    FOREIGN KEY (tid) REFERENCES tournament (id)
);

CREATE TABLE match (
    id serial PRIMARY KEY,
    match_num INTEGER,
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
