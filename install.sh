#!/usr/bin/env bash
set -e

REPO="https://github.com/your-username/Scour"
CONFIG_DIR="$HOME/.config/scour"
ENV_FILE="$CONFIG_DIR/.env"

echo ""
echo "  Installing Scour..."
echo ""

# Check Python 3.11+
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3.11+ is required. Install it from https://python.org" >&2
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)" 2>/dev/null)
if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_VERSION" -lt 11 ]; then
    echo "Error: Python 3.11+ is required (found $(python3 --version))" >&2
    exit 1
fi

# Install pipx if missing
if ! command -v pipx &>/dev/null; then
    echo "  Installing pipx..."
    python3 -m pip install --user pipx --quiet
    python3 -m pipx ensurepath --quiet
    export PATH="$PATH:$HOME/.local/bin"
fi

# Install Scour
echo "  Installing scour via pipx..."
pipx install "git+$REPO" --quiet --force

# Create config dir and .env if missing
mkdir -p "$CONFIG_DIR"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<EOF
SERPER_API_KEY=your_serper_api_key_here
TINYFISH_API_KEY=your_tinyfish_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
EOF
    echo ""
    echo "  Created $ENV_FILE"
fi

echo ""
echo "  Scour installed successfully!"
echo ""
echo "  Next: add your API keys to $ENV_FILE"
echo "    - Serper:   https://serper.dev"
echo "    - Tinyfish: https://tinyfish.ai"
echo "    - Gemini:   https://aistudio.google.com"
echo ""
echo "  Then run: scour"
echo ""
