import MySQLdb
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

cursor.execute ("ALTER TABLE photogallery2  \
    ADD COLUMN User TEXT AFTER URL \
    ;")

cursor.close ()
conn.close ()
