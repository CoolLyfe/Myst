#!/bin/bash

# --- Myst Uninstaller ---

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Myst Game Uninstaller ===${NC}"

# 1. Remove Virtual Environment
if [ -d ".venv" ]; then
    echo -e "${BLUE}Removing virtual environment (.venv)...${NC}"
    rm -rf .venv
    echo -e "${GREEN}Virtual environment removed.${NC}"
else
    echo -e "Virtual environment not found, skipping."
fi

# 2. Remove Launcher
if [ -f "Myst" ]; then
    echo -e "${BLUE}Removing game launcher (Myst)...${NC}"
    rm Myst
    echo -e "${GREEN}Launcher removed.${NC}"
else
    echo -e "Launcher not found, skipping."
fi

# 3. Optional: Remove generated map
if [ -f "game/assets/map/map_game.png" ]; then
    read -p "Do you want to remove the generated map asset? (y/n): " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        rm game/assets/map/map_game.png
        echo -e "${GREEN}Map asset removed.${NC}"
    fi
fi

# 4. Clean up any other temporary files
echo -e "${BLUE}Cleaning up __pycache__ folders...${NC}"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo -e "\n${GREEN}=== Uninstallation Complete ===${NC}"
echo -e "Note: This script did NOT remove system libraries (ffmpeg, sdl2). You can remove them manually if needed."
