-- Create content_items table
CREATE TABLE IF NOT EXISTS content_items (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    source VARCHAR(1000) NOT NULL,
    content TEXT NOT NULL,
    message_id BIGINT,  -- For forwarded messages
    chat_id BIGINT,     -- For forwarded messages
    content_type VARCHAR(50), -- video, text, audio, etc.
    short_description TEXT DEFAULT '',
    status VARCHAR(100) DEFAULT 'unread',
    date_added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date_read TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_status CHECK (status IN ('unread', 'processed'))
);

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(1000) NOT NULL,
    UNIQUE (user_id, name)
);

-- Create content_item_tags table for many-to-many relationship
CREATE TABLE IF NOT EXISTS content_item_tags (
    content_item_id INTEGER REFERENCES content_items(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (content_item_id, tag_id)
);

-- Create indexes for better performance
CREATE INDEX idx_content_items_user_id ON content_items(user_id);
CREATE INDEX idx_content_items_status ON content_items(status);
CREATE INDEX idx_content_items_content_type ON content_items(content_type);
CREATE INDEX idx_content_items_date_added ON content_items(date_added);
CREATE INDEX idx_tags_user_id ON tags(user_id);
CREATE INDEX idx_content_item_tags_content_item_id ON content_item_tags(content_item_id);
CREATE INDEX idx_content_item_tags_tag_id ON content_item_tags(tag_id);