import matplotlib.pyplot as plt
import matplotlib.animation as animation

class Plot:
    def __init__(self, data, labels):
        self.data = data
        self.labels = labels
        self.fig, self.ax = plt.subplots()

    def show(self):
        self.ax.cla()
        for i in range(len(self.data)):
            self.ax.plot(range(len(self.data[i])), self.data[i], label=self.labels[i])
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.legend()
        plt.draw()
        plt.pause(0.01)
    
    def close(self):
        plt.close("all")
