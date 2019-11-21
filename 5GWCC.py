from flask import Flask, render_template, request, url_for, redirect, json, g, session
import re
import sqlite3
import pandas as pd 
import numpy as np
import math
import datetime as DT 
import lightgbm as lgb
from gurobipy import Model,GRB,quicksum
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super secret key"
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("5GWCC.db")
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    #Close connection
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def get_EventsDB():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("5Events.db")
    db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connectionEvents(exception):
    #Close connection
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

@app.route("/test")
def test():
    return render_template('test.html')

@app.route("/calendar-page")
def calendar():
    return render_template('calendar-page.html')

@app.route("/home-page")
def homepage():
    #Load home-page
    return render_template('home-page.html')

@app.route("/")
def loginpage():
    #Load login-page
    return render_template('login-page.html')


@app.route("/roompage")
def roompage():
    data = request.args.get("data")
    eventInfo = request.args.get("eventInfo")
    return render_template("room-page.html", data=data,  eventInfo=eventInfo)


@app.route("/outputpage")
def outputpage():
    cost = request.args.get("cost")
    margin = request.args.get("margin")
    eventName = request.args.get("eventName")
    eventID = request.args.get("eventID")
    dfMargins = pd.read_csv("marginFinal.csv")
    cluster = request.args.get("cluster")
    demand = int(request.args.get("demand"))
    dfTypeDemand = dfMargins[(dfMargins["Cluster"]==cluster) & (dfMargins["Demand"]==demand)] 
    marginList  = dfTypeDemand["PM"].values.tolist()
    #return render_template("home-page.html")
    return render_template("output-page.html", cost=cost, margin=margin, eventName=eventName, eventID=eventID, marginList = json.dumps(marginList))

@app.route("/search", methods=["POST"])
def search():
    eventId = request.form['eventId']
    try:
        eventInfo = transQueryEvents("SELECT * FROM EVENTS WHERE eventId = ?", [eventId])[0]
        status = "pass"
    except:
        status = "fail"
        eventInfo = ""
    return json.dumps({"eventInfo": eventInfo, "status": status})

@app.route("/remove", methods=["POST"])
def remove():
    eventId = request.form['eventId']
    eventInfo = insertQueryEvents("DELETE FROM EVENTS WHERE eventId = ?", [eventId])
    return json.dumps({"status": "deleted"})

@app.route("/search-page")
def searchpage():
    return render_template("search-page.html")

@app.route("/help-page")
def helppage():
    return render_template("help-page.html")

@app.route("/graph")
def graph():
    return render_template('graph.html')

def loginQuery(query, args=(), one=False):
    #Execute query for login and make sure credentials match in DB
    cur = get_db().cursor().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    #Return none if no result found; otherwise, return results (sqlite3 Rows)
    
    return (rv[0] if rv else None) if one else rv

@app.route('/loginCheck', methods=['POST', 'GET'])
def loginUser():
    #Extract form information for employee ID and password
    employeeId = request.form['empId']
    empPassword = request.form['password']

    #Use Regex to check if employee ID is 5 digits and not empty

    # #Check if employee ID exists in database
    res = loginQuery("SELECT employeeId FROM user WHERE employeeId = ?",
                        [employeeId])
    if res is None or len(res)==0:
         return json.dumps({"status": "BAD", "user": "Incorrect employee ID."})

    # #Check if password matches employee ID. If all above conditions are met, login user
    res2 = loginQuery("SELECT employeeId, empPassword FROM user WHERE employeeId = ? AND empPassword = ?",
                       [employeeId, empPassword])
    if res2 is None or len(res2)==0:
         return json.dumps({"status": "BAD", "user": "Incorrect password."})
    # else:
    session["empId"] = employeeId
    return json.dumps({"status": "OK", "user": "Logging in."})

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def transQueryEvents(query, args=(), one=False):
    #Execute query to extract all transaction history for current user
    con = get_EventsDB()
    con.row_factory = dict_factory
    cur = con.cursor().execute(query, args)
    rv = cur.fetchall()
    rv = [row for row in rv]
    cur.close()
    #Return none if no result
    #return (rv if rv else None) if one else rv
    return rv

def insertQueryEvents(query, args=(), one=False):
    #Execute query to extract all transaction history for current user
    con = get_EventsDB()
    cur = con.cursor().execute(query, args)
    con.commit()
    cur.close()

def transQuery(query, args=(), one=False):
    #Execute query to extract all transaction history for current user
    con = get_db()
    con.row_factory = dict_factory
    cur = con.cursor().execute(query, args)
    rv = cur.fetchall()
    rv = [row for row in rv]
    cur.close()
    #Return none if no result
    #return (rv if rv else None) if one else rv
    return rv

def excel_date(date1):
    temp = DT.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
    delta = date1 - temp
    return float(delta.days) + (float(delta.seconds) / 86400)

@app.route('/regmodel', methods=['POST', 'GET'])
def regmodel():
    eventInfo = {}

    #transQueryEvents("INSERT INTO EVENTS (eventID, name, type, startDate, endDate, attendance, sqft, roomNights, subDate, rooms, cost, baselinePrice)")

    eventInfo["sqftPerEvent"] = int(request.args.get("sqftPerEvent"))
    eventInfo["orderedRentTotal"] = int(request.args.get("orderedRentTotal"))
    eventInfo["Attendance"] = int(request.args.get("Attendance"))
    eventInfo["totalRoomNights"] = int(request.args.get("totalRoomNights"))
    eventInfo["FB"] = float(request.args.get("FB"))
    eventInfo["eventDuration"] = int(request.args.get("eventDuration"))
    eventInfo["contactTillStart"] = int(request.args.get("contactTillStart"))
    eventInfo["rooms"] = request.args.get("rooms").split(",")
    
    startDate = datetime.strptime(request.args.get("startDate"), "%Y-%m-%d")
    startDateExcel = int(excel_date(startDate))
    endDate = datetime.strptime(request.args.get("endDate"), "%Y-%m-%d")
    endDateExcel = int(excel_date(endDate))
    subDate = datetime.strptime(request.args.get("subDate"), "%Y-%m-%d")
    subDateExcel = int(excel_date(subDate))

    maxId = transQueryEvents("SELECT MAX(eventID) AS maxId FROM EVENTS")[0]["maxId"]+1

    X_train = pd.read_csv("X_train.csv", index_col=0)
    y_train = pd.read_csv("y_train.csv", index_col=0)

    lgbParams = {'subsample': 0.36000000000000004,
                        'reg_lambda': 0.7100000000000001,
                        'reg_alpha': 0.9,
                        'objective': 'regression_l1',
                        'num_leaves': 29,
                        'min_child_weight': 0.0001,
                        'max_depth': 10,
                        'learning_rate': 0.1,
                        'boosting': 'gbdt',
                        'n_estimators': int(np.ceil((330+93+43)/3))}
    
    lgbr = lgb.LGBMRegressor(**lgbParams)
    lgbr.fit(X_train, y_train)

    roomClassif = pd.read_csv("Rooms.csv")
    e = [0,1,2,40,41,42,43,44,106,107, 108, 109, 143, 23, 24,87]
    a = [39, 122, 123]
    b = [102,103,104,105,137,138,139]
    E_A = 0
    E_B = 0
    E_C = 0
    M_A = 0
    M_B = 0
    M_C = 0
    
    if len(roomClassif)>0:
        for room in eventInfo["rooms"]:
            roomMapped = roomClassif[roomClassif["Name"]==room]
            roomId = roomMapped["RoomID"].values[0]
            bldg = roomMapped["Building"].values[0]
            if(bldg==0):
                bldg="A"
            elif(bldg==200):
                bldg="B"
            else:
                bldg="C"
            

            if bldg=="A" and roomId in e:
                E_A += 1
            elif bldg=="B" and roomId in e:
                E_B += 1 
            elif bldg=="C" and roomId in e:
                E_C += 1
            if bldg=="A" and (roomId not in e and roomId not in a and roomId not in b):
                M_A += 1
            elif bldg=="B" and (roomId not in e and roomId not in a and roomId not in b):
                M_B += 1 
            elif bldg=="C" and (roomId not in e and roomId not in a and roomId not in b):
                M_C += 1
    eventInfo["E-A"] = E_A
    eventInfo["E-B"] = E_B
    eventInfo["E-C"] = E_C
    eventInfo["M-A"] = M_A
    eventInfo["M-B"] = M_B
    eventInfo["M-C"] = M_C
    
    del eventInfo["rooms"]
    
    cost = lgbr.predict(pd.Series(eventInfo).to_frame().T)
    eventInfo["eventType"] = request.args.get("eventType")
    eventInfo["dateIn"] = request.args.get("dateIn")
    

    mappingType = pd.read_csv("mappingTypes.csv")
    mappedType = mappingType[mappingType["Original"]==eventInfo["eventType"]]["New"].values
    if mappedType=="CHRTY" or mappedType=="GRAD":
        cluster = "CHRTY_GRAD"
    elif mappedType=="COMP":
        cluster = "COMP"
    elif mappedType=="CON" or mappedType=="P":
        cluster = "CON_P"
    elif mappedType=="CONF" or mappedType=="GAM":
        cluster = "CONF_GAM"
    elif mappedType=="CONV":
        cluster = "CONV"
    elif mappedType=="FILM" or mappedType=="AWC":
        cluster = "FILM_AWC"
    elif mappedType=="ME" or mappedType=="OTH":
        cluster = "ME_OTH"
    elif mappedType=="MEET":
        cluster = "MEET"
    elif mappedType=="PUB":
        cluster = "PUB"
    else:
        cluster = "SMALL"
    
    clusterPeak = pd.read_csv("clusterPeak.csv")
    demand = clusterPeak[(clusterPeak["Cluster"]==cluster) & (clusterPeak["Month"]==int(eventInfo["dateIn"]))]["Demand"].values[0]
    
    dfMargins = pd.read_csv("marginFinal.csv")
    dfTypeDemand = dfMargins[(dfMargins["Cluster"]==cluster) & (dfMargins["Demand"]==demand)] 
    if demand==0:
        suggMargin = np.percentile(dfTypeDemand["PM"].values, 45)
    elif demand==1:
        suggMargin = np.percentile(dfTypeDemand["PM"].values, 50)
    elif demand==2:
        suggMargin = np.percentile(dfTypeDemand["PM"].values, 55)
    
    eventName = request.args.get("eventName")
    insertQueryEvents('INSERT INTO EVENTS (eventID, name, type, startDate, endDate, attendance, sqft, roomNights, subDate, rooms, cost, baselinePrice) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    [maxId+1, eventName, eventInfo["eventType"], startDateExcel, endDateExcel, eventInfo["Attendance"], eventInfo["sqftPerEvent"], eventInfo["totalRoomNights"], subDateExcel, request.args.get("rooms"), float(cost), float(cost*(1+suggMargin))])
    return redirect(url_for('outputpage', cost=cost, margin=suggMargin, eventName=eventName, eventID=maxId+1, cluster=cluster, demand=demand))
    

@app.route('/optmodel', methods=['GET', 'POST'])
def optmodel():
#form need to be in html
    datein = request.form['startDate']
    dateout = request.form['endDate']
    nhall = int(request.form['ExhibitHalls'])
    nmeeting = int(request.form['MeetingRooms'])
    naudi = int(request.form['Auditorium'])
    nball = int(request.form['Ballrooms'])
    minsqft = int(request.form['Minsqft'])


    rooms=transQuery("SELECT * FROM ROOM")
    roomsDF = pd.DataFrame(rooms,columns=["RoomID","Name","Sqft","Cost","Building","Floor","X","Y"])
    roomsIndex = [int(i) for i in roomsDF["RoomID"]]
    convName = ["Sqft","Cost","Building","Floor","X","Y"]
    for name in convName:
        roomsDF[name] = pd.to_numeric(roomsDF[name], errors='ignore')
    OccupiedID = transQuery("SELECT RoomID FROM BOOKED WHERE dateIN BETWEEN ? AND ? AND dateout BETWEEN ? AND ?",(datein,dateout,datein,dateout,))
    OccupiedID = pd.DataFrame(OccupiedID,columns=["RoomID"])
    OccupiedID = [int(i) for i in OccupiedID["RoomID"]]

    Arooms = transQuery("SELECT * FROM ROOM WHERE RoomID NOT IN (SELECT RoomID FROM booked WHERE dateIN BETWEEN ? AND ? AND dateout BETWEEN ? AND ?)",(datein,dateout,datein,dateout,))
    #"SELECT * FROM ROOM WHERE RoomID NOT IN (SELECT RoomID FROM booked WHERE dateIN BETWEEN '2019-08-14' AND '2019-08-20' AND dateout BETWEEN '2019-08-14' AND '2019-08-20');"
    #[40, 41, 42, 106, 107, 108, 109, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 140, 141]
    AroomsDF = pd.DataFrame(Arooms,columns=["RoomID","Name","Sqft","Cost","Building","Floor","X","Y"])
    for name in convName:
        AroomsDF[name] = pd.to_numeric(AroomsDF[name], errors='ignore')
    # AroomsDF.astype({"Sqft":'float32',"Cost":'float32',"Building":'float32',"Floor":'float32',"X":'float32',"Y":'float32'})
    AroomsIndex = [int(i) for i in AroomsDF["RoomID"]]

    #MODEL
    m = Model('Rooms')
    m.setParam('TimeLimit',360)
    x = m.addVars(roomsIndex,name="x",vtype=GRB.BINARY)
    d = m.addVar(0, name="d", vtype=GRB.CONTINUOUS)
    DearDaniel = 7  
    e = [0,1,2,40,41,42,43,44,106,107, 108, 109, 143, 23, 24,87]
    a = [39, 122, 123]
    b = [102,103,104,105,137,138,139]
    g = np.setdiff1d(roomsIndex,e+a+b)
    m.setObjective((quicksum(x[i] * roomsDF.iloc[i,3] for i in roomsIndex)+ DearDaniel*d) ,GRB.MINIMIZE) 
    #no occupied room #need to change room id 
    m.addConstr(sum(x[i] for i in OccupiedID) == 0)
    m.addConstr(sum(x[i] for i in e)>= nhall)
    m.addConstr(sum(x[i] for i in a)>= naudi)
    m.addConstr(sum(x[i] for i in b)>= nball)
    m.addConstr(sum(x[i] for i in g)>= nmeeting)
    #if E is selected, Meeting room in that can't be selected
    m.addConstr((x[2]*(x[4]+x[5]+x[3]))==0)
    m.addConstr((x[40]*(x[46]+x[47]+x[45]))==0)
    m.addConstr((x[106]*(x[112]+x[113]+x[110]+x[111]))==0)  
    m.addConstr(x[142]*(x[13]+x[14])==0)
    m.addConstr(x[78]*(x[79]+x[80])==0)
    m.addConstr(x[94]*(x[95]+x[96])==0)
    #minimum room
    m.addConstrs(x[i] == 0 for i in AroomsIndex if roomsDF.iloc[i,2] < minsqft)
    #calculate the distance 
    pRooms = [(AroomsDF.iloc[i,4],AroomsDF.iloc[i,5],AroomsDF.iloc[i,6],AroomsDF.iloc[i,7]) for i in range(len(AroomsIndex))]
    Sum = 0
    distMat = np.empty([AroomsDF.shape[0], AroomsDF.shape[0]])
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
    
    m.addConstr(d == sum([((x[i]*x[j]) * distMat[i][j]) for i in range(len(AroomsIndex)) for j in range(len(AroomsIndex))]))
    m.optimize()

    if m.status == GRB.Status.OPTIMAL or m.status == GRB.Status.TIME_LIMIT:
        x_sol = m.getAttr('x', x)    
        """
        chosenroom = []
        chosenbuild = []
        sumsqft = 0
        sumcost=0
        for i in roomsIndex:
            if round(x_sol[i])>= 1:
                chosenroom.append(roomsDF.iloc[i,1])
                chosenbuild.append(roomsDF.iloc[i,4])
                sumsqft = sumsqft + roomsDF.iloc[i,2]
                sumcost = sumcost + roomsDF.iloc[i,3]
        
        for i in range(len(chosenbuild)):
            if chosenbuild[i] == 0:
               chosenbuild[i] = "A"
            elif chosenbuild[i]== 200:
               chosenbuild[i] = "B"
            else:
               chosenbuild[i] = "C"
        """
        rdict = {}
        choosenroomA = []
        choosenroomB = []
        choosenroomC = []
        for i in roomsIndex:
            if round(x_sol[i])>=1:
                if roomsDF.iloc[i,4] == 0:
                    choosenroomA.append(roomsDF.iloc[i,1]) 
                    rdict.update({"A":choosenroomA})
                elif roomsDF.iloc[i,4] == 200:
                    choosenroomB.append(roomsDF.iloc[i,1])
                    rdict.update({"B":choosenroomB})
                else:
                    choosenroomC.append(roomsDF.iloc[i,1])
                    rdict.update({"C":choosenroomC})
        costinput = [key for key in rdict.keys()]
              
    
    sqft = float(request.form['sqft'])
    rentTotal = float(request.form['RentTotal'])
    attendance = int(request.form["attendance"])
    roomNights = int(request.form["RoomNights"])
    foodBev = float(request.form['FB'])
    
    dateIn = datetime.strptime(datein, "%Y-%m-%d")
    dateOut = datetime.strptime(dateout, "%Y-%m-%d")
    eventName = request.form["EventName"]
    eventType = request.form["eventType"]
    subDate = request.form["RFPSubmission"]
    eventDuration = abs((dateOut - dateIn).days)
    
    rfpSubmission = datetime.strptime(request.form["RFPSubmission"], "%Y-%m-%d")
    contactTillStart = abs((dateIn-rfpSubmission).days)
    #eventDuration = dateout-datein
    dictEvent = {"sqftPerEvent": sqft, "orderedRentTotal": rentTotal,
                 "Attendance": attendance, "totalRoomNights": roomNights,
                 "FB": foodBev, "eventDuration": eventDuration, "contactTillStart": contactTillStart,
                 "rooms": rdict, "eventType": eventType, "dateIn": dateIn.month, "eventName": eventName,
                 "startDate": datein, "endDate": dateout, "subDate": subDate}
    
    
    return redirect(url_for('roompage', data=rdict, eventInfo=dictEvent))
    #return render_template("room-page.html",summary = rdict)

@app.route("/main-page")
def mainPage():
   return render_template("info-page.html")

@app.route("/submit")
def submit(): 
    #Extract event information" 
    eventName = request.form['eventName']
    numAttend = request.form['numAttend']
    eventType = request.fomr['eventType']
    return json.dumps({"Event Name": eventName, "Number of Attendees": numAttend}), render_template("main-page.html")

@app.route("/calendar-page")
def cal(): 
    return  render_template("calendar-page.html")




if __name__ == "__main__":
    app.run()
