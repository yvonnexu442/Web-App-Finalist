#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 11:51:14 2019

@author: apple
""" 
import pandas as pd 
import numpy as np
import math
from gurobipy import Model,GRB,quicksum

data = pd.read_csv('opt1.csv', index_col=0, header=0)
roomsIndex = list(range(0,len(data.iloc[:,0])))

m = Model('Rooms')
x = m.addVars(roomsIndex,name="x",vtype=GRB.BINARY)
d = m.addVar(0, name="d", vtype=GRB.CONTINUOUS)
DearDaniel = 7

#S = data.iloc[2,10]
E = data.iloc[3,10]
print(type(E))
A = data.iloc[4,10]
B = data.iloc[5,10]
G = data.iloc[6,10]
SR = data.iloc[7,10]
#Available rooms  
Arooms = data.loc[data['Occupied'] == 0]
AroomsIndex = data.loc[data['Occupied'] == 0].index.values.tolist()
Orooms = data.loc[data['Occupied'] == 1].index.values.tolist()
#Available rooms

e = [0,1,2,40,41,42,43,44,106,107, 108, 109, 143, 23, 24,87]
a = [39, 122, 123]
b = [102,103,104,105,137,138,139]
g = np.setdiff1d(roomsIndex,e+a+b)

m.setObjective((quicksum(x[i] * data.iloc[i,2] for i in roomsIndex)+ DearDaniel*d) ,GRB.MINIMIZE)
#space requirment
#m.addConstr(quicksum(x[i] * data.iloc[i,1] for i in roomsIndex)>= S)
#no occupied room
m.addConstr(sum(x[i] for i in Orooms) == 0)
#Exhibit hall is provided while requested 
m.addConstr(sum(x[i] for i in e) == E)
#Auditorium is provided while requested
m.addConstr(sum(x[i] for i in a) == A)
#Ballroom is provided while requested
m.addConstr(sum(x[i] for i in b) == B)
#Meeting Rooms 
m.addConstr(sum(x[i] for i in g) == G)
#if E is selected, Meeting room in that can't be selected
m.addConstr((x[1]*(x[4]+x[5]+x[3]))==0)
m.addConstr((x[40]*(x[46]+x[47]+x[45]))==0)
m.addConstr((x[106]*(x[112]+x[113]+x[110]+x[111]))==0)
m.addConstr(x[142]*(x[13]+x[14])==0)
m.addConstr(x[78]*(x[79]+x[80])==0)
m.addConstr(x[94]*(x[95]+x[96])==0)
#Min SQFT
m.addConstrs(x[i] == 0 for i in roomsIndex if data.iloc[i,1] < SR)
#distance stuff
pRooms = [(Arooms.iloc[i,3],Arooms.iloc[i,4],Arooms.iloc[i,5],Arooms.iloc[i,6]) for i in range(len(AroomsIndex))]

Sum = 0
distMat = np.empty([len(Arooms), len(Arooms)])
i = 0
while i < len(Arooms):
    room1 = pRooms[i]
    j = i
    while j < len(Arooms):
        room2 = pRooms[j]
        adiff = [((room1[k] - room2[k])**2) for k in range(4)]
        dist = math.sqrt(sum(adiff))
        distMat[i][j] = dist
        distMat[j][i] = dist
        Sum += dist
        j+=1
    i+=1
   
#distance calculation
m.addConstr(d == sum([((x[i]*x[j]) * distMat[i][j]) for i in range(len(AroomsIndex)) for j in range(len(AroomsIndex))]))
m.optimize()

if m.status == GRB.Status.OPTIMAL:
    x_sol = m.getAttr('x', x)    
    #d_sol = d.getAttr
    chosen = []
    sumsqft = 0
    sumcost=0
    for i in roomsIndex:
        if round(x_sol[i])>= 1:
            chosen.append(data.iloc[i,0])
            sumsqft = sumsqft + data.iloc[i,1]
            sumcost = sumcost + data.iloc[i,2]
    if len(chosen) == 1:
        print('{} is selected.'.format(chosen[0]))
    else :
        print('{} are selected.'.format(tuple(chosen)))
    print('the sqft is {}'.format(sumsqft))
    print('The room cost is {}'.format(sumcost))
    print('The total cost is {}'.format(m.objVal))

#if S> upper bound, return all the room 