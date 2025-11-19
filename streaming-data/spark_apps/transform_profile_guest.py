import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, trim, upper, lower, concat_ws, regexp_replace, to_json, struct,
    to_date, date_format, to_timestamp, coalesce, substring, from_json, expr,
    udf, split, size
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, FloatType, DecimalType,
    ArrayType
)

def _payload_schema():
    return StructType([
        StructField("id", IntegerType()),
        StructField("csv_upload_id", IntegerType()),
        StructField("guest_id", StringType()),
        StructField("name", StringType()),
        StructField("email", StringType()),
        StructField("phone", StringType()),
        StructField("address", StringType()),
        StructField("birth_date", StringType()),
        StructField("occupation", StringType()),
        StructField("city", StringType()),
        StructField("country", StringType()),
        StructField("segment", StringType()),
        StructField("type_id", StringType()),
        StructField("id_no", StringType()),
        StructField("sex", StringType()),
        StructField("zip_code", StringType()),
        StructField("local_region", StringType()),
        StructField("telefax", StringType()),
        StructField("mobile_no", StringType()),
        StructField("comments", StringType()),
        StructField("credit_limit", StringType()),
        StructField("created_at", StringType()),
        StructField("deleted_at", StringType()),
    ])

def _message_schema(p):
    return StructType([StructField("after", p), StructField("op", StringType())])

_BAD_TOKENS = ["NAN", "NONE", "NULL", "NA", "N A", "N/A", "", "NaN", "nan", "null"]

def _nz(c, default=''):
    return when(c.isNull() | (trim(c) == ''), lit(default)).otherwise(c)

def _is_blank(c):
    return c.isNull() | (trim(c) == "") | c.isin(*_BAD_TOKENS)

def _strip_dot_zero(c):
    return regexp_replace(c.cast("string"), r"\.0$", "")

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

_NAME_TITLES_REGEX = r"\b(MR|MRS|MS|MISS|DR|PROF|SIR|MADAM|BPK)\b\.?,?\s*"

def _clean_name(c):
    c_clean = trim(c)
    c_clean = regexp_replace(upper(c_clean), _NAME_TITLES_REGEX, "")
    
    parts = split(c_clean, ",")
    c_swapped = when(size(parts) == 2,
                     trim(concat_ws(" ", trim(parts[1]), trim(parts[0])))) \
                .otherwise(c_clean)
    
    return trim(c_swapped)

def _clean_email(c):
    c_clean = lower(trim(c))
    is_bad_token = upper(c_clean).isin(*_BAD_TOKENS)
    is_only_symbols = c_clean.rlike(r"^[\W_]+$")
    
    return when(is_bad_token | is_only_symbols, lit(None).cast(StringType())) \
           .otherwise(c_clean)

def _clean_text_field(c, use_upper=False):
    c_clean = trim(c)
    if use_upper:
        c_clean = upper(c_clean)
        
    is_bad_token = upper(c_clean).isin(*_BAD_TOKENS)
    is_only_symbols = c_clean.rlike(r"^[\W_]+$")
    
    return when(is_bad_token | is_only_symbols, lit(None).cast(StringType())) \
           .otherwise(c_clean)

def _clean_segment(c):
    c_clean = upper(trim(c))
    return when(c_clean == "COMPL", lit("COMP")).otherwise(c_clean)

def _clean_sex(c):
    c_clean = upper(trim(c))
    return when(c_clean.isin("M", "F", "U"), lit("UNIDENTIFIED")) \
           .otherwise(c_clean)

OCCUPATION_MAPPING = {
'KARYAWAN BUMD': [
    'KARYAWAN BUMD', 'karyawan bumd', 'KARYAWAN bumd', 'karyawan BUMD',
    'BUMD', 'bumd', 'SLEMAN'
],
'KARYAWAN BUMN': [
    'KARYAWAN BUMN', 'karyawan bumn', 'KARYAWAN bumn', 'karyawan BUMN',
    'BUMN', 'bumn', 'KARYWN BUMN', 'karywn bumn', 'KARYWN bumn', 'karywn BUMN',
    'KARY BUMN', 'kary bumn', 'KARY bumn', 'kary BUMN'
],
'HONORER': [
    'HONORER', 'honorer', 'Honorer',
    'KARYAWAN HONORER', 'karyawan honorer', 'KARYAWAN honorer', 'karyawan HONORER'
],
'IBU RUMAH TANGGA': [
    'IBU RUMAH TANGGA', 'ibu rumah tangga', 'IBU rumah tangga', 'ibu RUMAH TANGGA',
    'IRT', 'irt', 'IRT ', 'irt ',
    'MENGURUS RUMAH TANGGA', 'mengurus rumah tangga', 'MENGURUS rumah tangga', 'mengurus RUMAH TANGGA',
    'MRT', 'mrt', 'RUMAH TANGGA', 'rumah tangga', 'RUMAH tangga', 'rumah TANGGA'
],
'PEDAGANG': [
    'PEDAGANG', 'pedagang', 'Pedagang',
    'PERDAGANGAN', 'perdagangan', 'Perdagangan'
],
'PEGAWAI NEGERI SIPIL': [
    'PEG NEGERI', 'peg negeri', 'PEG negeri', 'peg NEGERI',
    'PEGAWAI NEGERI', 'pegawai negeri', 'PEGAWAI negeri', 'pegawai NEGERI',
    'PEGAWAI NEGERI SIPIL', 'pegawai negeri sipil', 'PEGAWAI negeri sipil', 'pegawai NEGERI SIPIL',
    'PEGAWAI NEGRI', 'pegawai negri', 'PEGAWAI negri', 'pegawai NEGRI',
    'PEGAWAI NEGRI SIPIL', 'pegawai negri sipil', 'PEGAWAI negri sipil', 'pegawai NEGRI SIPIL',
    'PNS', 'pns'
],
'KARYAWAN SWASTA': [
    'KAR SWASTA', 'kar swasta', 'KAR swasta', 'kar SWASTA',
    'KARYAWAN SWASTA', 'karyawan swasta', 'KARYAWAN swasta', 'karyawan SWASTA',
    'KARY SWASTA', 'kary swasta', 'KARY swasta', 'kary SWASTA',
    'KARYAWAB SWASTA', 'karyawab swasta', 'KARYAWAB swasta', 'karyawab SWASTA',
    'KARYAWAN SWATA', 'karyawan swata', 'KARYAWAN swata', 'karyawan SWATA',
    'KARYWAN SWASTA', 'karywan swasta', 'KARYWAN swasta', 'karywan SWASTA',
    'PEG. SWASTA', 'peg. swasta', 'PEG. swasta', 'peg. SWASTA',
    'PEGAWAI SWASTA', 'pegawai swasta', 'PEGAWAI swasta', 'pegawai SWASTA',
    'KARYAWAN', 'karyawan', 'KARYAWAN', 'karyawan',
    'KARYAWATI', 'karyawati', 'KARYAWATI', 'karyawati',
    'SWASTA', 'swasta', "Swasta"
],
'TIDAK BEKERJA': [
    'BELM BEKERJA', 'belm bekerja', 'BELM bekerja', 'belm BEKERJA',
    'BELUM BEKERJA', 'belum bekerja', 'BELUM bekerja', 'belum BEKERJA',
    'BELUM TIDAK BEKERJA', 'belum tidak bekerja', 'BELUM tidak bekerja', 'belum TIDAK BEKERJA',
    'BELUM/TIDAK BEKERJA', 'belum/tidak bekerja', 'BELUM/tidak bekerja', 'belum/TIDAK BEKERJA',
    'TDK BEKERJA', 'tdk bekerja', 'TDK bekerja', 'tdk BEKERJA', 'Tdk bekerja',
    'TIDAK BEKERJA', 'tidak bekerja', 'TIDAK bekerja', 'tidak BEKERJA'
],
'WIRASWASTA': [
    'WIRASWASTA', 'wiraswasta', 'WIRASWASTA', 'wiraswasta',
    'WIRASWATA', 'wiraswata', 'WIRASWATA', 'wiraswata'
],
'PELAJAR MAHASISWA': [
    'pelajar', 'Pelajar', 'PELAJAR', 'PELAJAR ',
    'mahasiswa', 'Mahasiswa', 'MAHASISWA',
    'siswa', 'Siswa', 'SISWA',
    'pelajar mahasiswa', 'PELAJAR MAHASISWA',
    'MAHASISWI', 'PELAJAR / MAHASISWA',
    'PELAJAR/ MAHASISWA', 'PELAJAR/MAHASISWA',
    'PELAJAR/MAHASIWA', 'PELAJAR/MHS',
    'PELAJAR/NAHASISWA'
],
'DOSEN': [
    'DOSEN', 'dosen', 'Dosen'
]
}

_OCCUPATION_INVERTED_MAP = {}
for replacement, patterns in OCCUPATION_MAPPING.items():
    for pattern in patterns:
        _OCCUPATION_INVERTED_MAP[pattern.upper()] = replacement

def _clean_occupation_logic(occupation):
    if not occupation:
        return None
        
    occupation_str = str(occupation).strip()
    occupation_upper = occupation_str.upper()
    
    if occupation_upper in _OCCUPATION_INVERTED_MAP:
        return _OCCUPATION_INVERTED_MAP[occupation_upper]
    
    return occupation_str

clean_occupation_udf = udf(_clean_occupation_logic, StringType())

def _generate_guest_id(df):    
    c_name = _nz(col("name"))
    c_final_phone = coalesce(_nz(col("mobile_no")), _nz(col("phone")))
    c_email = _nz(col("email"))
    c_id = col("id").cast("string")
    c_csv_id = col("csv_upload_id").cast("string")

    c_phone_clean = regexp_replace(c_final_phone, r"\+", "")
    cand1_base = concat_ws("_", c_name, c_phone_clean)
    cand1_clean = regexp_replace(cand1_base, r"[ \-]+", "_")
    cand1 = substring(cand1_clean, 1, 50)

    cand2_base = concat_ws("_", c_name, c_email)
    cand2_clean = regexp_replace(cand2_base, r"[ \.@]+", "_")
    cand2 = substring(cand2_clean, 1, 50)
    
    cand3_base = concat_ws("_", c_name, c_id)
    cand3_clean = regexp_replace(cand3_base, r" +", "_")
    cand3 = substring(cand3_clean, 1, 50)
    
    cand4 = concat_ws("_", lit("GUEST"), c_csv_id, c_id)
    cand4 = substring(cand4, 1, 50)

    generated_id = when(~_is_blank(c_name) & ~_is_blank(c_final_phone), cand1) \
                   .when(~_is_blank(c_name) & ~_is_blank(c_email), cand2) \
                   .when(~_is_blank(c_name), cand3) \
                   .otherwise(cand4)
                   
    guest_id_clean_original = _strip_dot_zero(_nz(col("guest_id")))
    
    return when(_is_blank(guest_id_clean_original), generated_id) \
           .otherwise(guest_id_clean_original)

def run(spark: SparkSession, kafka_bootstrap: str, source_topic: str, sink_topic: str, checkpoint: str):
    print(f"[profile_guest] {source_topic} -> {sink_topic}")
    payload = _payload_schema()
    msg = _message_schema(payload)

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
    
    df_cleaned = (df
        .withColumn("name", _clean_name(col("name")))
        .filter(~_is_blank(col("name")))
        
        .withColumn("guest_id", _strip_dot_zero(col("guest_id")))
        
        .withColumn("phone", trim(col("phone")))
        .withColumn("mobile_no", trim(col("mobile_no")))

        .withColumn("phone", 
            when(~_is_blank(col("mobile_no")), col("mobile_no"))
            .otherwise(col("phone"))
        )
        
        .withColumn("email", _clean_email(col("email")))
        
        .withColumn("occupation", clean_occupation_udf(col("occupation")))
        
        .withColumn("city", _clean_text_field(col("city"), use_upper=False))
        
        .withColumn("country", trim(col("country")))
        
        .withColumn("segment", _clean_segment(col("segment")))
        
        .withColumn("type_id", trim(col("type_id")))
        .withColumn("id_no", trim(col("id_no")))
        
        .withColumn("address", _clean_text_field(col("address"), use_upper=True))
        
        .withColumn("telefax", trim(regexp_replace(col("telefax"), r"\D", "")))
        
        .withColumn("sex", _clean_sex(col("sex")))
        
        .withColumn("zip_code", trim(col("zip_code")))
        .withColumn("local_region", trim(col("local_region")))
        .withColumn("comments", trim(col("comments")))
        
        .withColumn("credit_limit", _nz(trim(col("credit_limit")), "0"))
    )

    df_with_gid = df_cleaned.withColumn("guest_id", _generate_guest_id(df_cleaned))

    df_final = df_with_gid
    if "created_at" in df_final.columns:
        df_final = df_final.withColumn(
            "created_at",
            when(_is_blank(col("created_at")), lit(None).cast(StringType()))
            .otherwise(_fmt_no_t_no_tz(_parse_to_ts_local(col("created_at"))))
        )

    if "deleted_at" in df_final.columns:
        df_final = df_final.withColumn(
            "deleted_at",
            when(_is_blank(col("deleted_at")), lit(None).cast(StringType()))
            .otherwise(_fmt_no_t_no_tz(_parse_to_ts_local(col("deleted_at"))))
        )
    out = df_final.select(to_json(struct([col(c) for c in df_final.columns])).alias("value"))

    q = (out.writeStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("topic", sink_topic)
        .option("checkpointLocation", checkpoint)
        .start())
    return q