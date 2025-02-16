import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",  # MySQL host
        user="root",       # Your MySQL username
        password="ajmal203",   # Your MySQL password
        database="expense_tracker"  # The name of your database
    )
