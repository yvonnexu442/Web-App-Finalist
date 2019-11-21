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



.separator ,
.import loginCredentials.csv user
.import Rooms.csv ROOM
.import OccupiedRoomsData.csv BOOKED
