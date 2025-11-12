-- Data Warehouse tables (idempotent)
-- Usando TIMESTAMPTZ para manejo correcto de timezones

CREATE TABLE IF NOT EXISTS dim_users (
  user_id INT PRIMARY KEY,
  handle TEXT NOT NULL,
  display_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_chats (
  chat_id INT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS bridge_chat_members (
  chat_id INT NOT NULL,
  user_id INT NOT NULL,
  role TEXT NOT NULL,
  joined_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (chat_id, user_id),
  FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES dim_users(user_id) ON DELETE CASCADE
);

-- Tabla de hechos de mensajes
CREATE TABLE IF NOT EXISTS fact_messages (
  message_id INT PRIMARY KEY,
  chat_id INT NOT NULL,
  sender_id INT,
  body TEXT NOT NULL,
  message_length INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  edited_at TIMESTAMPTZ NULL,
  reply_to_id INT NULL,
  created_day DATE NOT NULL,
  created_hour SMALLINT NOT NULL,
  FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
  FOREIGN KEY (sender_id) REFERENCES dim_users(user_id) ON DELETE SET NULL
);

-- Índices para consultas analíticas comunes
CREATE INDEX IF NOT EXISTS idx_fact_messages_chat_date 
  ON fact_messages(chat_id, created_day);
CREATE INDEX IF NOT EXISTS idx_fact_messages_sender_date 
  ON fact_messages(sender_id, created_day) WHERE sender_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_fact_messages_created_at 
  ON fact_messages(created_at);

-- Tabla de hechos de reacciones
CREATE TABLE IF NOT EXISTS fact_reactions (
  message_id INT NOT NULL,
  chat_id INT NOT NULL,
  user_id INT NOT NULL,
  emoji TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  created_day DATE NOT NULL,
  created_hour SMALLINT NOT NULL,
  PRIMARY KEY (message_id, user_id, emoji),
  FOREIGN KEY (message_id) REFERENCES fact_messages(message_id) ON DELETE CASCADE,
  FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES dim_users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fact_reactions_chat_date 
  ON fact_reactions(chat_id, created_day);
CREATE INDEX IF NOT EXISTS idx_fact_reactions_message 
  ON fact_reactions(message_id);

-- Tabla de hechos de bookings
CREATE TABLE IF NOT EXISTS fact_bookings (
  booking_id INT PRIMARY KEY,
  chat_id INT NOT NULL,
  user_id INT NOT NULL,
  message_id INT,
  booking_type TEXT,
  booking_date TIMESTAMPTZ,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  created_day DATE NOT NULL,
  created_hour SMALLINT NOT NULL,
  FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES dim_users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (message_id) REFERENCES fact_messages(message_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_bookings_date_status 
  ON fact_bookings(created_day, status);
CREATE INDEX IF NOT EXISTS idx_fact_bookings_chat 
  ON fact_bookings(chat_id);

-- Tabla de eventos de bookings
CREATE TABLE IF NOT EXISTS fact_booking_events (
  event_id INT PRIMARY KEY,
  booking_id INT NOT NULL,
  event_type TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  created_day DATE NOT NULL,
  created_hour SMALLINT NOT NULL,
  FOREIGN KEY (booking_id) REFERENCES fact_bookings(booking_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fact_booking_events_booking 
  ON fact_booking_events(booking_id);
CREATE INDEX IF NOT EXISTS idx_fact_booking_events_date 
  ON fact_booking_events(created_day);

-- Tabla de watermarks para ETL incremental
CREATE TABLE IF NOT EXISTS etl_watermarks (
  key TEXT PRIMARY KEY,
  value TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
