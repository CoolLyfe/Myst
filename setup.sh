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
echo -e "${BLUE}[2/4] Creating virtual environment (this may take a moment)...${NC}"
python3 -m venv --system-site-packages .venv > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create virtual environment.${NC}"
    exit 1
fi

# 3. Install Dependencies
echo -e "${BLUE}[3/4] Installing dependencies...${NC}"
source .venv/bin/activate
python3 -m pip install --upgrade pip --quiet > /dev/null 2>&1

# Use the requirements file in the game folder
python3 -m pip install -r game/requirements.txt --quiet > /dev/null 2>&1

# ffpyplayer check and automated fix
if python3 -c "import ffpyplayer" > /dev/null 2>&1; then
    echo -e "${GREEN}[3/4] Dependencies installed (ffpyplayer ready).${NC}"
else
    echo -e "${BLUE}[3/4] Video support not found. Attempting automated fix...${NC}"
    
    if [ -f /etc/arch-release ]; then
        sudo pacman -S --needed --noconfirm ffmpeg4.4 sdl2 pkgconf > /dev/null 2>&1
        export CPATH="/usr/include/ffmpeg4.4:$CPATH"
        export LIBRARY_PATH="/usr/lib/ffmpeg4.4:$LIBRARY_PATH"
    elif [ -f /etc/debian_version ]; then
        sudo apt-get update > /dev/null 2>&1
        sudo apt-get install -y libavfilter-dev libavdevice-dev libavformat-dev libavcodec-dev libswresample-dev libswscale-dev libpostproc-dev libsdl2-dev > /dev/null 2>&1
    fi

    # Try pip install one last time silently
    if ! python3 -c "import ffpyplayer" > /dev/null 2>&1; then
        python3 -m pip install ffpyplayer --quiet > /dev/null 2>&1
    fi

    # Final validation
    if python3 -c "import ffpyplayer" > /dev/null 2>&1; then
        echo -e "${GREEN}[3/4] Dependencies installed (ffpyplayer ready).${NC}"
    else
        echo -e "${RED}Error: Failed to install mandatory video support (ffpyplayer).${NC}"
        echo -e "Your system environment may be incompatible with this library."
        exit 1
    fi
fi

# 4. Create Launcher Script
echo -e "${BLUE}[4/4] Creating launcher...${NC}"
cat << 'EOF' > Myst
#!/bin/bash
# Myst Launcher
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
source .venv/bin/activate
cd game
python3 menu.py
EOF

chmod +x Myst

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo -e "You can now start the game by running: ${BLUE}./Myst${NC}"
