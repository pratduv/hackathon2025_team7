import logging
import sqlite3

# 1) Logging PII directly without masking
def log_user_info(user):
    # Logs name, email and IP address in plain text
    logging.info(f"User connected: name={user['name']}, email={user['email']}, ip={user['ip_address']}")

# 2) Storing personal data in a plain-text file
def save_user_to_file(user):
    with open("user_data.csv", "a") as f:
        # Stores name and email without consent or encryption
        f.write(f"{user['name']},{user['email']}\n")

# 3) Inserting PII directly into a database without parameterization (and no deletion path)
def store_user_in_db(user):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            address TEXT
        )
    """)
    # Direct string interpolation — vulnerable to injection and storing PII unsafely
    query = f"""
        INSERT INTO users (name, email, address)
        VALUES ('{user['name']}', '{user['email']}', '{user['address']}')
    """
    cursor.execute(query)
    conn.commit()
    conn.close()

def main():
    # Sample user with PII
    user = {
        "name": "Alice Smith",
        "email": "alice.smith@example.com",
        "ip_address": "203.0.113.42",
        "address": "123 Main St, Springfield"
    }

    log_user_info(user)
    save_user_to_file(user)
    store_user_in_db(user)

    # NOTE: There is no function here to delete or anonymize user data → violates "right to be forgotten"

if __name__ == "__main__":
    main()