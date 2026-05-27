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
echo -e "${BLUE}[2/4] Creating virtual environment (with system site packages)...${NC}"
# We use --system-site-packages so that if you have ffpyplayer installed via pacman,
# the virtual environment can use it instead of trying to compile it.
python3 -m venv --system-site-packages .venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create virtual environment. You might need to install python3-venv.${NC}"
    exit 1
fi

# 3. Install Dependencies
echo -e "${BLUE}[3/4] Installing dependencies (this may take a minute)...${NC}"
source .venv/bin/activate
pip install --upgrade pip

# Use the requirements file in the game folder
pip install -r game/requirements.txt

# ffpyplayer often fails on Linux if FFmpeg headers aren't present.
# We first check if it's already available (e.g. from system site packages)
if python3 -c "import ffpyplayer" &> /dev/null; then
    echo -e "${GREEN}ffpyplayer already available.${NC}"
else
    echo -e "${BLUE}Attempting to install ffpyplayer (for video support)...${NC}"
    # Redundant pip install ffpyplayer is fine since it's already in requirements.txt
    # but we do it here to catch the failure and show the warning.
    if ! pip install ffpyplayer; then
        echo -e "${RED}Warning: Failed to install ffpyplayer.${NC}"
        echo -e "Video support will be disabled, but the game will still run."
        echo -e "To enable video, you must install system FFmpeg headers:"
        
        if [ -f /etc/arch-release ]; then
            echo -e "On Arch Linux, run: ${BLUE}sudo pacman -S ffmpeg sdl2 python-ffpyplayer pkgconf${NC}"
        else
            echo -e "On Ubuntu/Debian, run: ${BLUE}sudo apt-get install libavfilter-dev libavdevice-dev libavformat-dev libavcodec-dev libswresample-dev libswscale-dev libpostproc-dev libsdl2-dev${NC}"
        fi
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
