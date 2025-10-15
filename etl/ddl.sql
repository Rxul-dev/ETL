-- Data Warehouse tables (idempotent)
CREATE TABLE IF NOT EXISTS dim_users (
  user_id INT PRIMARY KEY,
  handle TEXT NOT NULL,
  display_name TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_chats (
  chat_id INT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS bridge_chat_members (
  chat_id INT NOT NULL,
  user_id INT NOT NULL,
  role TEXT NOT NULL,
  joined_at TIMESTAMP NOT NULL,
  PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS fact_messages (
  message_id INT PRIMARY KEY,
  chat_id INT NOT NULL,
  sender_id INT,
  body TEXT NOT NULL,
  message_length INT NOT NULL,
  created_at TIMESTAMP NOT NULL,
  edited_at TIMESTAMP NULL,
  reply_to_id INT NULL,
  created_day DATE NOT NULL,
  created_hour SMALLINT NOT NULL
);
