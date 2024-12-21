#Test script: run games between bot and human

import lib.Game as Game
import lib.Players as Players
import lib.Network as Network
import pygame as pg
import time

#initiate our current netowrk
model_default = Network.Model(offset=0)

#creates the various player configuations (player type, player color)
playerDic = {
    ('h', 'w') : Players.Human(),
    ('h', 'b') : Players.Human(),
    ('b', 'w') : Players.Bot(1, model_default, confidence=5.0),
    ('b', 'b') : Players.Bot(0, model_default, confidence=5.0),
    ('r', 'w') : Players.Bot(1, model_default, confidence=0.0),
    ('r', 'b') : Players.Bot(0, model_default, confidence=0.0)
}

playerTypes = ['h', 'b', 'r']

while True:

    print("Please indicate game configuration; '(white type) vs. (black type)' [human -> 'h', bot 3 -> 'b3', random -> 'r']: ", end='')
    config = input()

    config = config.split(" vs. ")
    white = config[0]
    black = config[1]

    #if the player types are valid
    if white[0] in playerTypes and black[0] in playerTypes:

        if white[0] != 'b' or len(white) == 1:
            whitePlayer = playerDic[(white, 'w')]
        else:
            model = Network.Model(index=int(white[1:]))
            whitePlayer = Players.Bot(1, model, confidence=5.0)
        
        if black[0] != 'b' or len(black) == 1:
            whitePlayer = playerDic[(black, 'w')]
        else:
            model = Network.Model(index=int(black[1:]))
            blackPlayer = Players.Bot(0, model, confidence=5.0)

        game = Game.Game([blackPlayer, whitePlayer])

        while not game.isEnd():

            #if a human is playing...
            if white == 'h' or black == 'h':
                
                #...just play as usual
                game.makeMove()

            #if its just bots...
            else:

                #...wait for the operator to step to the next move
                for event in pg.event.get():

                    if event.type == pg.MOUSEBUTTONDOWN:

                        t = time.time()
                        game.makeMove()
                        print("move time: " + str(time.time() - t))

        print("Do you want to play again? (y/n) ", end='')

        if input() != 'y':
            break

    #invalid player types
    else:
        print("Do not recognize player types")