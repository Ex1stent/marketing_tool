CREATE TABLE marketing_tool.conversations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) DEFAULT 'New Chat',
    messages_json JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE marketing_tool.messages (
    id SERIAL PRIMARY KEY,
    conversation_id INT REFERENCES meta.conversations(id),
    role VARCHAR(20),           -- user, assistant, system, tool
    message_type VARCHAR(30),   -- text, image, file, tool
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE marketing_tool.document_metadata (
    id SERIAL PRIMARY KEY,
    message_id INT REFERENCES meta.messages(id),
    file_name VARCHAR(255),
    file_path TEXT,
    file_extension VARCHAR(20),
    mime_type VARCHAR(100),
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE  marketing_tool.scheduled_post_batches (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) ,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
    status VARCHAR(20) DEFAULT 'active',
);