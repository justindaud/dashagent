# spark_apps/transform_chat_whatsapp.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, trim, upper, regexp_replace, to_json, struct,
    to_date, date_format, to_timestamp, coalesce, substring
)
from pyspark.sql.functions import from_json
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

def _payload():
    return StructType([
        StructField("id", IntegerType()),
        StructField("csv_upload_id", IntegerType()),
        StructField("phone_number", StringType()),
        StructField("message_type", StringType()),
        StructField("message_date", StringType()),
        StructField("message", StringType()),
        StructField("created_at", StringType()),
        StructField("deleted_at", StringType()),
    ])

def _message(p):
    return StructType([StructField("after", p), StructField("op", StringType())])

_BAD_TOKENS = ["NAN", "NONE", "NULL", "NA", "N A", "N/A", "", "NaN", "nan", "null", "None", "NONE", " "]

def _is_blank_str(c):
    return c.isNull() | (trim(c) == "") | upper(trim(c)).isin(*[t.upper() for t in _BAD_TOKENS])

def _nz(c, default=""):
    return when(_is_blank_str(c), lit(default)).otherwise(c)

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

def _transform(df):
    for c in ["phone_number", "message_type", "message", "message_date", "created_at", "deleted_at"]:
        if c in df.columns:
            df = df.withColumn(c, regexp_replace(col(c).cast("string"), r"\t", ""))
            df = df.withColumn(c, trim(col(c)))

    if "message_type" in df.columns:
        df = df.filter(~_is_blank_str(col("message_type")))
    if "message" in df.columns:
        df = df.filter(~_is_blank_str(col("message")))

    if "phone_number" in df.columns:
        pn = regexp_replace(col("phone_number"), r"[\s\-\(\)]", "")
        df = df.filter(pn.rlike(r"^\+?\d+$"))
        df = df.withColumn(
            "phone_number",
            when((pn.startswith("0")) & (pn != lit("0")), substring(pn, 2, 100)).otherwise(pn)
        )

    if "message_date" in df.columns:
        df = df.withColumn(
            "message_date",
            when(_is_blank_str(col("message_date")), lit(None).cast(StringType()))
            .otherwise(_fmt_no_t_no_tz(_parse_to_ts_local(col("message_date"))))
        )

    if "created_at" in df.columns:
        df = df.withColumn(
            "created_at",
            when(_is_blank_str(col("created_at")), lit(None).cast(StringType()))
            .otherwise(_fmt_no_t_no_tz(_parse_to_ts_local(col("created_at"))))
        )

    if "deleted_at" in df.columns:
        df = df.withColumn(
            "deleted_at",
            when(_is_blank_str(col("deleted_at")), lit(None).cast(StringType()))
            .otherwise(_fmt_no_t_no_tz(_parse_to_ts_local(col("deleted_at"))))
        )

    return df

def run(spark: SparkSession, kafka_bootstrap: str, source_topic: str, sink_topic: str, checkpoint: str):
    print(f"[chat_whatsapp] {source_topic} -> {sink_topic}")
    payload = _payload()
    msg = _message(payload)

    df_raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", source_topic)
        .option("startingOffsets", "earliest")
        .option("maxOffsetsPerTrigger", "1000")
        .load()
    )

    df = (
        df_raw
        .select(from_json(col("value").cast("string"), msg).alias("data"))
        .select("data.after.*", "data.op")
        .filter(col("op").isin("c", "u"))
        .drop("op")
    )

    df = _transform(df)

    out = df.select(to_json(struct([col(c) for c in df.columns])).alias("value"))

    q = (
        out.writeStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("topic", sink_topic)
        .option("checkpointLocation", checkpoint)
        .start()
    )
    return q
