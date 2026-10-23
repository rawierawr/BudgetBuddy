import mysql.connector
from mysql.connector import Error
from datetime import datetime


# ============================================================
# BudgetBuddy Database Layer
# XAMPP MySQL / MariaDB
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "budgetbuddies",
}

DEFAULT_CATEGORIES = [
    "Food",
    "Transportation",
    "Education",
    "Entertainment",
    "Shopping",
    "Bills",
    "Health",
    "Other",
]


def get_connection(with_database=True):
    config = DB_CONFIG.copy()
    if not with_database:
        config.pop("database", None)
    return mysql.connector.connect(**config)


def initialize_database():
    # Create database first because the database may not exist yet.
    conn = get_connection(with_database=False)
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.close()
    conn.close()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(120) NOT NULL,
            username VARCHAR(80) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin','user') NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add role to an older users table if it was created by the previous version.
    cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE users ADD COLUMN role "
            "ENUM('admin','user') NOT NULL DEFAULT 'user'"
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            description VARCHAR(255) NOT NULL,
            category VARCHAR(80) NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            expense_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_expense_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            monthly_budget DECIMAL(12,2) NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_budget_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(80) NOT NULL UNIQUE
        )
    """)

    for category in DEFAULT_CATEGORIES:
        cursor.execute(
            "INSERT IGNORE INTO categories (name) VALUES (%s)",
            (category,)
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            actor_user_id INT NULL,
            actor_username VARCHAR(80) NOT NULL,
            action VARCHAR(30) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INT NULL,
            description TEXT NOT NULL,
            old_data TEXT NULL,
            new_data TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_audit_created (created_at),
            INDEX idx_audit_actor (actor_user_id),
            CONSTRAINT fk_audit_user
                FOREIGN KEY (actor_user_id) REFERENCES users(id)
                ON DELETE SET NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, full_name, username, password, role "
        "FROM users WHERE username = %s LIMIT 1",
        (username,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and user["password"] == password:
        user.pop("password", None)
        return user
    return None


def register_user(full_name, username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = %s LIMIT 1",
        (username,)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError("That username is already registered.")

    cursor.execute(
        "INSERT INTO users (full_name, username, password, role) "
        "VALUES (%s, %s, %s, 'user')",
        (full_name, username, password)
    )
    user_id = cursor.lastrowid
    conn.commit()

    cursor.execute(
        "INSERT INTO budgets (user_id, monthly_budget) VALUES (%s, 0)",
        (user_id,)
    )
    conn.commit()

    cursor.close()
    conn.close()


def get_budget(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT monthly_budget FROM budgets "
        "WHERE user_id = %s LIMIT 1",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(row[0]) if row else 0.0


def set_budget(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budgets (user_id, monthly_budget)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            monthly_budget = VALUES(monthly_budget)
    """, (user_id, amount))
    conn.commit()
    cursor.close()
    conn.close()


def get_expenses(user_id, search="", month=None, year=None):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT id, expense_date, description, category, amount
        FROM expenses
        WHERE user_id = %s
    """
    params = [user_id]

    if search:
        sql += """
            AND (
                description LIKE %s
                OR category LIKE %s
                OR CAST(amount AS CHAR) LIKE %s
            )
        """
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    if month is not None:
        sql += " AND MONTH(expense_date) = %s"
        params.append(month)

    if year is not None:
        sql += " AND YEAR(expense_date) = %s"
        params.append(year)

    sql += " ORDER BY expense_date DESC, id DESC"

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_expense(user_id, expense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, expense_date, description, category, amount
        FROM expenses
        WHERE id = %s AND user_id = %s
        LIMIT 1
    """, (expense_id, user_id))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def add_expense(user_id, description, category, amount, expense_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO expenses
            (user_id, description, category, amount, expense_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, description, category, amount, expense_date))

    expense_id = cursor.lastrowid
    conn.commit()

    _audit(
        cursor, user_id, "ADD", "expense", expense_id,
        f"Added expense '{description}' for ₱{float(amount):,.2f}.",
        None,
        f"description={description}; category={category}; "
        f"amount={amount}; date={expense_date}"
    )

    conn.commit()
    cursor.close()
    conn.close()


def update_expense(user_id, expense_id, description, category, amount, expense_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT description, category, amount, expense_date
        FROM expenses
        WHERE id = %s AND user_id = %s
        LIMIT 1
    """, (expense_id, user_id))
    old = cursor.fetchone()

    if not old:
        cursor.close()
        conn.close()
        raise ValueError("Expense not found.")

    cursor.execute("""
        UPDATE expenses
        SET description = %s,
            category = %s,
            amount = %s,
            expense_date = %s
        WHERE id = %s AND user_id = %s
    """, (
        description, category, amount,
        expense_date, expense_id, user_id
    ))

    _audit(
        cursor, user_id, "EDIT", "expense", expense_id,
        f"Edited expense '{description}'.",
        f"description={old[0]}; category={old[1]}; "
        f"amount={old[2]}; date={old[3]}",
        f"description={description}; category={category}; "
        f"amount={amount}; date={expense_date}"
    )

    conn.commit()
    cursor.close()
    conn.close()


def delete_expense(user_id, expense_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT description, category, amount, expense_date
        FROM expenses
        WHERE id = %s AND user_id = %s
        LIMIT 1
    """, (expense_id, user_id))
    old = cursor.fetchone()

    if not old:
        cursor.close()
        conn.close()
        raise ValueError("Expense not found.")

    cursor.execute(
        "DELETE FROM expenses WHERE id = %s AND user_id = %s",
        (expense_id, user_id)
    )

    _audit(
        cursor, user_id, "DELETE", "expense", expense_id,
        f"Deleted expense '{old[0]}' for ₱{float(old[2]):,.2f}.",
        f"description={old[0]}; category={old[1]}; "
        f"amount={old[2]}; date={old[3]}",
        None
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_total_expenses(user_id, month=None, year=None):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
    """
    params = [user_id]

    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year

    sql += " AND MONTH(expense_date) = %s AND YEAR(expense_date) = %s"
    params.extend([month, year])

    cursor.execute(sql, tuple(params))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(row[0] or 0)


def get_transaction_count(user_id, month=None, year=None):
    conn = get_connection()
    cursor = conn.cursor()

    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year

    cursor.execute("""
        SELECT COUNT(*)
        FROM expenses
        WHERE user_id = %s
          AND MONTH(expense_date) = %s
          AND YEAR(expense_date) = %s
    """, (user_id, month, year))

    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return int(row[0] or 0)


def get_recent_expenses(user_id, limit=3):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, expense_date, description, category, amount
        FROM expenses
        WHERE user_id = %s
          AND MONTH(expense_date) = MONTH(CURDATE())
          AND YEAR(expense_date) = YEAR(CURDATE())
        ORDER BY expense_date DESC, id DESC
        LIMIT %s
    """, (user_id, int(limit)))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_category_totals(user_id, month=None, year=None):
    conn = get_connection()
    cursor = conn.cursor()

    if month is None:
        month = datetime.now().month
    if year is None:
        year = datetime.now().year

    cursor.execute("""
        SELECT category, COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
          AND MONTH(expense_date) = %s
          AND YEAR(expense_date) = %s
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (user_id, month, year))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return {row[0]: float(row[1]) for row in rows}


def _audit(cursor, actor_user_id, action, entity_type, entity_id,
           description, old_data, new_data):
    cursor.execute(
        "SELECT username FROM users WHERE id = %s LIMIT 1",
        (actor_user_id,)
    )
    row = cursor.fetchone()
    username = row[0] if row else "Unknown"

    cursor.execute("""
        INSERT INTO audit_logs
            (actor_user_id, actor_username, action, entity_type,
             entity_id, description, old_data, new_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        actor_user_id, username, action, entity_type,
        entity_id, description, old_data, new_data
    ))


def get_audit_logs(user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is None:
        cursor.execute("""
            SELECT id, created_at, actor_username, action, description
            FROM audit_logs
            ORDER BY created_at DESC, id DESC
        """)
    else:
        cursor.execute("""
            SELECT id, created_at, actor_username, action, description
            FROM audit_logs
            WHERE actor_user_id = %s
            ORDER BY created_at DESC, id DESC
        """, (user_id,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, username, role, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def set_user_role(target_user_id, new_role, actor_user_id):
    if new_role not in ("admin", "user"):
        raise ValueError("Invalid role.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, role FROM users WHERE id = %s LIMIT 1",
        (target_user_id,)
    )
    target = cursor.fetchone()

    if not target:
        cursor.close()
        conn.close()
        raise ValueError("User not found.")

    cursor.execute(
        "UPDATE users SET role = %s WHERE id = %s",
        (new_role, target_user_id)
    )

    _audit(
        cursor, actor_user_id, "ROLE_CHANGE", "user", target_user_id,
        f"Changed role of '{target[0]}' from {target[1]} to {new_role}.",
        f"role={target[1]}",
        f"role={new_role}"
    )

    conn.commit()
    cursor.close()
    conn.close()
