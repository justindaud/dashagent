set -euo pipefail

CONNECT_URL=${CONNECT_URL:-http://localhost:8083}

echo "Registering Debezium Postgres source..."
curl -s -X PUT "$CONNECT_URL/connectors/debezium-postgres-source/config" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "debezium-postgres-source",
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "plugin.name": "pgoutput",

    "database.hostname": "postgres-source-db",
    "database.port": "5432",
    "database.user": "admin",
    "database.password": "zildiray123",
    "database.dbname": "dash_agent_db",

    "topic.prefix": "postgres_server",

    "publication.name": "dbz_publication",
    "publication.autocreate.mode": "filtered",

    "table.include.list": "public.reservation_raw,public.profile_guest_raw,public.chat_whatsapp_raw,public.transaction_resto_raw",

    "snapshot.mode": "initial",

    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false",
    "max.batch.size": "1000",
    "max.queue.size": "20000",
    "poll.interval.ms": "1000"
    
  }' | jq

echo "Done."
