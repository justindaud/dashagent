-- Create Kafka Postgres to Spark Topic --
./scripts/register_debezium.sh
curl -s http://194.233.69.219:8083/connectors/debezium-postgres-source/status | jq

-- Create Kafka Spark to Clickhouse Topic --
./scripts/register_clickhouse.sh
curl -s http://194.233.69.219:8083/connectors/clickhouse-sink/status | jq

-- Checking Kafka Topic --
docker exec -it kafka kafka-topics --bootstrap-server kafka:9092 --list

-- Deleted Kafka Spark to Clickhouse Topic --
curl -s -X DELETE http://194.233.69.219:8083/connectors/clickhouse-sink | jq

-- Deleted Kafka Postgres to Spark Topic --
curl -s -X DELETE http://194.233.69.219:8083/connectors/debezium-postgres-source | jq


-- Create agent_user permission on clickhouse --
CREATE USER agent_user IDENTIFIED WITH plaintext_password BY 'pulangkeuttara';

REVOKE ALL ON *.* FROM agent_user;

GRANT SELECT ON default.datamart_reservations 	 TO agent_user;
GRANT SELECT ON default.datamart_transaction_resto  TO agent_user;
GRANT SELECT ON default.datamart_chat_whatsapp   TO agent_user;
GRANT SELECT ON default.datamart_profile_guest   TO agent_user;