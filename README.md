# Darts Window Cricket Game

A cross-platform darts cricket game that allows to choose 6 consecutive sectors to play, not only 20 to 15. The Bull points adjust accordingly to keep the game balance. Try a game from 6 to 1 with Bull worth 11 points!
Built with Kivy that works on both desktop computers and Android devices.

## Game Rules

This is a cricket darts game that uses customizable sectors and the Bull's eye. The rules are:

1. Players take turns throwing darts at the sectors (configurable range) and Bull
2. To score points in a sector, you must first "open" it by hitting it three times
3. Once a sector is open, you score points when hitting it if your opponent hasn't closed it
4. Points are awarded based on the sector value (Bull = 25 points or highest sector + 5, other sectors = sector value)
5. The game ends when one player has closed all sectors and has equal or more points than their opponent

## Features

- Game history tracking and replay functionality
- Player statistics and performance tracking
- Cross-platform compatibility (Desktop and Android)
- Customizable game settings:
  - Sector range (highest to lowest)
  - Bull points (25 or highest sector + 5)
- Game history features:
  - Replay games with adjustable speed
  - Export/import history files
- Player statistics:
  - Games played and won
  - Average, minimum, and maximum rounds
  - Average, minimum, and maximum MPR
  - Sector hit statistics
  - Performance tracking per sector
- Clean, modern dark theme UI with custom fonts
- Easy-to-use touch interface
- Score tracking with MPR (Marks Per Round) statistics
- Visual indicators for open/closed sectors

## Installation

1. Make sure you have Python 3.7 or higher installed
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

### On Desktop
Simply run:
```bash
python main.py
```

### On Android

1. First, install Buildozer:
```bash
pip install buildozer
```

2. Initialize Buildozer:
```bash
buildozer init
```

3. Build the Android APK:
```bash
buildozer android debug deploy run
```

## How to Play

1. Enter player names and game settings on the data input screen
2. The game starts with Player 1
3. Tap the sector buttons to record hits
4. Use the "Next Player" button to switch between players
5. The game automatically tracks scores and marks sectors as they are opened/closed
6. The game ends when one player has closed all sectors and has the highest score
7. After the game, you can:
   - Start a new game
   - View game history
   - Check player statistics
   - Replay the game

## Game History and Statistics

The game automatically saves your match history and player statistics. You can:
- View detailed game history
- Replay past games with adjustable speed
- Export/import game history files
- View comprehensive player statistics including:
  - Win/loss records
  - Performance metrics (MPR, rounds)
  - Sector-specific statistics
  - Historical performance trends
