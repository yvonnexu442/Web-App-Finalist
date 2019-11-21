# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 16:43:37 2019

@author: Danie
"""

import pandas as pd
import numpy as np

data = pd.read_csv('FutureEvents.csv', index_col=0, header=0)
#print(data)
newCSVData = [];
for i in range(0, len(data)):
    roomVec = data.iloc[i, 3:]
    #print(roomVec)
    roomVec = roomVec[roomVec.notna()]
    for j in range(0, len(roomVec)):
        newCSVData = newCSVData + [[roomVec[j], data.iloc[i, 1], data.iloc[i, 2]]]
print (newCSVData)
df = pd.DataFrame(np.array(newCSVData), columns=['Room Name', 'DateIn', 'DateOut'])
df.to_csv('Occupied.csv')
    
