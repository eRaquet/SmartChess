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

            if outcome == True:

                self.wins += 1
                winCount += 1
                winner = not self.game.board.turn

                #get dataset
                winnerData = self.game.players[winner].positions
                loserData = self.game.players[not winner].positions
                winnerOutput = np.ones(len(winnerData))
                loserOutput = -np.ones(len(loserData))
                inputData = np.concatenate((inputData, winnerData, loserData), axis=0)
                outputData = np.concatenate((outputData, winnerOutput, loserOutput), axis=0)

                self.noise = min(0.2, self.noise - (1 - self.winRatio) * 0.001)

            else:

                self.noise = min(0.2, self.noise + self.winRatio * 0.001)

        #train on the data
        self.currentNetwork.model.fit(x=inputData, y=outputData, batch_size=len(outputData), epochs=40, verbose=1)

    #play a game to its end, and return the outcome
    def playGame(self):

        self.rand = bool(round(random.random()))

        self.white = Players.Bot(chess.WHITE, self.currentNetwork, (1 - 0.8 * float(not self.rand)) * self.noise)
        self.black = Players.Bot(chess.BLACK, self.currentNetwork, (1 - 0.8 * float(self.rand)) * self.noise)
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

trainer = Trainer(games=10, startNoise=0.09)

trainer.trainSession(10)