DB_USERNAME = 'admin'
DB_PASSWORD = 'adminpass'
DB_NAME = 'photogallerydb'

conn = MySQLdb.connect(host = "mysql-db-instance.cm4jqnr18t4s.us-east-2.rds.amazonaws.com",
                        user = DB_USERNAME,
                        passwd = DB_PASSWORD,
                        db = DB_NAME,
                        port = 3306)

cursor = conn.cursor ()
cursor.execute ("SELECT VERSION()")

cursor.execute ("CREATE TABLE sport ( \
    ListID int PRIMARY KEY NOT NULL AUTO_INCREMENT, \
    UID INTEGER NOT NULL, \
    FORIEGN KEY(UID) REFERENCES Users(UID), \
    AvailableTimes TEXT NOT NULL, \
    Organization TEXT NOT NULL, \
    Boss TEXT NOT NULL, \
    Type TEXT NOT NULL, \
    Price int NOT NULL, \
    Description TEXT NOT NULL, \
    City TEXT NOT NULL, \
    Phone TEXT NOT NULL \
);")

cursor.close ()
conn.close ()