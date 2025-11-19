# spark_apps/transform_reservasi.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, trim, upper, lower, concat_ws, regexp_replace, to_json, struct,
    to_date, date_format, to_timestamp, coalesce, substring, from_json, expr
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, DecimalType

def _payload():
    return StructType([
        StructField("id", IntegerType()),
        StructField("csv_upload_id", IntegerType()),
        StructField("reservation_id", IntegerType()),
        StructField("guest_id", StringType()),
        StructField("first_name", StringType()),
        StructField("last_name", StringType()),
        StructField("room_number", StringType()),
        StructField("room_type", StringType()),
        StructField("arrangement", StringType()),
        StructField("in_house_date", StringType()),
        StructField("arrival_date", StringType()),
        StructField("depart_date", StringType()),
        StructField("check_in_time", StringType()),
        StructField("check_out_time", StringType()),
        StructField("created_date", StringType()),
        StructField("birth_date", StringType()),
        StructField("age", IntegerType()),
        StructField("member_no", StringType()),
        StructField("member_type", StringType()),
        StructField("email", StringType()),
        StructField("mobile_phone", StringType()),
        StructField("vip_status", StringType()),
        StructField("room_rate", FloatType()),
        StructField("lodging", FloatType()),
        StructField("breakfast", FloatType()),
        StructField("lunch", FloatType()),
        StructField("dinner", FloatType()),
        StructField("other_charges", FloatType()),
        StructField("bill_number", StringType()),
        StructField("pay_article", StringType()),
        StructField("rate_code", StringType()),
        StructField("adult_count", StringType()),
        StructField("child_count", StringType()),
        StructField("compliment", StringType()),
        StructField("nationality", StringType()),
        StructField("local_region", StringType()),
        StructField("company_ta", StringType()),
        StructField("sob", StringType()),
        StructField("nights", StringType()),
        StructField("segment", StringType()),
        StructField("created_by", StringType()),
        StructField("k_card", StringType()),
        StructField("remarks", StringType()),
        StructField("created_at", StringType()),
        StructField("deleted_at", StringType()),
    ])

def _message(p):
    return StructType([StructField("after", p), StructField("op", StringType())])

_BAD_TOKENS = ["NAN", "NONE", "NULL", "NA", "N A", "N/A", "", "NaN", "nan", "null"]

def _nz(c, default=""):
    return when(c.isNull() | (trim(c) == "") | c.isin(*_BAD_TOKENS), lit(default)).otherwise(c)

def _is_blank(c):
    return c.isNull() | (trim(c) == "") | c.isin(*_BAD_TOKENS)

def _strip_dot_zero(c):
    return regexp_replace(c.cast("string"), r"\.0$", "")

def _norm_time_hhmm(c):
    parsed = coalesce(
        to_timestamp(c, "H:mm"),
        to_timestamp(c, "HH:mm"),
        to_timestamp(regexp_replace(c, r"[^0-9:]", ""), "HHmm")
    )
    return when(parsed.isNotNull(), date_format(parsed, "HH:mm")).otherwise(lit(None).cast("string"))

def _norm_currency_decimal(c):
    s = regexp_replace(trim(c.cast("string")), ",", "")
    s = regexp_replace(s, r"[^\d\.\-\(\)]", "")
    sign = when(s.rlike(r"^\(.*\)$"), lit(-1)).otherwise(lit(1))
    num = regexp_replace(s, r"[()]", "")
    num = regexp_replace(num, r"[^0-9\.\-]", "")
    num_dec = num.cast("decimal(18,6)")
    res = (num_dec * sign.cast("decimal(18,6)")).cast("decimal(18,2)")
    return res

def _parse_to_ts_local(c):
    s = _nz(c)
    s = regexp_replace(s, r"[Tt]", " ")
    s = regexp_replace(s, r"Z$", "")
    s = regexp_replace(s, r"([+\-]\d{2}:\d{2})$", "")
    s = regexp_replace(s, r"([+\-]\d{2})(\d{2})$", "")
    s = regexp_replace(s, r"(\d{1,2})\.(\d{1,2})\.(\d{1,2})(\.\d{1,6})?", r"\1:\2:\3\4")
    s = regexp_replace(s, r"/", "-")
    s = trim(s)

    ts = coalesce(
        to_timestamp(s, "yyyy-MM-dd HH:mm:ss.SSS"),
        to_timestamp(s, "yyyy-MM-dd H:m:s.SSS"),
        to_timestamp(s, "yyyy-MM-dd HH:mm:ss"),
        to_timestamp(s, "yyyy-MM-dd H:m:s"),
        to_timestamp(s, "yyyy-M-d HH:mm:ss.SSS"),
        to_timestamp(s, "yyyy-M-d H:m:s.SSS"),
        to_timestamp(s, "yyyy-M-d HH:mm:ss"),
        to_timestamp(s, "yyyy-M-d H:m:s"),

        to_timestamp(s, "MM-dd-yyyy HH:mm:ss.SSS"),
        to_timestamp(s, "MM-dd-yyyy H:m:s.SSS"),
        to_timestamp(s, "MM-dd-yyyy HH:mm:ss"),
        to_timestamp(s, "MM-dd-yyyy H:m:s"),
        to_timestamp(s, "M-d-yyyy HH:mm:ss.SSS"),
        to_timestamp(s, "M-d-yyyy H:m:s.SSS"),
        to_timestamp(s, "M-d-yyyy HH:mm:ss"),
        to_timestamp(s, "M-d-yyyy H:m:s"),

        to_timestamp(s, "dd-MM-yyyy HH:mm:ss.SSS"),
        to_timestamp(s, "dd-MM-yyyy H:m:s.SSS"),
        to_timestamp(s, "dd-MM-yyyy HH:mm:ss"),
        to_timestamp(s, "dd-MM-yyyy H:m:s"),
        to_timestamp(s, "d-M-yyyy HH:mm:ss.SSS"),
        to_timestamp(s, "d-M-yyyy H:m:s.SSS"),
        to_timestamp(s, "d-M-yyyy HH:mm:ss"),
        to_timestamp(s, "d-M-yyyy H:m:s"),

        to_timestamp(s, "yyyy-MM-dd"),
        to_timestamp(s, "yyyy-M-d"),
        to_timestamp(s, "MM-dd-yyyy"),
        to_timestamp(s, "M-d-yyyy"),
        to_timestamp(s, "dd-MM-yyyy"),
        to_timestamp(s, "d-M-yyyy"),

        to_timestamp(s)
    )

    only_d = coalesce(
        to_date(s, "yyyy-MM-dd"), to_date(s, "yyyy-M-d"),
        to_date(s, "MM-dd-yyyy"), to_date(s, "M-d-yyyy"),
        to_date(s, "dd-MM-yyyy"), to_date(s, "d-M-yyyy"),
        to_date(s)
    )
    ts_midnight = to_timestamp(date_format(only_d, "yyyy-MM-dd"), "yyyy-MM-dd")

    return coalesce(ts, ts_midnight)


def _fmt_no_t_no_tz(c_ts):
    return when(c_ts.isNotNull(), date_format(c_ts, "yyyy-MM-dd HH:mm:ss")).otherwise(lit(None).cast("string"))

def _yyyymmdd_from_str(c_any):
    ts = _parse_to_ts_local(c_any)
    return date_format(ts, "yyyyMMdd")

def _guest_id_fallback(df):
    arrival_key = _yyyymmdd_from_str(_nz(col("arrival_date")))
    guest_name = upper(trim(concat_ws(" ", _nz(col("first_name")), _nz(col("last_name")))))
    room = _nz(col("room_number"))
    csv_id = col("csv_upload_id").cast("string")

    base1 = concat_ws("_", guest_name, room, arrival_key)
    base1_clean = regexp_replace(base1, r"[^\w]+", "_")
    base1_clean = regexp_replace(base1_clean, r"_+", "_")
    base1_clean = upper(trim(base1_clean))

    base2 = concat_ws("_", guest_name, arrival_key, col("id").cast("string"))
    base2_clean = regexp_replace(base2, r"[^\w]+", "_")
    base2_clean = regexp_replace(base2_clean, r"_+", "_")
    base2_clean = upper(trim(base2_clean))

    base3_clean = concat_ws("_", lit("GUEST"), csv_id, col("id").cast("string"))

    cand1 = substring(base1_clean, 1, 50)
    cand2 = substring(base2_clean, 1, 50)

    guest_id_clean = _strip_dot_zero(_nz(col("guest_id")))
    generated = when(
        (~_is_blank(guest_name)) & (~_is_blank(room)) & (~_is_blank(arrival_key)),
        cand1
    ).when(
        (~_is_blank(guest_name)),
        cand2
    ).otherwise(base3_clean)

    return when(_is_blank(guest_id_clean), generated).otherwise(guest_id_clean)

def _norm_phone_id_logic(c):
    s = regexp_replace(_nz(c).cast("string"), r"[^0-9+]", "")
    s = regexp_replace(s, r"(?<!^)\+", "")
    s = when(_is_blank(s), lit(None).cast("string")).otherwise(s)
    s = when((s.isNotNull()) & s.rlike(r"^62[0-9]+$"), concat_ws("", lit("+"), s)).otherwise(s)
    return s

def run(spark: SparkSession, kafka_bootstrap: str, source_topic: str, sink_topic: str, checkpoint: str):
    print(f"[reservasi] {source_topic} -> {sink_topic}")
    payload = _payload()
    msg = _message(payload)

    df_raw = (spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", source_topic)
        .option("startingOffsets", "earliest")
        .option("maxOffsetsPerTrigger", "1000")
        .load())

    df = (df_raw
        .select(from_json(col("value").cast("string"), msg).alias("data"))
        .select("data.after.*", "data.op")
        .filter(col("op").isin("c", "u"))
        .drop("op"))
    
    for c in ["arrival_date", "depart_date"]:
        if c in df.columns:
            df = df.withColumn(c, _fmt_no_t_no_tz(_parse_to_ts_local(col(c))))
    
    if "created_at" in df.columns:
        df = df.withColumn(
            "created_at",
            when(_is_blank(col("created_at")), lit(None).cast(StringType()))
            .otherwise(_fmt_no_t_no_tz(_parse_to_ts_local(col("created_at"))))
        )

    if "deleted_at" in df.columns:
        df = df.withColumn(
            "deleted_at",
            when(_is_blank(col("deleted_at")), lit(None).cast(StringType()))
            .otherwise(_fmt_no_t_no_tz(_parse_to_ts_local(col("deleted_at"))))
        )

    df = df.drop("op")

    if "check_in_time" in df.columns:
        df = df.withColumn("check_in_time", _norm_time_hhmm(col("check_in_time")))
    if "check_out_time" in df.columns:
        df = df.withColumn("check_out_time", _norm_time_hhmm(col("check_out_time")))

    guest_name_expr = upper(trim(concat_ws(" ", _nz(col("first_name")), _nz(col("last_name")))))
    df = df.withColumn(
        "guest_name",
        when(_is_blank(guest_name_expr), lit(None).cast("string")).otherwise(guest_name_expr)
    )

    if "room_number" in df.columns:
        df = df.withColumn("room_number", trim(col("room_number")))
    if "room_type" in df.columns:
        df = df.withColumn("room_type", upper(trim(col("room_type"))))
    if "segment" in df.columns:
        df = df.withColumn("segment", upper(trim(col("segment"))))
    if "email" in df.columns:
        email_clean = lower(trim(_nz(col("email"))))
        df = df.withColumn("email", when(_is_blank(email_clean), lit(None).cast("string")).otherwise(email_clean))
    if "mobile_phone" in df.columns:
        df = df.withColumn("mobile_phone", _norm_phone_id_logic(col("mobile_phone")))

    for c in ["room_rate", "lodging", "breakfast", "lunch", "dinner", "other_charges"]:
        if c in df.columns:
            df = df.withColumn(c, _norm_currency_decimal(col(c)))

    for c in ["guest_id", "bill_number"]:
        if c in df.columns:
            df = df.withColumn(c, _strip_dot_zero(col(c)))

    for c in ["age", "adult_count", "child_count", "nights"]:
        if c in df.columns:
            df = df.withColumn(c, when(col(c).cast("int").isNotNull(), col(c).cast("int")).otherwise(lit(0)))

    if "remarks" in df.columns:
        df = df.withColumn(
            "remarks",
            when(
                _nz(col("remarks")).rlike(r"(?i)^(nan|none|null|na|n/?a)$") |
                _nz(col("remarks")).rlike(r"^[\W_]+$"),
                lit("")
            ).otherwise(trim(col("remarks")))
        )

    df = df.withColumn("guest_id", _guest_id_fallback(df))

    out = df.select(to_json(struct([col(c) for c in df.columns])).alias("value"))

    q = (out.writeStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("topic", sink_topic)
        .option("checkpointLocation", checkpoint)
        .start())
    return q
