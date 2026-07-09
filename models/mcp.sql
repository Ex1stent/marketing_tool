-- CREATE TABLE insta_comments (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id VARCHAR(255),
--     comment_id VARCHAR(255),
--     created_time DATETIME,
--     text TEXT,
--     from_user VARCHAR(255),
--     timestamp DATETIME,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );



-- CREATE TABLE messages (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     from_id VARCHAR(255),
--     to_id VARCHAR(255),
--     message TEXT,
--     timestamp DATETIME,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );


-- CREATE TABLE webhook_events (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     platform VARCHAR(255) NOT NULL,
--     event_type VARCHAR(255) NOT NULL,
--     sender_id VARCHAR(255),
--     text TEXT,
--     raw_payload TEXT NOT NULL,
--     normalized_payload TEXT NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );



-- CREATE TABLE webhook_events (
--     id SERIAL PRIMARY KEY,
--     platform VARCHAR(255) NOT NULL,
--     event_type VARCHAR(255) NOT NULL,
--     sender_id VARCHAR(255),
--     text TEXT,
--     raw_payload JSONB NOT NULL,         
--     normalized_payload JSONB NOT NULL,  
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
