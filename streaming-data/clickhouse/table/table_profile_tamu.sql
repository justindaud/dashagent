CREATE TABLE IF NOT EXISTS default.profile_guest_transformed (
    id              Int32,
    csv_upload_id   Int32,
    guest_id        Nullable(String),
    name            String,
    email           Nullable(String),
    phone           Nullable(String),
    address         Nullable(String),
    birth_date      Nullable(String),
    occupation      Nullable(String),
    city            Nullable(String),
    country         Nullable(String),
    segment         Nullable(String),
    type_id         Nullable(String),
    id_no           Nullable(String),
    sex             Nullable(String),
    zip_code        Nullable(String),
    local_region    Nullable(String),
    telefax         Nullable(String),
    comments        Nullable(String),
    credit_limit    Nullable(String),
    mobile_no       Nullable(String),
    created_at      Nullable(DateTime64(3)),
    deleted_at      Nullable(DateTime64(3)),
    ingested_at     DateTime DEFAULT toTimeZone(now(), 'Asia/Jakarta'),
    version         UInt32   DEFAULT toUInt32(toUnixTimestamp(now()))
)
ENGINE = ReplacingMergeTree(version)
ORDER BY id
PRIMARY KEY id
SETTINGS index_granularity = 8192;