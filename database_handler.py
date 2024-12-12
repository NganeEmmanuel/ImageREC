import db_config


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


def add_request(request_id, user_email):
    """Add a new request to the database."""
    conn = db_config.create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO requests (request_id, user_email) 
        VALUES (%s, %s)
    """, (request_id, user_email))
    conn.commit()
    cursor.close()
    conn.close()


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
    """Retrieve the result associated with a specific request ID."""
    conn = db_config.create_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    cursor.execute("""
        SELECT result FROM results WHERE request_id = %s
    """, (request_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None


def delete_request(request_id):
    """Delete a request and its associated results from the database."""
    conn = db_config.create_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM requests WHERE request_id = %s
    """, (request_id,))
    cursor.execute("""
        DELETE FROM results WHERE request_id = %s
    """, (request_id,))
    conn.commit()
    cursor.close()
    conn.close()
