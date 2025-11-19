CREATE VIEW default.datamart_profile_guest AS
WITH stage1 AS
(
    SELECT
        name, guest_id, csv_upload_id,
        argMax(id, version) AS id_latest,
        argMax(email, version) AS email,
        argMax(phone, version) AS phone,
        argMax(address, version) AS address,
        argMax(birth_date, version) AS birth_date,
        argMax(occupation, version) AS occupation,
        argMax(city, version) AS city,
        argMax(country, version) AS country,
        argMax(segment, version) AS segment,
        argMax(type_id, version) AS type_id,
        argMax(id_no, version) AS id_no,
        argMax(sex, version) AS sex,
        argMax(zip_code, version) AS zip_code,
        argMax(local_region, version) AS local_region,
        argMax(telefax, version) AS telefax,
        argMax(comments, version) AS comments,
        argMax(credit_limit, version) AS credit_limit,
        argMax(mobile_no, version) AS mobile_no,
        argMax(created_at, version) AS created_at,
        argMax(deleted_at, version) AS deleted_at,
        argMax(ingested_at, version) AS ingested_at,
        argMax(version, version) AS version_val
    FROM default.profile_guest_transformed FINAL
    GROUP BY name, guest_id, csv_upload_id
),
grp AS
(
    SELECT
        name, guest_id,
        maxIf( (csv_upload_id, id_latest), deleted_at IS NULL ) AS w_active,
        max(    (csv_upload_id, id_latest) )                   AS w_any,
        max( if(deleted_at IS NULL, 1, 0) )                    AS has_active
    FROM stage1
    GROUP BY name, guest_id
),
final_rows AS
(
    SELECT
        s.name,
        s.guest_id,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.csv_upload_id, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.csv_upload_id, (s.csv_upload_id, s.id_latest))
        ) AS csv_upload_id,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.email, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.email, (s.csv_upload_id, s.id_latest))
        ) AS email,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.phone, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.phone, (s.csv_upload_id, s.id_latest))
        ) AS phone,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.address, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.address, (s.csv_upload_id, s.id_latest))
        ) AS address,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.birth_date, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.birth_date, (s.csv_upload_id, s.id_latest))
        ) AS birth_date,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.occupation, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.occupation, (s.csv_upload_id, s.id_latest))
        ) AS occupation,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.city, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.city, (s.csv_upload_id, s.id_latest))
        ) AS city,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.country, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.country, (s.csv_upload_id, s.id_latest))
        ) AS country,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.segment, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.segment, (s.csv_upload_id, s.id_latest))
        ) AS segment,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.type_id, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.type_id, (s.csv_upload_id, s.id_latest))
        ) AS type_id,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.id_no, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.id_no, (s.csv_upload_id, s.id_latest))
        ) AS id_no,
        multiIf(
            g.has_active = 1, 
            argMaxIf(s.sex, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.sex, (s.csv_upload_id, s.id_latest))
        ) AS sex,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.zip_code, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.zip_code, (s.csv_upload_id, s.id_latest))
        ) AS zip_code,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.local_region, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.local_region, (s.csv_upload_id, s.id_latest))
        ) AS local_region,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.telefax, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.telefax, (s.csv_upload_id, s.id_latest))
        ) AS telefax,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.comments, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.comments, (s.csv_upload_id, s.id_latest))
        ) AS comments,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.credit_limit, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.credit_limit, (s.csv_upload_id, s.id_latest))
        ) AS credit_limit,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.mobile_no, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.mobile_no, (s.csv_upload_id, s.id_latest))
        ) AS mobile_no,
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
    FROM stage1 s
    INNER JOIN grp g 
        ON g.name = s.name
        AND g.guest_id = s.guest_id
    GROUP BY s.name, s.guest_id, g.has_active
)
SELECT
    name,
    csv_upload_id,
    guest_id,
    email,
    phone,
    address,
    birth_date,
    occupation,
    city,
    country,
    segment,
    type_id,
    id_no,
    sex,
    zip_code,
    local_region,
    telefax,
    comments,
    credit_limit,
    mobile_no,
    created_at,
    deleted_at,
    is_deleted,
    ingested_at,
    version
FROM final_rows;