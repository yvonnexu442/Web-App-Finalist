DROP TABLE ROOM;
DROP TABLE BOOKED;

CREATE TABLE ROOM(
    RoomID          INTEGER PRIMARY KEY,
    Name            TEXT NOT NULL,
    Sqft            INTEGER NOT NULL,
    Cost            INTEGER NOT NULL,
    Coordinate      TEXT NOT NULL
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
.import Rooms.csv ROOM
.import OccupiedRoomsData.csv BOOKED

/* SELECT * FROM BOOKED WHERE DATE(DateIn) > DATE('2019-08-12');*/