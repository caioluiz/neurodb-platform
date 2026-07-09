-- =====================================================
-- Schema Fase 1: Data Warehouse de Sinais EEG
-- =====================================================

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id      SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    source_url      TEXT,
    license         VARCHAR(100),
    description     TEXT,
    imported_at     TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id      SERIAL PRIMARY KEY,
    dataset_id      INTEGER REFERENCES datasets(dataset_id),
    external_code   VARCHAR(100),
    age             INTEGER,
    sex             VARCHAR(20),
    handedness      VARCHAR(20),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id      SERIAL PRIMARY KEY,
    subject_id      INTEGER REFERENCES subjects(subject_id),
    session_date    DATE,
    task            VARCHAR(255),
    condition       VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS recordings (
    recording_id    SERIAL PRIMARY KEY,
    session_id      INTEGER REFERENCES sessions(session_id),
    file_path       TEXT NOT NULL,
    format          VARCHAR(20),
    sampling_rate   NUMERIC,
    duration_seconds NUMERIC,
    num_channels    INTEGER
);

CREATE TABLE IF NOT EXISTS channels (
    channel_id      SERIAL PRIMARY KEY,
    recording_id    INTEGER REFERENCES recordings(recording_id),
    label           VARCHAR(20),
    position_x      NUMERIC,
    position_y      NUMERIC,
    position_z      NUMERIC,
    unit            VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS events (
    event_id        SERIAL PRIMARY KEY,
    recording_id    INTEGER REFERENCES recordings(recording_id),
    onset_seconds   NUMERIC,
    duration_seconds NUMERIC,
    label           VARCHAR(255),
    description     TEXT
);

CREATE TABLE IF NOT EXISTS features (
    feature_id      SERIAL PRIMARY KEY,
    recording_id    INTEGER REFERENCES recordings(recording_id),
    channel_id      INTEGER REFERENCES channels(channel_id),
    feature_name    VARCHAR(100),
    frequency_band  VARCHAR(50),
    value           NUMERIC,
    computed_at     TIMESTAMP DEFAULT now()
);

-- Índices úteis para as queries mais comuns
CREATE INDEX IF NOT EXISTS idx_subjects_dataset ON subjects(dataset_id);
CREATE INDEX IF NOT EXISTS idx_sessions_subject ON sessions(subject_id);
CREATE INDEX IF NOT EXISTS idx_recordings_session ON recordings(session_id);
CREATE INDEX IF NOT EXISTS idx_channels_recording ON channels(recording_id);
CREATE INDEX IF NOT EXISTS idx_events_recording ON events(recording_id);
CREATE INDEX IF NOT EXISTS idx_features_recording ON features(recording_id);
