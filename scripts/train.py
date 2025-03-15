#Test script: train the network for a certain volume of games

import lib.Trainer as Trainer

trainer = Trainer.Trainer()

# meant to be terminated by keyboard interrupt
while True:
    # train one model iteration
    trainer.trainSession(5, 140)
