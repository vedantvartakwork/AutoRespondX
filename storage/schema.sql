-- Core tables for AutoRespondX

CREATE TABLE IF NOT EXISTS processed_tweets (
    id SERIAL PRIMARY KEY,
    original_tweet TEXT NOT NULL,
    cleaned_tweet TEXT,
    hashed_user_id VARCHAR(64) NOT NULL,
    predicted_label VARCHAR(50),
    confidence FLOAT,
    is_duplicate BOOLEAN DEFAULT FALSE,
    is_near_duplicate BOOLEAN DEFAULT FALSE,
    reply_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reply_outbox (
    id SERIAL PRIMARY KEY,
    processed_tweet_id INTEGER REFERENCES processed_tweets(id) ON DELETE CASCADE,
    reply_text TEXT NOT NULL,
    reply_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    batch_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_processed_tweets_hashed_user_id ON processed_tweets(hashed_user_id);
CREATE INDEX IF NOT EXISTS idx_processed_tweets_label ON processed_tweets(predicted_label);
CREATE INDEX IF NOT EXISTS idx_processed_tweets_is_duplicate ON processed_tweets(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_processed_tweets_created_at ON processed_tweets(created_at);
CREATE INDEX IF NOT EXISTS idx_reply_outbox_status ON reply_outbox(reply_status);
CREATE INDEX IF NOT EXISTS idx_reply_outbox_processed_tweet_id ON reply_outbox(processed_tweet_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_batch_id ON metrics(batch_id);
