#!/usr/bin/env bash
set -euo pipefail

echo ""
echo "Google OAuth2 App (TypeScript) - Setup"
echo "======================================="
echo ""

if ! command -v node &>/dev/null; then
  echo "Error: Node.js is not installed. Install it from https://nodejs.org"
  exit 1
fi

NODE_VER=$(node -e "process.stdout.write(process.versions.node)")
echo "Node.js $NODE_VER detected."
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
echo "Installing dependencies..."
npm install

echo ""
echo "Building..."
npm run build

echo ""
echo "Setup complete."
echo ""
echo "Make sure this redirect URI is authorised in your Google OAuth2 client:"
echo ""
echo "  ${BASE_URL}/auth/callback"
echo ""
echo "Then run:"
echo ""
echo "  npm start"
echo ""
if [[ "$DUMMY_VAL" == "true" ]]; then
  echo "Dummy login: ${BASE_URL}/auth/dummy/list"
  echo ""
fi
