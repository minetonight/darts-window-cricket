import os
import json
from datetime import datetime
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore

class GameHistory:
    def __init__(self):
        # Get the appropriate storage directory based on platform
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            from android.storage import primary_external_storage_path
            
            # Request storage permissions
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
            
            # Use Android's external storage for game history
            self.base_dir = os.path.join(primary_external_storage_path(), 'WindowCricket')
        else:
            # For desktop platforms, use a local directory
            self.base_dir = os.path.join(os.path.expanduser('~'), '.window_cricket')
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Initialize JsonStore for metadata
        self.metadata_store = JsonStore(os.path.join(self.base_dir, 'metadata.json'))
        
    def save_game(self, game):
        """Save game history to a file"""
        try:
            # Create filename with player names and date
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{game.players[0].name}_vs_{game.players[1].name}_{timestamp}.txt"
            filepath = os.path.join(self.base_dir, filename)
            
            # Prepare game data for serialization
            game_data = {
                'players': [
                    {'name': game.players[0].name, 'score': game.players[0].score, 'mpr': game.players[0].mpr},
                    {'name': game.players[1].name, 'score': game.players[1].score, 'mpr': game.players[1].mpr}
                ],
                'settings': {
                    'highest_sector': game.highest_sector,
                    'lowest_sector': game.lowest_sector,
                    'bull_points': game.bull_points
                },
                'history': []
            }
            
            # Add each round's marks
            for round_marks in game.mark_history:
                round_data = []
                for mark in round_marks:
                    round_data.append({
                        'player': mark['player'],
                        'sector': mark['sector'],
                        'was_scoring': mark['was_scoring'],
                        'points': mark['points']
                    })
                game_data['history'].append(round_data)
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(game_data, f, indent=2)
            
            # Update metadata with latest game info
            self.metadata_store.put('latest_game', 
                player1_name=game.players[0].name,
                player2_name=game.players[1].name,
                timestamp=timestamp,
                filepath=filepath
            )
            
            return filepath, None
            
        except Exception as e:
            return None, str(e)
    
    def get_latest_players(self):
        """Get the latest player names from history"""
        try:
            if self.metadata_store.exists('latest_game'):
                data = self.metadata_store.get('latest_game')
                return data['player1_name'], data['player2_name']
            return None, None
        except Exception as e:
            return None, None 