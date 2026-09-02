#!/usr/bin/env bash
set -euo pipefail

echo ""
echo "Google OAuth2 App (Python) - Setup"
echo "===================================="
echo ""

if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is not installed."
  exit 1
fi

PY_VER=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "Python $PY_VER detected."
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
echo ""
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo ""
echo "Installing dependencies..."
pip install --quiet -r requirements.txt

echo ""
echo "Setup complete."
echo ""
echo "Make sure this redirect URI is authorised in your Google OAuth2 client:"
echo ""
echo "  ${BASE_URL}/auth/callback"
echo ""
echo "Then run:"
echo ""
echo "  source .venv/bin/activate"
echo "  python3 server.py"
echo ""
if [[ "$DUMMY_VAL" == "true" ]]; then
  echo "Dummy login: ${BASE_URL}/auth/dummy/list"
  echo ""
fi
