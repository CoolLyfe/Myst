# 🕯️ Myst

Myst is a multiplayer asynchronous RPG dungeon crawler where players explore procedurally generated rooms, fight dangerous monsters, and face off against powerful bosses.

## 🚀 Quick Start

### For Linux
Run the setup script from the root of the project:
```bash
./setup.sh
```
After installation, start the game with:
```bash
./Myst
```

### For Windows
Run the setup batch file from the root of the project:
```batch
setup.bat
```
After installation, start the game with:
```batch
Myst.bat
```

## 🛠️ Requirements & Dependencies

The game requires **Python 3.10+**.

### Video Support (Optional)
If you want to view the intro videos, the library `ffpyplayer` requires system-level FFmpeg headers. If the setup fails to install it, the game will still run, but videos will be skipped.

**To enable video on Ubuntu/Debian:**
```bash
sudo apt-get install libavfilter-dev libavdevice-dev libavformat-dev libavcodec-dev libswresample-dev libswscale-dev libpostproc-dev libsdl2-dev
```

**To enable video on Arch Linux:**
```bash
sudo pacman -S ffmpeg sdl2 python-ffpyplayer pkgconf
```

---

## 🎮 Game Features

- **Multiplayer:** Play with friends over a local network.
- **Procedural Generation:** Every run features a unique dungeon layout.
- **Three Monster Types:**
  - **Shadow Monster:** High health, slow movement.
  - **Light Monster:** Fast and agile, low health.
  - **Tank Monster:** Massive hitbox and huge HP pool.
- **Loot System:** Collect potions from defeated monsters and find lootable chests.
- **Boss Fights:** Face the legendary boss Αλέξις Μαφφάρτ in his dedicated chamber.
- **Save System:** Keybindings and volume settings are saved automatically.

### 🧹 Uninstallation

To remove the virtual environment and the launcher:

**Linux:** `./uninstall.sh`
**Windows:** `uninstall.bat`

## 📂 Project Structure

- `setup.sh` / `setup.bat`: Automated installer and environment setup.
- `Myst` / `Myst.bat`: (Generated after setup) Main game launcher.
- `uninstall.sh` / `uninstall.bat`: Clean up the project environment.
- `game/`: Contains all source code, assets (sounds, music, images), and game logic.
- `.venv/`: (Generated after setup) Local virtual environment.
- `requirements.txt`: List of Python dependencies.

---

*Enjoy the exploration!*
