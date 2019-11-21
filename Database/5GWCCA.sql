DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS ROOM;
DROP TABLE IF EXISTS BOOKED;
-- DROP TABLE IF EXISTS transactions;
-- DROP TABLE IF EXISTS items;

CREATE TABLE user(
    employeeId TEXT NOT NULL,
    empPassword TEXT NOT NULL
);

CREATE TABLE ROOM(
    RoomID          INTEGER PRIMARY KEY,
    Name            TEXT NOT NULL,
    Sqft            INTEGER NOT NULL,
    Cost            INTEGER NOT NULL,
    Building        INTEGER NOT NULL,
    Floor           INTEGER NOT NULL,
    X               INTEGER NOT NULL,
    Y               INTEGER NOT NULL,
);

CREATE TABLE BOOKED(
	RoomID		    INTEGER NOT NULL,
    Name            TEXT NOT NULL,
	DateIN		    INTEGER NOT NULL,
	DateOut			INTEGER NOT NULL,
	PRIMARY KEY (RoomID,DateIn,DateOut),
    FOREIGN KEY(RoomID) REFERENCES ROOM(RoomID)
        ON DELETE CASCADE ON UPDATE CASCADE
); 



-- CREATE TABLE items(
--     itemId INTEGER PRIMARY KEY NOT NULL,
--     itemName TEXT,
--     restaurant TEXT,
--     isSide BOOLEAN,
--     calories FLOAT,
--     protein FLOAT,
--     fat FLOAT,
--     carb FLOAT,
--     fiber FLOAT,
--     sugar FLOAT,
--     calcium FLOAT,
--     iron FLOAT,
--     phosphorous FLOAT,
--     sodium FLOAT,
--     vitaminA FLOAT,
--     vitaminC FLOAT,
--     cholesterol FLOAT,
--     isMeal BOOLEAN
-- );

-- CREATE TABLE transactions(
--     transactionId INTEGER PRIMARY KEY NOT NULL,
--     employeeID INTEGER NOT NULL,
--     dateTrans TEXT NOT NULL,
--     itemId INTEGER NOT NULL,
--     FOREIGN KEY(employeeID) REFERENCES user(employeeId),
--     FOREIGN KEY(itemId) REFERENCES items(itemId)
-- );

.separator ,
--.import loginCredentials.csv user
.import Rooms.csv ROOM
.import OccupiedRoomsData.csv BOOKED

-- .import itemInfo.csv items
-- .import transactions.csv transactions