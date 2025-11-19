import os, importlib
from typing import List
from pyspark.sql import SparkSession

JOBS = {
    "reservasi": ("transform_reservasi", "run"),
    "profile_guest": ("transform_profile_guest", "run"),
    "chat_whatsapp": ("transform_chat_whatsapp", "run"),
    "transaction_resto": ("transform_transaction_resto", "run"),
}

def getenv(n, d):
    v = os.getenv(n)
    return v if v and v.strip() != "" else d

def parse_jobs_env() -> List[str]:
    raw = getenv("JOB", "all").lower()
    return list(JOBS.keys()) if raw == "all" else [j for j in raw.split(",") if j in JOBS]

def build_spark() -> SparkSession:
    # --- [ INI YANG DIPERBAIKI ] ---
    return (SparkSession.builder
        .appName("KafkaDebeziumTransform")
        .config("spark.kafka.consumer.cache.enabled", "false")
        .config("spark.sql.session.timeZone", "Asia/Jakarta")
        .getOrCreate()
    )

def start_job(spark: SparkSession, job: str):
    mod_name, fn = JOBS[job]
    mod = importlib.import_module(mod_name)
    run = getattr(mod, fn)

    if job == "reservasi":
        return run(
            spark=spark,
            kafka_bootstrap=getenv("KAFKA_BOOTSTRAP_SERVERS","kafka:9092"),
            source_topic=getenv("RESERVASI_SOURCE_TOPIC","postgres_server.public.reservation_raw"),
            sink_topic=getenv("RESERVASI_SINK_TOPIC","reservations_transformed"),
            checkpoint=getenv("RESERVASI_CHECKPOINT","/tmp/spark_checkpoints/reservasi")
        )
    if job == "profile_guest":
        return run(
            spark=spark,
            kafka_bootstrap=getenv("KAFKA_BOOTSTRAP_SERVERS","kafka:9092"),
            source_topic=getenv("PROFILE_SOURCE_TOPIC","postgres_server.public.profile_guest_raw"),
            sink_topic=getenv("PROFILE_SINK_TOPIC","profile_guest_transformed"),
            checkpoint=getenv("PROFILE_CHECKPOINT","/tmp/spark_checkpoints/profile_guest")
        )
    if job == "chat_whatsapp":
        return run(
            spark=spark,
            kafka_bootstrap=getenv("KAFKA_BOOTSTRAP_SERVERS","kafka:9092"),
            source_topic=getenv("CHAT_WHATSAPP_SOURCE_TOPIC","postgres_server.public.chat_whatsapp_raw"),
            sink_topic=getenv("CHAT_WHATSAPP_SINK_TOPIC","chat_whatsapp_transformed"),
            checkpoint=getenv("CHAT_WHATSAPP_CHECKPOINT","/tmp/spark_checkpoints/chat_whatsapp")
        )
    if job == "transaction_resto":
        return run(
            spark=spark,
            kafka_bootstrap=getenv("KAFKA_BOOTSTRAP_SERVERS","kafka:9092"),
            source_topic=getenv("TRANSACTION_RESTO_SOURCE_TOPIC","postgres_server.public.transaction_resto_raw"),
            sink_topic=getenv("TRANSACTION_RESTO_SINK_TOPIC","transaction_resto_transformed"),
            checkpoint=getenv("TRANSACTION_RESTO_CHECKPOINT","/tmp/spark_checkpoints/transaction_resto")
        )
def main():
    jobs = parse_jobs_env()
    print(f"[main] running jobs: {jobs}")
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")
    queries = [start_job(spark, j) for j in jobs]
    for q in queries:
        q.awaitTermination()

if __name__ == "__main__":
    main()
