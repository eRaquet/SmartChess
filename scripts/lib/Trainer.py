import lib.Game as Game
import lib.Network as Network
import lib.Players as Players
import lib.Display as Display
import time
import chess
import keras
import random
import numpy as np
import sys

path = sys.path[0]

#go up one directory
path = path[0 : len(path) - 8]

#class for training the model
class Trainer ():

    def __init__(self, games=10, winRatio=0.8, save=4, networkOffset=0, startNoise=0.2):

        self.gamesPerEpoch = games
        self.winRatio = winRatio
        self.saveFraction = save
        self.noise = startNoise

        self.currentNetwork = Network.Model(offset=networkOffset)

        self.testPos = np.load(path + '\\testPositions\\testPositions.npy')
        self.testEval = np.load(path + '\\testPositions\\testEvaluations.npy')

    #train an entire session
    def trainSession(self, epochs):

        saveCount = 0
        epochCount = 0

        #train each epoch of games
        while epochCount < epochs:

            self.wins = 0
            self.games = 0
            
            self.trainEpoch()

            self.validate()

            saveCount += 1
            if saveCount == self.saveFraction:
                self.currentNetwork.saveModel()
                self.game.saveGame()
                saveCount = 0

            print('Win ratio: ' + str(self.wins / self.games))

            epochCount += 1

        if (saveCount != 0):
            self.currentNetwork.saveModel()
            self.game.saveGame()
    
    #train one epoch of games
    def trainEpoch(self):

        inputData = np.ndarray((0, 769), np.bool_)
        outputData = np.ndarray(0)

        winCount = 0

        while winCount != self.gamesPerEpoch:

            outcome = self.playGame()

            self.games += 1

            if outcome:
                self.wins += 1
                winCount += 1
                winner = not self.game.board.turn

                #get dataset
                winnerData = self.game.players[winner].positions
                loserData = self.game.players[not winner].positions

                winnerEvaluations = self.currentNetwork.model.predict_on_batch(np.array(self.game.players[winner].positions)).T[0]
                loserEvaluations = self.currentNetwork.model.predict_on_batch(np.array(self.game.players[not winner].positions)).T[0]

                #apply correction to the model
                winnerOutput = np.clip(winnerEvaluations + np.ones(len(winnerData)) / len(winnerData), -1.0, 1.0)
                loserOutput = np.clip(loserEvaluations - np.ones(len(loserData)) / len(loserData), -1.0, 1.0)
                inputData = np.concatenate((inputData, winnerData, loserData), axis=0)
                outputData = np.concatenate((outputData, winnerOutput, loserOutput), axis=0)

        #train on the data
        self.currentNetwork.model.fit(x=inputData, y=outputData, batch_size=len(outputData), epochs=7, verbose=1)

    #play a game to its end, and return the outcome
    def playGame(self):

        self.white = Players.Bot(chess.WHITE, self.currentNetwork, self.noise)
        self.black = Players.Bot(chess.BLACK, self.currentNetwork, self.noise)
        self.game = Game.Game([self.black, self.white], display=False)

        while self.game.isEnd() == False:

            self.game.makeMove()

        #if the game ended in a win, return True
        if self.game.board.is_checkmate():

            return True
        
        else:

            return False

    #test the network on some archived positions (not for training...just a way to reality check)
    def validate(self):
        
        print('Current loss on training set: ' + str(self.currentNetwork.model.evaluate(self.testPos, self.testEval)))

#get a distibution of opponents given a number of games to play (play better bots more)
def getGameDist(gameNum):
    opponentNum = 5
    gameList = np.zeros(opponentNum)
    for i in range(0, opponentNum):
        gameList[i] = gameDist(i, opponentNum)
    gameList = (gameList * gameNum).astype(int)
    print(gameList)

#game distibution function --> used in getGameDist
def gameDist(index, n):

    #adjust index to function to a midpoint rectagular approximation
    index += 0.5
    return (-2 / n**2) * index + (2 / n)