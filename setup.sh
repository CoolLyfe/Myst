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

# Install base requirements (this might fail for ffpyplayer, which we fix next)
python3 -m pip install -r game/requirements.txt --quiet > /dev/null 2>&1

# Exact "Expert Fix" command sequence
if ! python3 -c "import ffpyplayer" > /dev/null 2>&1; then
    echo -e "${BLUE}[3/4] Video support not found. Applying explicit fix...${NC}"
    
    # 1. Install build-time dependencies in the venv first
    echo -e "${BLUE}Installing build tools (Cython, wheel)...${NC}"
    pip install Cython wheel setuptools --quiet

    if [ -f /etc/arch-release ]; then
        echo -e "${BLUE}Ensuring Arch system dependencies are present...${NC}"
        sudo pacman -S --needed --noconfirm ffmpeg4.4 sdl2 pkgconf libmediainfo > /dev/null 2>&1
        
        # --- THE EXACT COMMANDS & FLAGS ---
        export CPATH="/usr/include/ffmpeg4.4:$CPATH"
        export LIBRARY_PATH="/usr/lib/ffmpeg4.4:$LIBRARY_PATH"
        export LDFLAGS="-L/usr/lib/ffmpeg4.4 $LDFLAGS"
        export PKG_CONFIG_PATH="/usr/lib/ffmpeg4.4/pkgconfig:$PKG_CONFIG_PATH"
        export CFLAGS="-O3 -Wno-error=incompatible-pointer-types"
        
        echo -e "${BLUE}Building ffpyplayer (this will take a moment)...${NC}"
        # --no-build-isolation is critical so pip uses our exported flags and installed Cython
        pip install ffpyplayer --no-build-isolation
        # --------------------------
        
    elif [ -f /etc/debian_version ]; then
        sudo apt-get update > /dev/null 2>&1
        sudo apt-get install -y libavfilter-dev libavdevice-dev libavformat-dev libavcodec-dev libswresample-dev libswscale-dev libpostproc-dev libsdl2-dev > /dev/null 2>&1
        pip install ffpyplayer
    fi

    # Final validation
    if python3 -c "import ffpyplayer" > /dev/null 2>&1; then
        echo -e "${GREEN}[3/4] Dependencies installed (ffpyplayer ready).${NC}"
    else
        echo -e "${RED}Error: Failed to install mandatory video support (ffpyplayer).${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[3/4] Dependencies installed (ffpyplayer ready).${NC}"
fi

# 4. Create Launcher Script
echo -e "${BLUE}[4/4] Creating launcher...${NC}"
cat << 'EOF' > Myst
#!/bin/bash
# Myst Launcher
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Arch specific: force legacy ffmpeg 4.4 at runtime to prevent undefined symbol errors
if [ -d "/usr/lib/ffmpeg4.4" ]; then
    export LD_LIBRARY_PATH="/usr/lib/ffmpeg4.4:$LD_LIBRARY_PATH"
fi

source .venv/bin/activate
cd game
python3 menu.py
EOF

chmod +x Myst

echo -e "${GREEN}=== Setup Complete ===${NC}"
echo -e "You can now start the game by running: ${BLUE}./Myst${NC}"
