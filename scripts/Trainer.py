import Game
import Network
import Players
import Display
import time
import chess
import keras
import random
import numpy as np

#class for training the model
class Trainer ():

    def __init__(self, epochs, games=10, winRatio=0.8, save=4, networkOffset=0, startNoise=0.2):

        self.epochs = epochs
        self.gamesPerEpoch = games
        self.winRatio = winRatio
        self.saveFraction = save
        self.noise = startNoise

        self.winCount = 0
        self.gameCount = 0

        self.currentNetwork = Network.Model(offset=networkOffset)

    #train one epoch of games
    def trainEpoch(self):

        inputData = np.ndarray((0, 769))
        outputData = np.ndarray(0)

        while self.winCount != self.gamesPerEpoch:

            outcome = self.playGame()

            self.gameCount += 1

            if outcome == True:

                self.winCount += 1
                winner = not self.game.board.turn

                #get dataset
                winnerData = self.game.players[winner].boardStack
                loserData = self.game.players[winner].boardStack
                winnerOutput = np.ones(len(winnerData))
                loserOutput = np.zeros(len(loserData))
                inputData = np.concatenate((inputData, winnerData, loserData), axis=0)
                outputData = np.concatenate((outputData, winnerOutput, loserOutput), axis=0)

                self.noise = min(1.0, self.noise - (1 - self.winRatio) * 0.01)
                self.game.players[chess.WHITE].noise = float(not self.rand) * self.noise
                self.game.players[chess.BLACK].noise = float(self.rand) * self.noise

            else:

                self.noise = min(1.0, self.noise + self.winRatio * 0.01)

        #train on the data
        self.currentNetwork.model.fit(x=inputData, y=outputData, batch_size=len(outputData))

    #play a game to its end, and return the outcome
    def playGame(self):

        self.rand = bool(round(random.random()))

        self.white = Players.Bot(chess.WHITE, self.currentNetwork, float(not self.rand) * self.noise)
        self.black = Players.Bot(chess.BLACK, self.currentNetwork, float(self.rand) * self.noise)
        self.game = Game.Game([self.black, self.white], display=True)

        while self.game.isEnd() == False:

            self.game.makeMove()

        #if the game ended in a win, return True
        if self.game.board.is_checkmate():

            return True
        
        else:

            return False
        
trainer = Trainer(1, games=1)

trainer.trainEpoch()