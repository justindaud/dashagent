CREATE VIEW default.datamart_transaction_resto AS
WITH stage1 AS
(
    SELECT
        bill_number, article_number, guest_name, item_name, quantity, sales, payment,
        article_category, article_subcategory, outlet, table_number, posting_id,
        reservation_number, travel_agent_name, prev_bill_number, transaction_date,
        start_time, close_time, time, bill_discount, bill_compliment, total_deduction,
        csv_upload_id,
        argMax(id,              version) AS id_latest,
        argMax(created_at,      version) AS created_at,
        argMax(deleted_at,      version) AS deleted_at,
        argMax(ingested_at,     version) AS ingested_at,
        argMax(version, version) AS version_val
    FROM default.transaction_resto_transformed FINAL
    GROUP BY
        bill_number, article_number, guest_name, item_name, quantity, sales, payment,
        article_category, article_subcategory, outlet, table_number, posting_id,
        reservation_number, travel_agent_name, prev_bill_number, transaction_date,
        start_time, close_time, time, bill_discount, bill_compliment, total_deduction,
        csv_upload_id
),
grp AS
(
    SELECT
        bill_number, article_number, guest_name, item_name, quantity, sales, payment,
        article_category, article_subcategory, outlet, table_number, posting_id,
        reservation_number, travel_agent_name, prev_bill_number, transaction_date,
        start_time, close_time, time, bill_discount, bill_compliment, total_deduction,
        maxIf( (csv_upload_id, id_latest), deleted_at IS NULL ) AS w_active,
        max(    (csv_upload_id, id_latest) )                   AS w_any,
        max( if(deleted_at IS NULL, 1, 0) )                    AS has_active
    FROM stage1
    GROUP BY bill_number, article_number, guest_name, item_name, quantity, sales, payment,
        article_category, article_subcategory, outlet, table_number, posting_id,
        reservation_number, travel_agent_name, prev_bill_number, transaction_date,
        start_time, close_time, time, bill_discount, bill_compliment, total_deduction
),
final_rows AS
(
    SELECT
        s.bill_number,
        s.article_number,
        s.guest_name,
        s.item_name,
        s.quantity,
        s.sales,
        s.payment,
        s.article_category,
        s.article_subcategory,
        s.outlet,
        s.table_number,
        s.posting_id,
        s.reservation_number,
        s.travel_agent_name,
        s.prev_bill_number,
        s.transaction_date,
        s.start_time,
        s.close_time,
        s.time,
        s.bill_discount,
        s.bill_compliment,
        s.total_deduction,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.csv_upload_id, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.csv_upload_id, (s.csv_upload_id, s.id_latest))
        ) AS csv_upload_id,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.created_at, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.created_at, (s.csv_upload_id, s.id_latest))
        ) AS created_at,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.deleted_at, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.deleted_at, (s.csv_upload_id, s.id_latest))
        ) AS deleted_at,
        if(g.has_active = 1, 0, 1) AS is_deleted,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.ingested_at, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.ingested_at, (s.csv_upload_id, s.id_latest))
        ) AS ingested_at,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.version_val, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.version_val, (s.csv_upload_id, s.id_latest))
        ) AS version
    FROM stage1 AS s
    INNER JOIN grp AS g
        ON  coalesce(g.bill_number,      '') = coalesce(s.bill_number,      '')
        AND coalesce(g.article_number,   '') = coalesce(s.article_number,   '')
        AND coalesce(g.guest_name,      '') = coalesce(s.guest_name,      '')
        AND coalesce(g.item_name,       '') = coalesce(s.item_name,       '')
        AND coalesce(g.quantity,        0)   = coalesce(s.quantity,        0)
        AND coalesce(g.sales,           0)   = coalesce(s.sales,           0)
        AND coalesce(g.payment,         0)   = coalesce(s.payment,         0)
        AND coalesce(g.article_category,    '') = coalesce(s.article_category,    '')
        AND coalesce(g.article_subcategory, '') = coalesce(s.article_subcategory, '')
        AND coalesce(g.outlet,           '') = coalesce(s.outlet,           '')
        AND coalesce(g.table_number,    0)   = coalesce(s.table_number,    0)
        AND coalesce(g.posting_id,      '') = coalesce(s.posting_id,      '')
        AND coalesce(g.reservation_number, '') = coalesce(s.reservation_number, '')
        AND coalesce(g.travel_agent_name,  '') = coalesce(s.travel_agent_name,  '')
        AND coalesce(g.prev_bill_number,   '') = coalesce(s.prev_bill_number,   '')
        AND coalesce(
                g.transaction_date,
                toDateTime64('1970-01-01 00:00:00', 3, 'Asia/Jakarta')
            ) = coalesce(
                s.transaction_date,
                toDateTime64('1970-01-01 00:00:00', 3, 'Asia/Jakarta')
            )
        AND coalesce(g.start_time,      '')   = coalesce(s.start_time,      '')
        AND coalesce(g.close_time,      '')   = coalesce(s.close_time,      '')
        AND coalesce(g.time,            '')   = coalesce(s.time,            '')
        AND coalesce(g.bill_discount,    0) = coalesce(s.bill_discount,    0)
        AND coalesce(g.bill_compliment,  0) = coalesce(s.bill_compliment,  0)
        AND coalesce(g.total_deduction,  0) = coalesce(s.total_deduction,  0)
    GROUP BY
        s.bill_number, s.article_number, s.guest_name, s.item_name, s.quantity, s.sales, s.payment,
        s.article_category, s.article_subcategory, s.outlet, s.table_number, s.posting_id,
        s.reservation_number, s.travel_agent_name, s.prev_bill_number, s.transaction_date,
        s.start_time, s.close_time, s.time, s.bill_discount, s.bill_compliment, s.total_deduction, g.has_active
)
SELECT
    bill_number,
    article_number,
    guest_name,
    item_name,
    quantity,
    sales,
    payment,
    article_category,
    article_subcategory,
    outlet,
    table_number,
    posting_id,
    reservation_number,
    travel_agent_name,
    prev_bill_number,
    transaction_date,
    start_time,
    close_time,
    time,
    bill_discount,
    bill_compliment,
    total_deduction,
    csv_upload_id,
    created_at,
    deleted_at,
    is_deleted,
    ingested_at,
    version
FROM final_rows;