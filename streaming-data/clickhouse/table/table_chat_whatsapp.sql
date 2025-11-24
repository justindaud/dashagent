CREATE TABLE IF NOT EXISTS default.chat_whatsapp_transformed (
    id              Int32,
    csv_upload_id   Nullable(Int32),
    phone_number    Nullable(String),
    message_type    Nullable(String),
    message_date    Nullable(DateTime64(3)),
    message         Nullable(String),
    created_at      Nullable(DateTime64(3)),
    deleted_at      Nullable(DateTime64(3)),
    ingested_at     DateTime DEFAULT toTimeZone(now(), 'Asia/Jakarta'),
    version         UInt32   DEFAULT toUInt32(toUnixTimestamp(now()))
)
ENGINE = ReplacingMergeTree(version)
ORDER BY id
PRIMARY KEY id
SETTINGS index_granularity = 8192;