import os
import json
from datetime import datetime
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
import zipfile

class GameHistory:
    def __init__(self):
        # Get the appropriate storage directory based on platform
        if platform == 'android':
            from jnius import autoclass
            
            # Get Android's app private storage directory
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            self.base_dir = activity.getFilesDir().getAbsolutePath()
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
            rounds = int((len(game.mark_history) + 1) / 2)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"R{rounds} {game.players[0].name}{{{game.players[0].mpr:.2f}}} vs {game.players[1].name}{{{game.players[1].mpr:.2f}}} on {timestamp}.json"
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

    def request_storage_permissions(self):
        """Request storage permissions on Android"""
        if platform != 'android':
            return True
            
        try:
            from android.permissions import request_permissions, Permission
            from jnius import autoclass
            
            # Get Android version
            Build = autoclass('android.os.Build')
            if Build.VERSION.SDK_INT >= 29:  # Android 10 and above
                # Request MANAGE_EXTERNAL_STORAGE permission
                Environment = autoclass('android.os.Environment')
                if not Environment.isExternalStorageManager():
                    Intent = autoclass('android.content.Intent')
                    Settings = autoclass('android.provider.Settings')
                    activity = autoclass('org.kivy.android.PythonActivity').mActivity
                    intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                    activity.startActivity(intent)
                    return False
                return True
            else:
                # For older Android versions, request read/write permissions
                permissions = [
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ]
                request_permissions(permissions)
                return True
        except Exception as e:
            # Log the error but don't crash
            print(f"Failed to request permissions: {str(e)}")
            return False

    def export_history(self):
        """Export game history to a zip file"""
        try:
            # Request permissions if on Android
            if platform == 'android' and not self.request_storage_permissions():
                return None, "Storage permission denied"

            # Create a temporary directory for the zip file
            if platform == 'android':
                # On Android, use the primary external storage
                from android.storage import primary_external_storage_path
                export_dir = os.path.join(primary_external_storage_path(), 'Download')
            else:
                # On other platforms, use the current directory
                export_dir = os.path.expanduser('~')

            # Create zip filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'window_cricket_history_{timestamp}.zip'
            zip_path = os.path.join(export_dir, zip_filename)

            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all game files
                for f in os.listdir(self.base_dir):
                    if f.endswith('.txt') or f.endswith('.json'):
                        file_path = os.path.join(self.base_dir, f)
                        zipf.write(file_path, f)

            return zip_path, None

        except Exception as e:
            return None, str(e)

    def import_history(self):
        """Import game history from a zip file"""
        try:
            # Request permissions if on Android
            if platform == 'android' and not self.request_storage_permissions():
                return None, "Storage permission denied"

            if platform == 'android':
                # On Android, use the primary external storage
                from android.storage import primary_external_storage_path
                import_dir = os.path.join(primary_external_storage_path(), 'Download')
            else:
                # On other platforms, use the current directory
                import_dir = os.path.expanduser('~')

            # Find the most recent zip file in the directory
            zip_files = [f for f in os.listdir(import_dir) if f.startswith('window_cricket_history_') and f.endswith('.zip')]
            if not zip_files:
                raise Exception(f'No history zip files found in {import_dir}')

            # Sort by modification time, most recent first
            latest_zip = max(zip_files, key=lambda f: os.path.getmtime(os.path.join(import_dir, f)))
            zip_path = os.path.join(import_dir, latest_zip)

            # Extract files to game history directory
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(self.base_dir)

            return zip_path, None

        except Exception as e:
            return None, str(e)

    def get_history_files(self):
        """Get list of history files sorted by modification time"""
        # Get list of files with their modification times
        files = []
        for f in os.listdir(self.base_dir):
            if (f.endswith('.json') or f.endswith('.txt')) and f != 'metadata.json':
                filepath = os.path.join(self.base_dir, f)
                mtime = os.path.getmtime(filepath)
                files.append((f, mtime))
        
        # Sort by modification time, most recent first
        files.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the filenames
        return [f[0] for f in files]

    def load_game(self, filename):
        """Load game data from a file"""
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)

    def delete_game(self, filename):
        """Delete a game file"""
        filepath = os.path.join(self.base_dir, filename)
        try:
            os.remove(filepath)
            return True, None
        except Exception as e:
            return False, str(e)