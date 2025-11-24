CREATE TABLE IF NOT EXISTS default.transaction_resto_transformed (
    id                  Int32,
    csv_upload_id       Nullable(Int32),
    bill_number         Nullable(String),
    article_number      Nullable(String),
    guest_name          Nullable(String),
    item_name           Nullable(String),
    quantity            Nullable(Int64),
    sales               Nullable(Int64),
    payment             Nullable(Int64),
    article_category    Nullable(String),
    article_subcategory Nullable(String),
    outlet              Nullable(String),
    table_number        Nullable(Int64),
    posting_id          Nullable(String),
    reservation_number  Nullable(String),
    travel_agent_name   Nullable(String),
    prev_bill_number    Nullable(String),
    transaction_date    Nullable(DateTime64(3)),
    start_time          Nullable(String),
    close_time          Nullable(String),
    time                Nullable(String),
    bill_discount       Nullable(Decimal(18,2)),
    bill_compliment     Nullable(Decimal(18,2)),
    total_deduction     Nullable(Decimal(18,2)),
    created_at          Nullable(DateTime64(3)),
    deleted_at          Nullable(DateTime64(3)),
    ingested_at         DateTime DEFAULT toTimeZone(now(), 'Asia/Jakarta'),
    version             UInt32   DEFAULT toUInt32(toUnixTimestamp(now()))
)
ENGINE = ReplacingMergeTree(version)
ORDER BY id
PRIMARY KEY id
SETTINGS index_granularity = 8192;