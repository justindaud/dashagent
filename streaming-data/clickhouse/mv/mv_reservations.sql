CREATE VIEW default.datamart_reservations AS
WITH stage1 AS
(
    SELECT
        guest_name, arrival_date, depart_date, room_number,
        csv_upload_id,
        argMax(id,             version) AS id_latest,
        argMax(reservation_id, version) AS reservation_id,
        argMax(guest_id,       version) AS guest_id,
        argMax(room_type,      version) AS room_type,
        argMax(arrangement,    version) AS arrangement,
        argMax(in_house_date,  version) AS in_house_date,
        argMax(check_in_time,  version) AS check_in_time,
        argMax(check_out_time, version) AS check_out_time,
        argMax(created_date,   version) AS created_date,
        argMax(birth_date,     version) AS birth_date,
        argMax(age,            version) AS age,
        argMax(member_no,      version) AS member_no,
        argMax(member_type,    version) AS member_type,
        argMax(email,          version) AS email,
        argMax(mobile_phone,   version) AS mobile_phone,
        argMax(vip_status,     version) AS vip_status,
        argMax(bill_number,    version) AS bill_number,
        argMax(pay_article,    version) AS pay_article,
        argMax(rate_code,      version) AS rate_code,
        argMax(adult_count,    version) AS adult_count,
        argMax(child_count,    version) AS child_count,
        argMax(compliment,     version) AS compliment,
        argMax(nationality,    version) AS nationality,
        argMax(local_region,   version) AS local_region,
        argMax(company_ta,     version) AS company_ta,
        argMax(sob,            version) AS sob,
        argMax(segment,        version) AS segment,
        argMax(created_by,     version) AS created_by,
        argMax(k_card,         version) AS k_card,
        argMax(remarks,        version) AS remarks,
        argMax(nights,         version) AS nights_stage1,
        argMax(room_rate,      version) AS room_rate_stage1,
        argMax(lodging,        version) AS lodging_stage1,
        argMax(breakfast,      version) AS breakfast_stage1,
        argMax(lunch,          version) AS lunch_stage1,
        argMax(dinner,         version) AS dinner_stage1,
        argMax(other_charges,  version) AS other_charges_stage1,
        argMax(created_at,     version) AS created_at,
        argMax(deleted_at,     version) AS deleted_at,
        argMax(ingested_at,    version) AS ingested_at,
        argMax(version, version) AS version_val
    FROM default.reservations_transformed FINAL
    GROUP BY
        guest_name, arrival_date, depart_date, room_number, csv_upload_id
),
grp AS
(
    SELECT
        guest_name, arrival_date, depart_date, room_number,
        maxIf( (csv_upload_id, id_latest), deleted_at IS NULL ) AS w_active,
        max(    (csv_upload_id, id_latest) )                   AS w_any,
        max( if(deleted_at IS NULL, 1, 0) )                    AS has_active
    FROM stage1
    GROUP BY guest_name, arrival_date, depart_date, room_number
),
final_rows AS
(
    SELECT
        s.guest_name,
        s.arrival_date,
        s.depart_date,
        s.room_number,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.csv_upload_id, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.csv_upload_id, (s.csv_upload_id, s.id_latest))
        ) AS csv_upload_id,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.reservation_id, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.reservation_id, (s.csv_upload_id, s.id_latest))
        ) AS reservation_id,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.guest_id, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.guest_id, (s.csv_upload_id, s.id_latest))
        ) AS guest_id,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.room_type, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.room_type, (s.csv_upload_id, s.id_latest))
        ) AS room_type,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.arrangement, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.arrangement, (s.csv_upload_id, s.id_latest))
        ) AS arrangement,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.in_house_date, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.in_house_date, (s.csv_upload_id, s.id_latest))
        ) AS in_house_date,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.check_in_time, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.check_in_time, (s.csv_upload_id, s.id_latest))
        ) AS check_in_time,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.check_out_time, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.check_out_time, (s.csv_upload_id, s.id_latest))
        ) AS check_out_time,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.created_date, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.created_date, (s.csv_upload_id, s.id_latest))
        ) AS created_date,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.birth_date, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.birth_date, (s.csv_upload_id, s.id_latest))
        ) AS birth_date,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.age, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.age, (s.csv_upload_id, s.id_latest))
        ) AS age,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.member_no, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.member_no, (s.csv_upload_id, s.id_latest))
        ) AS member_no,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.member_type, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.member_type, (s.csv_upload_id, s.id_latest))
        ) AS member_type,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.email, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.email, (s.csv_upload_id, s.id_latest))
        ) AS email,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.mobile_phone, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.mobile_phone, (s.csv_upload_id, s.id_latest))
        ) AS mobile_phone,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.vip_status, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.vip_status, (s.csv_upload_id, s.id_latest))
        ) AS vip_status,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.bill_number, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.bill_number, (s.csv_upload_id, s.id_latest))
        ) AS bill_number,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.pay_article, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.pay_article, (s.csv_upload_id, s.id_latest))
        ) AS pay_article,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.rate_code, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.rate_code, (s.csv_upload_id, s.id_latest))
        ) AS rate_code,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.adult_count, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.adult_count, (s.csv_upload_id, s.id_latest))
        ) AS adult_count,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.child_count, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.child_count, (s.csv_upload_id, s.id_latest))
        ) AS child_count,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.compliment, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.compliment, (s.csv_upload_id, s.id_latest))
        ) AS compliment,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.nationality, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.nationality, (s.csv_upload_id, s.id_latest))
        ) AS nationality,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.local_region, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.local_region, (s.csv_upload_id, s.id_latest))
        ) AS local_region,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.company_ta, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.company_ta, (s.csv_upload_id, s.id_latest))
        ) AS company_ta,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.sob, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.sob, (s.csv_upload_id, s.id_latest))
        ) AS sob,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.nights_stage1, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.nights_stage1, (s.csv_upload_id, s.id_latest))
        ) AS nights,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.segment, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.segment, (s.csv_upload_id, s.id_latest))
        ) AS segment,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.created_by, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.created_by, (s.csv_upload_id, s.id_latest))
        ) AS created_by,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.k_card, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.k_card, (s.csv_upload_id, s.id_latest))
        ) AS k_card,
        multiIf(
            g.has_active = 1,
            argMaxIf(s.remarks, (s.csv_upload_id, s.id_latest), s.deleted_at IS NULL),
            argMax(   s.remarks, (s.csv_upload_id, s.id_latest))
        ) AS remarks,
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
        ON g.guest_name   = s.guest_name
       AND g.arrival_date = s.arrival_date
       AND g.depart_date  = s.depart_date
       AND g.room_number  = s.room_number
    GROUP BY
        s.guest_name, s.arrival_date, s.depart_date, s.room_number, g.has_active
),
agg_active AS
(
    SELECT
        guest_name, arrival_date, depart_date, room_number,
        
        toDecimal64(avg(room_rate_stage1), 2)     AS room_rate,
        toDecimal64(avg(lodging_stage1), 2)       AS lodging,
        toDecimal64(avg(breakfast_stage1), 2)     AS breakfast,
        toDecimal64(avg(lunch_stage1), 2)         AS lunch,
        toDecimal64(avg(dinner_stage1), 2)        AS dinner,
        toDecimal64(avg(other_charges_stage1), 2) AS other_charges,
        toDecimal64(avg(room_rate_stage1 * nights_stage1), 2) AS total_amount
        
    FROM stage1
    WHERE deleted_at IS NULL
    GROUP BY guest_name, arrival_date, depart_date, room_number
),
final_rows_enriched AS
(
    SELECT
        f.*,
        CASE
            WHEN f.room_type IS NULL OR f.room_type = '' THEN ''
            WHEN startsWith(upper(f.room_type), 'FS') THEN 'Family Suite'
            WHEN startsWith(upper(f.room_type), 'D')  THEN 'Deluxe'
            WHEN startsWith(upper(f.room_type), 'E')  THEN 'Executive Suite'
            WHEN startsWith(upper(f.room_type), 'J')  THEN 'Executive Suite'
            WHEN startsWith(upper(f.room_type), 'B')  THEN 'Suite'
            ELSE ''
        END AS room_type_desc
    FROM final_rows AS f
)
SELECT
    f.guest_name,
    f.arrival_date,
    f.depart_date,
    f.room_number,
    f.csv_upload_id,
    f.reservation_id,
    f.guest_id,
    f.room_type,
    f.room_type_desc,
    f.arrangement,
    f.in_house_date,
    coalesce(a.room_rate,     toDecimal64(0, 2)) AS room_rate,
    coalesce(a.lodging,       toDecimal64(0, 2)) AS lodging,
    coalesce(a.breakfast,     toDecimal64(0, 2)) AS breakfast,
    coalesce(a.lunch,         toDecimal64(0, 2)) AS lunch,
    coalesce(a.dinner,        toDecimal64(0, 2)) AS dinner,
    coalesce(a.other_charges, toDecimal64(0, 2)) AS other_charges,
    coalesce(a.total_amount,  toDecimal64(0, 2)) AS total_amount,
    f.check_in_time,
    f.check_out_time,
    f.created_date,
    f.birth_date,
    f.age,
    f.member_no,
    f.member_type,
    f.email,
    f.mobile_phone,
    f.vip_status,
    f.bill_number,
    f.pay_article,
    f.rate_code,
    f.adult_count,
    f.child_count,
    f.compliment,
    f.nationality,
    f.local_region,
    f.company_ta,
    f.sob,
    f.nights,
    f.segment,
    f.created_by,
    f.k_card,
    f.remarks,
    f.created_at,
    f.deleted_at,
    f.is_deleted,
    f.ingested_at,
    f.version
FROM final_rows_enriched AS f
LEFT JOIN agg_active AS a
  ON a.guest_name   = f.guest_name
 AND a.arrival_date = f.arrival_date
 And a.depart_date  = f.depart_date
 And a.room_number  = f.room_number;