#!/bin/bash

# Initialize PostgreSQL schema from storage/schema.sql
# Usage: bash scripts/init_db.sh

set -e
trap 'echo "❌ Schema initialization failed." >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🗄️  Initializing PostgreSQL schema..."
echo ""

# Check if postgres container is running
if ! docker-compose ps | grep -q "autorespond-postgres"; then
  echo "❌ PostgreSQL container not running."
  echo "   Run: docker-compose up -d"
  exit 1
fi

# Wait for PostgreSQL to be ready (max 30 seconds)
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
  if docker-compose exec -T postgres psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ PostgreSQL failed to start after 30 seconds"
    exit 1
  fi
  sleep 1
done

echo ""
echo "📝 Applying schema from storage/schema.sql..."

# Apply schema.sql to the autorespond database
docker-compose exec -T postgres psql -U postgres -d autorespond -f /dev/stdin < "$PROJECT_DIR/storage/schema.sql"

echo ""
echo "✓ Schema applied successfully!"
echo ""

# Verify tables were created
echo "📊 Verifying tables..."
docker-compose exec -T postgres psql -U postgres -d autorespond -c "
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
"

echo ""
echo "✅ PostgreSQL schema initialization complete!"
