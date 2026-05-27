#!/bin/bash

# --- Myst Installer & Launcher Creator ---

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Myst Game Setup ===${NC}"

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install it to continue.${NC}"
    exit 1
fi

echo -e "${GREEN}[1/4] Python 3 detected.${NC}"

# 2. Create Virtual Environment
echo -e "${BLUE}[2/4] Creating virtual environment...${NC}"
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create virtual environment. You might need to install python3-venv.${NC}"
    exit 1
fi

# 3. Install Dependencies
echo -e "${BLUE}[3/4] Installing dependencies (this may take a minute)...${NC}"
source .venv/bin/activate
pip install --upgrade pip
pip install pygame Pillow ffpyplayer pymediainfo
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    exit 1
fi

# 4. Create Launcher Script
echo -e "${BLUE}[4/4] Creating launcher...${NC}"
cat << 'EOF' > myst.sh
#!/bin/bash
# Myst Launcher
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
source .venv/bin/activate
python3 menu.py
EOF

chmod +x myst.sh

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo -e "You can now start the game by running: ${BLUE}./myst.sh${NC}"
