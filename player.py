import random
import engine

class Player:
    def __repr__(self):
        return f"{self.colour} "

    def __init__(self, colour = None):
        self.colour = colour
        self.head_location = None
        self.alive = True
        self.bites = 0
        self.piece = None

class AIPlayer(Player):
    def take_turn(self, game):
        """Take a turn using GameRules to find valid moves.
        
        The AI can now:
        1. Get the current state via game.get_state()
        2. Use GameRules.get_valid_moves() to find all valid moves
        3. (Future) Clone state to simulate moves for lookahead
        """
        state = game.get_state()
        valid_moves = engine.GameRules.get_valid_moves(state, self.piece)

        if valid_moves:
            # AI can now clone state to simulate moves:
            # simulated_state = state.clone()
            # ... evaluate moves ...
            
            orientation, pos = self.select_move(state, valid_moves)
            self.piece.set_orientation(orientation)
            game.new_tile_positions = game.drop(game.grid, self.piece, pos)
            return True
        else:
            print(f"no allowable plays for computer player {self.colour}")
            return False
    
    def select_move(self, state, valid_moves):
        """Select a move from valid moves.
        
        This method can be overridden by subclasses to implement
        different AI strategies (e.g., minimax, Monte Carlo, etc.).
        
        The default implementation selects a random move.
        
        Args:
            state: The current GameState (can be cloned for simulation)
            valid_moves: List of (orientation, position) tuples
            
        Returns:
            A tuple (orientation, position) representing the selected move
        """
        return random.choice(valid_moves)