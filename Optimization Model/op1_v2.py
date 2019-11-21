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
import csv

def optModel(roomdata, S, E, A, B, G, SR=None):
    roomsIndex = list(range(0,len(roomdata.iloc[:,0])))
    m = Model('Rooms')
    x = m.addVars(roomsIndex,name="x",vtype=GRB.BINARY)
    d = m.addVar(0, name="d", vtype=GRB.CONTINUOUS)
    DearDaniel = 7
    m.setParam("TIME_LIMIT", 45)

    #E = data.iloc[3,10]
    #A = data.iloc[4,10]
    #B = data.iloc[5,10]
    #G = data.iloc[6,10]
    #S = data.iloc[2,10]
    if SR is None:
        SR = 1800
    #Available rooms  
    """x<= enddate & x>=startdate"""
    BoolInd = np.array([x>=float(startdate) for x in [float(a) for a in roomdata.columns.tolist()[11:]]])
    BoolInd2 = np.array([x<=float(enddate) for x in [float(a) for a in roomdata.columns.tolist()[11:]]])
    DateHeaders = [i+11 for i, x in enumerate(BoolInd&BoolInd2) if x]
    #print(IntInd)

    OccupiedRooms = roomdata.iloc[:, DateHeaders]
    OccupiedRoomsBool = np.sum(OccupiedRooms, axis=1)==1
    print(OccupiedRoomsBool)
    #print(OccupiedRooms)

    Orooms = roomdata.loc[OccupiedRoomsBool, :].index.values.tolist()
    Arooms = roomdata.loc[[not(a) for a in OccupiedRoomsBool],:]
    AroomsIndex = Arooms.index.values.tolist()
    print(Orooms)

    #Available rooms

    e = [0,1,2,40,41,42,43,44,106,107, 108, 109, 143, 23, 24,87]
    a = [39, 122, 123]
    b = [102,103,104,105,137,138,139]
    g = np.setdiff1d(roomsIndex,e+a+b)

    m.setObjective((quicksum(x[i] * roomdata.iloc[i,2] for i in roomsIndex))+ DearDaniel*d ,GRB.MINIMIZE)
    #space requirment
    #m.addConstr(quicksum(x[i] * data.iloc[i,1] for i in roomsIndex)>= S)
    #no occupied room
    m.addConstr(sum(x[i] for i in Orooms) == 0)
    #Exhibit hall is provided while requested 
    m.addConstr(sum(x[i] for i in e)>= E)
    #Auditorium is provided while requested
    m.addConstr(sum(x[i] for i in a)>= A)
    #Ballroom is provided while requested
    m.addConstr(sum(x[i] for i in b)>= B)
    #Meeting Rooms 
    m.addConstr(sum(x[i] for i in g)>= G)
    #if E is selected, Meeting room in that can't be selected
    m.addConstr((x[2]*(x[4]+x[5]+x[3]))==0)
    m.addConstr((x[40]*(x[46]+x[47]+x[45]))==0)
    m.addConstr((x[106]*(x[112]+x[113]+x[110]+x[111]))==0)
    m.addConstr(x[142]*(x[13]+x[14])==0)
    m.addConstr(x[78]*(x[79]+x[80])==0)
    m.addConstr(x[94]*(x[95]+x[96])==0)
    #Min SQFT
    m.addConstrs(x[i] == 0 for i in roomsIndex if roomdata.iloc[i,1] < SR)
    #distance stuff
    pRooms = [(Arooms.iloc[i,7],Arooms.iloc[i,8],Arooms.iloc[i,9],Arooms.iloc[i,10]) for i in range(len(AroomsIndex))]
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

    if m.status == GRB.Status.OPTIMAL or m.status == GRB.Status.TIME_LIMIT:
        x_sol = m.getAttr('x', x)    
        chosenroom = []
        chosenbuild = []
        sumsqft = 0
        sumcost=0
        for i in roomsIndex:
            if round(x_sol[i])>= 1:
                chosenroom.append(roomdata.iloc[i,0])
                chosenbuild.append(roomdata.iloc[i,3])
                sumsqft = sumsqft + roomdata.iloc[i,1]
                sumcost = sumcost + roomdata.iloc[i,2]
#        #Chosen is the list of room selected
#        
        for i in range(len(chosenbuild)):
            if chosenbuild[i] == 0:
               chosenbuild[i] = "A"
            elif chosenbuild[i]== 200:
               chosenbuild[i] = "B"
            else:
               chosenbuild[i] = "C"
        chosenbuild = set(chosenbuild)  
    else:
    	sumcost = 0
    	chosenroom = []  
#        print(chosenbuild)
#       if len(chosenroom) == 1:
#            print('{} is selected.'.format(chosenroom[0]))
#        else :
#           print('{} are selected.'.format(tuple(chosenroom)))
#        print('the sqft is {}'.format(sumsqft))
#        print('The room cost is {}'.format(sumcost))
#        print('The total cost is {}'.format(m.objVal))
    m.reset()
    return [sumcost, chosenroom]

if __name__ == "__main__":
	eventdata = pd.read_csv('TestData_v2.csv', index_col=0, header=0)
	roomdata = pd.read_csv('RoomInfo.csv', index_col=0, header=0)
	roomdata = roomdata[:143]
	csvOut = [['Cost', 'Rooms']]
	for i in range(0, len(eventdata)):
		startdate = eventdata.iloc[i, 3]
		enddate = eventdata.iloc[i, 4]
		optOut = optModel(roomdata, eventdata.iloc[i, 5], eventdata.iloc[i, 6], eventdata.iloc[i, 7], eventdata.iloc[i, 8], eventdata.iloc[i, 9], eventdata.iloc[i, 10])
		csvOut = csvOut + [optOut]
		
		BoolInd = np.array([x>=float(startdate) for x in [float(a) for a in roomdata.columns.tolist()[11:]]])
		BoolInd2 = np.array([x<=float(enddate) for x in [float(a) for a in roomdata.columns.tolist()[11:]]])
		IntInd = [i+11 for i, x in enumerate(BoolInd&BoolInd2) if x]
		print(IntInd)
		for a in optOut[1]:
			val = [a is b for b in roomdata.iloc[:, 0]]
			roomInd = [a for a, i in enumerate(val) if i]
			roomdata.iloc[roomInd, IntInd] = 1

			
	roomdata.to_csv('justforme.csv')
	with open('NewDataRoomsSelected.csv','w', newline="") as out:
		csv_out = csv.writer(out)
		for a in csvOut:
			csv_out.writerow(a)

    #if S> upper bound, return all the room  