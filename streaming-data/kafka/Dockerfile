FROM debezium/connect:2.6
USER root

RUN microdnf install -y unzip curl && \
    microdnf clean all

ENV CLICKHOUSE_CONNECTOR_VERSION=v1.3.1
ENV CLICKHOUSE_CONNECTOR_URL=https://github.com/ClickHouse/clickhouse-kafka-connect/releases/download/${CLICKHOUSE_CONNECTOR_VERSION}/clickhouse-kafka-connect-${CLICKHOUSE_CONNECTOR_VERSION}.zip

RUN curl -L -o /tmp/clickhouse-connector.zip $CLICKHOUSE_CONNECTOR_URL && \
    unzip /tmp/clickhouse-connector.zip -d /kafka/connect/ && \
    rm /tmp/clickhouse-connector.zip

USER kafka