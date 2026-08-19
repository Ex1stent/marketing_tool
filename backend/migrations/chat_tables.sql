CREATE TABLE marketing_tool.conversations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);


CREATE TABLE marketing_tool.messages (
    id SERIAL PRIMARY KEY,
    conversation_id INT REFERENCES marketing_tool.conversations(id),
    role VARCHAR(20),           -- user, assistant, system, tool
    message_type VARCHAR(30),   -- text, image, file, tool
    content TEXT,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);


CREATE TABLE marketing_tool.document_metadata (
    id SERIAL PRIMARY KEY,
    message_id INT REFERENCES marketing_tool.messages(id),
    file_name VARCHAR(255),
    file_path TEXT,
    file_extension VARCHAR(20),
    mime_type VARCHAR(100),
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE marketing_tool.scheduled_post_batches (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE marketing_tool.scheduled_posts (
    id SERIAL PRIMARY KEY,
    batch_id INT REFERENCES marketing_tool.scheduled_post_batches(id),
    post_type VARCHAR(50),
    platform VARCHAR(50),
    media_url TEXT,
    message TEXT,
    recipient_id VARCHAR(255),
    topic TEXT,
    scheduled_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_id VARCHAR(100),
    error_message TEXT
);

CREATE TABLE marketing_tool.webhook_events (
    id BIGINT PRIMARY KEY,
    platform VARCHAR(50),
    direction VARCHAR(20),
    sender_id VARCHAR(255),
    recipient_id VARCHAR(255),
    message_id VARCHAR(255),
    text TEXT,
    status VARCHAR(20) DEFAULT 'received',
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc'),
    message_json JSONB
);