#!/usr/bin/env bash
set -euo pipefail

echo ""
echo "Google OAuth2 App (Python) - Setup"
echo "===================================="
echo ""

# --- Check Python ---
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is not installed."
  exit 1
fi

PY_VER=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "Python $PY_VER detected."
echo ""

# --- Collect credentials ---
echo "You need a Google OAuth2 Client ID and Secret."
echo "Create one at: https://console.cloud.google.com/apis/credentials"
echo ""

read -rp "Google Client ID: " CLIENT_ID
read -rp "Google Client Secret: " CLIENT_SECRET
read -rp "Port [3000]: " PORT
PORT="${PORT:-3000}"
read -rp "Base URL [http://localhost:${PORT}]: " BASE_URL
BASE_URL="${BASE_URL:-http://localhost:${PORT}}"
read -rp "Enable dummy auth for testing? (yes/no) [no]: " DUMMY
DUMMY_VAL="false"
[[ "${DUMMY,,}" == "yes" || "${DUMMY,,}" == "y" ]] && DUMMY_VAL="true"

# --- Write .env ---
cat > .env << EOF
GOOGLE_CLIENT_ID=${CLIENT_ID}
GOOGLE_CLIENT_SECRET=${CLIENT_SECRET}
PORT=${PORT}
HOST=localhost
BASE_URL=${BASE_URL}
ENABLE_DUMMY_AUTH=${DUMMY_VAL}
EOF

echo ""
echo ".env written."

# --- Virtual environment ---
echo ""
echo "Creating virtual environment (.venv)..."
python3 -m venv .venv
echo "    created .venv/"

echo ""
echo "Activating virtual environment..."
source .venv/bin/activate
echo "    activated."

# --- Dependencies ---
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo ""
echo "    Dependencies installed:"
pip list --format=columns | grep -E "fastapi|uvicorn|jinja2|pydantic|google-auth|httpx|oauthlib" | sed 's/^/    /'

# --- Done ---
echo ""
echo "========================================="
echo "  Setup complete."
echo "========================================="
echo ""
echo "Make sure this redirect URI is authorised in your Google OAuth2 client:"
echo ""
echo "    ${BASE_URL}/auth/callback"
echo ""
echo "Then run:"
echo ""
echo "    source .venv/bin/activate"
echo "    uvicorn main:app --host localhost --port ${PORT} --reload"
echo ""
if [[ "$DUMMY_VAL" == "true" ]]; then
  echo "Dummy login available at:"
  echo ""
  echo "    ${BASE_URL}/auth/dummy/list"
  echo ""
fi
