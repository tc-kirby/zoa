import random
import grid, media

PLAYER_MAX_BITES = 7
BONUS_TEETH_CHANCE = 0.02
FIRST_BONUS_TEETH_ROUND = 8
BONUS_TEETH_WAIT_ROUNDS = 3

class Game:
    def __init__(self, board_size_squares, players = [], ):
        self.players = players
        self.current_player = None
        self.winner = None
        self.turn_count = 0
        self.new_tile_positions = []
        self.grid = grid.Grid(board_size_squares)
        self.grid.blank_squares()
        self.last_bonus_teeth_round = 0

        # print(f"Setting up game with {len(self.players)} players...")
        if len(self.players) == 2:
            self.players[0].head_location = (4, 4)
            self.players[1].head_location = (15, 15)
        elif len(self.players) == 3:
            self.players[0].head_location = (10, 4)
            self.players[1].head_location = (4, 15)
            self.players[2].head_location = (15, 15)
        elif len(self.players) == 4:
            self.players[0].head_location = (4, 4)
            self.players[1].head_location = (15, 4)
            self.players[2].head_location = (4, 15)
            self.players[3].head_location = (15, 15)

        # Place players' heads on board
        for player in self.players:
            self.grid.set_square(player.head_location, Tile(player = player, head = True))

        self.grid.set_square((0, 0), Tile(tooth = True))
        self.grid.set_square((0, 19), Tile(tooth = True))
        self.grid.set_square((19, 0), Tile(tooth = True))
        self.grid.set_square((19, 19), Tile(tooth = True))

        # Start with a random player
        self.current_player = self.players[random.randint(0, len(self.players) - 1)]

    def can_drop(self, grid, piece, drop_tile_pos):
        drop_tile_x, drop_tile_y = drop_tile_pos

        left, top, right, bottom = piece.get_bounds()
        piece_width = right + 1
        piece_height = bottom + 1

        width_squares, height_squares = grid.size

        # 1. Is the piece entirely on the board?
        if (drop_tile_x < 0 or 
            drop_tile_y < 0 or 
            drop_tile_x + piece_width > width_squares or 
            drop_tile_y + piece_height > height_squares):
            
            return False

        # 2. Is every part of the piece on a substrate tile?
        # 3. If dropped, would the piece in some way attach to the current player?

        has_connection = False

        for pos in piece.squares.keys():
            x, y = pos
            source_tile = piece.squares[pos]
            if source_tile == None: continue # If there is nothing in this part of the source tile, ignore it
            dest_x = drop_tile_x + x
            dest_y = drop_tile_y + y
            dest_tile = grid.get_square((dest_x, dest_y))
            if dest_tile.player != None:
                # print("piece is not (fully) on neutral spaces")
                return False
            
            # Check connections
            neighbours = grid.get_neighbour_squares((dest_x, dest_y))
            
            if source_tile.player in [tile.player for tile in neighbours]: has_connection = True

        if has_connection:
            return True
        else:
            # print("piece has no connection")
            return False

    def drop(self, grid, piece, drop_tile_pos):
        new_tile_positions, add_tooth_count = grid.drop(piece, drop_tile_pos)
        piece.player.bites = min(piece.player.bites + add_tooth_count, PLAYER_MAX_BITES)
        return new_tile_positions

    def add_player(self, player):
        player.colour = len(self.players)
        self.players.append(player)

    # Remove any dead players
    def remove_dead_players(self):
        new_players = []
        for player in self.players:
            if player.alive:
                new_players.append(player)
            else:
                player.alive = False

        self.players = new_players

    # If we are far enough through the game, there is a chance that extra teeth might appear on the board.
    # We allocate one per player into random empty squares.
    # If there are more players than empty squares, just put a tooth in every empty square.
    # Returns an animation queue containing the 'oh smooth' sound.

    def add_bonus_teeth(self):
        animation_queue = []
        round_count = len(self.players) * self.turn_count
        if (round_count >= FIRST_BONUS_TEETH_ROUND and
            round_count >= self.last_bonus_teeth_round + BONUS_TEETH_WAIT_ROUNDS and
            random.random() < BONUS_TEETH_CHANCE
        ):
            self.last_bonus_teeth_round = round_count
            empty_squares = self.grid.get_player_squares(None)
            n_players = len(self.players)
            random.shuffle(empty_squares)
            n_teeth = n_players if n_players < len(empty_squares) else len(empty_squares)
            for square in empty_squares[:n_teeth]:
                square.tooth = True

            animation_queue.append(media.SoundEvent("oh_smooth"))
            return animation_queue

    def next_turn(self):
        self.current_player.piece = None
        new_player_index = (self.players.index(self.current_player) + 1) % len(self.players)
        
        self.turn_count += 1
        self.current_player = self.players[new_player_index]
        self.current_player.piece = Piece(player = self.current_player)

    # Attempt to mark a square as bitten. If valid, return the (now adjusted) bite attempt positions array. If invalid, return None.
    def mark_bitten_square(self, bite_mark_pos, current_bite_attempt_positions = None):
        bite_mark_square = self.grid.get_square(bite_mark_pos)
        neighbour_positions = self.grid.get_neighbour_positions(bite_mark_pos)
        neighbour_squares = self.grid.get_neighbour_squares(bite_mark_pos)
        next_to_own = self.current_player in [neighbour.player for neighbour in neighbour_squares]

        if current_bite_attempt_positions:
            bites_left = self.current_player.bites - len(current_bite_attempt_positions)
            #print(f"player {self.current_player} has {self.current_player.bites} available and {len(current_bite_attempt_positions)} attempted bite positions")

            # If there is any overlap between neighbour_positions and bite_attempt_positions, this is a continuation of a bite that has already begun to be marked
            continuation = True if len(list(set(neighbour_positions) & set(current_bite_attempt_positions))) > 0 else False

        else:
            bites_left = self.current_player.bites
            continuation = False

        #print(f"current player: {self.current_player}, target player: {bite_mark_square.player}, bites left: {bites_left}, next to own: {next_to_own}, continuation: {continuation}, target is head: {bite_mark_square.head}")

        if (bites_left > 0 and
            (next_to_own or continuation) and
            not bite_mark_square.head and
            not bite_mark_square.player == None and
            not bite_mark_square.player == self.current_player):

            bite_mark_square.tooth = True
            return True
        
        else: return False

    def clear_bitten_squares(self, bite_attempt_positions):
        #print(f"Clearing bite {bite_attempt_positions}")
        if bite_attempt_positions:
            for pos in bite_attempt_positions:
                bite_attempt_square = self.grid.get_square(pos)
                bite_attempt_square.tooth = False

    # Called when a bite has been validated and needs to be executed
    def get_bite_anim_stages(self, bite_attempt_positions):
        #print(f"Determining bite animation stages for positions {bite_attempt_positions}")
        animation_queue = []
        
        for pos in bite_attempt_positions:
            current_tile = self.grid.get_square(pos)
            mid_tile = Tile(player = current_tile.player, animation_state = media.TileAnimation.CUT)
            dest_tile = Tile(player = None)

            animation_queue.append(media.Transition(pos, current_tile, mid_tile, dest_tile))
            current_tile.player = None # TODO: HACK

        self.current_player.bites -= len(bite_attempt_positions)

        return animation_queue

    def kill(self, killer, victim):
        animation_queue = []

        victim.alive = False
        # Take over all this player's tiles
        for takeover_pos in self.grid.get_player_positions(victim):
            takeover_tile = self.grid.get_square(takeover_pos)
            mid_tile = Tile(player = victim, dest_player = killer)
            dest_tile = Tile(player = killer)
            animation_queue.append(media.Transition(takeover_pos, takeover_tile, mid_tile, dest_tile))

        return animation_queue

    def get_valid_capture_radials(self, new_tile_pos, capturing_player):
        capture_radials = []

        # generate radials for this tile
        radials = self.grid.get_radials(new_tile_pos)

        # iterate over radials to see if this tile placement results in a capture
        print(f"---{len(radials)}")
        for r in radials:
            adjacent_player = self.grid.get_square(r[0]).player if len(r) > 0 else None
            
            # Only proceed if the tile we are querying is adjacent to a tile of a different player
            print(len(r), capturing_player, adjacent_player)
            if len(r) > 0 and capturing_player != adjacent_player and adjacent_player != None:
                print(f"Computing captures...")
                print(f"Could {capturing_player} capture {adjacent_player}?")
                current_radial_stack = []
                for distance, pos in enumerate(r):
                    square = self.grid.get_square(pos)
                    if square.player == capturing_player:
                        print(f"hit self at {distance}: capture!")
                        capture_radials.append(current_radial_stack)
                        break
                    elif square.player == None:
                        print(f"hit neutral ground at {distance} - no capture")
                        break
                    elif square.player != adjacent_player:
                        print(f"hit a different player {square.player} at {distance} - no capture")
                        break
                    current_radial_stack.append(pos)
                        
                else:
                    #print("no adjacent player")
                    pass
            else:
                #print("no radial")
                pass

        return capture_radials

    def compute_captures(self, capturing_player):
        capture_radials = []

        for pos in self.new_tile_positions:
            capture_radials += self.get_valid_capture_radials(pos, capturing_player)

        return capture_radials
            

    def compute_captures_old(self):
        # We assume that this subroutine is only called once per turn, as it only provides for one player to make captures.
        capture_radials = []

        # Check new tiles for ability to capture
        for new_tile_pos in self.new_tile_positions:
            current_tile = self.grid.get_square(new_tile_pos)
            capturing_player = current_tile.player
            # generate radials for this tile
            radials = self.grid.get_radials(new_tile_pos)
            
            # iterate over radials to see if this tile placement results in a capture
            for r in radials:
                adjacent_player = r[0].player if len(r) > 0 else None
                
                # Only proceed if the tile we are querying is adjacent to a tile of a different player
                if len(r) > 0 and capturing_player != adjacent_player and adjacent_player != None:
                    # print(f"Computing captures...")
                    # print(f"Could {capturing_player} capture {adjacent_player}?")
                    current_radial_stack = []
                    for distance, tile in enumerate(r):
                        
                        # Stop iterating if we have gone onto neutral ground or if we have hit a third player
                        if tile.player == None:
                            # print(f"hit neutral ground at {distance} - no capture")
                            break
                        elif tile.player == capturing_player:
                            # print(f"hit self at {distance}: capture!")
                            capture_radials.append(current_radial_stack)
                            break
                        elif tile.player != adjacent_player:
                            # print(f"hit a different player {tile.player.index} at {distance} - no capture")
                            break
                        current_radial_stack.append(tile)
                            
                    else:
                        #print("no adjacent player")
                        pass
                else:
                    #print("no radial")
                    pass
        
        #if capture_radials: print(f"Player {capturing_player} to capture in radial(s):")
        #for cr in capture_radials: print(cr)

        return capturing_player, capture_radials
    
    def get_capture_anim_stages(self, capturing_player, capture_radials):
        animation_queue = []
        death_transitions = None
        captured_tile_positions = []

        # Perform any captures from the queue
        #print(f"Computing transition queue with {len(capture_radials)} capture radials...")

        for cr in capture_radials:
            for current_pos in cr:
                current_tile = self.grid.get_square(current_pos)
                # print(f"Tile {current_tile} captured by player {capturing_player}.")

                # Only capture tiles that haven't already been captured
                if current_pos not in captured_tile_positions:
                    captured_tile_positions.append(current_pos)
                    if not current_tile.head:
                        mid_tile = Tile(player = current_tile.player, dest_player = capturing_player)
                        
                    else: # head captured - he's dead!
                        mid_tile = Tile(player = current_tile.player, animation_state = media.TileAnimation.PANIC)
                        death_transitions = self.kill(capturing_player, current_tile.player)

                    dest_tile = Tile(player = capturing_player)

                    animation_queue.append(media.Capture(current_pos, current_tile, mid_tile, dest_tile))

        if death_transitions:
            animation_queue = animation_queue + death_transitions

        # prepend making the capturing player happy, and append going back to normal
        if len(animation_queue) > 0:
            capturer_head_tile = self.grid.get_square(capturing_player.head_location)
            mid_tile = Tile(player = capturing_player, animation_state = media.TileAnimation.HAPPY)
            dest_tile = mid_tile
            transition_to_happy = media.Transition(capturing_player.head_location, capturer_head_tile, mid_tile, dest_tile)
            animation_queue.insert(0, transition_to_happy)
            transition_back_to_normal = media.Transition(capturing_player.head_location, mid_tile, capturer_head_tile, capturer_head_tile)
            animation_queue.append(transition_back_to_normal)

        #print(f"Transition queue complete. Length = {len(animation_queue)}")
        return animation_queue
                    

    def check_alive(self):
        # Check all players' heads to see which tiles are connected to them, and mark all those tiles as alive. 
        # All other tiles are dead and should be expunged.

        # First, mark all tiles as dead.
        for y in range(grid.BOARD_HEIGHT_SQUARES):
            for x in range(grid.BOARD_WIDTH_SQUARES):
                current_tile = self.grid.get_square((x, y))
                current_tile.alive = False

        # Iterate over all living players and mark all connected tiles as alive
        for player in self.players:
            if player.alive:
                # Get list of all tiles connected to this player's head
                connected_tile_positions = self.grid.get_connected(player.head_location)
                # Mark each connected tile as alive
                for pos in connected_tile_positions:
                    self.grid.get_square(pos).alive = True

    def get_death_anim_stages(self):
        animation_queue = []
        # Some tiles may now be dead as they are disconnected.
        # Prepare them to animate the transition to being empty.
        for y in range(grid.BOARD_HEIGHT_SQUARES):
            for x in range(grid.BOARD_WIDTH_SQUARES):
                current_tile = self.grid.get_square((x, y))
                if current_tile.player != None and current_tile.alive == False:
                    # print(f"Tile {current_tile} died.")
                    mid_tile = Tile(player = current_tile.player, animation_state = media.TileAnimation.CUT)
                    dest_tile = Tile(player = None)
                    animation_queue.append(media.Transition((x, y), current_tile, mid_tile, dest_tile))

        return animation_queue

class Tile:
    def __repr__(self):
        if not (self.alive and self.player): return "x"
        return f"#{self.player}#"

    def __init__(self, player = None, head = False, tooth = False, dest_player = None, background = True, animation_state = media.TileAnimation.NONE):
        self.src_image = media.TILES_SRC_IMAGE
        self.player = player
        self.head = head
        self.tooth = tooth
        self.background = background
        self.animation_state = animation_state
        
        self.dest_player = dest_player if dest_player else self.player
        self.alive = True
        self.renderer = media.TileRenderer(self)
        
    def reset_state(self):
        self.head = False
        self.tooth = False
        self.animation_state = media.TileAnimation.NONE

class Piece(grid.Grid):
    piece_types = {
    0: ["....",
        "..#.",
        "....",
        "...."],

    1: ["..#.",
        "..#.",
        "..#.",
        "..#."],

    2: ["..#.",
        ".##.",
        "..#.",
        "...."],
        
    3: [".##.",
        "..#.",
        "..#.",
        "...."],
        
    4: ["....",
        ".##.",
        "..##",
        "...."],
        
    5: ["....",
        ".##.",
        ".##.",
        "...."],

    6: ["..#.",
        "..#.",
        "..#.",
        "...."],

    7: [".##.",
        ".#..",
        ".#..",
        "...."],

    8: [".#..",
        ".#..",
        "....",
        "...."],
    
    9: ["....",
        ".##.",
        "##..",
        "...."]
    }

    def __init__(self, piece_type = None, player = None):
        super().__init__(4)
        self.piece_type = random.randint(0, len(self.piece_types) - 1) if not piece_type else piece_type
        self.player = player
        self.set_orientation(0)

    def set_orientation(self, orientation):
        self.orientation = orientation

        piece_str_arr = self.piece_types[self.piece_type]

        self.squares = {}
        
        for y, line in enumerate(piece_str_arr):
            for x, char in enumerate(line):
                if char == "#":
                    self.squares[(x, y)] = Tile(player = self.player)
                    
        for _ in range(orientation): self.rotate()
        
        self.trim()

    def rotate(self):
        new_squares = {}

        for pos in self.squares.keys():
            x, y = pos
            new_squares[(3 - y, x)] = self.squares[(x, y)]

        self.squares = new_squares
        self.trim()
        self.orientation = (self.orientation + 1) % 4

    def get_bounds(self):
        xs = [coord[0] for coord in self.squares.keys()]
        ys = [coord[1] for coord in self.squares.keys()]

        # Find and return the maximum and minimum values of x and y
        return(min(xs), min(ys), max(xs), max(ys))

    def trim(self):
        left_col, top_row, right_col, bottom_row = self.get_bounds()
        new_squares = {}

        for pos in self.squares.keys():
            x, y = pos
            new_squares[(x - left_col, y - top_row)] = self.squares[pos]

        self.squares = new_squares