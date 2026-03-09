#!/bin/bash
set -euo pipefail

# Only run in Claude Code remote (web) sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> Installing Python dependencies..."

# Install sgmllib3k manually (its build system is broken on this Python/setuptools version)
SGMLLIB_URL="https://files.pythonhosted.org/packages/source/s/sgmllib3k/sgmllib3k-1.0.0.tar.gz"
SITE_PKG=$(python -c "import site; print(site.getsitepackages()[0])")
if ! python -c "import sgmllib" 2>/dev/null; then
  echo "  -> Installing sgmllib3k manually..."
  TMP=$(mktemp -d)
  pip download sgmllib3k -d "$TMP" -q
  tar xzf "$TMP"/sgmllib3k-*.tar.gz -C "$TMP"
  cp "$TMP"/sgmllib3k-*/sgmllib.py "$SITE_PKG"/
  rm -rf "$TMP"
fi

# Install all other dependencies (excluding feedparser first, then add it --no-deps)
pip install -q fastapi==0.115.0 uvicorn==0.30.6 httpx==0.27.2 \
  beautifulsoup4==4.12.3 lxml==5.3.0 python-dateutil==2.9.0 \
  "scikit-learn==1.5.2" "nltk==3.9.1" "aiohttp==3.10.5" "numpy>=1.26.0"

# Install feedparser without its broken sgmllib3k build dependency
pip install -q feedparser==6.0.11 --no-deps

echo "==> Downloading NLTK data..."
python -c "
import nltk
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)
" 2>/dev/null || true

echo "==> Starting US News Radar server on port 8001..."
# Kill any existing instance
fuser -k 8001/tcp 2>/dev/null || true
sleep 1

# Start server in background
cd "$CLAUDE_PROJECT_DIR"
nohup python radar.py > /tmp/radar.log 2>&1 &

# Wait until server is ready (max 15s)
for i in $(seq 1 15); do
  if curl -sf http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "==> Radar server is up at http://localhost:8001"
    exit 0
  fi
  sleep 1
done

echo "WARNING: Radar server did not respond in time. Check /tmp/radar.log"
exit 0
