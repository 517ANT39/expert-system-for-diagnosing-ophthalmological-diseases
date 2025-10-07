#!/bin/bash
set -e

# Разбираем переменную NEO4J_AUTH
# Формат: username/password
IFS='/' read -r NEO4J_USER NEO4J_PASSWORD <<< "$NEO4J_AUTH"

# Запускаем Neo4j в фоне
/startup/docker-entrypoint.sh neo4j &
NEO4J_PID=$!

# Ждём, пока Neo4j будет готов к приёму запросов
until cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" 'RETURN 1;' >/dev/null 2>&1; do
  sleep 2
done

cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" -f /init/init.cypher

# Ждём завершения процесса Neo4j
wait $NEO4J_PID
