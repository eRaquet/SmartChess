import numpy as np
import keras
from keras import layers
import sys
import csv
import time

path = sys.path[0]
path = path[0 : len(path) - 8]

class Model ():

    #initiate a neural network with a certain shape
    def __init__(self, dim=None, offset=None):
            
        if dim != None:

            self.inputLayer = keras.Input(dim[0], dtype='bool')
            x = self.inputLayer
            
            #create my hidden layers
            for i in range(1, len(dim) - 1):

                x = layers.Dense(dim[i], 'gelu')(x)

            self.outputLayer = layers.Dense(dim[len(dim) - 1], 'tanh')(x)

            self.model = keras.Model(inputs=self.inputLayer, outputs=self.outputLayer, name='boardEval')
            self.opt = keras.optimizers.Adam(learning_rate = 0.00001)
            self.model.compile(optimizer=self.opt, loss='mean_absolute_error', run_eagerly=True)

        elif offset != None:

            self.loadModel(offset)

    def saveModel(self):

        with open(path + '\\savedNetworks\\config.csv') as netConfig:

            read = csv.reader(netConfig)
            
            #extract game number from row with text (for some reason there are empty rows!)
            for row in read:
                if row != []:
                    netNum = int(row[0])

        netConfig.close()

        self.model.save(path + '\\savedNetworks\\model_' + str(netNum) + '.keras')

        with open(path + '\\savedNetworks\\config.csv', 'w') as netConfig:

            write = csv.writer(netConfig)
            write.writerow([str(netNum + 1)])

        netConfig.close()

    def loadModel(self, indexOffset):

        with open(path + '\\savedNetworks\\config.csv') as netConfig:

            read = csv.reader(netConfig)
            
            #extract game number from row with text (for some reason there are empty rows!)
            for row in read:
                if row != []:
                    netNum = int(row[0])

        netConfig.close()

        if netNum >= indexOffset + 1:

            index = netNum - indexOffset - 1

        else:

            index = netNum - 1

        self.model = keras.models.load_model(path + '\\savedNetworks\\model_' + str(index) + '.keras')