import sys, pygame, time
import engine, grid, player, media

MARGIN = 20

PIECE_DRAW_OFFSET = 0 - (media.SQUARE_SIZE // 2)

DESCRIPTION_1_TEXT = "You are a fungus. Only the other fungi"
DESCRIPTION_2_TEXT = "stand between you and freedom."
DESCRIPTION_3_TEXT = "Surround the other fungi to win!"

PIECE_MAX_WIDTH = 4
PIECE_MAX_HEIGHT = 4

class UIElement:
    def __init__(self, pos, size, bg_colour, pygame_flags = 0):
        self.rect = pygame.Rect(pos, size)
        self.surface = pygame.Surface(size, pygame_flags)
        self.bg_colour = bg_colour

class Overlay(UIElement):
    def __init__(self, size, piece_pal_element):
        super().__init__((0, 0), size, pygame.Color(0,0,0,0), pygame.SRCALPHA)
        self.dragging = False
        self.cursor_pos = (0, 0)
        self.piece_pal_element = piece_pal_element
        self.bite_cursor = False
        self.bite_cursor_tile = engine.Tile(tooth = True, background = False)

    def draw(self, piece = None):
        self.surface.fill(self.bg_colour)
        cursor_x, cursor_y = self.cursor_pos
        if piece and self.dragging:
            for pos in piece.squares.keys():
                x, y = pos
                this_tile = piece.squares[pos]

                this_tile.renderer.draw()

                draw_x = ((x * media.SQUARE_SIZE) + cursor_x) + PIECE_DRAW_OFFSET
                draw_y = ((y * media.SQUARE_SIZE) + cursor_y) + PIECE_DRAW_OFFSET

                self.surface.blit(this_tile.renderer.surface, (draw_x, draw_y))

        if self.bite_cursor:
            self.bite_cursor_tile.renderer.draw()
            self.surface.blit(self.bite_cursor_tile.renderer.surface, (cursor_x, cursor_y))

    def set_bite_cursor(self):
        self.bite_cursor = True
        self.cursor_pos = pygame.mouse.get_pos()
        pygame.mouse.set_visible(False)

    def unset_bite_cursor(self):
        if self.bite_cursor:
            self.bite_cursor = False
            pygame.mouse.set_visible(True)

class PiecePal(UIElement):
    def __init__(self, pos, size, bg_colour):
        super().__init__(pos, size, bg_colour)
        self.has_piece = True

    def draw(self, piece = None):
        pygame.draw.rect(self.surface, self.bg_colour, self.surface.get_rect())
        if self.has_piece:
            for pos in piece.squares.keys():
                x, y = pos
                this_square = piece.squares[pos]
                this_square.renderer.draw()
                self.surface.blit(this_square.renderer.surface, (x * media.SQUARE_SIZE, y * media.SQUARE_SIZE))

class ScoreBoard(UIElement):
    def draw(self, game):
        pygame.draw.rect(self.surface, self.bg_colour, self.surface.get_rect())
        
        for i, player in enumerate(game.players):
            head_tile = engine.Tile(player = player, head = True)
            head_tile.renderer.draw()
            self.surface.blit(head_tile.renderer.surface, (0, i * media.SQUARE_SIZE * 2))
            for j in range(0, player.bites):
                bite_tile = engine.Tile(player = None, tooth = True, background = False)
                bite_tile.renderer.draw()
                if j <= 2:
                    x_pos = (j + 1) * media.SQUARE_SIZE
                    y_pos = i * media.SQUARE_SIZE * 2
                else:
                    x_pos = (j - 3) * media.SQUARE_SIZE
                    y_pos = (i + 0.5) * media.SQUARE_SIZE * 2

                self.surface.blit(bite_tile.renderer.surface, (x_pos, y_pos))

class BoardElement(UIElement):
    def draw(self, grid):
        pygame.draw.rect(self.surface, self.bg_colour, self.surface.get_rect())
            
        width, height = grid.size

        for y in range(width):
            for x in range(height):
                this_square = grid.get_square((x, y))
                this_square.renderer.draw()
                self.surface.blit(this_square.renderer.surface, (x * media.SQUARE_SIZE, y * media.SQUARE_SIZE))

    def point_to_square(self, grid, point_pos):
        point_x, point_y = point_pos
        square_x = (point_x + (media.SQUARE_SIZE // 2)) // media.SQUARE_SIZE
        square_y = (point_y + (media.SQUARE_SIZE // 2)) // media.SQUARE_SIZE
        width, height = grid.size
        if square_x < 0 or square_y < 0 or square_x >= width or square_y >= height: return None
        else: return (square_x, square_y)    

class UI:
    def __init__(self):
        standard_bg_colour = pygame.Color(100, 100, 100)

        self.board_size_squares = (grid.BOARD_WIDTH_SQUARES, grid.BOARD_HEIGHT_SQUARES)

	    # Initialize UI elements
        self.board_element = BoardElement((MARGIN, MARGIN), (grid.BOARD_WIDTH_SQUARES * media.SQUARE_SIZE, grid.BOARD_HEIGHT_SQUARES * media.SQUARE_SIZE), standard_bg_colour)
        self.piece_pal_element = PiecePal((MARGIN + self.board_element.rect.width + MARGIN, MARGIN), (PIECE_MAX_WIDTH * media.SQUARE_SIZE, PIECE_MAX_HEIGHT * media.SQUARE_SIZE), standard_bg_colour)
        self.overlay_element = Overlay((self.board_element.rect.width + self.piece_pal_element.rect.width + (MARGIN * 3), self.board_element.rect.height + (MARGIN * 2)), piece_pal_element = self.piece_pal_element)
        self.score_board_element = ScoreBoard((MARGIN + self.board_element.rect.width + MARGIN, (MARGIN * 2) + self.piece_pal_element.rect.height),(4 * media.SQUARE_SIZE, 8 * media.SQUARE_SIZE), standard_bg_colour)
        self.screen_element = UIElement((0, 0), (self.board_element.rect.width + self.piece_pal_element.rect.width + (MARGIN * 3), self.board_element.rect.height + (MARGIN * 2)), standard_bg_colour)

        self.screen = pygame.display.set_mode((self.screen_element.rect.width, self.screen_element.rect.height))
        self.sounds = media.Sounds("./sounds/")
        self.splash = SplashScreen(self.screen_element.rect, "./images/bg_tiles.bmp")

        self.animation_manager = media.AnimationManager(None, self.sounds, self.board_element, self.screen)

        self.game = None
        self.biting = False
        self.bite_attempt_positions = []
        
    def set_game(self, game):
        self.game = game
        self.animation_manager.game = game

    def get_player_numbers(self):
        n_humans = None
        n_cpus = None

        while n_humans == None or n_cpus == None:
            n_humans, n_cpus = self.splash.do_events()
            pygame.draw.rect(self.screen, pygame.Color(255, 255, 255), self.screen.get_rect())
            self.splash.draw()
            self.screen.blit(self.splash.surface, (0, 0))
            pygame.display.flip()

        return n_humans, n_cpus

    def start_piece_drag(self, piece):
        self.overlay_element.dragging = True
        self.overlay_element.cursor_pos = pygame.mouse.get_pos()

    def end_piece_drag(self):
        if self.overlay_element.dragging:
            self.overlay_element.dragging = False
            self.draw_elements()

    def return_piece(self):
        self.piece_pal_element.has_piece = True

    def draw_elements(self):
        self.board_element.draw(self.game.grid)
        self.score_board_element.draw(self.game)
        self.piece_pal_element.draw(self.game.current_player.piece)
        self.overlay_element.draw(self.game.current_player.piece)

    def draw_screen(self):
        pygame.draw.rect(self.screen, pygame.Color(255, 255, 255), self.screen.get_rect())

        self.screen.blit(self.board_element.surface, self.board_element.rect)
        self.screen.blit(self.piece_pal_element.surface, self.piece_pal_element.rect)
        self.screen.blit(self.score_board_element.surface, self.score_board_element.rect)
        self.screen.blit(self.overlay_element.surface, (0, 0))
        
        pygame.display.flip()

    def keydown(self, key):
        match key:
            case pygame.K_ESCAPE:
                if not self.overlay_element.dragging: self.next_turn()
            case pygame.K_SPACE:
                self.game.current_player.piece.rotate()

    def mouse_motion(self, mouse_data):
        mouse_pos, in_window, in_piecepal, in_board, bd_rel_pos = mouse_data

        if in_window:
            self.overlay_element.cursor_pos = mouse_pos

        if True in pygame.mouse.get_pressed() and in_window:
            if self.overlay_element.dragging and not in_window:
                self.end_piece_drag() # End the drag if the mouse goes outside the window
                self.return_piece()
                self.sounds.play("scratch")
                print("mouse outside window")
            if self.biting:
                self.bite_action(bd_rel_pos)
                self.board_element.draw(self.game.grid)
                self.overlay_element.draw(self.game.current_player.piece)
                self.draw_screen()
        else:
            if in_board and self.game.current_player.bites > 0:
                self.overlay_element.set_bite_cursor()
            else:
                self.overlay_element.unset_bite_cursor()

    def mouse_button_down(self, mouse_data):
        mouse_pos, in_window, in_piecepal, in_board, bd_rel_pos = mouse_data
        if in_piecepal:
            self.start_piece_drag(self.game.current_player.piece)
            self.piece_pal_element.has_piece = False
        if in_board:
            if self.game.current_player.bites > 0:
                self.start_bite()
                self.mouse_motion(mouse_data)

    def mouse_button_up(self, mouse_data):
        mouse_pos, in_window, in_piecepal, in_board, bd_rel_pos = mouse_data
        if self.overlay_element.dragging:
            if in_piecepal:
                self.end_piece_drag()
                self.return_piece()
                self.game.current_player.piece.rotate()
            elif in_board:
                self.end_piece_drag()
                if self.drop_piece(self.game.current_player.piece, bd_rel_pos):
                    self.end_turn_actions()
                    self.next_turn()
            else:
                self.sounds.play("scratch")
                self.end_piece_drag()
                self.return_piece()
                print(f"piece released outside board (rect = {self.board_element.rect}; mouse_pos = {mouse_pos} bd_rel_pos = {bd_rel_pos})")

        elif self.biting:
            self.overlay_element.unset_bite_cursor()
            self.overlay_element.draw()
            self.draw_screen()
            self.bite()

    def do_events(self):
        events = pygame.event.get()

        for event in events:
            mouse_pos = pygame.mouse.get_pos()
            mouse_x, mouse_y = mouse_pos

            # Get the mouse position relative to the different areas
            if mouse_x > 0 and mouse_y > 0 and mouse_x < self.screen_element.rect.width - 1 and mouse_y < self.screen_element.rect.height - 1:
                in_window = True
            else:
                in_window = False

            in_piecepal = self.piece_pal_element.rect.collidepoint(mouse_pos)
            in_board = self.board_element.rect.collidepoint(mouse_pos)

            bd_x, bd_y, bd_w, bd_h = self.board_element.rect
            bd_rel_pos = (mouse_x - bd_x, mouse_y - bd_y)

            mouse_data = (mouse_pos, in_window, in_piecepal, in_board, bd_rel_pos)

            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN:
                    self.keydown(event.key)
                case pygame.MOUSEMOTION:
                    self.mouse_motion(mouse_data)
                case pygame.MOUSEBUTTONDOWN:
                    self.mouse_button_down(mouse_data)
                case pygame.MOUSEBUTTONUP:
                    self.mouse_button_up(mouse_data)
        if events: return True
        else: return False

    def drop_piece(self, piece, bd_rel_pos):
        mouse_x, mouse_y = bd_rel_pos

        drop_tile_x = mouse_x // media.SQUARE_SIZE
        drop_tile_y = mouse_y // media.SQUARE_SIZE

        if self.game.can_drop(self.game.grid, self.game.current_player.piece, (drop_tile_x, drop_tile_y)):
            self.game.new_tile_positions = self.game.drop(self.game.grid, self.game.current_player.piece, (drop_tile_x, drop_tile_y))
            self.piece_pal_element.draw(self.game.current_player.piece)
            self.overlay_element.draw()
            self.board_element.draw(self.game.grid)
            self.draw_screen()
            return True
        else:
            self.return_piece()
            self.sounds.play("scratch")
            print("invalid drop")
            return False

    def bite(self):
        # Push the pizza sound to the animation queue, to be played before the bite is executed
        animation_queue = [media.SoundEvent("pizza", delay = 0.5)]
        # Get the bite animation stages and push to the queue
        animation_queue += self.game.get_bite_anim_stages(self.bite_attempt_positions)

        # Check for dead tiles and push tile death animations to the queue
        self.game.check_alive()
        animation_queue += self.game.get_death_anim_stages()

        self.animation_manager.animate(animation_queue)
        self.game.clear_bitten_squares(self.bite_attempt_positions)
        self.end_bite()

    def next_turn(self):
        self.game.next_turn()
        animation_queue = self.game.add_bonus_teeth()
        if animation_queue: self.animation_manager.animate(animation_queue)

        # Is the current player an AI? If so, give it a turn
        while isinstance(self.game.current_player, player.AIPlayer) and not self.game.winner:
            if self.game.current_player.take_turn(self.game):
                self.end_turn_actions()
                self.draw_elements()
                self.draw_screen()
                time.sleep(0.2)
            self.game.next_turn()

        # Back to human players, so enable the piece pal
        self.piece_pal_element.has_piece = True

    def end_turn_actions(self):
        animation_queue = []

        # Check for and animate captures
        capture_radials = self.game.compute_captures(self.game.current_player)
        if capture_radials:
            animation_queue = animation_queue + self.game.get_capture_anim_stages(self.game.current_player, capture_radials)

            if animation_queue:
                self.animation_manager.animate(animation_queue)

        # Check which squares are alive, remove dead ones and animate cuts to the removed squares
        self.game.check_alive()
        animation_queue = self.game.get_death_anim_stages()
        if animation_queue:
            self.animation_manager.animate(animation_queue)

        # Check if any players have died
        self.game.remove_dead_players()

        if len(self.game.players) == 1:
            self.animation_manager.animate([media.WinEvent(self.game.players[0])])
            self.game.winner = self.game.players[0]

        self.game.new_tile_positions = []

    def start_bite(self):
        print("Starting bite")
        self.biting = True

    def end_bite(self):
        print(f"Ending bite {self.bite_attempt_positions}")
        self.game.clear_bitten_squares(self.bite_attempt_positions)
        self.biting = False
        self.bite_attempt_positions = []

    def bite_action(self, bd_rel_pos):
        bite_mark_pos = self.board_element.point_to_square(self.game.grid, bd_rel_pos)
        invalid = False

        # If we are trying to bite outside the board
        if bite_mark_pos == None:
            self.end_bite()
            self.sounds.play("scratch")
            print("attempting to bite outside the board")
            return

        if self.bite_attempt_positions:
            if not bite_mark_pos in self.bite_attempt_positions:
                if self.game.mark_bitten_square(bite_mark_pos, self.bite_attempt_positions):
                    self.bite_attempt_positions.append(bite_mark_pos)
                    self.start_bite()
                else: invalid = True
        else:
            if self.game.mark_bitten_square(bite_mark_pos):
                self.bite_attempt_positions = [bite_mark_pos]
                self.start_bite()
            else: invalid = True
                
        if invalid:
            print("invalid bite position")
            self.end_bite()
            self.sounds.play("scratch")

class SplashScreen:
    def __init__(self, pos_rect, bg_image_path):
        self.pos_rect = pos_rect
        self.n_humans = 1
        self.n_cpus = 1

        huge_font_size = 140
        big_font_size = 100
        medium_font_size = 80
        small_font_size = 40

        WHITE = (255, 255, 255)
        GREY = (150, 150, 150)
        BLACK = (0, 0, 0)

        self.ui_elements = {}

        self.surface = pygame.Surface(self.pos_rect.size)

        self.ui_elements['title'] = TextBox((self.pos_rect.width // 2, int(self.pos_rect.height * (3/24))), "Zoa", "aerial", huge_font_size, WHITE, BLACK, 20)
        self.ui_elements['description1'] = TextBox((self.pos_rect.width // 2, int(self.pos_rect.height * (7/24))), DESCRIPTION_1_TEXT, "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['description2'] = TextBox((self.pos_rect.width // 2, int(self.pos_rect.height * (10/24))), DESCRIPTION_2_TEXT, "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['description3'] = TextBox((self.pos_rect.width // 2, int(self.pos_rect.height * (13/24))), DESCRIPTION_3_TEXT, "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['choose_prompt'] = TextBox((self.pos_rect.width // 2, int(self.pos_rect.height * (17/24))), "How many players?", "aerial", medium_font_size, WHITE, BLACK, 20)
        self.ui_elements['human'] = TextBox((int(self.pos_rect.width * (1.5 / 16)), int(self.pos_rect.height * (21/24))), 'Human', "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['human_minus'] = TextBox((int(self.pos_rect.width * (3.8 / 16)), int(self.pos_rect.height * (21/24))), '-', "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['human_count'] = TextBox((int(self.pos_rect.width * (5 / 16)), int(self.pos_rect.height * (21/24))), str(self.n_humans), "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['human_plus'] = TextBox((int(self.pos_rect.width * (6.2 / 16)), int(self.pos_rect.height * (21/24))), '+', "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['cpu'] = TextBox((int(self.pos_rect.width * (8 / 16)), int(self.pos_rect.height * (21/24))), 'CPU', "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['cpu_minus'] = TextBox((int(self.pos_rect.width * (9.8 / 16)), int(self.pos_rect.height * (21/24))), '-', "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['cpu_count'] = TextBox((int(self.pos_rect.width * (11 / 16)), int(self.pos_rect.height * (21/24))), str(self.n_cpus), "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['cpu_plus'] = TextBox((int(self.pos_rect.width * (12.2 / 16)), int(self.pos_rect.height * (21/24))), '+', "aerial", small_font_size, WHITE, BLACK, 20)
        self.ui_elements['play'] = TextBox((int(self.pos_rect.width * (14 / 16)), int(self.pos_rect.height * (21/24))), 'Play!', "aerial", small_font_size, WHITE, BLACK, 20)
        
        self.bg_image = pygame.image.load(bg_image_path)

    def draw(self):
        self.surface.blit(self.bg_image, (0, 0))

        for ui_element in self.ui_elements.values():
            ui_element.draw()
            self.surface.blit(ui_element.surface, ui_element.pos)

    def do_events(self):
        for event in pygame.event.get():
            mouse_pos = pygame.mouse.get_pos()

            for ui_element in self.ui_elements.values():
                ui_element.mouse_in = True if ui_element.surface.get_rect().collidepoint(ui_element.get_rel_pos(mouse_pos)) else False

            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.MOUSEBUTTONUP:
                if self.ui_elements['human_minus'].mouse_in:
                    if self.n_humans > 0: self.n_humans -= 1
                    if self.n_humans == 0 and self.n_cpus < 2: self.n_cpus = 2
                elif self.ui_elements['human_plus'].mouse_in:
                    if self.n_humans + self.n_cpus < 4: self.n_humans += 1
                elif self.ui_elements['cpu_minus'].mouse_in:
                    if self.n_cpus > 0: self.n_cpus -= 1
                    if self.n_cpus == 0 and self.n_humans < 2: self.n_humans = 2
                elif self.ui_elements['cpu_plus'].mouse_in:
                    if self.n_humans + self.n_cpus < 4: self.n_cpus += 1
                elif self.ui_elements['play'].mouse_in:
                    return (self.n_humans, self.n_cpus)
                
                self.ui_elements['human_count'].set_text(str(self.n_humans))
                self.ui_elements['cpu_count'].set_text(str(self.n_cpus))
                self.draw()
                pygame.display.flip()

        return (None, None)

class TextBox:
    def __init__(self, centre_pos, text_string, font_name, font_size, text_colour, background_colour, margin):
        self.text_string = text_string
        self.font_name = font_name
        self.font_size = font_size
        self.text_colour = text_colour
        self.background_colour = background_colour
        self.margin = margin
        self.centre_pos = centre_pos
        self.enabled = True
        
        self.set_text(self.text_string)

        self.surface = pygame.Surface((self.width, self.height))
        self.surface.set_alpha(200)

        self.mouse_in = False

    def set_text(self, text_string):
        self.text_string = text_string
        self.font= pygame.font.SysFont(self.font_name, self.font_size)
        self.text = self.font.render(self.text_string, True, self.text_colour, (0, 0, 0))

        self.text_width = self.text.get_width()
        self.text_height = self.text.get_height()
        
        self.width = self.text_width + (self.margin * 2)
        self.height = self.text_height + (self.margin * 2)

        # Centre text box horizontally and vertically
        pos_x, pos_y = self.centre_pos
        pos_x -= self.width // 2
        pos_y -= self.height // 2

        self.pos = (pos_x, pos_y)

    def draw(self):
        self.font = pygame.font.SysFont(self.font_name, self.font_size)
        self.text = self.font.render(self.text_string, True, self.text_colour, (0, 0, 0))
        
        pygame.draw.rect(self.surface, self.background_colour, self.surface.get_rect())
        self.surface.blit(self.text, (self.margin , self.margin))

    def get_rel_pos(self, pos):
        self_pos_x, self_pos_y = self.pos
        pos_x, pos_y = pos
        return pos_x - self_pos_x, pos_y - self_pos_y