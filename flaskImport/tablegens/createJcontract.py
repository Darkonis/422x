DB_USERNAME = 'admin'
DB_PASSWORD = 'adminpass'
DB_NAME = 'photogallerydb'

conn = MySQLdb.connect(host = "mysql-db-instance.cm4jqnr18t4s.us-east-2.rds.amazonaws.com",
                        user = DB_USERNAME,
                        passwd = DB_PASSWORD,
                        db = DB_NAME,
                        port = 3306)

cursor = conn.cursor ()
cursor.exectue ("SELECT VERSION()")

cursor.exectue ("CREATE TABLE contract ( \
    ListID int PRIMARY KEY NOT NULL AUTO_INCREMENT, \
    UID INTEGER NOT NULL, \
    FORIEGN KEY(UID) REFERENCES Users(UID), \
    Term TEXT NOT NULL, \
    Company TEXT NOT NULL, \
    Experience TEXT NOT NULL, \
    Type TEXT NOT NULL, \
    WageType int NOT NULL, \
    Rate int NOT NULL, \
    Remote int NOT NULL, \
    City TEXT NOT NULL, \
    Phone TEXT NOT NULL \
);")

cursor.close ()
conn.close ()