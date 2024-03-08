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

#the training breakdown (with apporpriate iterators at each stage):

#Trainer -- trainSession() -> trainEpoch() -> playBot() -> playGame()

class Trainer ():

    def __init__(self, networkOffset=0, startNoise=0.1, opponentNum=9, saveCount=5):

        self.noise = startNoise
        self.opponentNum = opponentNum
        self.saveCount = saveCount

        self.currentNetwork = Network.Model(offset=networkOffset)

        self.testPos = np.load(path + '\\testPositions\\testPositions.npy')
        self.testEval = np.load(path + '\\testPositions\\testEvaluations.npy')

    #train an entire session
    def trainSession(self, epochs, gameNum):

        epochCount = 0
        self.gamesPerEpoch = gameNum

        #train each epoch of games
        while epochCount < epochs:

            #count how many games we played that resulted in a victory
            self.games = 0
            
            self.trainEpoch()

            epochCount += 1

            #if we are due to update the network
            if epochCount % self.saveCount == 0:
                #save the current network
                self.currentNetwork.saveModel()

        #if we haven't just saved a network
        if epochCount % self.saveCount != 0:
            #save the current network
            self.currentNetwork.saveModel()


    #train one epoch of games (and create one new model)
    def trainEpoch(self):

        self.inputTrainData = np.ndarray((0, 769), np.bool_)
        self.outputTrainData = np.ndarray(0)

        #define an array that keeps track of how many wins the current model has had against other models
        #this is to be compared with the array of scheduled games
        self.winsPerBot = np.zeros(self.opponentNum, int)

        #the list of bots that have already been loaded into the session
        #indexed by offset value (loadedBots[n] => model_"(maxIndex - n)".keras)
        self.loadedBots = []

        #generate the scheduled games
        self.gameSchedule = getGameDist(self.gamesPerEpoch, self.opponentNum)

        self.botOffset = 0

        while self.botOffset != self.opponentNum:

            #load opponent bot (first one will be self)
            self.loadedBots.append(Network.Model(offset=self.botOffset))

            #play all the games against one bot
            self.playBot(self.gameSchedule[self.botOffset])

            #save game for loging purposes
            self.game.saveGame()

            self.botOffset += 1

        self.verifyTraining()

        #train on the data
        self.currentNetwork.model.fit(x=self.inputTrainData, y=self.outputTrainData, batch_size=len(self.outputTrainData), epochs=14, verbose=0)

        self.verifyTraining()

        self.validate()

    #play all the games against one specific bot and add the data to the training data
    def playBot(self, gameNum):

        winCount = 0

        while winCount != gameNum:

            #play a game against the current bot (using implicit pass of botOffset from trainEpoch())
            outcome = self.playGame()

            self.games += 1

            if outcome:
                winCount += 1
                winner = not self.game.board.turn

                #get dataset
                winnerData = self.game.players[winner].positions
                loserData = self.game.players[not winner].positions

                #I can't use a fixed offset (-1 or 1) for my evaluation, because worse positions will receive higher gradients.
                #I can't use logged evaluations, because they may conform my network to previous versions.

                #The best strategy will be to evaluate all the positions with the current network, and accept the error between
                #different models choices.

                winnerEvaluations = self.currentNetwork.model.predict_on_batch(np.array(self.game.players[winner].positions)).T[0]
                loserEvaluations = self.currentNetwork.model.predict_on_batch(np.array(self.game.players[not winner].positions)).T[0]

                #apply correction to the model
                winnerOutput = np.clip(winnerEvaluations + rewardVal(len(winnerData)), -1.0, 1.0)
                loserOutput = np.clip(loserEvaluations - rewardVal(len(loserData)), -1.0, 1.0)
                self.inputTrainData = np.concatenate((self.inputTrainData, winnerData, loserData), axis=0)
                self.outputTrainData = np.concatenate((self.outputTrainData, winnerOutput, loserOutput), axis=0)

                #check if the bot that one was the main bot
                if (self.rand == winner):
                    #add one to the appropriate tally
                    self.winsPerBot[self.botOffset] += 1

        #record how many times the mainBot won over the contender
        #(for recording purposes)
        

    #play a game to its end, and return the outcome
    def playGame(self):

        #define a random value to determine which bot gets which color
        self.rand = bool(round(random.random()))

        #main bot gets white
        if self.rand:
            whiteBot = self.currentNetwork
            blackBot = self.loadedBots[self.botOffset]
        #main bot gets black
        else:
            whiteBot = self.loadedBots[self.botOffset]
            blackBot = self.currentNetwork

        self.white = Players.Bot(chess.WHITE, whiteBot, self.noise)
        self.black = Players.Bot(chess.BLACK, blackBot, self.noise)
        self.game = Game.Game([self.black, self.white], display=False)

        while self.game.isEnd() == False:

            self.game.makeMove()

        #if the game ended in a win, return True
        if self.game.board.is_checkmate():

            return True
        
        else:

            return False
        
    #check how well the model conformed to the training
    def verifyTraining(self):

        cost = keras.losses.mean_absolute_error(self.outputTrainData, self.currentNetwork.model.predict_on_batch(np.array(self.inputTrainData)).T[0])
        print('Current loss on training set: ' + str(cost.numpy()))

    #test the network on some archived positions (not for training...just a way to reality check)
    def validate(self):

        print('Current loss on testing set: ' + str(self.currentNetwork.model.evaluate(self.testPos, self.testEval)))

#get a distibution of opponents given a number of games to play (play better bots more)
def getGameDist(gameNum, opponentNum):
    gameList = np.zeros(opponentNum)
    for i in range(0, opponentNum):
        gameList[i] = gameDist(i, opponentNum)
    gameList = (gameList * gameNum).astype(int)
    return gameList

#game distibution function --> used in getGameDist
def gameDist(index, n):

    #adjust index to function to a midpoint rectagular approximation
    index += 0.5
    return (-2 / n**2) * index + (2 / n)

#reward function
def rewardVal(length):

    #a constant term and a dependant term
    value = 0.2 - (0.2 / 60) * length
    return max(value, 0.02)