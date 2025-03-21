# Darts Cricket Game

A cross-platform darts cricket game built with Kivy that works on both desktop computers and Android devices.

## Game Rules

This is a cricket darts game that uses sectors 4-9 and the Bull's eye. The rules are:

1. Players take turns throwing darts at the sectors (4-9 and Bull)
2. To score points in a sector, you must first "open" it by hitting it three times
3. Once a sector is open, you score points when hitting it if your opponent hasn't closed it
4. Points are awarded based on the sector value (Bull = 25 points, other sectors = sector value)
5. The game ends when one player has closed all sectors and has equal or more points than their opponent

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

1. The game starts with Player 1
2. Tap the sector buttons (4-9 or Bull) to record hits
3. Use the "Next Player" button to switch between players
4. The game automatically tracks scores and marks sectors as they are opened/closed
5. The game ends when one player has closed all sectors and has the highest score

## Features

- Clean, modern UI
- Easy-to-use touch interface
- Score tracking
- Visual indicators for open/closed sectors
- Cross-platform compatibility 