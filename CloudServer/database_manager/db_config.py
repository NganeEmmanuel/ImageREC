import mysql.connector
from mysql.connector import Error


def create_connection():
    """
    Establishes a connection to the MySQL database.
    Returns a connection object if successful, None otherwise.
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3307,
            user='root',  # Replace with your MySQL username
            password='',  # Replace with your MySQL password
            database='imagerec'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
