import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # replace with your MySQL username
        password="",          # replace with your MySQL password
        database="salary_prediction_app",
        connection_timeout=600
    )

def init_db():
    # Connect without specifying database
    init_conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    init_cur = init_conn.cursor()
    init_cur.execute("CREATE DATABASE IF NOT EXISTS salary_prediction_app")
    init_cur.close()
    init_conn.close()

    # Now connect to the new database
    conn = get_connection()
    cur = conn.cursor()

    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        country VARCHAR(255),
        education VARCHAR(255),
        employment VARCHAR(255),
        experience INT,
        webframework VARCHAR(255),
        undergradmajor VARCHAR(255),
        predicted_salary FLOAT,
        predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database and tables initialized successfully")

if __name__ == "__main__":
    init_db()