PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS student_hidden_event_requests;
DROP TABLE IF EXISTS event_registrations;
DROP TABLE IF EXISTS room_bookings;

DROP TABLE IF EXISTS event_requests;
DROP TABLE IF EXISTS admin_settings;

DROP TABLE IF EXISTS email_verifications;
DROP TABLE IF EXISTS users;

DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS info_pages;

-- -------------------------
-- Core domain tables
-- -------------------------

CREATE TABLE rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL CHECK (type IN ('single','shared','studio')),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  price_eur INTEGER NOT NULL CHECK (price_eur >= 0),
  capacity INTEGER NOT NULL CHECK (capacity >= 1),
  available INTEGER NOT NULL DEFAULT 1 CHECK (available IN (0,1))
);

-- Only ACCEPTED events become visible in events list
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('social','orientation','study_group')),
  date_time TEXT NOT NULL,
  location TEXT NOT NULL,
  description TEXT NOT NULL,
  quota INTEGER NULL CHECK (quota IS NULL OR quota >= 0), -- NULL = unlimited
  created_by_email TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE info_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  content TEXT NOT NULL
);

-- -------------------------
-- Auth tables (prototype: store plain code too)
-- -------------------------

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student','admin')),
  created_at TEXT NOT NULL
);

-- Prototype mode: store code_plain so UI can display it
-- Real mode: you would NOT store code_plain
CREATE TABLE email_verifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  code_hash TEXT NOT NULL,
  code_plain TEXT NOT NULL,         -- <---- ADDED
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  last_sent_at TEXT NOT NULL
);

-- -------------------------
-- Admin settings
-- -------------------------

CREATE TABLE admin_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT INTO admin_settings (key, value) VALUES ('rooms_open', '1');

-- -------------------------
-- One room per student
-- -------------------------

CREATE TABLE room_bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  room_id INTEGER NOT NULL,
  user_email TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
);

-- -------------------------
-- Event registrations
-- -------------------------

CREATE TABLE event_registrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL,
  user_email TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(event_id, user_email),
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- -------------------------
-- Student event requests
-- -------------------------

CREATE TABLE event_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('social','orientation','study_group')),
  date_time TEXT NOT NULL,
  location TEXT NOT NULL,
  description TEXT NOT NULL,
  quota INTEGER NULL CHECK (quota IS NULL OR quota >= 0),
  requested_by_email TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending','accepted','rejected')),
  admin_comment TEXT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE student_hidden_event_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL,
  student_email TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(request_id, student_email),
  FOREIGN KEY (request_id) REFERENCES event_requests(id) ON DELETE CASCADE
);

-- Helpful indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

CREATE INDEX idx_room_bookings_room ON room_bookings(room_id);
CREATE INDEX idx_event_regs_event ON event_registrations(event_id);

CREATE INDEX idx_event_requests_student ON event_requests(requested_by_email);
CREATE INDEX idx_event_requests_status ON event_requests(status);

CREATE INDEX idx_hidden_req_student ON student_hidden_event_requests(student_email);
