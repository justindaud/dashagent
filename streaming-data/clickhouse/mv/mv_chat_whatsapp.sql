CREATE VIEW default.datamart_chat_whatsapp AS
WITH stage1 AS
(
    SELECT
        phone_number, message_type, message_date, message,
        csv_upload_id,
        argMax(id,              version) AS id_latest,
        argMax(created_at,      version) AS created_at,
        argMax(deleted_at,      version) AS deleted_at,
        argMax(ingested_at,     version) AS ingested_at,
        argMax(version, version) AS version_val
    FROM default.chat_whatsapp_transformed FINAL
    GROUP BY
        phone_number, message_type, message_date, message, csv_upload_id
),
grp AS
(
    SELECT
        phone_number, message_type, message_date, message,
        maxIf( (csv_upload_id, id_latest), deleted_at IS NULL ) AS w_active,
        max(    (csv_upload_id, id_latest) )                   AS w_any,
        max( if(deleted_at IS NULL, 1, 0) )                    AS has_active
    FROM stage1
    GROUP BY phone_number, message_type, message_date, message
),
final_rows AS
(
    SELECT
        s.phone_number,
        s.message_type,
        s.message_date,
        s.message,
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
        ON g.phone_number   = s.phone_number
       AND g.message_type = s.message_type
       AND g.message_date  = s.message_date
       AND g.message  = s.message
    GROUP BY
        s.phone_number, s.message_type, s.message_date, s.message, g.has_active
)
SELECT
    phone_number,
    message_type,
    message_date,
    message,
    csv_upload_id,
    created_at,
    deleted_at,
    is_deleted,
    ingested_at,
    version
FROM final_rows;