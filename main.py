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
        # Dictionary to track hits on each sector (0 = open, 1-3 = hits, 4 = closed)
        self.sectors = {str(i): 0 for i in range(4, 10)}
        self.sectors['Bull'] = 0
        self.marks_this_round = 0

class CricketGame:
    def __init__(self):
        self.players = [Player("Verano"), Player("Invierno")]
        self.current_player = 0
        self.game_over = False

    def switch_player(self):
        self.current_player = 1 - self.current_player
        self.players[self.current_player].marks_this_round = 0

    def add_hit(self, sector, hits=1):
        if self.game_over:
            return False

        current = self.players[self.current_player]
        
        # Check if player has already used 9 marks this round
        if current.marks_this_round + hits > 9:
            return False

        opponent = self.players[1 - self.current_player]
        
        # Update hits for the sector
        if current.sectors[sector] < 3:
            old_hits = current.sectors[sector]
            current.sectors[sector] = min(3, current.sectors[sector] + hits)
            actual_hits = current.sectors[sector] - old_hits
            current.marks_this_round += actual_hits
            remaining_hits = hits - actual_hits
        else:
            remaining_hits = hits
            current.marks_this_round += hits

        # Add points if sector is closed by current player
        if remaining_hits > 0 and current.sectors[sector] >= 3:
            if opponent.sectors[sector] < 3:
                points = remaining_hits * (25 if sector == 'Bull' else int(sector))
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
        # Update button color based on state
        if value == 'normal':
            self.background_color = [0.2, 0.6, 0.8, 1]  # Blue
        elif value == 'opponent_scoring':
            self.background_color = [1.0, 0.65, 0.0, 1]  # Orange
        elif value == 'player_scoring':
            self.background_color = [0.3, 0.8, 0.3, 1]  # Green
        else:  # closed
            self.background_color = [0.7, 0.7, 0.7, 1]  # Gray

class SectorIndicator(BoxLayout):
    sector = StringProperty('')
    hits = NumericProperty(0)

    def __init__(self, **kwargs):
        # If sector is passed directly, save it before super init
        sector_arg = kwargs.pop('sector', None)
        if sector_arg:
            self.sector = str(sector_arg)
            
        super().__init__(**kwargs)
        
        # Create marks container if not created by KV
        if not hasattr(self, 'marks_box'):
            self.orientation = 'horizontal'
            self.size_hint_y = None
            self.height = dp(50)  # Match button height
            self.padding = [dp(5), dp(5)]
            self.spacing = dp(5)

            # Add sector label
            self.label = Label(
                text=str(self.sector),
                size_hint_x=0.3,
                font_size='20sp',
                bold=True,
                color=(0.2, 0.2, 0.2, 1)
            )
            self.add_widget(self.label)
            
            # Create marks container
            self.marks_box = BoxLayout(
                orientation='horizontal',
                spacing=dp(4),
                size_hint_x=0.7,
                padding=[dp(2), dp(8)]
            )
            self.add_widget(self.marks_box)
            self.update_marks(0)

    def update_marks(self, hits):
        self.hits = hits
        self.marks_box.clear_widgets()
        for i in range(3):
            mark = Label(
                size_hint_x=None,
                width=dp(30),
                font_size='24sp',
                bold=True
            )
            
            if i < hits:
                mark.text = 'v'  # self-made checkmark
                mark.color = (0.2, 0.8, 0.2, 1)  # Bright green
            else:
                mark.text = '_'
                mark.color = (0.7, 0.7, 0.7, 1)  # Gray underscore
                
            self.marks_box.add_widget(mark)

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = CricketGame()
        self.setup_ui()

    def setup_ui(self):
        # Store references to sector buttons and indicators
        self.sector_buttons = {}
        self.p1_indicators = {}
        self.p2_indicators = {}
        
        # Map the IDs to the dictionaries after kv file is loaded
        for sector in list(range(4, 10)) + ['Bull']:
            sector_str = str(sector)
            # Get button reference
            btn_id = f'btn_sector_{sector_str.lower()}'
            self.sector_buttons[sector_str] = self.ids[btn_id]
            
            # Get indicator references
            p1_id = f'p1_sector_{sector_str.lower()}'
            p2_id = f'p2_sector_{sector_str.lower()}'
            self.p1_indicators[sector_str] = self.ids[p1_id]
            self.p2_indicators[sector_str] = self.ids[p2_id]
        
        self.update_display()

    def on_sector_press(self, sector):
        current_player = self.game.players[self.game.current_player]
        if current_player.marks_this_round >= 9:
            return
            
        if self.game.add_hit(sector):
            self.update_display()
            if self.game.game_over:
                winner = self.game.players[0] if self.game.players[0].score > self.game.players[1].score else self.game.players[1]
                self.ids.player1_name.text = "Game Over!"
                self.ids.player2_name.text = f"{winner.name} wins!"
                self.ids.player1_score.text = ""
                self.ids.player2_score.text = ""

    def next_player(self, *args):
        if not self.game.game_over:
            self.game.switch_player()
            self.update_display()

    def update_display(self):
        # Update player scores
        self.ids.player1_score.text = str(self.game.players[0].score)
        self.ids.player2_score.text = str(self.game.players[1].score)
        
        # Calculate and update differences
        p1_score = self.game.players[0].score
        p2_score = self.game.players[1].score
        p1_diff = p1_score - p2_score
        p2_diff = p2_score - p1_score
        self.ids.player1_diff.text = f"Diff: {p1_diff}"
        self.ids.player2_diff.text = f"Diff: {p2_diff}"
        
        # Update player backgrounds based on current player
        p1_bg = [0.3, 0.7, 0.3, 1] if self.game.current_player == 0 else [0.9, 0.9, 0.9, 1]
        p2_bg = [0.3, 0.7, 0.3, 1] if self.game.current_player == 1 else [0.9, 0.9, 0.9, 1]
        
        # Update player name backgrounds
        for widget_id, bg in [('player1_name', p1_bg), ('player2_name', p2_bg),
                            ('player1_score', p1_bg), ('player2_score', p2_bg),
                            ('player1_diff', p1_bg), ('player2_diff', p2_bg)]:
            widget = self.ids[widget_id]
            widget.canvas.before.clear()
            with widget.canvas.before:
                Color(*bg)
                Rectangle(pos=widget.pos, size=widget.size)
        
        # Update sector buttons and indicators
        current = self.game.current_player
        opponent = 1 - current
        
        for sector, btn in self.sector_buttons.items():
            current_hits = self.game.players[current].sectors[sector]
            opponent_hits = self.game.players[opponent].sectors[sector]
            
            # Update button state from current player's perspective
            if current_hits >= 3 and opponent_hits >= 3:
                btn.sector_state = 'closed'
            elif current_hits >= 3 and opponent_hits < 3:
                btn.sector_state = 'player_scoring'
            elif opponent_hits >= 3 and current_hits < 3:
                btn.sector_state = 'opponent_scoring'
            else:
                btn.sector_state = 'normal'
            
            # Update scoring indicators
            self.p1_indicators[sector].update_marks(self.game.players[0].sectors[sector])
            self.p2_indicators[sector].update_marks(self.game.players[1].sectors[sector])

class DartsCricketApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    DartsCricketApp().run() 