from CloudServer.database_manager import db_config


def initialize_database():
    """Create the necessary tables in the MySQL database."""
    conn = db_config.create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            request_id VARCHAR(36) PRIMARY KEY,
            request_date DATETIME NOT NULL,
            user_email VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_id VARCHAR(36) NOT NULL,
            result TEXT NOT NULL,
            processed_date DATETIME NOT NULL,
            user_email VARCHAR(255) NOT NULL,
            FOREIGN KEY(request_id) REFERENCES requests(request_id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def add_request(request_id, user_email, model_name, action_type):
    """Add a new request to the database."""
    conn = db_config.create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO requests (request_id, user_email, model_name, action_type) 
        VALUES (%s, %s,%s,%s)
    """, (request_id, user_email, model_name, action_type))
    conn.commit()
    cursor.close()
    conn.close()


def update_request_status(request_id, status):
    """Update the status of a request in the database."""
    conn = db_config.create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE requests SET status = %s 
    WHERE request_id = %s""", (status, request_id))
    conn.commit()
    cursor.close()
    conn.close()


def get_request(request_id, user_email):
    """
    Get request from the database.
        :param request_id: (str): The ID of the request.
        :param user_email: (str): The user's emails.
        :return: (str): The requested request.

    """
    conn = None
    cursor = None
    try:
        conn = db_config.create_connection()
        if not conn:
            print("Failed to establish database connection.")
            return None
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT model_name, action_type 
            FROM requests
            WHERE request_id = %s AND user_email = %s""", (request_id, user_email)
        )
        result = cursor.fetchone()
        print(f"Query result: {result}")
        return result
    except Exception as e:
        print(f"Error for request {request_id}: {e}")
        return None
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"Error closing cursor: {e}")
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing connection: {e}")


def get_all_requests(user_email):
    """Get all requests in the database for a given user."""
    conn = None
    cursor = None
    try:
        conn = db_config.create_connection()
        if not conn:
            print("Failed to establish database connection.")
            return []
        cursor = conn.cursor(dictionary=True)  # Use dictionary cursor
        cursor.execute("""
        SELECT request_id, status, request_date FROM requests 
        WHERE user_email = %s""", user_email)
        results = cursor.fetchall()
        print(f"Query results: {results}")
        return results
    except Exception as e:
        print(f"Error fetching requests: {e}")
        return []
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"Error closing cursor: {e}")
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing connection: {e}")




def add_result(request_id, result, user_email):
    """Add a new result to the database."""
    conn = db_config.create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO results (request_id, result, user_email) 
        VALUES (%s, %s, %s)
    """, (request_id, result, user_email))
    conn.commit()
    cursor.close()
    conn.close()


def get_result_by_request_id(request_id):
    """Retrieve the result associated with a specific request ID.
        Fetches the processing result for a given request_id from the database.
    """
    connection = db_config.create_connection()
    if not connection:
        raise Exception("Database connection failed.")

    query = "SELECT result FROM results WHERE request_id = %s"
    cursor = connection.cursor()

    try:
        cursor.execute(query, (request_id,))
        row = cursor.fetchone()  # Fetch the first result
        # Ensure the cursor is cleared of unread results
        cursor.fetchall()  # Clears any remaining results, if applicable
        return row[0] if row else None
    except Exception as e:
        print(f"Error retrieving result from database: {e}")
        raise
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def delete_request(request_id, email):
    """Delete a request and its associated results from the database."""
    conn = db_config.create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM requests WHERE request_id = %s AND user_email = %s
    """, (request_id, email))
    cursor.execute("""
        DELETE FROM results WHERE request_id = %s AND user_email = %s
    """, (request_id, email))
    conn.commit()
    cursor.close()
    conn.close()
    return True
