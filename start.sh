#!/bin/bash
# RAG Demo — one-command setup. Only requires Docker.
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${GREEN}▶${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $1"; }
error()   { echo -e "${RED}✗${NC} $1"; exit 1; }

# ── 1. Check Docker ──────────────────────────────────────────────────────────
command -v docker &>/dev/null || error "Docker is required. Install from https://docker.com/get-started"
docker info &>/dev/null       || error "Docker daemon is not running. Start Docker Desktop and try again."

# ── 2. Create .env if missing ────────────────────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env
    warn ".env created from .env.example — fill in your API keys, then re-run ./start.sh"
    echo ""
    echo "  Required:"
    echo "    OPENAI_API_KEY=sk-..."
    echo "    LANGFUSE_PUBLIC_KEY=..."
    echo "    LANGFUSE_SECRET_KEY=..."
    echo ""
    exit 0
fi

# ── 3. Check keys are filled in ──────────────────────────────────────────────
if grep -q 'OPENAI_API_KEY=sk-\.\.\.' .env; then
    error "OPENAI_API_KEY is not set in .env. Please fill it in and re-run ./start.sh"
fi

# ── 4. Build and start (migrations run automatically inside the container) ───
info "Starting services (this builds the image on first run)..."
docker compose up -d --build

# ── 5. Wait for the app to be healthy ────────────────────────────────────────
info "Waiting for app to be ready..."
ATTEMPTS=0
until curl -sf http://localhost:7932/health &>/dev/null; do
    ATTEMPTS=$((ATTEMPTS + 1))
    [ $ATTEMPTS -gt 30 ] && error "App did not start. Run: docker compose logs app"
    sleep 2
done

# ── 6. Download and ingest demo data (once) ──────────────────────────────────
if [ ! -f data/adventures-of-sherlock-holmes.txt ]; then
    info "Downloading demo dataset (Sherlock Holmes, public domain)..."
    curl -sL -o data/a-study-in-scarlet.txt \
        "https://www.gutenberg.org/files/244/244-0.txt"
    curl -sL -o data/adventures-of-sherlock-holmes.txt \
        "https://www.gutenberg.org/files/1661/1661-0.txt"

    info "Ingesting data into the vector DB (~2 min)..."
    docker compose exec app rag-ingest --source-dir data/
else
    info "Demo data already ingested — skipping."
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}✓ Ready!${NC} Open http://localhost:7932"
echo ""
echo "  Stop with:  docker compose down"
echo "  Logs:       docker compose logs -f app"
