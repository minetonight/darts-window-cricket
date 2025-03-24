from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, NumericProperty, BooleanProperty, StringProperty
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.sectors = {}  # Will be initialized with game settings
        self.marks_this_round = 0  # Total marks made this round
        self.sectors_marked = 0  # Number of sectors marked this round
        self.mpr = 1.0

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

    def switch_player(self):
        self.current_player = 1 - self.current_player
        self.players[self.current_player].marks_this_round = 0
        self.players[self.current_player].sectors_marked = 0

    def add_hit(self, sector, hits=1):
        if self.game_over:
            return False

        current = self.players[self.current_player]
        
        # Check if player has already used 9 marks this round
        if current.marks_this_round + hits > 9:
            return False
            
        # Check if sector is already marked and if we've reached the limit of 3 sectors
        if current.sectors[sector] == 0 and current.sectors_marked >= 3:
            return False

        opponent = self.players[1 - self.current_player]
        
        # Update hits for the sector
        if current.sectors[sector] < 3:
            old_hits = current.sectors[sector]
            current.sectors[sector] = min(3, current.sectors[sector] + hits)
            actual_hits = current.sectors[sector] - old_hits
            current.marks_this_round += actual_hits
            
            # If this is the first hit on this sector, increment sectors_marked
            if old_hits == 0:
                current.sectors_marked += 1
                
            remaining_hits = hits - actual_hits
        else:
            # Sector is already closed (has 3 marks)
            remaining_hits = hits
            current.marks_this_round += hits  # Count hits on closed sectors towards the 9 marks limit

        # Add points if sector is closed by current player
        if remaining_hits > 0 and current.sectors[sector] >= 3:
            if opponent.sectors[sector] < 3:
                points = remaining_hits * (self.bull_points if sector == 'Bull' else int(sector))
                current.score += points

        # Check if game is over
        self.check_game_over()
        return True

    def check_game_over(self):
        for player in self.players:
            all_closed = all(hits >= 3 for hits in player.sectors.values())
            if all_closed and player.score >= max(p.score for p in self.players):
                self.game_over = True
                return True
        return False

class SectorButton(Button):
    sector_state = StringProperty('normal')  # 'normal', 'opponent_scoring', 'player_scoring', 'closed'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # Remove default button background
        self.background_color = [0.2, 0.6, 0.8, 1]  # Initialize with blue color

    def on_sector_state(self, instance, value):
        # Update button color based on state (dark theme)
        if value == 'normal':
            self.background_color = [0.2, 0.4, 0.6, 1]  # Darker blue
        elif value == 'opponent_scoring':
            self.background_color = [0.6, 0.4, 0.0, 1]  # Darker orange
        elif value == 'player_scoring':
            self.background_color = [0.2, 0.5, 0.2, 1]  # Darker green
        else:  # closed
            self.background_color = [0.3, 0.3, 0.3, 1]  # Dark gray

class SectorIndicator(BoxLayout):
    sector = StringProperty('')
    hits = NumericProperty(0)

    def update_marks(self, hits):
        """Update the visual marks to show the number of hits"""
        self.hits = hits
        mark_widgets = [self.ids.mark1, self.ids.mark2, self.ids.mark3]
        
        for i, mark in enumerate(mark_widgets):
            if i < hits:
                mark.text = 'v'  # Checkmark for hit
                mark.color = (0.2, 0.8, 0.2, 1)  # Bright green for contrast
            else:
                mark.text = '_'  # Underscore for empty
                mark.color = (0.4, 0.4, 0.4, 1)  # Dark gray

class DataInputScreen(Screen):
    def update_lowest_sector(self):
        highest = int(self.ids.highest_sector.text)
        lowest = highest - 5
        self.ids.lowest_sector.text = str(lowest)
        self.update_bull_points()

    def update_bull_points(self):
        if self.ids.bull_highest_plus_5.state == 'down':
            highest = int(self.ids.highest_sector.text)
            self.bull_points = highest + 5
        else:
            self.bull_points = 25

    def switch_positions(self):
        # Get current values
        player1_text = self.ids.player1_name.text
        player2_text = self.ids.player2_name.text
        
        # Swap the values
        self.ids.player1_name.text = player2_text
        self.ids.player2_name.text = player1_text

    def start_game(self):
        # Get player names
        player1_name = self.ids.player1_name.text.strip() or "Player 1"
        player2_name = self.ids.player2_name.text.strip() or "Player 2"
        
        # Get game settings
        highest_sector = int(self.ids.highest_sector.text)
        lowest_sector = int(self.ids.lowest_sector.text)
        
        # Create game instance with settings
        game = CricketGame(player1_name, player2_name, highest_sector, lowest_sector, self.bull_points)
        
        # Switch to game screen and initialize it
        game_screen = self.manager.get_screen('game')
        game_screen.initialize_game(game)
        self.manager.current = 'game'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.setup_ui()

    def initialize_game(self, game):
        self.game = game
        self.create_sector_buttons()
        self.update_display()

    def create_sector_buttons(self):
        # Clear existing sector buttons (except bull)
        game_grid = self.ids.game_grid
        # Keep the bull row (last 3 widgets) in correct order
        bull_widgets = list(reversed(game_grid.children[:3]))  # Reverse to get correct order
        game_grid.clear_widgets()
        
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
        
        # Add bull row back in correct order
        for widget in bull_widgets:
            game_grid.add_widget(widget)
            
        # Store Bull indicators in our dictionaries
        self.p1_indicators['Bull'] = self.ids.p1_sector_bull
        self.p2_indicators['Bull'] = self.ids.p2_sector_bull
        self.sector_buttons['Bull'] = self.ids.btn_sector_bull

    def setup_ui(self):
        # Store references to sector buttons and indicators
        self.sector_buttons = {}
        self.p1_indicators = {}
        self.p2_indicators = {}

    def on_sector_press(self, sector):
        if not self.game:
            return
            
        current_player = self.game.players[self.game.current_player]
        if current_player.marks_this_round >= 9:
            return
            
        if self.game.add_hit(sector):
            self.update_display()
            if self.game.game_over:
                winner = self.game.players[0] if self.game.players[0].score > self.game.players[1].score else self.game.players[1]
                self.ids.player1_name.text = "Game Over!"
                self.ids.player2_name.text = f"{winner.name} wins!"
                self.ids.player1_score.text = str(self.game.players[0].score)
                self.ids.player2_score.text = str(self.game.players[1].score)

    def next_player(self, *args):
        if not self.game or self.game.game_over:
            return
        self.game.switch_player()
        self.update_display()

    def update_display(self):
        if not self.game:
            return

        # Update player names and scores
        self.ids.player1_name.text = self.game.players[0].name
        self.ids.player2_name.text = self.game.players[1].name
        self.ids.player1_score.text = str(self.game.players[0].score)
        self.ids.player2_score.text = str(self.game.players[1].score)
        
        # Calculate and update differences
        p1_score = self.game.players[0].score
        p2_score = self.game.players[1].score
        p1_diff = p1_score - p2_score
        p2_diff = p2_score - p1_score
        
        # Format diffs with brackets and explicit sign
        self.ids.player1_diff.text = f"({'+' if p1_diff > 0 else '-' if p1_diff == 0 else ''}{p1_diff})"
        self.ids.player2_diff.text = f"({'+' if p2_diff > 0 else '-' if p2_diff == 0 else ''}{p2_diff})"

        # Update MPR displays
        self.ids.player1_mpr.text = f"MPR: {self.game.players[0].mpr:.1f}"
        self.ids.player2_mpr.text = f"MPR: {self.game.players[1].mpr:.1f}"
        
        # Update player backgrounds based on current player (dark theme)
        p1_bg = [0.2, 0.5, 0.2, 1] if self.game.current_player == 0 else [0.18, 0.18, 0.18, 1]
        p2_bg = [0.2, 0.5, 0.2, 1] if self.game.current_player == 1 else [0.18, 0.18, 0.18, 1]
        
        # Update container backgrounds
        for container_id, bg in [('player1_container', p1_bg), ('player2_container', p2_bg)]:
            container = self.ids[container_id]
            container.canvas.before.clear()
            with container.canvas.before:
                Color(*bg)
                Rectangle(pos=container.pos, size=container.size)
        
        # Update sector buttons and indicators
        current = self.game.current_player
        opponent = 1 - current
        
        # Update Bull button text with points
        self.ids.btn_sector_bull.text = f'Bull[{self.game.bull_points} pts]'
        
        # Update all sector buttons and indicators
        for sector in range(self.game.highest_sector, self.game.lowest_sector - 1, -1):
            sector_str = str(sector)
            if sector_str not in self.sector_buttons:
                continue
                
            current_hits = self.game.players[current].sectors[sector_str]
            opponent_hits = self.game.players[opponent].sectors[sector_str]
            
            # Update button state from current player's perspective
            if current_hits >= 3 and opponent_hits >= 3:
                self.sector_buttons[sector_str].sector_state = 'closed'
            elif current_hits >= 3 and opponent_hits < 3:
                self.sector_buttons[sector_str].sector_state = 'player_scoring'
            elif opponent_hits >= 3 and current_hits < 3:
                self.sector_buttons[sector_str].sector_state = 'opponent_scoring'
            else:
                self.sector_buttons[sector_str].sector_state = 'normal'
            
            # Update scoring indicators
            self.p1_indicators[sector_str].update_marks(self.game.players[0].sectors[sector_str])
            self.p2_indicators[sector_str].update_marks(self.game.players[1].sectors[sector_str])
        
        # Update Bull indicators
        self.p1_indicators['Bull'].update_marks(self.game.players[0].sectors['Bull'])
        self.p2_indicators['Bull'].update_marks(self.game.players[1].sectors['Bull'])
        
        # Update Bull button state
        current_hits = self.game.players[current].sectors['Bull']
        opponent_hits = self.game.players[opponent].sectors['Bull']
        
        if current_hits >= 3 and opponent_hits >= 3:
            self.ids.btn_sector_bull.sector_state = 'closed'
        elif current_hits >= 3 and opponent_hits < 3:
            self.ids.btn_sector_bull.sector_state = 'player_scoring'
        elif opponent_hits >= 3 and current_hits < 3:
            self.ids.btn_sector_bull.sector_state = 'opponent_scoring'
        else:
            self.ids.btn_sector_bull.sector_state = 'normal'

class DartsCricketApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DataInputScreen(name='data_input'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    DartsCricketApp().run() 