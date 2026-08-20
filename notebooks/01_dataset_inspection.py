import os
import pandas as pd

folder = "datasets/NASA"

for root, dirs, files in os.walk(folder):
    for file in files:
        print(os.path.join(root, file))