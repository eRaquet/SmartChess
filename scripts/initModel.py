#Test script: initiate and save a 'model_0.keras' file
#used for restarting with a new training method

import lib.Network as Network
import sys
import json

path = sys.path[0]
path = path[0 : len(path) - 8]

for i in range(0, 10):
    model = Network.Model((100, 70, 40, 10))
    model.model.save_weights(path + '/savedNetworks/model_' + str(i) + '.weights.h5')
    if i == 0:
        with open(path + '/savedNetworks/model_format.json', 'w') as f:
            json.dump(model.model.to_json(), f)
        f.close()