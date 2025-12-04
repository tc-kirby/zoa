from enum import Enum
import pygame, os, time

TILES_SRC_IMAGE = pygame.image.load("./images/tiles_big.bmp")
SQUARE_SIZE = 32

class TileAnimation(Enum):
    NONE = 0
    CUT = 1
    PANIC = 2
    HAPPY = 3

class AnimationManager():
    def __init__(self, game, sounds, board_element, screen):
        self.game = game
        self.sounds = sounds
        self.screen = screen
        self.board_element = board_element

    def refresh_board(self):
        self.screen.blit(self.board_element.surface, self.board_element.rect)
        pygame.display.flip()

    def animate(self, animation_queue):
        for animation in animation_queue:
            if isinstance(animation, Transition):
                match animation.mid_tile.animation_state:
                    case TileAnimation.CUT:
                        self.sounds.play("cut")
                    case TileAnimation.PANIC:
                        self.sounds.play("burp")
                if isinstance(animation, Capture):
                    self.sounds.play("pop")
                    
                self.game.grid.set_square(animation.pos, animation.mid_tile)
                self.board_element.draw(self.game.grid)
                self.refresh_board()
                time.sleep(0.2)
            elif isinstance(animation, SoundEvent):
                self.sounds.play(animation.sound_name)
                time.sleep(animation.delay)
            elif isinstance(animation, WinEvent):
                self.animate_win(self.game.grid, animation.winner)
            
        for animation in animation_queue:
            if isinstance(animation, Transition): self.game.grid.set_square(animation.pos, animation.to_tile)
            
        self.board_element.draw(self.game.grid)
        self.refresh_board()

        animation_queue = []

    def animate_win(self, grid, winner):
        # We have a winner!
        # Fill expanding rects outwards from the head
        head_x, head_y = winner.head_location

        left = head_x - 1
        right = head_x + 1
        top = head_y - 1
        bottom = head_y + 1

        width, height = grid.size

        can_expand = True

        while can_expand:
            can_expand = False

            if left > 0:
                left -= 1
                can_expand = True
            if right < width:
                right += 1
                can_expand = True
            if top > 0:
                top -= 1
                can_expand = True
            if bottom < height:
                bottom +=1
                can_expand = True

            for y_fill in range(top, bottom):
                for x_fill in range(left, right):
                    current_square = grid.get_square((x_fill, y_fill))
                    if not current_square.player == winner:
                        current_square.player = winner
                        current_square.head = False
                        current_square.tooth = False
                        current_square.animation_state = TileAnimation.NONE
            self.board_element.draw(self.game.grid)
            self.refresh_board()
            time.sleep(0.1)

class TileRenderer:
    def __init__(self, tile):
        self.tile = tile
        self.surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
        self.surface.set_colorkey(pygame.Color(255, 0, 128))

    def draw(self):
        x_offset = 0 if not self.tile.player else self.tile.player.colour + 1
        background_rect = pygame.Rect(x_offset * SQUARE_SIZE, 0, SQUARE_SIZE, SQUARE_SIZE)
        if self.tile.head:
            foreground_rect = pygame.Rect(x_offset * SQUARE_SIZE, 1 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        elif self.tile.dest_player and self.tile.dest_player != self.tile.player:
            foreground_rect = pygame.Rect((self.tile.dest_player.colour + 1) * SQUARE_SIZE, 2 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        elif self.tile.tooth:
            foreground_rect = pygame.Rect(0, 1 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        else:
            match self.tile.animation_state:
                case TileAnimation.CUT:
                    foreground_rect = pygame.Rect(0, 2 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                case TileAnimation.PANIC:
                    foreground_rect = pygame.Rect(x_offset * SQUARE_SIZE, 3 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                case TileAnimation.HAPPY:
                    foreground_rect = pygame.Rect(x_offset * SQUARE_SIZE, 4 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                case TileAnimation.NONE:
                    foreground_rect = None

        # Fill with key colour so that if there is no background, the background will be transparent
        pygame.draw.rect(self.surface, pygame.Color(255, 0, 128), self.surface.get_rect())
        if self.tile.background:
            self.surface.blit(self.tile.src_image, (0, 0), background_rect)            

        if foreground_rect:
            foreground_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            foreground_surface.blit(self.tile.src_image, (0, 0), foreground_rect)
            foreground_surface.set_colorkey(pygame.Color(255, 0, 128))
            self.surface.blit(foreground_surface, (0, 0))

class Sounds:
    def __init__(self, base_path):
        self.base_path = base_path
        self.sounds = {}
        sound_files = [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f)) and f.endswith('.wav')]

        for filename in sound_files:
            sound_name = filename[:-4]
            self.sounds[sound_name] = pygame.mixer.Sound(os.path.join(base_path, filename))

    def play(self, sound_name):
        pygame.mixer.Sound.play(self.sounds[sound_name])

class Animation:
    def __init__(self):
        pass

class WinEvent(Animation):
    def __init__(self, winner):
        self.winner = winner

class SoundEvent(Animation):
    def __init__(self, sound_name, delay = 0):
        self.sound_name = sound_name
        self.delay = delay

class Transition(Animation):
    def __init__(self, pos, from_tile, mid_tile, to_tile):
        self.from_tile = from_tile
        self.mid_tile = mid_tile
        self.to_tile = to_tile
        self.pos = pos

class Capture(Transition):
    pass