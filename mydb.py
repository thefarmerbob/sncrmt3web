import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="S4mplePassword#3m4r3u3(beta)",
)

cursorObject = mydb.cursor()

cursorObject.execute("CREATE DATABASE db")

print("Database created")