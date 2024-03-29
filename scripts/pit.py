import lib.Game as Game
import lib.Players as Players
import lib.Network as Network
import csv
import sys
import random

#get spects in a clash between two bots

path = sys.path[0]

#go up one directory
path = path[0 : len(path) - 8]

#prompt for information regarding bots -- uses absolute number, not offset as before
print("Please list the index of the competing bots (e.g. '1, 2'):")
string = input()
indexList = string.split(", ")

#load networks
net1 = Network.Model(index=indexList[0])
net2 = Network.Model(index=indexList[1])

#prompt for number of wins
print("How many completed games should they play?")
gameNum = int(input())

gameCount = 0
completionCount = 0
win1Count = 0
win2Count = 0

while completionCount != gameNum:

    rand = bool(round(random.random()))

    if rand:
        game = Game.Game([Players.Bot(0, net1, noise=0.1), Players.Bot(1, net2, noise=0.1)], display=False)
    else:
        game = Game.Game([Players.Bot(0, net2, noise=0.1), Players.Bot(1, net1, noise=0.1)], display=False)
    
    while game.isEnd() == False:
        game.makeMove()
    
    gameCount += 1

    #increment the appropriate counters
    if game.board.is_checkmate():
        winner = not game.board.turn
        completionCount += 1
        if winner != rand:
            win1Count += 1
        else:
            win2Count += 1
    
    #print output
    if gameCount != 1:
        #delete previous line
        print("\033[F" * 5, end="")
    
    print("-" * 20)
    print("Total games: " + str(gameCount))
    print("Draws: " + str(gameCount - completionCount))
    print("Bot " + indexList[0] + " wins: " + str(win1Count))
    print("Bot " + indexList[1] + " wins: " + str(win2Count))
    print("-" * 20, end="")

#print final ratios
print("") #<- new line
print("Bot " + indexList[0] + " win percentage: " + f"{(win1Count / completionCount * 100):.3}" + "%")
print("Bot " + indexList[1] + " win percentage: " + f"{(win2Count / completionCount * 100):.3}" + "%")