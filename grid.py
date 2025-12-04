import engine

BOARD_WIDTH_SQUARES = 20
BOARD_HEIGHT_SQUARES = 20
   
class Grid():
    def __init__(self, size):
        self.size = size
        self.squares = {}

    # Initialize the whole grid with blank squares.
    # Good for the board, but unnecessary for pieces.
    def blank_squares(self):
        width, height = self.size
        for y in range(height):
            for x in range(width):
                self.squares[(x, y)] = engine.Tile()

    def drop(self, piece, drop_tile_pos):
        new_tile_positions = []
        add_tooth_count = 0

        drop_tile_x, drop_tile_y = drop_tile_pos

        for pos in piece.squares.keys():
            x, y = pos
            dest_pos = (drop_tile_x + x, drop_tile_y + y)

            if self.get_square(dest_pos).tooth:
                add_tooth_count += 1
                self.get_square(dest_pos).tooth = False

            self.set_square(dest_pos, piece.squares[pos])
            new_tile_positions.append(dest_pos)

        return (new_tile_positions, add_tooth_count)

    def set_square(self, pos, tile):
        self.squares[pos] = tile

    def get_square(self, pos):
        return self.squares[pos]
    
    def get_pos(self, tile):
        positions = list(self.squares.keys())
        tiles = list(self.squares.values())
        tile_index = tiles.index(tile)
        return positions[tile_index]

    # Return a list of positions of squares occupied by player
    def get_player_positions(self, player):
        positions = list(self.squares.keys())
        tiles = list(self.squares.values())
        player_positions = []

        for pos in positions:
            this_square = self.get_square(pos)
            if this_square.player == player: player_positions.append(pos)

        return player_positions

    def get_player_squares(self, player):
        player_positions = self.get_player_positions(player)

        return [self.get_square(pp) for pp in player_positions]
    
    def get_neighbour_positions(self, pos):
        x, y = pos
        width, height = self.size
        neighbour_positions = []

        if x > 0: neighbour_positions.append((x - 1, y))
        if y > 0: neighbour_positions.append((x, y - 1))
        if x < width - 1: neighbour_positions.append((x + 1, y))
        if y < height - 1: neighbour_positions.append((x, y +1))

        return neighbour_positions

    def get_neighbour_squares(self, pos):
        neighbour_positions = self.get_neighbour_positions(pos)

        return [self.get_square(np) for np in neighbour_positions]
    
    # returns a list of tuples that are the positions of squares connected with the square at pos
    def get_connected(self, pos):
        width, height = self.size
        current_player = self.get_square(pos).player
        connected_squares = []
        # Inside matrix for flood-fill algorithm corresponding to all tiles on the board.
        # True means it belongs to this player and so can be filled.
        inside_matrix = [[False for x in range(width)] for y in range(height)]

        for y in range(height):
            for x in range(width):
                inside_matrix[x][y] = True if self.get_square((x, y)).player == current_player else False

        # Set matrix for flood-fill algorithm corresponding to all tiles on the board.
        # True means it has been filled.
        set_matrix = [[False for x in range(width)] for y in range(height)]

        self.flood_fill(inside_matrix, set_matrix, pos)

        for y, row in enumerate(set_matrix):
            for x, col in enumerate(row):
                if set_matrix[x][y]: connected_squares.append((x, y))

        return connected_squares
    
    # Return a line of squares starting from pos and incrementing or decrementing x and y by deltas
    # The effect is to produce a horizontal, vertical or diagonal line of squares from pos to the edge of the board
    # This is used to determine whether a capture should take place once a piece has been placed on the board
    def get_radial(self, pos, x_delta, y_delta):
        width, height = self.size
        x, y = pos

        radial = []
        
        x_end = width if x_delta == 1 else -1
        y_end = height if y_delta == 1 else -1

        # Increment/decrement x and y once, as we are not interested in the current square
        x = x + x_delta
        y = y + y_delta

        while x != x_end and y != y_end:
            radial.append((x, y))
            x = x + x_delta
            y = y + y_delta

        return radial
    
    # Return a tuple of all 8 radials from pos
    def get_radials(self, pos):
        north = self.get_radial(pos, 0, -1)
        northeast = self.get_radial(pos, 1, -1)
        east = self.get_radial(pos, 1, 0)
        southeast = self.get_radial(pos, 1, 1)
        south = self.get_radial(pos, 0, 1)
        southwest = self.get_radial(pos, -1, 1)
        west = self.get_radial(pos, -1, 0)
        northwest = self.get_radial(pos, -1, -1)
        return (north, northeast, east, southeast, south, southwest, west, northwest)
    
    # Recursive function
    def flood_fill(self, inside_matrix, set_matrix, pos):
        x, y = pos
        if inside_matrix[x][y]:
            set_matrix[x][y] = True
            inside_matrix[x][y] = False
            if x < BOARD_WIDTH_SQUARES - 1: self.flood_fill(inside_matrix, set_matrix, (x + 1, y))
            if y < BOARD_HEIGHT_SQUARES - 1: self.flood_fill(inside_matrix, set_matrix, (x, y + 1))
            if x > 0: self.flood_fill(inside_matrix, set_matrix, (x - 1, y))
            if y > 0: self.flood_fill(inside_matrix, set_matrix, (x, y - 1))
