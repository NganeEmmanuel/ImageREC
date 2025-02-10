import configparser
import hashlib

from CloudServer.database_manager import db_config

CONFIG_FILE = "../../auth_config.ini"


# Initialize config file
def initialize_config():
    config = configparser.ConfigParser()
    config['User'] = {
        'username': '',
        'email': '',
        'password': ''
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def hash_password(password):
    """Returns the SHA256 hash of a password."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, email, password):
    """Registers a new user in the database."""
    connection = db_config.create_connection()
    if not connection:
        print("Database connection failed.")
        return False

    hashed_password = hash_password(password)
    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"

    cursor = connection.cursor()
    try:
        cursor.execute(query, (username, email, hashed_password))
        connection.commit()
        print("New user registered successfully.")
        return True
    except Exception as e:
        print(f"Error registering user: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def authenticate_user(username, email, password):
    """
    Authenticates the user based on the config file and database.
    If the user doesn't exist, it registers the user and authenticates.
    """

    if not username or not email or not password:
        print("Error: Configure email, username, and password.")
        return False

    connection = db_config.create_connection()
    if not connection:
        print("Database connection failed.")
        return False

    hashed_password = hash_password(password)
    query_check_user = "SELECT * FROM users WHERE email = %s"
    cursor = connection.cursor()

    try:
        # Check if user exists
        cursor.execute(query_check_user, (email,))
        user = cursor.fetchone()

        if user:
            # User exists, check password
            if user[3] == hashed_password:  # Assuming password_hash is the 4th column
                print("User authenticated successfully.")
                return True
            else:
                print("Wrong credentials.")
                return False
        else:
            # User does not exist, register new user
            if register_user(username, email, password):
                print("New user authenticated successfully.")
                return True
            else:
                print("Failed to register new user.")
                return False

    except Exception as e:
        print(f"Error during authentication: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
