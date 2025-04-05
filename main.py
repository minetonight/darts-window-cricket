from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import NumericProperty, StringProperty, ColorProperty, BooleanProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from game_history import GameHistory
import json
import os
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp
import zipfile
from datetime import datetime
from kivy.utils import platform

class PlayerContainer(BoxLayout):
    background_color = ColorProperty([0.18, 0.18, 0.18, 1])  # Default dark gray

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.sectors = {}  # Will be initialized with game settings
        self.marks_this_round = 0  # Total marks made this round
        self.sectors_hit_this_round = set()  # Set of sectors hit in current round
        self.current_round_sector_hits = {}  # Track hits per sector in current round
        self.mpr = 0.0
        self.rounds = 1  # Add rounds counter

    def calculate_mpr(self):
        """Calculate Marks Per Round based on total marks in sectors"""
        if self.rounds == 0:
            return 1.0
        total_marks = sum(self.sectors.values())
        return total_marks / self.rounds

class CricketGame:
    def __init__(self, player1_name, player2_name, highest_sector, lowest_sector, bull_points):
        self.players = [Player(player1_name), Player(player2_name)]
        self.current_player = 0
        self.game_over = False
        self.highest_sector = highest_sector
        self.lowest_sector = lowest_sector
        self.bull_points = bull_points
        
        # Initialize sectors for both players
        for player in self.players:
            player.sectors = {str(i): 0 for i in range(lowest_sector, highest_sector + 1)}
            player.sectors['Bull'] = 0
            player.current_round_sector_hits = {str(i): 0 for i in range(lowest_sector, highest_sector + 1)}
            player.current_round_sector_hits['Bull'] = 0
            
        # Initialize mark history tracking
        self.mark_history = []  # List of rounds
        self.current_round_marks = []  # List of marks in current round
        self.current_round_marks.append([])  # Initialize first round
    
    def switch_player(self):
        # Increment rounds for the leaving player
        self.players[self.current_player].rounds += 1
        
        # Save current round marks to history and start new round
        self.mark_history.append(self.current_round_marks[-1])  # Always store the round, even if empty
        self.current_round_marks.append([])  # Start new round
        
        self.current_player = 1 - self.current_player
        self.players[self.current_player].marks_this_round = 0
        self.players[self.current_player].sectors_hit_this_round.clear()
        # Reset current round sector hits for the new player
        for sector in self.players[self.current_player].current_round_sector_hits:
            self.players[self.current_player].current_round_sector_hits[sector] = 0
        self.players[self.current_player].mpr = self.players[self.current_player].calculate_mpr()
        
    def add_hit(self, sector, hits=1):
        if self.game_over:
            return False

        current = self.players[self.current_player]
        opponent = self.players[1 - self.current_player]
        
        # Check if sector is closed (both players have 3 marks)
        if current.sectors[sector] >= 3 and opponent.sectors[sector] >= 3:
            return False  # Don't count hits on closed sectors
        
        # Check if player has already used 9 marks this round
        if current.marks_this_round >= 9:
            return False
            
        # Check if we've reached the limit of 3 sectors per turn
        if len(current.sectors_hit_this_round) >= 3 and sector not in current.sectors_hit_this_round:
            return False
        
        # Record the mark before making changes
        mark_info = {
            'player': self.current_player,
            'sector': sector,
            'was_scoring': current.sectors[sector] >= 3 and opponent.sectors[sector] < 3,
            'points': self.bull_points if sector == 'Bull' else int(sector) if current.sectors[sector] >= 3 and opponent.sectors[sector] < 3 else 0
        }
        self.current_round_marks[-1].append(mark_info)
        
        # Update hits for the sector
        if current.sectors[sector] < 3:
            current.sectors[sector] += 1
            current.marks_this_round += 1
            current.sectors_hit_this_round.add(sector)
            current.current_round_sector_hits[sector] += 1
        else:
            # Sector is already open (has 3 marks)
            current.marks_this_round += 1
            # Add points if sector is open by current player and not closed by opponent
            if opponent.sectors[sector] < 3:
                points = self.bull_points if sector == 'Bull' else int(sector)
                current.sectors[sector] += 1
                current.score += points
                current.sectors_hit_this_round.add(sector)
                current.current_round_sector_hits[sector] += 1

        # Update MPR after the hit
        current.mpr = current.calculate_mpr()
        return True

    def undo_last_mark(self):
        if not self.current_round_marks or not self.current_round_marks[-1]:
            return False
            
        # Get the last mark
        last_mark = self.current_round_marks[-1].pop()
        current = self.players[last_mark['player']]
        sector = last_mark['sector']
        
        # Undo the mark
        if current.sectors[sector] > 0:
            current.sectors[sector] -= 1
            current.marks_this_round -= 1
            current.current_round_sector_hits[sector] -= 1
            
            # If this was the last hit in this sector for this round, remove from sectors_hit_this_round
            if current.current_round_sector_hits[sector] == 0:
                current.sectors_hit_this_round.discard(sector)
            
            # If this was a scoring hit, remove the points
            if last_mark['was_scoring']:
                current.score -= last_mark['points']
        
        # Update MPR after the undo
        current.mpr = current.calculate_mpr()
        return True

    def undo_last_throw(self):
        """Undo the current player's entire round and restore previous player's round"""
        if not self.mark_history or not self.current_round_marks:
            return False
            
        # Get the previous round from history
        previous_round = self.mark_history.pop()
        
        # Undo all marks in current round
        while self.current_round_marks[-1]:
            self.undo_last_mark()
            
        # Remove the empty current round
        self.current_round_marks.pop()
        
        # Switch back to previous player
        self.current_player = 1 - self.current_player
        
        # Decrement rounds for the current player (since we're going back)
        self.players[self.current_player].rounds -= 1
        
        # Restore previous player's round
        self.current_round_marks.append(previous_round)
        
        # Restore previous player's state
        current = self.players[self.current_player]
        current.marks_this_round = len(previous_round)
        current.sectors_hit_this_round.clear()
        current.current_round_sector_hits = {str(i): 0 for i in range(self.lowest_sector, self.highest_sector + 1)}
        current.current_round_sector_hits['Bull'] = 0
        
        # Restore sector hits from previous round
        for mark in previous_round:
            sector = mark['sector']
            current.current_round_sector_hits[sector] += 1
            current.sectors_hit_this_round.add(sector)
        
        # Update MPR
        current.mpr = current.calculate_mpr()
        return True

    def check_game_over(self):
        for player in self.players:
            # Check if all sectors are closed (3 marks by both players)
            all_closed = all(hits >= 3 for hits in player.sectors.values())
            if all_closed and player.score >= max(p.score for p in self.players):
                self.game_over = True
                return True
        return False
    
    def get_winner_index(self):
        """Get the index of the winner"""
        if not self.game_over:
            raise ValueError("Game is not over")
        
        if self.players[0].score == self.players[1].score:
            p1_closed_sectors = len([hits for hits in self.players[0].sectors.values() if hits >= 3])
            p2_closed_sectors = len([hits for hits in self.players[1].sectors.values() if hits >= 3])
            if p1_closed_sectors > p2_closed_sectors:
                return 0
            elif p1_closed_sectors < p2_closed_sectors:
                return 1
            else:
                raise ValueError("Game is a draw")
            
        elif self.players[0].score > self.players[1].score:
            return 0
        else:
            return 1
    
class SectorButton(Button):
    sector_state = StringProperty('normal')  # 'normal', 'opponent_open', 'player_open', 'closed'
    BLUE    = [0.2, 0.6, 0.9, 1] # dark blue
    ORANGE  = [0.8, 0.6, 0.0, 1] # dark orange
    GREEN   = [0.2, 0.8, 0.2, 1] # dark green
    GRAY    = [0.3, 0.3, 0.3, 1] # dark gray
    WHITE   = [1, 1, 1, 1] # white

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # Remove default button background
        self.color = SectorButton.BLUE  # Initialize with blue color
        self.font_size = '46sp'
        self.bold = True

    def on_sector_state(self, instance, value):
        self.background_normal = ''  # Remove default button background
        # Update button color based on state (dark theme)
        if value == 'normal':
            self.color = SectorButton.BLUE
        elif value == 'opponent_open':
            self.color = SectorButton.ORANGE
        elif value == 'player_open':
            self.color = SectorButton.GREEN
        else:  # closed
            self.color = SectorButton.GRAY

class SectorIndicator(BoxLayout):
    sector = StringProperty('')
    hits = NumericProperty(0)
    current_round_hits = NumericProperty(0)  # New property for current round hits

    def update_marks(self, hits, current_round_hits=0):
        """Update the visual marks to show the number of hits"""
        self.hits = hits
        self.current_round_hits = current_round_hits
        
        # Get mark widgets
        mark1 = self.ids.get('mark1')
        mark2 = self.ids.get('mark2')
        mark3 = self.ids.get('mark3')
        mark_widgets = [mark1, mark2, mark3]
        
        for i, mark in enumerate(mark_widgets):
            if i < hits:
                mark.text = '✓'  # check mark for hit
                mark.color = (0.2, 0.8, 0.2, 1)  # Bright green for contrast
            else:
                mark.text = '-'  # dash for empty
                mark.color = (0.4, 0.4, 0.4, 1)  # Dark gray

        # Update dots display
        dots = '•' * current_round_hits
        # Add space after every 3 dots
        dots = ' '.join(dots[i:i+3] for i in range(0, len(dots), 3))
        self.ids.dots_label.text = dots

class SelectableItem(RecycleDataViewBehavior, BoxLayout):
    """Base class for selectable items with double tap support"""
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    text = StringProperty('')
    _last_tap_times = {}  # Class-level dictionary to store last tap times

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        self.text = data.get('text', '')
        self.selected = data.get('selected', False)

    def on_touch_down(self, touch):
        """Add selection on touch down and handle double tap"""
        if super(SelectableItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            current_time = Clock.get_time()
            # Check for double tap (within 0.3 seconds)
            if current_time - self._last_tap_times.get(self.text, 0) < 0.3:
                # Get the RecycleView parent
                rv = self.parent.parent
                # Find the parent screen by traversing up the widget tree
                parent = rv
                while parent is not None:
                    if isinstance(parent, self.get_target_screen_class()):
                        self.handle_double_tap(parent)
                        return True
                    parent = parent.parent
            # Update last_tap_time for both single tap and failed double tap
            self._last_tap_times[self.text] = current_time
            rv = self.parent.parent
            parent = rv
            while parent is not None:
                if isinstance(parent, self.get_target_screen_class()):
                    return parent.select_with_touch(self.index, touch)
                parent = parent.parent
        return False

    def get_target_screen_class(self):
        """Return the target screen class for this item type"""
        raise NotImplementedError("Subclasses must implement get_target_screen_class")

    def handle_double_tap(self, screen):
        """Handle double tap action"""
        raise NotImplementedError("Subclasses must implement handle_double_tap")

class HistoryItem(SelectableItem):
    """Item for history list with replay on double tap"""
    def get_target_screen_class(self):
        return HistoryScreen

    def handle_double_tap(self, screen):
        screen.replay_selected_file()

class PlayerStatsItem(SelectableItem):
    """Item for player stats list with details on double tap"""
    def get_target_screen_class(self):
        return PlayerStatsScreen

    def handle_double_tap(self, screen):
        screen.show_player_details()

class MessageScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_data = None
        self.is_message = False
        self.message_title = ''
        self.message_text = ''
        self.on_confirm = None
        self.caller_screen = None

    def scroll_to_top(self):
        """Scroll the message to the top"""
        if hasattr(self, 'ids') and 'history_text' in self.ids:
            self.ids.history_text.parent.scroll_y = 1.0  # 1.0 is top, 0.0 is bottom

    def show_message(self, title, message, on_confirm=None, caller_screen=None):
        """Show a message in the text screen"""
        self.is_message = True
        self.message_title = title
        self.message_text = message
        self.on_confirm = on_confirm
        self.caller_screen = caller_screen
        self.ids.title_label.text = title
        # self.ids.history_text.text = message
        # count message lines and add lines up to 500 lines
        # REASON: the message text screen label is created once and some messages longer than the first message are not fully displayed
        lines = message.split('\n')
        for line in range(0, 500-len(lines)):
            message += '\n' # add empty lines to the message
        self.ids.history_text.text = message
        self.scroll_to_top()

    def on_back(self):
        """Handle back button press"""
        if self.on_confirm:
            # If this was a confirmation dialog, go back without confirming
            self.on_confirm = None
        # Return to the caller screen
        self.manager.current = self.caller_screen

    def on_ok(self):
        """Handle OK button press"""
        if self.on_confirm:
            # If this was a confirmation dialog, call the callback
            self.on_confirm()
            self.on_confirm = None
        # Return to the caller screen
        self.manager.current = self.caller_screen

class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_history = GameHistory()
        self.selected_index = None

    def show_message(self, title, message, callback=None):
        """Show a message in the text screen"""
        text_screen = self.manager.get_screen('message')
        text_screen.show_message(title, message, callback, caller_screen='history')
        self.manager.current = 'message'

    def format_game_data(self, game_data):
        """Format game data into displayable text"""
        try:
            # Validate required fields
            if not isinstance(game_data, dict):
                return "Invalid game data format"
                
            players = game_data.get('players', [])
            if len(players) < 2:
                return "Invalid player data"
                
            settings = game_data.get('settings', {})
            history = game_data.get('history', [])
            
            # Build the history text
            text = []
            
            # Add game info header
            text.append(f"{players[0].get('name', 'Unknown')} vs {players[1].get('name', 'Unknown')}")
            text.append(f"{players[0].get('mpr', 0):.2f} vs {players[1].get('mpr', 0):.2f}")
            
            # Calculate rounds safely
            rounds = int((len(history) + 1) / 2) if history else 0
            text.append(f"Game of {rounds} rounds")
            
            # Add settings info
            text.append(f"Sectors: {settings.get('highest_sector', '?')} to {settings.get('lowest_sector', '?')}")
            text.append(f"Bull Points: {settings.get('bull_points', '?')}")
            text.append("")  # Empty line for spacing
            
            # Add round history
            current_round = 1
            for round_num, round_marks in enumerate(history, 1):
                # Determine which player's turn it is
                player_idx = 0 if round_num % 2 == 1 else 1
                player_name = players[player_idx].get('name', 'Unknown') if player_idx < len(players) else 'Unknown'
                
                text.append(f"Round {current_round} for {player_name}")
                
                if not round_marks:
                    text.append("    --- (No marks)")
                else:
                    line_text = "    "
                    for mark in round_marks:
                        sector = mark.get('sector', '?')
                        points = mark.get('points', 0)
                        scoring = mark.get('was_scoring', False)
                        if scoring:
                            line_text += f"(+{points})"
                        else:
                            line_text += f"{sector}"
                        line_text += ", "
                    # remove the last comma
                    line_text = line_text[:-2]
                    text.append(line_text)
                
                text.append("")  # Empty line between rounds
                
                # Only increment round counter when we've seen both players' turns
                if round_num % 2 == 0:
                    current_round += 1
                
            return "\n".join(text)
            
        except Exception as e:
            return f"Error formatting game data: {str(e)}"

    def list_history_files(self):
        """List all history files in the RecycleView"""
        try:
            files = self.game_history.get_history_files()
            self.ids.history_list.data = [{'text': f, 'selected': False} for f in files]
            # Clear selection when refreshing the list
            self.selected_index = None
        except Exception as e:
            self.show_message('Error', f'Failed to list history files:\n{str(e)}')

    def select_with_touch(self, index, touch):
        """Handle selection of items in the RecycleView"""
        # Deselect all items
        for item in self.ids.history_list.data:
            item['selected'] = False
        
        # Select the touched item
        if index is not None:
            self.ids.history_list.data[index]['selected'] = True
            self.selected_index = index
        
        # Refresh the view
        self.ids.history_list.refresh_from_data()

    def load_selected_file(self):
        """Load the selected game file and show history in a text screen"""
        if self.selected_index is None:
            return
            
        try:
            # Validate that the index is within bounds
            if self.selected_index >= len(self.ids.history_list.data):
                self.selected_index = None
                return
                
            selected_file = self.ids.history_list.data[self.selected_index]['text']
            game_data = self.game_history.load_game(selected_file)
            
            # Format the game data into text
            formatted_text = self.format_game_data(game_data)
            self.show_message('Game History', formatted_text)
            
        except Exception as e:
            self.show_message('Error', f'Failed to load game:\n{str(e)}')

    def replay_selected_file(self):
        """Replay the selected game file"""
        if self.selected_index is None:
            return
            
        try:
            selected_file = self.ids.history_list.data[self.selected_index]['text']
            game_data = self.game_history.load_game(selected_file)
            
            
            # Initialize replay screen
            replay_screen = self.manager.get_screen('replay')
            replay_screen.initialize_replay(game_data)
            self.manager.current = 'replay'
            
        except Exception as e:
            self.show_message('Error', f'Failed to load replay:\n{str(e)}')

    def export_history(self):
        """Export game history to a zip file"""
        zip_path, error = self.game_history.export_history()
        
        if zip_path:
            self.show_message('Success', f'History exported to:\n{zip_path}')
        else:
            self.show_message('Error', f'Failed to export history:\n{error}')

    def import_history(self):
        """Import game history from a zip file"""
        zip_path, error = self.game_history.import_history()
        
        if zip_path:
            # Refresh the history list
            self.list_history_files()
        else:
            self.show_message('Error', f'Failed to import history:\n{error}')

    def delete_game(self):
        """Delete the selected game file"""
        if self.selected_index is None:
            return
            
        try:
            selected_file = self.ids.history_list.data[self.selected_index]['text']
            success, error = self.game_history.delete_game(selected_file)
            
            if success:
                # Refresh the list and show success message
                self.list_history_files()
            else:
                self.show_message('Error', f'Failed to delete game:\n{error}')
                
        except Exception as e:
            self.show_message('Error', f'Failed to delete game:\n{str(e)}')

    def confirm_delete(self):
        """Show confirmation dialog for deleting a game"""
        if self.selected_index is None:
            return
            
        selected_file = self.ids.history_list.data[self.selected_index]['text']
        self.show_message(
            'Confirm Delete',
            f'Are you sure you want to delete:\n{selected_file}\n\nPress OK to delete or Back to cancel.',
            self.delete_game
        )

class ReplayScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.game_history = GameHistory()
        self.replay_event = None
        self.current_round = 0
        self.current_mark = 0
        self.is_replaying = False
        self.is_replay_finished = False
        self.is_paused = False
        self.pause_duration = 1.0  # Default pause duration in seconds
        # Initialize dictionaries for sector buttons and indicators
        self.sector_buttons = {}
        self.p1_indicators = {}
        self.p2_indicators = {}
        # Set initial UI state
        self.ids.player1_container.background_color = [0.18, 0.18, 0.18, 1]
        self.ids.player2_container.background_color = [0.18, 0.18, 0.18, 1]

    def toggle_pause(self):
        """Toggle between pause and resume states"""
        if not self.is_replaying:
            return
            
        if self.is_paused:
            # Resume the replay
            self.is_paused = False
            self.ids.pause_button.text = '⏸️'
            self.ids.step_back_button.disabled = False # TODO: enable when implemented working back button 
            self.ids.step_forward_button.disabled = True
            self.replay_event = Clock.schedule_interval(self.replay_next_mark, self.pause_duration)
        else:
            # Pause the replay
            self.is_paused = True
            self.ids.pause_button.text = '▶️'
            self.ids.step_back_button.disabled = False
            self.ids.step_forward_button.disabled = False
            if self.replay_event:
                self.replay_event.cancel()

    def step_forward(self):
        """Step forward one mark in the replay"""
        if not self.is_paused or not self.is_replaying:
            return
            
        if self.current_round >= len(self.game_history):
            return
            
        current_round = self.game_history[self.current_round]
        
        if self.current_mark >= len(current_round):
            # Move to next round
            self.current_round += 1
            self.current_mark = 0
            if self.current_round < len(self.game_history):
                self.game.switch_player()
                self.ids.progress_label.text = f"Replaying round {self.current_round + 1}/{len(self.game_history)}"
            else:
                self.ids.stop_button.text = '🚪'
                self.is_replay_finished = True
            return
            
        # Replay the current mark
        mark = current_round[self.current_mark]
        self.game.add_hit(mark['sector'])
        self.current_mark += 1
        self.update_display()

    def step_backward(self):
        """Step backward one mark in the replay
        Does not work:
         - does not remove checkmarks from older rounds.
         - I dont see the tick marks disappearing going backwards. 
         - I dont see the marks dots appear all at once and disappear one by one going backwards.
        """
        # if not self.is_paused or not self.is_replaying:
        #     return
            
        # if self.current_round < 0:
        #     return
            
        # current_round = self.game_history[self.current_round]
        
        
        # if self.current_mark <= 0:
        #     # Move to previous round
        #     if self.current_round > 0:
        #         # Get the previous round from history
        #         previous_round = self.game_history[self.current_round - 1]
                
        #         # Undo all marks in current round
        #         while self.game.current_round_marks[-1]:
        #             self.game.undo_last_mark()
                
        #         # Remove the empty current round
        #         self.game.current_round_marks.pop()
                
        #         # Switch back to previous player
        #         self.current_round -= 1
        #         self.game.switch_player()
                
        #         # Decrement rounds for the current player (since we're going back)
        #         self.game.players[self.game.current_player].rounds -= 1
                
        #         # Restore previous player's round
        #         self.game.current_round_marks.append(previous_round)
                
        #         # Restore previous player's state
        #         current = self.game.players[self.game.current_player]
        #         current.marks_this_round = len(previous_round)
        #         current.sectors_hit_this_round.clear()
        #         current.current_round_sector_hits = {str(i): 0 for i in range(self.game.lowest_sector, self.game.highest_sector + 1)}
        #         current.current_round_sector_hits['Bull'] = 0
                
        #         # Restore sector hits from previous round
        #         for mark in previous_round:
        #             sector = mark['sector']
        #             current.current_round_sector_hits[sector] += 1
        #             current.sectors_hit_this_round.add(sector)
                
        #         # Update MPR
        #         current.mpr = current.calculate_mpr()
                
        #         # Set current mark to the last mark in previous round
        #         self.current_mark = len(previous_round) - 1
        #         self.ids.progress_label.text = f"Replaying round {self.current_round + 1}/{len(self.game_history)}"
        #     else:
        #         return
        # else:
        #     # Undo the current mark
        #     mark = current_round[self.current_mark]
        #     self.game.undo_last_mark()
        #     self.current_mark -= 1
            
        self.update_display()

    def update_replay_speed(self):
        """Update the pause duration when the speed setting changes"""
        try:
            self.pause_duration = float(self.ids.replay_speed.text)
            # If replay is currently running, restart it with new speed
            if self.is_replaying and self.replay_event and not self.is_paused:
                self.replay_event.cancel()
                self.replay_event = Clock.schedule_interval(self.replay_next_mark, self.pause_duration)
        except ValueError:
            # If conversion fails, keep the previous value
            self.ids.replay_speed.text = str(self.pause_duration)

    def initialize_replay(self, game_data):
        """Initialize a new replay from game data"""
        # Create a new game instance with the same settings
        settings = game_data['settings']
        self.game = CricketGame(
            game_data['players'][0]['name'],
            game_data['players'][1]['name'],
            settings['highest_sector'],
            settings['lowest_sector'],
            settings['bull_points']
        )
        
        # Store the history for replay
        self.game_history = game_data['history']
        
        # Initialize the UI
        self.create_sector_buttons()
        self.update_display()
        
        # Reset replay state
        self.is_replay_finished = False
        self.is_paused = False
        self.ids.stop_button.text = '⏹️'
        self.ids.pause_button.text = '⏸️'
        self.ids.step_back_button.disabled = True
        self.ids.step_forward_button.disabled = True
        self.ids.replay_speed.text = str(self.pause_duration)
        
        # Start the replay
        self.start_replay()

    def start_replay(self):
        """Start the replay animation"""
        self.is_replaying = True
        self.current_round = 0
        self.current_mark = 0
        self.replay_event = Clock.schedule_interval(self.replay_next_mark, self.pause_duration)
        self.ids.progress_label.text = f"Replaying round {self.current_round + 1}/{len(self.game_history)}"

    def stop_replay(self):
        """Stop the replay animation and clock"""
        if self.replay_event:
            self.replay_event.cancel()
        self.is_replaying = False
        self.manager.current = 'history'
        

    def replay_next_mark(self, dt):
        """Replay the next mark in the sequence"""
        if not self.is_replaying or self.current_round >= len(self.game_history):
            #keep the replay screen on and dont call stop_replay()
            self.ids.stop_button.text = '⬆️'
            self.is_replay_finished = True
            return

        current_round = self.game_history[self.current_round]
        
        if self.current_mark >= len(current_round):
            # Move to next round
            self.current_round += 1
            self.current_mark = 0
            if self.current_round < len(self.game_history):
                self.game.switch_player()
                self.ids.progress_label.text = f"Replaying round {self.current_round + 1}/{len(self.game_history)}"
            else:
                #keep the replay screen on and dont call stop_replay()
                self.ids.stop_button.text = '⬆️'
                self.is_replay_finished = True
            return

        # Replay the current mark
        mark = current_round[self.current_mark]
        self.game.add_hit(mark['sector'])
        self.current_mark += 1
        self.update_display()

    def create_sector_buttons(self):
        # Clear existing sector buttons
        game_grid = self.ids.game_grid
        game_grid.clear_widgets()
        
        # Clear old button and indicator references
        self.sector_buttons.clear()
        self.p1_indicators.clear()
        self.p2_indicators.clear()
        
        # Add sector buttons in reverse order (highest to lowest)
        for sector in range(self.game.highest_sector, self.game.lowest_sector - 1, -1):
            sector_str = str(sector)
            
            # Create indicator for player 1
            p1_indicator = SectorIndicator(sector=sector_str)
            p1_indicator.id = f'p1_sector_{sector_str}'
            self.p1_indicators[sector_str] = p1_indicator
            
            # Create sector button (disabled during replay)
            btn = SectorButton(text=sector_str)
            btn.id = f'btn_sector_{sector_str}'
            btn.disabled = True
            self.sector_buttons[sector_str] = btn
            
            # Create indicator for player 2
            p2_indicator = SectorIndicator(sector=sector_str)
            p2_indicator.id = f'p2_sector_{sector_str}'
            self.p2_indicators[sector_str] = p2_indicator
            
            # Add widgets to grid
            game_grid.add_widget(p1_indicator)
            game_grid.add_widget(btn)
            game_grid.add_widget(p2_indicator)
        
        # Add Bull row
        # Create Bull indicators
        p1_bull = SectorIndicator(sector='Bull')
        p1_bull.id = 'p1_sector_bull'
        self.p1_indicators['Bull'] = p1_bull
        
        # Create Bull button (disabled during replay)
        bull_btn = SectorButton(text=f'Bull [{self.game.bull_points}]')
        bull_btn.font_size = '28sp'
        bull_btn.id = 'btn_sector_bull'
        bull_btn.disabled = True
        self.sector_buttons['Bull'] = bull_btn
        
        # Create Bull indicator for player 2
        p2_bull = SectorIndicator(sector='Bull')
        p2_bull.id = 'p2_sector_bull'
        self.p2_indicators['Bull'] = p2_bull
        
        # Add Bull widgets to grid
        game_grid.add_widget(p1_bull)
        game_grid.add_widget(bull_btn)
        game_grid.add_widget(p2_bull)

    def update_display(self):
        if not self.game:
            return

        # Update player names and scores
        self.ids.player1_name.text = self.game.players[0].name
        self.ids.player2_name.text = self.game.players[1].name
        self.ids.player1_score.text = str(self.game.players[0].score)
        self.ids.player2_score.text = str(self.game.players[1].score)
        self.ids.player1_mpr.text = f"MPR: {self.game.players[0].mpr:.2f}"
        self.ids.player2_mpr.text = f"MPR: {self.game.players[1].mpr:.2f}"
       
        # Update rounds display
        self.ids.rounds.text = f"R: {self.game.players[1].rounds}"
        
        # Calculate and update differences
        p1_score = self.game.players[0].score
        p2_score = self.game.players[1].score
        p1_diff = p1_score - p2_score
        p2_diff = p2_score - p1_score
        
        # Format diffs with brackets and explicit sign
        self.ids.player1_diff.text = f"({'+' if p1_diff > 0 else '-' if p1_diff == 0 else ''}{p1_diff})"
        self.ids.player2_diff.text = f"({'+' if p2_diff > 0 else '-' if p2_diff == 0 else ''}{p2_diff})"
        
        # Update player backgrounds based on current player (dark theme)
        p1_bg = [0.2, 0.5, 0.2, 1] if self.game.current_player == 0 else [0.18, 0.18, 0.18, 1]
        p2_bg = [0.2, 0.5, 0.2, 1] if self.game.current_player == 1 else [0.18, 0.18, 0.18, 1]
        
        # Update container backgrounds using the property
        self.ids.player1_container.background_color = p1_bg
        self.ids.player2_container.background_color = p2_bg
        
        # Update sector buttons and indicators
        current = self.game.current_player
        opponent = 1 - current
        
        # Create list of all sectors including Bull
        sectors = [str(i) for i in range(self.game.highest_sector, self.game.lowest_sector - 1, -1)]
        sectors.append('Bull')
        
        # Update all sector buttons and indicators in a single iteration
        for sector in sectors:
            if sector not in self.sector_buttons:
                continue
                
            current_hits = self.game.players[current].sectors[sector]
            opponent_hits = self.game.players[opponent].sectors[sector]
            
            # Update button state from current player's perspective
            if current_hits >= 3 and opponent_hits >= 3:
                self.sector_buttons[sector].sector_state = 'closed'  # Sector is closed (both players have 3 marks)
            elif current_hits >= 3 and opponent_hits < 3:
                self.sector_buttons[sector].sector_state = 'player_open'  # Sector is open for current player
            elif opponent_hits >= 3 and current_hits < 3:
                self.sector_buttons[sector].sector_state = 'opponent_open'  # Sector is open for opponent
            else:
                self.sector_buttons[sector].sector_state = 'normal'  # Sector is not open for either player
            
            # Update scoring indicators with current round hits per sector
            p1_current_hits = self.game.players[0].current_round_sector_hits[sector]
            p2_current_hits = self.game.players[1].current_round_sector_hits[sector]
            
            self.p1_indicators[sector].update_marks(self.game.players[0].sectors[sector], p1_current_hits)
            self.p2_indicators[sector].update_marks(self.game.players[1].sectors[sector], p2_current_hits)

class PlayerStatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_history = GameHistory()
        self.selected_index = None
        self.player_stats = {}

    def show_message(self, title, message, callback=None):
        """Show a message in the text screen"""
        text_screen = self.manager.get_screen('message')
        text_screen.show_message(title, message, callback, caller_screen='player_stats')
        self.manager.current = 'message'

    def select_with_touch(self, index, touch):
        """Handle selection of items in the RecycleView"""
        # Deselect all items
        for item in self.ids.player_list.data:
            item['selected'] = False
        
        # Select the touched item
        if index is not None:
            self.ids.player_list.data[index]['selected'] = True
            self.selected_index = index
        
        # Refresh the view
        self.ids.player_list.refresh_from_data()

    def load_player_stats(self):
        """Load and calculate player statistics from game history"""
        try:
            # Get all game files
            files = self.game_history.get_history_files()
            
            # Initialize player stats dictionary
            self.player_stats = {}
            
            # Process each game file
            for file in files:
                game_data = self.game_history.load_game(file)
                if not game_data:
                    continue
                    
                # Process each player in the game
                for player in game_data['players']:
                    name = player['name']
                    if name not in self.player_stats:
                        self.player_stats[name] = {
                            'games_played': 0,
                            'games_won': 0,
                            'total_rounds': 0,
                            'min_rounds': float('inf'),
                            'max_rounds': 0,
                            'total_mpr': 0,
                            'min_mpr': float('inf'),
                            'max_mpr': 0,
                            'sector_hits': {},
                            'sector_games': {},  # Track games played per sector
                            'total_sector_hits': 0
                        }
                    
                    stats = self.player_stats[name]
                    stats['games_played'] += 1
                    
                    # Calculate rounds in this game
                    rounds = int((len(game_data['history']) + 1) / 2)
                    stats['total_rounds'] += rounds
                    stats['min_rounds'] = min(stats['min_rounds'], rounds)
                    stats['max_rounds'] = max(stats['max_rounds'], rounds)
                    
                    # Track MPR
                    mpr = player['mpr']
                    stats['total_mpr'] += mpr
                    stats['min_mpr'] = min(stats['min_mpr'], mpr)
                    stats['max_mpr'] = max(stats['max_mpr'], mpr)
                    
                    # Track sector hits and games played per sector
                    sectors_hit_in_game = set()  # Track unique sectors hit in this game
                    for round_marks in game_data['history']:
                        for mark in round_marks:
                            if mark['player'] == game_data['players'].index(player):
                                sector = mark['sector']
                                if sector not in stats['sector_hits']:
                                    stats['sector_hits'][sector] = 0
                                    stats['sector_games'][sector] = 0
                                stats['sector_hits'][sector] += 1
                                sectors_hit_in_game.add(sector)
                                stats['total_sector_hits'] += 1
                    
                    # Increment games played for each sector hit in this game
                    for sector in sectors_hit_in_game:
                        stats['sector_games'][sector] += 1
                    
                    # Track wins
                    if game_data['winner']['name'] == name:
                        stats['games_won'] += 1
            
            # Calculate averages and format stats for display
            for name, stats in self.player_stats.items():
                if stats['games_played'] > 0:
                    stats['avg_rounds'] = stats['total_rounds'] / stats['games_played']
                    stats['avg_mpr'] = stats['total_mpr'] / stats['games_played']
                    stats['win_rate'] = stats['games_won'] / stats['games_played'] * 100
                    
                    # Calculate average hits per game for each sector
                    stats['sector_avgs'] = {}
                    for sector in stats['sector_hits']:
                        if stats['sector_games'][sector] > 0:
                            stats['sector_avgs'][sector] = stats['sector_hits'][sector] / stats['sector_games'][sector]
                    
                    # Find most and least hit sectors
                    if stats['sector_hits']:
                        stats['most_hit_sector'] = max(stats['sector_hits'].items(), key=lambda x: x[1])[0]
                        stats['least_hit_sector'] = min(stats['sector_hits'].items(), key=lambda x: x[1])[0]
            
            # Update the player list
            self.ids.player_list.data = [
                {'text': name, 'selected': False} for name in self.player_stats.keys()
            ]
            
        except Exception as e:
            self.show_message('Error', f'Failed to load player stats:\n{str(e)}')

    def show_player_details(self):
        """Show detailed statistics for the selected player"""
        if self.selected_index is None:
            return
            
        try:
            selected_name = self.ids.player_list.data[self.selected_index]['text']
            stats = self.player_stats[selected_name]
            
            # Format the details text
            details = []
            details.append(f"Player: {selected_name}")
            details.append(f"Games Played: {stats['games_played']}")
            details.append(f"Games Won: {stats['games_won']}")
            details.append(f"Win Rate: {stats['win_rate']:.1f}%")
            details.append(f"Average Rounds: {stats['avg_rounds']:.1f}")
            details.append(f"Min Rounds: {stats['min_rounds']}")
            details.append(f"Max Rounds: {stats['max_rounds']}")
            details.append(f"Average MPR: {stats['avg_mpr']:.2f}")
            details.append(f"Min MPR: {stats['min_mpr']:.2f}")
            details.append(f"Max MPR: {stats['max_mpr']:.2f}")
            
            # Add sector statistics
            details.append("\nSector Statistics:")
            for sector in sorted(stats['sector_hits'].keys()):
                hits = stats['sector_hits'][sector]
                games = stats['sector_games'][sector]
                avg = stats['sector_avgs'][sector]
                details.append(f"{sector if sector != 'Bull' else 'Bull'}: {avg:.2f} hit/game) ({hits} hits in {games} games)")
            
            # Show details in message screen
            text_screen = self.manager.get_screen('message')
            text_screen.show_message(f"{selected_name}'s Statistics", "\n".join(details), caller_screen='player_stats')
            self.manager.current = 'message'
            
        except Exception as e:
            self.show_message('Error', f'Failed to show player details:\n{str(e)}')

class DataInputScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bull_points = 25  # Default value
        self.game_history = GameHistory()
        self.load_latest_players()

    def load_latest_players(self):
        """Load the latest player names from history"""
        player1_name, player2_name = self.game_history.get_latest_players()
        if player1_name and player2_name:
            self.ids.player1_name.text = player1_name
            self.ids.player2_name.text = player2_name
            self.validate_names()  # Update start button state

    def is_valid_sector_range(self, highest, lowest):
        """Check if the sectors from highest to lowest not are adjacent on the dart board
        Heuristically we know that the sectors from 16 to 10 contain adjacent sectors"""
        
        return not (9 < highest < 17)

    def update_lowest_sector(self):
        highest = int(self.ids.highest_sector.text)
        lowest = highest - 5
        self.ids.lowest_sector.text = str(lowest)
        
        # Validate sector range using adjacency check
        if not self.is_valid_sector_range(highest, lowest):
            self.ids.sector_warning.text = "Warning: Adjacent sectors on the board: 6, 10, 8, 11, 14"
        else:
            self.ids.sector_warning.text = ""
            
        self.update_bull_points()

    def update_bull_points(self):
        if self.ids.bull_highest_plus_5.state == 'down':
            highest = int(self.ids.highest_sector.text)
            self.bull_points = highest + 5
        else:
            self.bull_points = 25

    def navigate_next(self, current_id):
        # Handle navigation between inputs
        if current_id == 'player1_name':
            self.ids.player2_name.focus = True
            self.ids.player2_name.cursor = (0, 0)  # Move cursor to start
        elif current_id == 'player2_name':
            self.ids.highest_sector.focus = True
            self.ids.highest_sector.is_open = True  # Open the spinner dropdown

    def switch_positions(self):
        # Get current values
        player1_text = self.ids.player1_name.text
        player2_text = self.ids.player2_name.text
        
        # Swap the values
        self.ids.player1_name.text = player2_text
        self.ids.player2_name.text = player1_text

    def validate_names(self):
        # Get player names and strip whitespace
        player1_name = self.ids.player1_name.text.strip()
        player2_name = self.ids.player2_name.text.strip()
        
        # Check if names are empty or only whitespace
        is_valid = bool(player1_name and player2_name)
        self.ids.start_game_button.disabled = not is_valid
        return is_valid

    def start_game(self):
            
        # Get player names
        player1_name = self.ids.player1_name.text.strip()
        player2_name = self.ids.player2_name.text.strip()
        
        # Get game settings
        highest_sector = int(self.ids.highest_sector.text)
        lowest_sector = int(self.ids.lowest_sector.text)
        
        # Create game instance with settings
        game = CricketGame(player1_name, player2_name, highest_sector, lowest_sector, self.bull_points)
        
        # Switch to game screen and initialize it
        game_screen = self.manager.get_screen('game')
        game_screen.initialize_game(game)
        self.manager.current = 'game'

    def show_history(self):
        """Show the history screen"""

        # refresh the history list every time the history screen is shown
        historyScreen = self.manager.get_screen('history')
        historyScreen.list_history_files()
        self.manager.current = 'history'

    def show_player_stats(self):
        """Show the player statistics screen"""
        # Initialize and show player stats screen
        stats_screen = self.manager.get_screen('player_stats')
        stats_screen.load_player_stats()
        self.manager.current = 'player_stats'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.game_history = GameHistory()
        # Initialize dictionaries for sector buttons and indicators
        self.sector_buttons = {}
        self.p1_indicators = {}
        self.p2_indicators = {}
        # Set initial UI state
        self.ids.player1_container.background_color = [0.18, 0.18, 0.18, 1]
        self.ids.player2_container.background_color = [0.18, 0.18, 0.18, 1]
        self.ids.next_player_btn.text = 'Next Player'

    def initialize_game(self, game):
        """Initialize a new game"""
        self.game = game
        self.create_sector_buttons()
        self.update_display()

    def create_sector_buttons(self):
        # Clear existing sector buttons
        game_grid = self.ids.game_grid
        game_grid.clear_widgets()
        
        # Clear old button and indicator references
        self.sector_buttons.clear()
        self.p1_indicators.clear()
        self.p2_indicators.clear()
        
        # Add sector buttons in reverse order (highest to lowest)
        for sector in range(self.game.highest_sector, self.game.lowest_sector - 1, -1):
            sector_str = str(sector)
            
            # Create indicator for player 1
            p1_indicator = SectorIndicator(sector=sector_str)
            p1_indicator.id = f'p1_sector_{sector_str}'
            self.p1_indicators[sector_str] = p1_indicator
            
            # Create sector button
            btn = SectorButton(text=sector_str)
            btn.id = f'btn_sector_{sector_str}'
            btn.bind(on_release=lambda x, s=sector_str: self.on_sector_press(s))
            self.sector_buttons[sector_str] = btn
            
            # Create indicator for player 2
            p2_indicator = SectorIndicator(sector=sector_str)
            p2_indicator.id = f'p2_sector_{sector_str}'
            self.p2_indicators[sector_str] = p2_indicator
            
            # Add widgets to grid
            game_grid.add_widget(p1_indicator)
            game_grid.add_widget(btn)
            game_grid.add_widget(p2_indicator)
        
        # Add Bull row
        # Create Bull indicators
        p1_bull = SectorIndicator(sector='Bull')
        p1_bull.id = 'p1_sector_bull'
        self.p1_indicators['Bull'] = p1_bull
        
        # Create Bull button
        bull_btn = SectorButton(text=f'Bull [{self.game.bull_points}]')
        bull_btn.font_size = '28sp'
        bull_btn.id = 'btn_sector_bull'
        bull_btn.bind(on_release=lambda x: self.on_sector_press('Bull'))
        self.sector_buttons['Bull'] = bull_btn
        
        # Create Bull indicator for player 2
        p2_bull = SectorIndicator(sector='Bull')
        p2_bull.id = 'p2_sector_bull'
        self.p2_indicators['Bull'] = p2_bull
        
        # Add Bull widgets to grid
        game_grid.add_widget(p1_bull)
        game_grid.add_widget(bull_btn)
        game_grid.add_widget(p2_bull)

    def on_sector_press(self, sector):
        if not self.game:
            return
            
        current_player = self.game.players[self.game.current_player]
        if current_player.marks_this_round >= 9:
            return
            
        if self.game.add_hit(sector):
            self.update_display()

    def next_player(self, *args):
        if not self.game:
            return
            
        if self.game.game_over:
            # Return to data input screen
            self.ids.next_player_btn.text = "Next Player" # reset button text
            self.ids.file_messages_label.text = ""
            self.manager.current = 'data_input'
            return
        else:    
            # Check for game over after switching players
            self.game.switch_player()
            self.update_display()
            
            self.game.check_game_over()

            if self.game.game_over:
                winner = self.game.players[self.game.get_winner_index()]
                # Set winner container to gold, loser to brown
                winner_idx = 0 if winner == self.game.players[0] else 1
                self.ids.player1_container.background_color = [0.8, 0.7, 0.2, 1] if winner_idx == 0 else [0.6, 0.4, 0.2, 1]
                self.ids.player2_container.background_color = [0.8, 0.7, 0.2, 1] if winner_idx == 1 else [0.6, 0.4, 0.2, 1]
                # Update next player button text
                self.ids.next_player_btn.text = f"{winner.name} wins!\nNew Game?"
                self.ids.undo_mark_btn.disabled = True
                self.ids.undo_throw_btn.disabled = True

                 # Save game history
                filepath, error = self.game_history.save_game(self.game)
                if filepath:
                    self.ids.file_messages_label.color = [0, 1, 0, 1] # green
                    # make it two lines so it is readable on android
                    two_line_path = '\n'.join(filepath[i:i+len(filepath)//2] for i in range(0, len(filepath), len(filepath)//2)) 
                    self.ids.file_messages_label.text = f"Game saved to:{two_line_path}"
                else:
                    self.ids.file_messages_label.color = [1, 0, 0, 1]
                    self.ids.file_messages_label.text = f"Error saving game:\n{error}"
                return  

    def update_undo_button_states(self):
        """Update the enabled/disabled state of undo buttons based on game state"""
        if not self.game:
            self.ids.undo_mark_btn.disabled = True
            self.ids.undo_throw_btn.disabled = True
            return

        # Enable/disable Undo a Hit button based on current round marks
        has_current_marks = bool(self.game.current_round_marks and self.game.current_round_marks[-1])
        self.ids.undo_mark_btn.disabled = not has_current_marks

        # Enable/disable Undo Prev Throw button based on history
        has_previous_rounds = bool(self.game.mark_history)
        self.ids.undo_throw_btn.disabled = not has_previous_rounds

    def update_display(self):
        if not self.game:
            return

        # Update player names and scores
        self.ids.player1_name.text = self.game.players[0].name
        self.ids.player2_name.text = self.game.players[1].name
        self.ids.player1_score.text = str(self.game.players[0].score)
        self.ids.player2_score.text = str(self.game.players[1].score)
        self.ids.player1_mpr.text = f"MPR: {self.game.players[0].mpr:.2f}"
        self.ids.player2_mpr.text = f"MPR: {self.game.players[1].mpr:.2f}"
       
        # Update rounds display
        self.ids.rounds.text = f"R: {self.game.players[1].rounds}"
        
        # Calculate and update differences
        p1_score = self.game.players[0].score
        p2_score = self.game.players[1].score
        p1_diff = p1_score - p2_score
        p2_diff = p2_score - p1_score
        
        # Format diffs with brackets and explicit sign
        self.ids.player1_diff.text = f"({'+' if p1_diff > 0 else '-' if p1_diff == 0 else ''}{p1_diff})"
        self.ids.player2_diff.text = f"({'+' if p2_diff > 0 else '-' if p2_diff == 0 else ''}{p2_diff})"
        # set the text color to orange if the diff is negative, and white otherwise 
        self.ids.player1_diff.color = SectorButton.ORANGE if p1_diff < 0 else SectorButton.WHITE
        self.ids.player2_diff.color = SectorButton.ORANGE if p2_diff < 0 else SectorButton.WHITE


        # Update player backgrounds based on current player (dark theme)
        p1_bg = [0.2, 0.5, 0.2, 1] if self.game.current_player == 0 else [0.18, 0.18, 0.18, 1]
        p2_bg = [0.2, 0.5, 0.2, 1] if self.game.current_player == 1 else [0.18, 0.18, 0.18, 1]
        
        # Update container backgrounds using the property
        self.ids.player1_container.background_color = p1_bg
        self.ids.player2_container.background_color = p2_bg
        
        # Update sector buttons and indicators
        current = self.game.current_player
        opponent = 1 - current
        
        # Create list of all sectors including Bull
        sectors = [str(i) for i in range(self.game.highest_sector, self.game.lowest_sector - 1, -1)]
        sectors.append('Bull')
        
        # Update all sector buttons and indicators in a single iteration
        for sector in sectors:
            if sector not in self.sector_buttons:
                continue
                
            current_hits = self.game.players[current].sectors[sector]
            opponent_hits = self.game.players[opponent].sectors[sector]
            
            # Update button state from current player's perspective
            if current_hits >= 3 and opponent_hits >= 3:
                self.sector_buttons[sector].sector_state = 'closed'  # Sector is closed (both players have 3 marks)
            elif current_hits >= 3 and opponent_hits < 3:
                self.sector_buttons[sector].sector_state = 'player_open'  # Sector is open for current player
            elif opponent_hits >= 3 and current_hits < 3:
                self.sector_buttons[sector].sector_state = 'opponent_open'  # Sector is open for opponent
            else:
                self.sector_buttons[sector].sector_state = 'normal'  # Sector is not open for either player
            
            # Update scoring indicators with current round hits per sector
            p1_current_hits = self.game.players[0].current_round_sector_hits[sector]
            p2_current_hits = self.game.players[1].current_round_sector_hits[sector]
            
            self.p1_indicators[sector].update_marks(self.game.players[0].sectors[sector], p1_current_hits)
            self.p2_indicators[sector].update_marks(self.game.players[1].sectors[sector], p2_current_hits)
            
        # Update undo button states
        self.ids.undo_mark_btn.text = f"Undo {self.game.players[self.game.current_player].name}'s marks"
        self.ids.undo_throw_btn.text = f"Undo {self.game.players[1-self.game.current_player].name}'s marks"
        self.update_undo_button_states()

    def undo_last_mark(self, *args):
        """Handle undo last mark button press"""
        if not self.game:
            return
            
        if self.game.undo_last_mark():
            self.update_display()

    def undo_last_throw(self, *args):
        """Handle undo last throw button press"""
        if not self.game:
            return
            
        if self.game.undo_last_throw():
            self.update_display()

    def show_message(self, title, message, callback=None):
        """Show a message in the text screen"""
        text_screen = self.manager.get_screen('message')
        text_screen.show_message(title, message, callback, caller_screen='game')
        self.manager.current = 'message'

    def abort_match(self):
        """Show confirmation dialog for aborting the match"""
        self.show_message(
            'Abort Match',
            'Are you sure you want to abort the current match?\n\nPress OK to abort or Back to cancel.',
            self.confirm_abort
        )

    def confirm_abort(self):
        """Save the aborted game and return to data input screen"""
        if not self.game:
            return

        # Save game with 'aborted' prefix using GameHistory
        filepath, error = self.game_history.save_aborted_game(self.game)
        
        if filepath:
            # Show success message
            self.ids.file_messages_label.color = [0, 1, 0, 1]  # green
            two_line_path = '\n'.join(filepath[i:i+len(filepath)//2] for i in range(0, len(filepath), len(filepath)//2))
            self.ids.file_messages_label.text = f"Aborted game saved to:\n{two_line_path}"
        else:
            # Show error message
            self.ids.file_messages_label.color = [1, 0, 0, 1]  # red
            self.ids.file_messages_label.text = f"Failed to save aborted game: {error}"
        

        # essential to have this here, otherwise the message logic will set the current screen to game screen
        # and then the return_to_data_input will not set it to data_input screen
        Clock.schedule_once(lambda dt: self.return_to_data_input(), 1) # pause 1s to allow the message to be read

    def return_to_data_input(self):
        """Return to data input screen"""
        self.ids.file_messages_label.text = ""
        self.manager.current = 'data_input'


class DartsCricketApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DataInputScreen(name='data_input'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(ReplayScreen(name='replay'))
        sm.add_widget(MessageScreen(name='message'))
        sm.add_widget(PlayerStatsScreen(name='player_stats'))
        return sm

if __name__ == '__main__':
    DartsCricketApp().run() 