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

cursor.execute ("CREATE TABLE lookingwork ( \
    ListID int PRIMARY KEY NOT NULL AUTO_INCREMENT, \
    UID INTEGER NOT NULL, \
    FORIEGN KEY(UID) REFERENCES Users(UID), \
    Type TEXT NOT NULL, \
    Resume TEXT NOT NULL, \
    Experience TEXT NOT NULL, \
    Industry TEXT NOT NULL, \
    Salary int NOT NULL, \
    Remote int NOT NULL, \
    City TEXT NOT NULL, \
    Phone TEXT NOT NULL \
);")

cursor.close ()
conn.close ()