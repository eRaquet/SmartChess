#Test script: initiate and save a 'model_0.keras' file
#used for restarting with a new training method

import lib.Network as Network
import sys

path = sys.path[0]
path = path[0 : len(path) - 8]

for i in range(0, 10):
    model = Network.Model((769, 1000, 40, 1))
    model.model.save(path + '\\savedNetworks\\model_' + str(i) + '.keras')