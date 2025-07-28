-- UUID support for unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 'thermostat', 'light', 'appliance', 'outlet'
    room TEXT NOT NULL, -- 'living_room', 'bedroom', 'kitchen', etc.
    power_rating FLOAT DEFAULT 1.0, -- Placeholder until schedule is set
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE device_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    day_of_week INT NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_hour INT NOT NULL CHECK (start_hour >= 0 AND start_hour < 24),
    end_hour INT NOT NULL CHECK (end_hour >= 0 AND end_hour < 24),
    power_consumption FLOAT NOT NULL CHECK (power_consumption >= 0),
    UNIQUE(device_id, day_of_week, start_hour)
);

CREATE TABLE telemetry (
    timestamp TIMESTAMPTZ NOT NULL,
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    energy_usage FLOAT NOT NULL,
    PRIMARY KEY (timestamp, device_id)
);

-- Speed up device history lookups
CREATE INDEX idx_telemetry_device_id_timestamp ON telemetry (device_id, timestamp DESC);