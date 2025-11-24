set -euo pipefail

CONNECT_URL=${CONNECT_URL:-http://localhost:8083}

echo "Registering ClickHouse sink..."
curl -s -X PUT "$CONNECT_URL/connectors/clickhouse-sink/config" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "clickhouse-sink",
    "connector.class": "com.clickhouse.kafka.connect.ClickHouseSinkConnector",
    "tasks.max": "1",
    "topics": "reservations_transformed,profile_guest_transformed,chat_whatsapp_transformed,transaction_resto_transformed",

    "hostname": "clickhouse-server",
    "port": "8123",
    "database": "default",
    "username": "default",
    "password": "password123",
    "http.scheme": "http",
    "ssl": "false",

    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter.schemas.enable": "false",

    "errors.tolerance": "all",
    "errors.log.enable": "true",
    "errors.log.include.messages": "true",
    "consumer.override.max.poll.records": "1000"
  }' | jq

echo "Done."
