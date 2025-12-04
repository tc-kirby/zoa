#!/usr/bin/python3

import pygame, random, time
import engine, interface, player

def main():
    pygame.init()
    pygame.display.set_caption("Zoa")

    the_ui = interface.UI()
    
    while True:
        n_humans, n_cpus = the_ui.get_player_numbers()
        players = []
        player_colours = list(range(0,4))
        random.shuffle(player_colours)

        for i in range(n_humans):
            players.append(player.Player(player_colours[i]))

        for j in range(n_humans, n_cpus + n_humans):
            players.append(player.AIPlayer(player_colours[j]))

        the_game = engine.Game(board_size_squares = the_ui.board_size_squares, players = players)
        the_ui.set_game(the_game)
        the_ui.next_turn()

        while not the_game.winner:
            if the_ui.do_events():
                the_ui.draw_elements()
                the_ui.draw_screen()
            else: time.sleep(0.01)

if __name__ == "__main__":
    main()

