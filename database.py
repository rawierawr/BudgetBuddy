import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os


# ============================================================
# BudgetBuddy Database Layer
# XAMPP MySQL / MariaDB
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "budgetbuddy",
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

    cursor.execute("SHOW TABLES LIKE 'monthly_budgets'")
    monthly_budgets_table_existed = cursor.fetchone() is not None
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_budgets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            budget_year SMALLINT NOT NULL,
            budget_month TINYINT NOT NULL,
            monthly_budget DECIMAL(12,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_user_budget_month (user_id, budget_year, budget_month),
            CONSTRAINT fk_monthly_budget_user FOREIGN KEY (user_id)
                REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    # One-time migration only: carry legacy budget values into the current month.
    # Never repeat this migration on later months, because each month needs a fresh budget.
    if not monthly_budgets_table_existed:
        cursor.execute("""
            INSERT IGNORE INTO monthly_budgets (user_id, budget_year, budget_month, monthly_budget)
            SELECT user_id, YEAR(CURDATE()), MONTH(CURDATE()), monthly_budget FROM budgets
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
    cursor.execute("""INSERT IGNORE INTO monthly_budgets
        (user_id, budget_year, budget_month, monthly_budget)
        VALUES (%s, YEAR(CURDATE()), MONTH(CURDATE()), 0)""", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()


def change_password(user_id, current_password, new_password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE id = %s LIMIT 1",
        (user_id,)
    )
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        raise ValueError("User account not found.")

    if row[0] != current_password:
        cursor.close()
        conn.close()
        raise ValueError("Current password is incorrect.")

    cursor.execute(
        "UPDATE users SET password = %s WHERE id = %s",
        (new_password, user_id)
    )

    _audit(
        cursor, user_id, "PASSWORD_CHANGE", "user", user_id,
        "Changed account password.", None, None
    )

    conn.commit()
    cursor.close()
    conn.close()


def has_monthly_budget(user_id, year=None, month=None):
    """Return True when a budget has explicitly been set for the selected month."""
    now = datetime.now()
    year = int(year or now.year)
    month = int(month or now.month)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT 1 FROM monthly_budgets
        WHERE user_id=%s AND budget_year=%s AND budget_month=%s
          AND monthly_budget > 0 LIMIT 1""",
        (user_id, year, month))
    found = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return found


def get_year_budget_total(user_id, year=None):
    year = int(year or datetime.now().year)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(monthly_budget), 0) FROM monthly_budgets WHERE user_id=%s AND budget_year=%s", (user_id, year))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(row[0] or 0)


def get_budget(user_id, year=None, month=None):
    """Get the budget for a month; defaults to the current calendar month."""
    now = datetime.now()
    year = int(year or now.year)
    month = int(month or now.month)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT monthly_budget FROM monthly_budgets
        WHERE user_id=%s AND budget_year=%s AND budget_month=%s LIMIT 1""",
        (user_id, year, month))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(row[0]) if row else 0.0


def set_budget(user_id, amount, year=None, month=None):
    """Save/update a budget for a specific month without overwriting other months."""
    now = datetime.now()
    year = int(year or now.year)
    month = int(month or now.month)
    amount = float(amount)
    if amount <= 0:
        raise ValueError("Monthly budget must be greater than zero.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO monthly_budgets
        (user_id, budget_year, budget_month, monthly_budget)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE monthly_budget=VALUES(monthly_budget)""",
        (user_id, year, month, amount))
    _audit(cursor, user_id, "SET_BUDGET", "budget", None,
           f"Set budget for {year}-{month:02d} to ₱{amount:,.2f}.", None,
           f"year={year}; month={month}; amount={amount}")
    conn.commit()
    cursor.close()
    conn.close()


def update_user_profile(user_id, full_name=None, username=None):
    """Update a user's name and/or username, enforcing unique usernames."""
    full_name = (full_name or "").strip()
    username = (username or "").strip()
    if not full_name or not username:
        raise ValueError("Full name and username are required.")
    if len(username) > 80:
        raise ValueError("Username must be 80 characters or fewer.")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT full_name, username FROM users WHERE id=%s LIMIT 1", (user_id,))
        old = cursor.fetchone()
        if not old:
            raise ValueError("Account not found.")
        cursor.execute("SELECT id FROM users WHERE username=%s AND id<>%s LIMIT 1", (username, user_id))
        if cursor.fetchone():
            raise ValueError("That username is already in use. Choose another one.")
        cursor.execute("UPDATE users SET full_name=%s, username=%s WHERE id=%s", (full_name, username, user_id))
        _audit(cursor, user_id, "PROFILE_UPDATE", "user", user_id,
               "Updated account name and/or username.",
               f"full_name={old[0]}; username={old[1]}",
               f"full_name={full_name}; username={username}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def delete_user_account(user_id, current_password):
    """Delete the current user's account after password verification; retain audit history."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, password, role FROM users WHERE id=%s LIMIT 1", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise ValueError("Account not found.")
        if user[1] != current_password:
            raise ValueError("Password is incorrect.")
        if user[2] == "admin":
            cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
            if int(cursor.fetchone()[0]) <= 1:
                raise ValueError("You cannot delete the last administrator account. Create another admin first.")
        _audit(cursor, user_id, "ACCOUNT_DELETE", "user", user_id,
               f"Account '{user[0]}' deleted by its owner.",
               f"username={user[0]}; role={user[2]}", None)
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_expense_years(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT YEAR(expense_date) FROM expenses WHERE user_id=%s ORDER BY 1 DESC", (user_id,))
    years = [int(row[0]) for row in cursor.fetchall() if row[0] is not None]
    cursor.close()
    conn.close()
    return years


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

    now = datetime.now()
    if month is None and year is None:
        month, year = now.month, now.year
    if year is not None:
        sql += " AND YEAR(expense_date) = %s"
        params.append(int(year))
    if month is not None:
        sql += " AND MONTH(expense_date) = %s"
        params.append(int(month))

    cursor.execute(sql, tuple(params))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return float(row[0] or 0)


def get_transaction_count(user_id, month=None, year=None):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    if month is None and year is None:
        month, year = now.month, now.year
    sql = "SELECT COUNT(*) FROM expenses WHERE user_id = %s"
    params = [user_id]
    if year is not None:
        sql += " AND YEAR(expense_date) = %s"
        params.append(int(year))
    if month is not None:
        sql += " AND MONTH(expense_date) = %s"
        params.append(int(month))
    cursor.execute(sql, tuple(params))

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

    now = datetime.now()
    if month is None and year is None:
        month, year = now.month, now.year
    sql = """
        SELECT category, COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = %s
    """
    params = [user_id]
    if year is not None:
        sql += " AND YEAR(expense_date) = %s"
        params.append(int(year))
    if month is not None:
        sql += " AND MONTH(expense_date) = %s"
        params.append(int(month))
    sql += " GROUP BY category ORDER BY SUM(amount) DESC"
    cursor.execute(sql, tuple(params))

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



def count_admins():
    """Return how many administrator accounts currently exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return int(count)


def create_admin_account(full_name, username, password, actor_admin_id=None, secret_code=None):
    """Create an admin account.

    The first admin may be created only while no admin exists (bootstrap setup).
    After that, an existing admin account is required to create more admins.
    """
    full_name = (full_name or "").strip()
    username = (username or "").strip()
    if not full_name or not username or not password:
        raise ValueError("Full name, username, and password are required.")
    if len(password) < 8:
        raise ValueError("Use a password with at least 8 characters.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = int(cursor.fetchone()[0])

        if actor_admin_id is None:
            expected_code = os.environ.get("BUDGETBUDDY_ADMIN_CODE", "onlybudgetadmins")
            if not secret_code or secret_code != expected_code:
                raise PermissionError("A valid administrator secret code is required.")
        else:
            cursor.execute(
                "SELECT role, username FROM users WHERE id = %s LIMIT 1",
                (actor_admin_id,)
            )
            actor = cursor.fetchone()
            if not actor or actor[0] != "admin":
                raise PermissionError("Administrator access is required to create an Admin account.")

        cursor.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
        if cursor.fetchone():
            raise ValueError("That username is already registered.")

        cursor.execute(
            "INSERT INTO users (full_name, username, password, role) VALUES (%s, %s, %s, 'admin')",
            (full_name, username, password)
        )
        new_admin_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO budgets (user_id, monthly_budget) VALUES (%s, 0)",
            (new_admin_id,)
        )
        cursor.execute("""INSERT IGNORE INTO monthly_budgets
            (user_id, budget_year, budget_month, monthly_budget)
            VALUES (%s, YEAR(CURDATE()), MONTH(CURDATE()), 0)""", (new_admin_id,))

        # Log creation when an existing admin performed the action.
        if actor_admin_id is not None:
            _audit(
                cursor, actor_admin_id, "CREATE_ADMIN", "user", new_admin_id,
                f"Created administrator account '{username}'.", None,
                f"role=admin; username={username}"
            )
        conn.commit()
        return new_admin_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


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
