from betting import bettingapp
from obsdriver import obsdriver

if __name__ == "__main__":
    obsdriver.Initialize()
    bettingapp.InitializeAndRun()