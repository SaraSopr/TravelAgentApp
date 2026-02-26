#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOBILE_DIR="$ROOT_DIR/mobile-app"

if [[ ! -d "$MOBILE_DIR" ]]; then
  echo "[error] mobile-app directory not found at: $MOBILE_DIR"
  exit 1
fi

if [[ -f "$HOME/.nvm/nvm.sh" ]]; then
  source "$HOME/.nvm/nvm.sh"
  if [[ -f "$MOBILE_DIR/.nvmrc" ]]; then
    nvm use >/dev/null
  fi
fi

npm --prefix "$MOBILE_DIR" run start:stable
