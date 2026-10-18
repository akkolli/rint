#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .local
PG_BIN="$(brew --prefix postgresql@17)/bin"
if [ ! -f .local/postgres/PG_VERSION ]; then
  "$PG_BIN/initdb" -D .local/postgres --auth=trust --encoding=UTF8 >/dev/null
fi
if ! "$PG_BIN/pg_ctl" -D .local/postgres status >/dev/null 2>&1; then
  "$PG_BIN/pg_ctl" -D .local/postgres -l .local/postgres.log -o '-h 127.0.0.1 -p 55432 -k /private/tmp' start
fi
redis-server --bind 127.0.0.1 --port 56379 --daemonize yes --pidfile "$PWD/.local/redis.pid" --dir "$PWD/.local" --logfile "$PWD/.local/redis.log"
if [ ! -f .local/env ]; then
  .venv/bin/python -c 'import secrets; from pathlib import Path; Path(".local/env").write_text("export APP_SECRET_KEY="+secrets.token_hex(32)+"\nexport UI_URL=http://localhost:5080\nexport DATABASE_URL=postgresql://localhost:55432/rint\nexport DATABASE_TEST_URL=postgresql://localhost:55432/rint_test\nexport REDIS_URL=redis://localhost:56379\nexport APP_SETTINGS=fittrackee.config.DevelopmentConfig\n"); Path(".local/env").chmod(0o600)'
fi
"$PG_BIN/psql" -h 127.0.0.1 -p 55432 postgres -tAc "SELECT 1 FROM pg_database WHERE datname='rint'" | rg -q 1 || "$PG_BIN/createdb" -h 127.0.0.1 -p 55432 rint
"$PG_BIN/psql" -h 127.0.0.1 -p 55432 postgres -tAc "SELECT 1 FROM pg_database WHERE datname='rint_test'" | rg -q 1 || "$PG_BIN/createdb" -h 127.0.0.1 -p 55432 rint_test
"$PG_BIN/psql" -h 127.0.0.1 -p 55432 rint -c 'CREATE EXTENSION IF NOT EXISTS postgis'
"$PG_BIN/psql" -h 127.0.0.1 -p 55432 rint_test -c 'CREATE EXTENSION IF NOT EXISTS postgis'
