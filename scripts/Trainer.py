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

    def __init__(self, games=10, winRatio=0.8, save=4, networkOffset=0, startNoise=0.2):

        self.gamesPerEpoch = games
        self.winRatio = winRatio
        self.saveFraction = save
        self.noise = startNoise

        self.currentNetwork = Network.Model(offset=networkOffset)

    #train an entire session
    def trainSession(self, epochs):

        saveCount = 0
        epochCount = 0

        self.wins = 0
        self.games = 0

        #train each epoch of games
        while epochCount < epochs:
            
            self.trainEpoch()

            saveCount += 1
            if saveCount == self.saveFraction:
                self.currentNetwork.saveModel()
                saveCount = 0

            print(self.wins / self.games)

            epochCount += 1

        if (saveCount != 0):
            self.currentNetwork.saveModel()
    
    #train one epoch of games
    def trainEpoch(self):

        inputData = np.ndarray((0, 769), np.bool_)
        outputData = np.ndarray(0)

        winCount = 0

        while winCount != self.gamesPerEpoch:

            outcome = self.playGame()
            print(outcome)

            self.games += 1

            if outcome == True:

                self.wins += 1
                winCount += 1
                winner = not self.game.board.turn

                #get dataset
                winnerData = self.game.players[winner].boardStack
                loserData = self.game.players[winner].boardStack
                winnerOutput = np.ones(len(winnerData))
                loserOutput = -np.ones(len(loserData))
                inputData = np.concatenate((inputData, winnerData, loserData), axis=0)
                outputData = np.concatenate((outputData, winnerOutput, loserOutput), axis=0)

                self.noise = min(1.0, self.noise - (1 - self.winRatio) * 0.01)
                self.game.players[chess.WHITE].noise = float(not self.rand) * self.noise
                self.game.players[chess.BLACK].noise = float(self.rand) * self.noise

            else:

                self.noise = min(1.0, self.noise + self.winRatio * 0.01)

        #train on the data
        self.currentNetwork.model.fit(x=inputData, y=outputData, batch_size=len(outputData), epochs=3)

    #play a game to its end, and return the outcome
    def playGame(self):

        self.rand = bool(round(random.random()))

        self.white = Players.Bot(chess.WHITE, self.currentNetwork, float(not self.rand) * self.noise)
        self.black = Players.Bot(chess.BLACK, self.currentNetwork, float(self.rand) * self.noise)
        self.game = Game.Game([self.black, self.white], display=False)

        while self.game.isEnd() == False:

            self.game.makeMove()

        #if the game ended in a win, return True
        if self.game.board.is_checkmate():

            return True
        
        else:

            return False
        
trainer = Trainer(games=1)

trainer.trainSession(10)