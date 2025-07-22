import pyodbc

def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=AYAN\SQLEXPRESS;'  
        'DATABASE=cricket_tournament_management_system;'  
        'Trusted_Connection=yes;'
    )
    return conn
