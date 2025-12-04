import random

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
        grid = game.grid
        options = []

        for pos in grid.squares:
            for orientation in range(4):
                self.piece.set_orientation(orientation)
                if game.can_drop(game.grid, self.piece, pos):
                    options.append((orientation, pos))

        if len(options) > 0:
            orientation, pos = random.choice(options)
            self.piece.set_orientation(orientation)
            game.new_tile_positions = game.drop(game.grid, self.piece, pos)
            return True
        else:
            print(f"no allowable plays for computer player {self.colour}")
            return False