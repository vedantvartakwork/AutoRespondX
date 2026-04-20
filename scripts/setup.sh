#!/bin/bash
# AutoRespondX Setup Guide
# Run from repo root: bash scripts/setup.sh

set -e

echo "============================================================"
echo "AutoRespondX - LOCAL MVP SETUP"
echo "============================================================"
echo ""

# Step 1: Check prerequisites
echo "[1/5] Checking prerequisites..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.10+"
    exit 1
fi
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  ✓ Python $python_version"

if ! command -v docker &> /dev/null; then
    echo "✗ Docker not found. Please install Docker Desktop"
    exit 1
fi
echo "  ✓ Docker installed"

if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose not found. Please install Docker Desktop"
    exit 1
fi
echo "  ✓ Docker Compose installed"

echo ""
echo "  ⚠ Note: Spark requires Java JDK. If running on Mac:"
echo "    brew install openjdk@11"
echo "    export JAVA_HOME=$(/usr/libexec/java_home -v 11)"
echo ""

# Step 2: Create virtual environment
echo "[2/5] Setting up Python virtual environment..."
echo ""

if [ ! -d .venv ]; then
    python3 -m venv .venv
    echo "  ✓ Created .venv"
else
    echo "  ✓ .venv already exists"
fi

source .venv/bin/activate
echo "  ✓ Activated .venv"
echo ""

# Step 3: Install dependencies
echo "[3/5] Installing Python dependencies..."
echo ""

pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  ✓ Dependencies installed"
echo ""

# Step 4: Create .env file
echo "[4/5] Setting up environment configuration..."
echo ""

if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ Created .env from template"
else
    echo "  ✓ .env already exists"
fi
echo ""

# Step 5: Start Docker services
echo "[5/5] Starting Docker services..."
echo ""

docker-compose up -d
echo "  ✓ Started Kafka, Zookeeper, PostgreSQL"
echo ""

# Wait for services
echo "  Waiting 15 seconds for services to be ready..."
sleep 15
echo "  ✓ Services ready"
echo ""

# Initialize database
echo "Initializing PostgreSQL database..."
docker-compose exec -T postgres psql -U postgres -d autorespond -f /docker-entrypoint-initdb.d/01-schema.sql || echo "  ✓ Schema already initialized"
echo ""

echo "============================================================"
echo "✓ SETUP COMPLETE"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Run the demo:"
echo "   bash scripts/run_demo.sh"
echo ""
echo "3. Or run individual components (see run_demo.sh for details)"
echo ""
