import tkinter as tk
# tkinter → tk
from tkinter import ttk, messagebox, filedialog
# ttk provides modern-looking Tkinter widgets.
# messagebox = notifications, errors, warnings, and confirmations.
# filedialog = allows the user to choose where to save/open a file.
from datetime import date, datetime
import csv # csv = exporting/importing spreadsheet-style data.
import os # os = interacting with files, folders, and the operating system.
import sys # sys = information/control related to Python itself.
import tempfile # tempfile = temporary files used while the program is running.
import subprocess # subprocess = running external programs, like opening a CSV in Excel.
import database 

# │ tkinter       → GUI                 │
# │ ttk           → Modern widgets      │
# │ messagebox    → Popups              │
# │ filedialog    → File selection      │
# │ date/datetime → Dates & time        │
# │ csv           → CSV reports         │
# │ os            → Files/OS            │
# │ sys           → Python environment  │
# │ tempfile      → Temporary files     │
# │ subprocess    → External programs   │
# │ database      → MySQL/database      │

# ============================================================
# BudgetBuddy - Modern Desktop UI
# Tkinter + XAMPP MySQL
# ============================================================

BG = "#F5F7FB" # Background color
CARD = "#FFFFFF" # Card color
INPUT = "#F3F5F9" # Input field color
TEXT = "#1F2937" # Text color
MUTED = "#6B7280" # Muted text color
PRIMARY = "#4F46E5" # Primary color
PRIMARY_DARK = "#4338CA" # Darker shade of primary color
GREEN = "#16A34A" # Green color
BLUE = "#2563EB" # Blue color
ORANGE = "#F59E0B" # Orange color
RED = "#DC2626" # Red color
PURPLE = "#7C3AED" # Purple color
BORDER = "#E5E7EB" # Border color
LIGHT_PURPLE = "#EEF2FF" # Light purple color
LIGHT_GREEN = "#ECFDF5" # Light green color
LIGHT_RED = "#FEF2F2" # Light red color
LIGHT_BLUE = "#EFF6FF" # Light blue color
GRID = "#EEF1F5" # Grid color
SECONDARY_TEXT = "#374151" # Secondary text color
ROLE_BG = "#EEF2FF" # Role background color

THEMES = {
    "light": {
        "BG": "#F5F7FB", "CARD": "#FFFFFF", "INPUT": "#F3F5F9",
        "TEXT": "#1F2937", "MUTED": "#6B7280", "BORDER": "#E5E7EB",
        "LIGHT_PURPLE": "#EEF2FF", "LIGHT_GREEN": "#ECFDF5",
        "LIGHT_RED": "#FEF2F2", "LIGHT_BLUE": "#EFF6FF",
        "GRID": "#EEF1F5", "SECONDARY_TEXT": "#374151",
        "ROLE_BG": "#EEF2FF",
    },
    "dark": {
        "BG": "#111827", "CARD": "#1F2937", "INPUT": "#374151",
        "TEXT": "#F9FAFB", "MUTED": "#9CA3AF", "BORDER": "#374151",
        "LIGHT_PURPLE": "#312E81", "LIGHT_GREEN": "#064E3B",
        "LIGHT_RED": "#7F1D1D", "LIGHT_BLUE": "#1E3A8A",
        "GRID": "#374151", "SECONDARY_TEXT": "#D1D5DB",
        "ROLE_BG": "#312E81",
    }
} # themes for light and dark modes, with corresponding color values.


def apply_theme_globals(name):
    values = THEMES.get(name, THEMES["light"])
    globals().update(values) # Update global variables with the selected theme's color values.


CATEGORIES = [
    "Food", "Transportation", "Education", "Entertainment",
    "Shopping", "Bills", "Health", "Other"
] # Predefined expense categories for the application.


apply_theme_globals("light")

def money(value):
    return f"₱{float(value or 0):,.2f}"


class AuthWindow:
    def __init__(self, root):
        self.root = root
        self.mode = "login"
        root.title("BudgetBuddy - Login")
        root.geometry("980x620")
        root.minsize(820, 560)
        root.configure(bg=BG)
        self.setup_styles()
        self.build_login()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Budget.TCombobox",
            fieldbackground=INPUT,
            background=INPUT,
            foreground=TEXT,
            padding=8
        )

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_login(self):
        self.mode = "login"
        self.clear()
        self.create_auth_layout(
            "Welcome back",
            "Sign in to manage your money."
        )

    def build_register(self):
        self.mode = "register"
        self.clear()
        self.create_auth_layout(
            "Create an account",
            "Start tracking your expenses today."
        )

    def create_auth_layout(self, title, subtitle):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=45, pady=40)

        brand = tk.Frame(outer, bg=PRIMARY, width=330)
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)

        tk.Label(
            brand, text="● BudgetBuddy", bg=PRIMARY, fg="white",
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", padx=32, pady=(85, 10))

        tk.Label(
            brand, text="Personal Expense\nManagement",
            bg=PRIMARY, fg="white", justify="left",
            font=("Segoe UI", 17)
        ).pack(anchor="w", padx=32)

        tk.Label(
            brand,
            text="Track expenses, set your budget,\nand understand your spending.",
            bg=PRIMARY, fg="#E0E7FF", justify="left",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=32, pady=(18, 0))

        form_panel = tk.Frame(
            outer, bg=CARD,
            highlightbackground=BORDER, highlightthickness=1
        )
        form_panel.pack(side="left", fill="both", expand=True)

        form = tk.Frame(form_panel, bg=CARD)
        form.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72)

        tk.Label(
            form, text=title, bg=CARD, fg=TEXT,
            font=("Segoe UI", 23, "bold")
        ).pack(anchor="w")

        tk.Label(
            form, text=subtitle, bg=CARD, fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 25))

        if self.mode == "login":
            self.create_login_form(form)
        else:
            self.create_register_form(form)

    def create_entry(self, parent, label, show=""):
        tk.Label(
            parent, text=label, bg=CARD, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 6))

        entry = tk.Entry(
            parent, bg=INPUT, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, font=("Segoe UI", 10)
        )
        if show:
            entry.configure(show=show)
        entry.pack(fill="x", ipady=10)
        return entry

    def create_login_form(self, parent):
        self.username_entry = self.create_entry(parent, "Username")
        tk.Frame(parent, bg=CARD, height=14).pack()
        self.password_entry = self.create_entry(
            parent, "Password", show="*"
        )
        tk.Frame(parent, bg=CARD, height=20).pack()

        tk.Button(
            parent, text="Log In", command=self.login,
            bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK,
            activeforeground="white", relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"), cursor="hand2", pady=11
        ).pack(fill="x")

        tk.Label(
            parent, text="Don't have an account?", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(pady=(22, 4))

        tk.Button(
            parent, text="Create an account", command=self.build_register,
            bg=CARD, fg=PRIMARY, activebackground=CARD,
            activeforeground=PRIMARY_DARK, relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        ).pack()

        self.username_entry.focus()
        self.password_entry.bind("<Return>", lambda _: self.login())

    def create_register_form(self, parent):
        self.full_name_entry = self.create_entry(parent, "Full Name")
        tk.Frame(parent, bg=CARD, height=8).pack()
        self.username_entry = self.create_entry(parent, "Username")
        tk.Frame(parent, bg=CARD, height=8).pack()
        self.password_entry = self.create_entry(
            parent, "Password", show="*"
        )
        tk.Frame(parent, bg=CARD, height=8).pack()
        self.confirm_password_entry = self.create_entry(
            parent, "Confirm Password", show="*"
        )
        tk.Frame(parent, bg=CARD, height=16).pack()

        tk.Button(
            parent, text="Create Account", command=self.register,
            bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK,
            activeforeground="white", relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"), cursor="hand2", pady=11
        ).pack(fill="x")

        tk.Label(
            parent, text="Already have an account?", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(pady=(16, 4))

        tk.Button(
            parent, text="Back to Log In", command=self.build_login,
            bg=CARD, fg=PRIMARY, activebackground=CARD,
            activeforeground=PRIMARY_DARK, relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        ).pack()

        self.full_name_entry.focus()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Information",
                "Please enter your username and password.",
                parent=self.root
            )
            return

        try:
            user = database.authenticate_user(username, password)
            if not user:
                messagebox.showerror(
                    "Login Failed",
                    "Incorrect username or password.",
                    parent=self.root
                )
                return

            for widget in self.root.winfo_children():
                widget.destroy()

            BudgetBuddyApp(self.root, user, self)

        except Exception as e:
            messagebox.showerror(
                "Database Error", str(e), parent=self.root
            )

    def register(self):
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_password_entry.get()

        if not full_name or not username or not password or not confirm:
            messagebox.showwarning(
                "Missing Information",
                "Please complete all fields.",
                parent=self.root
            )
            return

        if password != confirm:
            messagebox.showerror(
                "Passwords Do Not Match",
                "Please make sure both passwords match.",
                parent=self.root
            )
            return

        try:
            database.register_user(full_name, username, password)
            messagebox.showinfo(
                "Account Created",
                "Your BudgetBuddy account is ready.",
                parent=self.root
            )
            self.build_login()

        except ValueError as e:
            messagebox.showwarning(
                "Registration Problem", str(e), parent=self.root
            )
        except Exception as e:
            messagebox.showerror(
                "Database Error", str(e), parent=self.root
            )


class BudgetBuddyApp:
    def __init__(self, root, user, auth_window):
        self.root = root
        self.user = user
        self.auth_window = auth_window
        self.role = str(user.get("role", "user")).lower()
        self.dark_mode = (BG == THEMES["dark"]["BG"])

        root.title(f"BudgetBuddy - {user['full_name']}")
        root.geometry("1350x950")
        root.minsize(1050, 680)
        root.configure(bg=BG)

        self.setup_styles()
        self.create_ui()
        self.show_dashboard()

    # --------------------------------------------------------
    # UI foundation
    # --------------------------------------------------------
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Budget.Treeview",
            background=CARD,
            foreground=TEXT,
            fieldbackground=CARD,
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        # Treeview header follows the active theme.
        # The previous version used a hard-coded light background, which
        # made the header unreadable in dark mode.
        heading_bg = "#111827" if self.dark_mode else "#F3F4F6"
        heading_fg = "#F9FAFB" if self.dark_mode else TEXT

        style.configure(
            "Budget.Treeview.Heading",
            background=heading_bg,
            foreground=heading_fg,
            font=("Segoe UI", 9, "bold"),
            padding=8,
            relief="flat"
        )
        style.map(
            "Budget.Treeview.Heading",
            background=[
                ("active", heading_bg),
                ("pressed", heading_bg)
            ],
            foreground=[
                ("active", heading_fg),
                ("pressed", heading_fg)
            ]
        )

        # Keep selected rows readable in both themes.
        selected_bg = "#4338CA" if self.dark_mode else "#E0E7FF"
        selected_fg = "#FFFFFF" if self.dark_mode else TEXT
        style.map(
            "Budget.Treeview",
            background=[("selected", selected_bg)],
            foreground=[("selected", selected_fg)]
        )
        style.configure(
            "Budget.TCombobox",
            fieldbackground=INPUT,
            background=INPUT,
            foreground=TEXT,
            padding=8
        )

    def create_ui(self):
        self.root_frame = tk.Frame(self.root, bg=BG)
        self.root_frame.pack(fill="both", expand=True)

        self.create_topbar()

        self.content = tk.Frame(self.root_frame, bg=BG)
        self.content.pack(fill="both", expand=True)

    def create_topbar(self):
        top = tk.Frame(
            self.root_frame, bg=CARD,
            highlightbackground=BORDER, highlightthickness=1
        )
        top.pack(fill="x")

        left = tk.Frame(top, bg=CARD)
        left.pack(side="left", padx=24, pady=13)

        tk.Label(
            left, text="●", bg=CARD, fg=PRIMARY,
            font=("Segoe UI", 18, "bold")
        ).pack(side="left", padx=(0, 5))

        tk.Label(
            left, text="BudgetBuddy", bg=CARD, fg=TEXT,
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")

        nav = tk.Frame(top, bg=CARD)
        nav.pack(side="left", padx=20)

        self.top_button(nav, "Home", self.show_dashboard)
        self.top_button(nav, "Add Expense", self.open_add_expense)
        self.top_button(nav, "Expenses", self.show_view_expenses)
        self.top_button(nav, "Edit Expense", self.show_edit_expenses)
        self.top_button(nav, "Delete Expense", self.show_delete_expenses)
        self.top_button(nav, "Budget", self.open_set_budget)
        self.top_button(nav, "Reports", self.show_reports)

        if self.role == "admin":
            self.top_button(nav, "Audit Trail", self.show_audit_trail)
            self.top_button(nav, "Admin", self.show_admin)

        right = tk.Frame(top, bg=CARD)
        right.pack(side="right", padx=22)

        role_text = "Administrator" if self.role == "admin" else "User"

        tk.Label(
            right, text=role_text, bg=THEMES["dark"]["ROLE_BG"] if self.dark_mode else THEMES["light"]["ROLE_BG"], fg=PRIMARY,
            font=("Segoe UI", 8, "bold"), padx=9, pady=5
        ).pack(side="left", padx=(0, 10))

        profile = tk.Frame(right, bg=CARD)
        profile.pack(side="left")

        # self.top_button(right, "Change Password", self.open_change_password)

        self.theme_button = tk.Button(
            right, text=("☀ Light" if self.dark_mode else "☾ Dark"),
            command=self.toggle_dark_mode,
            bg=CARD, fg=PRIMARY, activebackground=LIGHT_PURPLE,
            activeforeground=PRIMARY, relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 9, "bold"), padx=8, pady=6
        )
        self.theme_button.pack(side="left", padx=(4, 0))

        tk.Button(
            right, text="Log Out", command=self.logout,
            bg=CARD, fg=RED, activebackground=LIGHT_RED,
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(8, 0))

    def top_button(self, parent, text, command):
        button = tk.Button(
            parent, text=text, command=command,
            bg=CARD, fg=SECONDARY_TEXT, activebackground=LIGHT_PURPLE,
            activeforeground=PRIMARY, relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"), cursor="hand2",
            padx=10, pady=8
        )
        button.pack(side="left", padx=2)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        apply_theme_globals("dark" if self.dark_mode else "light")
        self.setup_styles()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_ui()
        self.show_dashboard()

    def open_change_password(self):
        form = tk.Toplevel(self.root)
        form.title("Change Password")
        form.geometry("430x390")
        form.resizable(False, False)
        form.configure(bg=BG)
        form.transient(self.root)
        form.grab_set()

        tk.Label(
            form, text="Change Password", bg=BG, fg=TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", padx=30, pady=(25, 4))

        tk.Label(
            form, text="Update the password for your BudgetBuddy account.",
            bg=BG, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=30, pady=(0, 15))

        card = self.card(form)
        card.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        self.form_label(card, "Current Password", top=20)
        current_entry = self.form_entry(card)
        current_entry.configure(show="*")

        self.form_label(card, "New Password")
        new_entry = self.form_entry(card)
        new_entry.configure(show="*")

        self.form_label(card, "Confirm New Password")
        confirm_entry = self.form_entry(card)
        confirm_entry.configure(show="*")

        def save():
            current = current_entry.get()
            new = new_entry.get()
            confirm = confirm_entry.get()

            if not current or not new or not confirm:
                messagebox.showwarning(
                    "Missing Information",
                    "Please complete all password fields.",
                    parent=form
                )
                return
            if new != confirm:
                messagebox.showwarning(
                    "Passwords Do Not Match",
                    "The new passwords do not match.",
                    parent=form
                )
                return
            if len(new) < 6:
                messagebox.showwarning(
                    "Weak Password",
                    "New password must be at least 6 characters.",
                    parent=form
                )
                return
            try:
                database.change_password(self.user["id"], current, new)
                messagebox.showinfo(
                    "Password Changed",
                    "Your password has been changed successfully.",
                    parent=form
                )
                form.destroy()
            except ValueError as e:
                messagebox.showwarning(
                    "Password Change Failed", str(e), parent=form
                )
            except Exception as e:
                messagebox.showerror(
                    "Database Error", str(e), parent=form
                )

        buttons = tk.Frame(card, bg=CARD)
        buttons.pack(fill="x", padx=20, pady=18)
        self.action_button(buttons, "Save Password", save, PRIMARY, "white").pack(side="left", padx=(0, 8))
        self.action_button(buttons, "Cancel", form.destroy, LIGHT_PURPLE, TEXT).pack(side="left")
        current_entry.focus()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def page_header(self, title, subtitle, action_text=None, action=None):
        header = tk.Frame(self.content, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 14))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left")

        tk.Label(
            left, text=title, bg=BG, fg=TEXT,
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w")

        tk.Label(
            left, text=subtitle, bg=BG, fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(3, 0))

        if action_text and action:
            self.action_button(
                header, action_text, action, PRIMARY, "white"
            ).pack(side="right")

    def action_button(self, parent, text, command, bg_color, fg_color):
        return tk.Button(
            parent, text=text, command=command,
            bg=bg_color, fg=fg_color,
            activebackground=PRIMARY_DARK,
            activeforeground="white",
            relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=16, pady=9, cursor="hand2"
        )

    def card(self, parent, **kwargs):
        return tk.Frame(
            parent, bg=CARD,
            highlightbackground=BORDER, highlightthickness=1,
            **kwargs
        )

    # --------------------------------------------------------
    # Dashboard
    # --------------------------------------------------------
    
    def show_dashboard(self):
        self.clear_content()
        first_name = self.user["full_name"].split()[0]

        self.page_header(
            "Dashboard",
            f"Good day, {first_name}! Take control of your money, one expense at a time."
        )

        today_text = datetime.now().strftime(
                        "%a • %b %d • %I:%M %p"
        )

        tk.Label(
            self.content, text=today_text, bg=BG, fg=MUTED,
            font=("Segoe UI", 9)
        ).place(relx=0.98, y=58, anchor="e")

        try:
            budget = float(database.get_budget(self.user["id"]))
            total = float(database.get_total_expenses(self.user["id"]))
            remaining = budget - total
            count = database.get_transaction_count(self.user["id"])
            recent = database.get_recent_expenses(
                self.user["id"], limit=3
            )
            categories = database.get_category_totals(self.user["id"])

        except Exception as e:
            messagebox.showerror(
                "Database Error", str(e), parent=self.root
            )
            return

        cards = tk.Frame(self.content, bg=BG)
        cards.pack(fill="x", padx=22, pady=5)

        self.stat_card(cards, "Monthly Budget", budget, GREEN, LIGHT_GREEN)
        self.stat_card(cards, "Total Spent", total, RED, LIGHT_RED)
        self.stat_card(
            cards, "Remaining", remaining,
            GREEN if remaining >= 0 else RED,
            LIGHT_GREEN if remaining >= 0 else LIGHT_RED
        )
        self.stat_card(cards, "Transactions", count, BLUE, LIGHT_BLUE)

        lower = tk.Frame(self.content, bg=BG)
        lower.pack(fill="both", expand=True, padx=22, pady=(14, 20))

        overview = self.card(lower)
        overview.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(
            overview, text="Spending Overview",
            bg=CARD, fg=TEXT, font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 0))

        tk.Label(
            overview,
            text="Current month spending by category",
            bg=CARD, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=20, pady=(2, 6))

        chart = tk.Canvas(
            overview, bg=CARD, highlightthickness=0, height=270
        )
        chart.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.draw_spending_chart(chart, categories)

        quick = self.card(lower, width=255)
        quick.pack(side="right", fill="y", padx=(8, 0))
        quick.pack_propagate(False)

        tk.Label(
            quick, text="Quick Actions",
            bg=CARD, fg=TEXT, font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 15))

        self.quick_button(
            quick, "+  Add Expense", self.open_add_expense, GREEN
        )
        self.quick_button(
            quick, "₱  Set Monthly Budget", self.open_set_budget, BLUE
        )
        self.quick_button(
            quick, "▤  View Expenses", self.show_view_expenses, PURPLE
        )
        self.quick_button(
            quick, "▣  Summary Reports", self.show_reports, PRIMARY
        )

        if self.role == "admin":
            self.quick_button(
                quick, "◉  Audit Trail", self.show_audit_trail, ORANGE
            )

        recent_card = self.card(self.content)
        recent_card.pack(fill="x", padx=22, pady=(0, 20))

        top = tk.Frame(recent_card, bg=CARD)
        top.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(
            top, text="Recent Transactions",
            bg=CARD, fg=TEXT, font=("Segoe UI", 13, "bold")
        ).pack(side="left")

        tk.Button(
            top, text="View All →",
            command=self.show_view_expenses,
            bg=CARD, fg=PRIMARY, activebackground=CARD,
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 9, "bold")
        ).pack(side="right")

        holder = tk.Frame(recent_card, bg=CARD)
        holder.pack(fill="x", padx=20, pady=(0, 16))

        tree = self.make_treeview(
            holder, columns=("date", "description", "category", "amount")
        )
        self.attach_scrollbar(holder, tree)

        for expense in recent:
            eid, edate, desc, cat, amount = expense
            tree.insert(
                "", "end",
                values=(str(edate), desc, cat, money(amount))
            )

        if not recent:
            tk.Label(
                holder, text="No transactions recorded for the current month.",
                bg=CARD, fg=MUTED, font=("Segoe UI", 9)
            ).pack(pady=15)

    def stat_card(self, parent, title, value, accent, bg_tint):
        card = self.card(parent)
        card.pack(side="left", fill="both", expand=True, padx=5)

        top = tk.Frame(card, bg=bg_tint, height=6)
        top.pack(fill="x")

        body = tk.Frame(card, bg=CARD)
        body.pack(fill="both", expand=True)

        tk.Label(
            body, text=title, bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=18, pady=(13, 3))

        tk.Label(
            body,
            text=money(value) if title != "Transactions" else str(value),
            bg=CARD, fg=accent,
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 13))

    def quick_button(self, parent, text, command, color):
        button = tk.Button(
            parent, text=text, command=command,
            bg=color, fg="white",
            activebackground=color, activeforeground="white",
            relief="flat", bd=0, cursor="hand2",
            anchor="w", font=("Segoe UI", 9, "bold"),
            padx=15, pady=10
        )
        button.pack(fill="x", padx=18, pady=5)

    def draw_spending_chart(self, canvas, categories):
        def draw(event=None):
            canvas.delete("all")
            width = max(canvas.winfo_width(), 500)
            height = max(canvas.winfo_height(), 230)

            if not categories:
                canvas.create_text(
                    width / 2, height / 2,
                    text="No spending recorded this month.",
                    fill=MUTED, font=("Segoe UI", 10)
                )
                return

            items = list(categories.items())
            max_value = max(float(v) for _, v in items) or 1
            left = 55
            right = width - 25
            bottom = height - 45
            top = 25
            plot_h = bottom - top
            slot = (right - left) / max(len(items), 1)
            bar_w = min(55, slot * 0.55)

            # horizontal grid lines
            for i in range(5):
                y = bottom - (plot_h * i / 4)
                value = max_value * i / 4
                canvas.create_line(
                    left, y, right, y, fill=THEMES["dark"]["GRID"] if self.dark_mode else THEMES["light"]["GRID"]
                )
                canvas.create_text(
                    left - 8, y, text=money(value),
                    anchor="e", fill=MUTED, font=("Segoe UI", 7)
                )

            bar_colors = [
                "#34D399", "#60A5FA", "#F59E0B", "#A78BFA",
                "#F472B6", "#94A3B8", "#22C55E", "#38BDF8"
            ]

            for i, (name, value) in enumerate(items):
                value = float(value)
                x_center = left + slot * (i + 0.5)
                bar_h = plot_h * value / max_value
                x1 = x_center - bar_w / 2
                x2 = x_center + bar_w / 2
                y1 = bottom - bar_h

                canvas.create_rectangle(
                    x1, y1, x2, bottom,
                    fill=bar_colors[i % len(bar_colors)],
                    outline=""
                )
                canvas.create_text(
                    x_center, bottom + 16,
                    text=name[:11], fill=MUTED,
                    font=("Segoe UI", 7)
                )
                canvas.create_text(
                    x_center, max(y1 - 8, 12),
                    text=money(value), fill=TEXT,
                    font=("Segoe UI", 7, "bold")
                )

        canvas.bind("<Configure>", draw)
        self.root.after(50, draw)

    # --------------------------------------------------------
    # Shared expense table
    # --------------------------------------------------------
    def make_treeview(self, parent, columns=None):
        if columns is None:
            columns = ("id", "date", "description", "category", "amount")

        tree = ttk.Treeview(
            parent, columns=columns, show="headings",
            selectmode="browse", style="Budget.Treeview"
        )

        headings = {
            "id": "#",
            "date": "DATE",
            "description": "DESCRIPTION",
            "category": "CATEGORY",
            "amount": "AMOUNT"
        }

        widths = {
            "id": 50, "date": 110, "description": 310,
            "category": 165, "amount": 130
        }

        for column in columns:
            tree.heading(column, text=headings.get(column, column.upper()))
            anchor = "center"
            if column in ("description", "category"):
                anchor = "w"
            elif column == "amount":
                anchor = "e"
            tree.column(
                column,
                width=widths.get(column, 130),
                anchor=anchor
            )

        return tree

    def attach_scrollbar(self, parent, tree):
        scrollbar = ttk.Scrollbar(
            parent, orient="vertical", command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def filter_bar(self, parent, include_date_filters=True):
        bar = tk.Frame(parent, bg=CARD)
        bar.pack(fill="x", padx=18, pady=18)

        tk.Label(
            bar, text="Search", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 7))

        search_var = tk.StringVar()
        search = tk.Entry(
            bar, textvariable=search_var, bg=INPUT, fg=TEXT,
            insertbackground=TEXT, relief="flat", bd=0,
            font=("Segoe UI", 9), width=28
        )
        search.pack(side="left", ipady=8, padx=(0, 12))

        month_var = tk.StringVar(value="All Months")
        year_var = tk.StringVar(value="All Years")

        if include_date_filters:
            tk.Label(
                bar, text="Month", bg=CARD, fg=MUTED,
                font=("Segoe UI", 9, "bold")
            ).pack(side="left", padx=(0, 6))

            month_combo = ttk.Combobox(
                bar, textvariable=month_var,
                values=["All Months"] + [
                    datetime(2000, m, 1).strftime("%B")
                    for m in range(1, 13)
                ],
                state="readonly", width=14,
                style="Budget.TCombobox"
            )
            month_combo.pack(side="left", padx=(0, 10))

            tk.Label(
                bar, text="Year", bg=CARD, fg=MUTED,
                font=("Segoe UI", 9, "bold")
            ).pack(side="left", padx=(0, 6))

            current_year = date.today().year
            years = ["All Years"] + [
                str(y) for y in range(current_year - 5, current_year + 2)
            ]
            year_combo = ttk.Combobox(
                bar, textvariable=year_var,
                values=years, state="readonly", width=11,
                style="Budget.TCombobox"
            )
            year_combo.pack(side="left")

            return bar, search_var, month_var, year_var, search, month_combo, year_combo

        return bar, search_var, month_var, year_var, search, None, None

    def read_filters(self, search_var, month_var, year_var):
        search = search_var.get().strip()
        month = None if month_var.get() == "All Months" else (
            datetime.strptime(month_var.get(), "%B").month
        )
        year = None if year_var.get() == "All Years" else int(year_var.get())
        return search, month, year

    def populate_expense_tree(self, tree, user_id, search="", month=None, year=None):
        for item in tree.get_children():
            tree.delete(item)

        expenses = database.get_expenses(
            user_id, search=search, month=month, year=year
        )

        for expense in expenses:
            eid, edate, desc, cat, amount = expense
            tree.insert(
                "", "end",
                values=(eid, str(edate), desc, cat, money(amount))
            )

        return expenses

    def selected_tree_id(self, tree):
        selected = tree.selection()
        if not selected:
            return None
        return int(tree.item(selected[0], "values")[0])

    # --------------------------------------------------------
    # View Expenses - dedicated page
    # --------------------------------------------------------
    def show_view_expenses(self):
        self.clear_content()
        self.page_header(
            "View Expenses",
            "Browse your complete expense history and filter it by month or year."
        )

        card = self.card(self.content)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        result = self.filter_bar(card, include_date_filters=True)
        _, search_var, month_var, year_var, search, month_combo, year_combo = result

        holder = tk.Frame(card, bg=CARD)
        holder.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        tree = self.make_treeview(holder)
        self.attach_scrollbar(holder, tree)

        status = tk.StringVar(value="")

        def refresh(*_):
            search_text, month, year = self.read_filters(
                search_var, month_var, year_var
            )
            rows = self.populate_expense_tree(
                tree, self.user["id"],
                search=search_text, month=month, year=year
            )
            status.set(f"{len(rows)} expense(s) found")

        search.bind("<KeyRelease>", refresh)
        month_combo.bind("<<ComboboxSelected>>", refresh)
        year_combo.bind("<<ComboboxSelected>>", refresh)

        footer = tk.Frame(card, bg=CARD)
        footer.pack(fill="x", padx=18, pady=(0, 18))

        tk.Label(
            footer, textvariable=status, bg=CARD, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        self.action_button(
            footer, "Add Expense", self.open_add_expense,
            PRIMARY, "white"
        ).pack(side="right")

        refresh()

    # --------------------------------------------------------
    # Edit page
    # --------------------------------------------------------
    def show_edit_expenses(self):
        self.clear_content()
        self.page_header(
            "Edit Expense",
            "Search the expense list, select one row, then edit its details."
        )

        card = self.card(self.content)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        result = self.filter_bar(card, include_date_filters=True)
        _, search_var, month_var, year_var, search, month_combo, year_combo = result

        holder = tk.Frame(card, bg=CARD)
        holder.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        tree = self.make_treeview(holder)
        self.attach_scrollbar(holder, tree)

        status = tk.StringVar(value="")

        def refresh(*_):
            s, m, y = self.read_filters(search_var, month_var, year_var)
            rows = self.populate_expense_tree(
                tree, self.user["id"], search=s, month=m, year=y
            )
            status.set(f"{len(rows)} expense(s) found")

        def edit():
            expense_id = self.selected_tree_id(tree)
            if expense_id is None:
                messagebox.showwarning(
                    "Nothing Selected",
                    "Select an expense from the table first.",
                    parent=self.root
                )
                return
            self.open_expense_form(expense_id)

        search.bind("<KeyRelease>", refresh)
        month_combo.bind("<<ComboboxSelected>>", refresh)
        year_combo.bind("<<ComboboxSelected>>", refresh)
        tree.bind("<Double-1>", lambda _: edit())

        footer = tk.Frame(card, bg=CARD)
        footer.pack(fill="x", padx=18, pady=18)

        tk.Label(
            footer, textvariable=status, bg=CARD, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        self.action_button(
            footer, "Edit Selected", edit, PRIMARY, "white"
        ).pack(side="right")

        refresh()

    # --------------------------------------------------------
    # Delete page
    # --------------------------------------------------------
    def show_delete_expenses(self):
        self.clear_content()
        self.page_header(
            "Delete Expense",
            "Search the expense list, select one row, then delete it."
        )

        card = self.card(self.content)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        result = self.filter_bar(card, include_date_filters=True)
        _, search_var, month_var, year_var, search, month_combo, year_combo = result

        holder = tk.Frame(card, bg=CARD)
        holder.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        tree = self.make_treeview(holder)
        self.attach_scrollbar(holder, tree)

        status = tk.StringVar(value="")

        def refresh(*_):
            s, m, y = self.read_filters(search_var, month_var, year_var)
            rows = self.populate_expense_tree(
                tree, self.user["id"], search=s, month=m, year=y
            )
            status.set(f"{len(rows)} expense(s) found")

        def delete():
            expense_id = self.selected_tree_id(tree)
            if expense_id is None:
                messagebox.showwarning(
                    "Nothing Selected",
                    "Select an expense from the table first.",
                    parent=self.root
                )
                return

            values = tree.item(tree.selection()[0], "values")
            confirm = messagebox.askyesno(
                "Delete Expense?",
                f"Delete '{values[2]}' for {values[4]}?\n\n"
                "This action cannot be undone.",
                parent=self.root
            )
            if not confirm:
                return

            try:
                database.delete_expense(self.user["id"], expense_id)
                messagebox.showinfo(
                    "Deleted", "Expense deleted successfully.",
                    parent=self.root
                )
                refresh()
            except Exception as e:
                messagebox.showerror(
                    "Database Error", str(e), parent=self.root
                )

        search.bind("<KeyRelease>", refresh)
        month_combo.bind("<<ComboboxSelected>>", refresh)
        year_combo.bind("<<ComboboxSelected>>", refresh)

        footer = tk.Frame(card, bg=CARD)
        footer.pack(fill="x", padx=18, pady=18)

        tk.Label(
            footer, textvariable=status, bg=CARD, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        self.action_button(
            footer, "Delete Selected", delete, RED, "white"
        ).pack(side="right")

        refresh()

    # --------------------------------------------------------
    # Add / edit expense
    # --------------------------------------------------------
    def open_add_expense(self):
        self.open_expense_form()

    def form_label(self, parent, text, top=18):
        tk.Label(
            parent, text=text, bg=CARD, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=20, pady=(top, 5))

    def form_entry(self, parent):
        entry = tk.Entry(
            parent, bg=INPUT, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, font=("Segoe UI", 10)
        )
        entry.pack(fill="x", padx=20, ipady=9)
        return entry

    def open_expense_form(self, expense_id=None):
        editing = expense_id is not None
        expense = None

        if editing:
            expense = database.get_expense(
                self.user["id"], expense_id
            )

        if editing and not expense:
            messagebox.showerror(
                "Error", "Expense not found.", parent=self.root
            )
            return

        form = tk.Toplevel(self.root)
        form.title("Edit Expense" if editing else "Add Expense")
        form.geometry("470x550")
        form.resizable(False, False)
        form.configure(bg=BG)
        form.transient(self.root)
        form.grab_set()

        tk.Label(
            form, text="Edit Expense" if editing else "Add Expense",
            bg=BG, fg=TEXT, font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", padx=30, pady=(25, 3))

        tk.Label(
            form,
            text="Update your expense information." if editing
            else "Enter the details of your expense.",
            bg=BG, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=30, pady=(0, 15))

        frame = self.card(form)
        frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        self.form_label(frame, "Description")
        desc_entry = self.form_entry(frame)

        self.form_label(frame, "Category")
        category = ttk.Combobox(
            frame, values=CATEGORIES, state="readonly",
            style="Budget.TCombobox", font=("Segoe UI", 10)
        )
        category.pack(fill="x", padx=20)

        self.form_label(frame, "Amount")
        amount_entry = self.form_entry(frame)

        self.form_label(frame, "Date (YYYY-MM-DD)")
        date_entry = self.form_entry(frame)

        if editing:
            desc_entry.insert(0, expense[2])
            category.set(expense[3])
            amount_entry.insert(0, str(expense[4]))
            date_entry.insert(0, str(expense[1]))
        else:
            category.set("Food")
            date_entry.insert(0, str(date.today()))

        def save():
            desc = desc_entry.get().strip()
            selected_category = category.get().strip()
            amount_text = amount_entry.get().strip()
            date_text = date_entry.get().strip()

            if not desc:
                messagebox.showwarning(
                    "Missing Information",
                    "Please enter a description.",
                    parent=form
                )
                return

            if not selected_category:
                messagebox.showwarning(
                    "Missing Information",
                    "Please select a category.",
                    parent=form
                )
                return

            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Invalid Amount",
                    "Enter an amount greater than 0.",
                    parent=form
                )
                return

            try:
                expense_date = datetime.strptime(
                    date_text, "%Y-%m-%d"
                ).date()
            except ValueError:
                messagebox.showwarning(
                    "Invalid Date",
                    "Date must use YYYY-MM-DD.",
                    parent=form
                )
                return

            try:
                if editing:
                    database.update_expense(
                        self.user["id"], expense_id,
                        desc, selected_category,
                        amount, expense_date
                    )
                    message = "Expense updated successfully."
                else:
                    database.add_expense(
                        self.user["id"], desc,
                        selected_category, amount, expense_date
                    )
                    message = "Expense added successfully."

                form.destroy()
                self.show_dashboard()
                messagebox.showinfo(
                    "Success", message, parent=self.root
                )

            except Exception as e:
                messagebox.showerror(
                    "Database Error", str(e), parent=form
                )

        buttons = tk.Frame(frame, bg=CARD)
        buttons.pack(fill="x", padx=20, pady=20)

        self.action_button(
            buttons, "Save", save, PRIMARY, "white"
        ).pack(side="left", padx=(0, 8))

        self.action_button(
            buttons, "Cancel", form.destroy, "#F3F4F6", TEXT
        ).pack(side="left")

        desc_entry.focus()

    # --------------------------------------------------------
    # Budget
    # --------------------------------------------------------
    def open_set_budget(self):
        form = tk.Toplevel(self.root)
        form.title("Set Monthly Budget")
        form.geometry("430x340")
        form.resizable(False, False)
        form.configure(bg=BG)
        form.transient(self.root)
        form.grab_set()

        tk.Label(
            form, text="Monthly Budget", bg=BG, fg=TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", padx=30, pady=(25, 3))

        tk.Label(
            form, text="Set the amount you want to spend this month.",
            bg=BG, fg=MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", padx=30, pady=(0, 15))

        card = self.card(form)
        card.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        self.form_label(card, "Budget Amount", top=25)

        entry = tk.Entry(
            card, bg=INPUT, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0, font=("Segoe UI", 12)
        )
        entry.pack(fill="x", padx=20, ipady=10)

        try:
            current_budget = database.get_budget(self.user["id"])
            entry.insert(0, f"{float(current_budget):.2f}")
        except Exception:
            entry.insert(0, "0.00")

        def save():
            try:
                amount = float(entry.get().strip())
                if amount < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Invalid Budget",
                    "Enter a valid budget amount.",
                    parent=form
                )
                return

            try:
                database.set_budget(self.user["id"], amount)
                form.destroy()
                self.show_dashboard()
                messagebox.showinfo(
                    "Budget Updated",
                    "Your monthly budget has been updated.",
                    parent=self.root
                )
            except Exception as e:
                messagebox.showerror(
                    "Database Error", str(e), parent=form
                )

        buttons = tk.Frame(card, bg=CARD)
        buttons.pack(fill="x", padx=20, pady=20)

        self.action_button(
            buttons, "Save Budget", save, PRIMARY, "white"
        ).pack(side="left", padx=(0, 8))
        self.action_button(
            buttons, "Cancel", form.destroy, "#F3F4F6", TEXT
        ).pack(side="left")

        entry.focus()
        entry.select_range(0, tk.END)

    # --------------------------------------------------------
    # Reports
    # --------------------------------------------------------
    def show_reports(self):
        self.clear_content()
        self.page_header(
            "Summary Reports",
            "Analyze spending and export the selected period as CSV or PDF."
        )

        card = self.card(self.content)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        controls = tk.Frame(card, bg=CARD)
        controls.pack(fill="x", padx=20, pady=18)

        tk.Label(
            controls, text="Month", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 6))

        month_var = tk.StringVar(value=datetime.now().strftime("%B"))
        month_combo = ttk.Combobox(
            controls, textvariable=month_var,
            values=[datetime(2000, m, 1).strftime("%B") for m in range(1, 13)],
            state="readonly", width=14, style="Budget.TCombobox"
        )
        month_combo.pack(side="left", padx=(0, 12))

        tk.Label(
            controls, text="Year", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 6))

        current_year = date.today().year
        year_var = tk.StringVar(value=str(current_year))
        year_combo = ttk.Combobox(
            controls, textvariable=year_var,
            values=[str(y) for y in range(current_year - 5, current_year + 2)],
            state="readonly", width=10, style="Budget.TCombobox"
        )
        year_combo.pack(side="left")

        self.action_button(
            controls, "Export CSV", lambda: export_csv(),
            GREEN, "white"
        ).pack(side="right", padx=(8, 0))

        self.action_button(
            controls, "Export PDF", lambda: export_pdf(),
            RED, "white"
        ).pack(side="right", padx=(8, 0))

        self.action_button(
            controls, "Printable View", lambda: printable_view(),
            PRIMARY, "white"
        ).pack(side="right")

        summary_frame = tk.Frame(card, bg=CARD)
        summary_frame.pack(fill="x", padx=20, pady=(0, 12))

        total_var = tk.StringVar()
        count_var = tk.StringVar()
        average_var = tk.StringVar()

        for title, var in [
            ("Total Spent", total_var),
            ("Transactions", count_var),
            ("Average Transaction", average_var)
        ]:
            box = self.card(summary_frame)
            box.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(
                box, text=title, bg=CARD, fg=MUTED,
                font=("Segoe UI", 9, "bold")
            ).pack(anchor="w", padx=14, pady=(12, 2))
            tk.Label(
                box, textvariable=var, bg=CARD, fg=TEXT,
                font=("Segoe UI", 15, "bold")
            ).pack(anchor="w", padx=14, pady=(0, 12))

        table_holder = tk.Frame(card, bg=CARD)
        table_holder.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        tree = self.make_treeview(
            table_holder,
            columns=("date", "description", "category", "amount")
        )
        self.attach_scrollbar(table_holder, tree)

        def get_report():
            month = datetime.strptime(month_var.get(), "%B").month
            year = int(year_var.get())
            rows = database.get_expenses(
                self.user["id"], month=month, year=year
            )
            total = sum(float(r[4]) for r in rows)
            count = len(rows)
            avg = total / count if count else 0

            total_var.set(money(total))
            count_var.set(str(count))
            average_var.set(money(avg))

            for item in tree.get_children():
                tree.delete(item)

            for row in rows:
                tree.insert(
                    "", "end",
                    values=(str(row[1]), row[2], row[3], money(row[4]))
                )
            return rows, total, count, avg, month, year

        def export_csv():
            rows, total, count, avg, month, year = get_report()
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title="Save CSV Report",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")]
            )
            if not path:
                return

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["BudgetBuddy Summary Report"])
                writer.writerow([
                    "Period",
                    f"{datetime(2000, month, 1).strftime('%B')} {year}"
                ])
                writer.writerow([])
                writer.writerow([
                    "Date", "Description", "Category", "Amount"
                ])
                for row in rows:
                    writer.writerow([
                        row[1], row[2], row[3], float(row[4])
                    ])
                writer.writerow([])
                writer.writerow(["Total Spent", total])
                writer.writerow(["Transactions", count])
                writer.writerow(["Average Transaction", avg])

            messagebox.showinfo(
                "Export Complete",
                f"CSV report saved to:\n{path}",
                parent=self.root
            )

        def export_pdf():
            rows, total, count, avg, month, year = get_report()
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title="Save PDF Report",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            if not path:
                return

            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.enums import TA_CENTER
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                from reportlab.platypus import (
                    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                )

                # Helvetica does not contain the Philippine peso sign (₱).
                # Use a Unicode TrueType font for the PDF so ₱ renders correctly.
                font_candidates = [
                    # Windows
                    r"C:\Windows\Fonts\arial.ttf",
                    r"C:\Windows\Fonts\calibri.ttf",
                    r"C:\Windows\Fonts\segoeui.ttf",
                    # Linux / common development environments
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
                ]

                font_path = next((fp for fp in font_candidates if os.path.exists(fp)), None)
                if not font_path:
                    raise RuntimeError(
                        "No Unicode TrueType font was found. "
                        "Install a font such as Arial or DejaVu Sans, then try again."
                    )

                font_name = "BudgetBuddyUnicode"
                bold_candidates = [
                    r"C:\Windows\Fonts\arialbd.ttf",
                    r"C:\Windows\Fonts\calibrib.ttf",
                    r"C:\Windows\Fonts\segoeuib.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
                ]
                bold_path = next((fp for fp in bold_candidates if os.path.exists(fp)), None)
                bold_name = "BudgetBuddyUnicodeBold"

                # Register fonts only once per application run.
                if font_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                if bold_path and bold_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                else:
                    bold_name = font_name

                doc = SimpleDocTemplate(
                    path,
                    pagesize=A4,
                    rightMargin=36,
                    leftMargin=36,
                    topMargin=36,
                    bottomMargin=36
                )

                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    "BudgetBuddyTitle",
                    parent=styles["Title"],
                    fontName=bold_name,
                    fontSize=20,
                    leading=24,
                    alignment=TA_CENTER,
                    spaceAfter=8
                )
                normal_style = ParagraphStyle(
                    "BudgetBuddyNormal",
                    parent=styles["Normal"],
                    fontName=font_name,
                    fontSize=9,
                    leading=12
                )
                table_header_style = ParagraphStyle(
                    "BudgetBuddyTableHeader",
                    parent=normal_style,
                    fontName=bold_name,
                    textColor=colors.white,
                    fontSize=8,
                    leading=10
                )
                table_cell_style = ParagraphStyle(
                    "BudgetBuddyTableCell",
                    parent=normal_style,
                    fontSize=8,
                    leading=10
                )

                story = [
                    Paragraph("BudgetBuddy - Summary Report", title_style),
                    Paragraph(
                        f"Period: {datetime(2000, month, 1).strftime('%B')} {year}",
                        normal_style
                    ),
                    Spacer(1, 12)
                ]

                # Use Paragraph objects so the Unicode peso sign is rendered
                # through the registered TrueType font instead of Helvetica.
                data = [[
                    Paragraph("Date", table_header_style),
                    Paragraph("Description", table_header_style),
                    Paragraph("Category", table_header_style),
                    Paragraph("Amount", table_header_style)
                ]]

                for row in rows:
                    data.append([
                        Paragraph(str(row[1]), table_cell_style),
                        Paragraph(str(row[2]), table_cell_style),
                        Paragraph(str(row[3]), table_cell_style),
                        Paragraph(money(row[4]), table_cell_style)
                    ])

                if len(data) == 1:
                    data.append([
                        Paragraph("-", table_cell_style),
                        Paragraph("No expenses", table_cell_style),
                        Paragraph("-", table_cell_style),
                        Paragraph(money(0), table_cell_style)
                    ])

                table = Table(
                    data,
                    colWidths=[75, 190, 100, 85],
                    repeatRows=1
                )
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                    ("TOPPADDING", (0, 0), (-1, 0), 7),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
                    ("TOPPADDING", (0, 1), (-1, -1), 5),
                ]))
                story.append(table)
                story.append(Spacer(1, 14))
                story.append(Paragraph(
                    f"Total Spent: {money(total)}<br/>"
                    f"Transactions: {count}<br/>"
                    f"Average Transaction: {money(avg)}",
                    normal_style
                ))

                doc.build(story)

                messagebox.showinfo(
                    "Export Complete",
                    f"PDF report saved to:\n{path}",
                    parent=self.root
                )
            except ImportError as e:
                messagebox.showerror(
                    "PDF Export Unavailable",
                    "ReportLab could not be loaded.\n\n"
                    f"Error:\n{e}\n\n"
                    "Install it with:\n"
                    "python -m pip install reportlab",
                    parent=self.root
                )
            except Exception as e:
                messagebox.showerror(
                    "PDF Export Error",
                    str(e),
                    parent=self.root
                )

        def printable_view():
            rows, total, count, avg, month, year = get_report()

            win = tk.Toplevel(self.root)
            win.title("BudgetBuddy - Printable Summary")
            win.geometry("900x650")
            win.configure(bg="white")

            text = tk.Text(
                win, bg="white", fg="black",
                font=("Consolas", 10), wrap="none"
            )
            text.pack(fill="both", expand=True, padx=20, pady=(20, 8))

            text.insert(
                "end",
                "BUDGETBUDDY - SUMMARY REPORT\n"
                f"Period: {datetime(2000, month, 1).strftime('%B')} {year}\n"
                f"{'=' * 78}\n"
            )
            text.insert(
                "end",
                f"{'Date':<14}{'Description':<30}{'Category':<18}{'Amount':>14}\n"
            )
            text.insert("end", "-" * 78 + "\n")

            for row in rows:
                desc = str(row[2])[:28]
                cat = str(row[3])[:16]
                text.insert(
                    "end",
                    f"{str(row[1]):<14}{desc:<30}{cat:<18}{money(row[4]):>14}\n"
                )

            text.insert(
                "end",
                "-" * 78 + "\n"
                f"Total Spent: {money(total)}\n"
                f"Transactions: {count}\n"
                f"Average Transaction: {money(avg)}\n"
            )
            text.configure(state="disabled")

            def print_text():
                try:
                    content = text.get("1.0", "end-1c")
                    fd, temp_path = tempfile.mkstemp(
                        suffix=".txt", prefix="budgetbuddy_report_"
                    )
                    os.close(fd)
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    if os.name == "nt":
                        os.startfile(temp_path, "print")
                    elif sys.platform == "darwin":
                        subprocess.run(["lp", temp_path], check=False)
                    else:
                        subprocess.run(["lp", temp_path], check=False)

                    messagebox.showinfo(
                        "Print",
                        "The report was sent to the system printer.",
                        parent=win
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Print Error",
                        f"Could not print the report.\n\n{e}",
                        parent=win
                    )

            self.action_button(
                win, "Print Report", print_text, PRIMARY, "white"
            ).pack(pady=(0, 18))

        month_combo.bind("<<ComboboxSelected>>", lambda _: get_report())
        year_combo.bind("<<ComboboxSelected>>", lambda _: get_report())
        get_report()

    # --------------------------------------------------------
    # Audit trail
    # --------------------------------------------------------
    def show_audit_trail(self):
        if self.role != "admin":
            messagebox.showerror(
                "Access Denied",
                "Administrator access is required.",
                parent=self.root
            )
            return

        self.clear_content()
        self.page_header(
            "Transaction Audit Trail",
            "Review who added, edited, or deleted transactions and when it happened."
        )

        card = self.card(self.content)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        filter_frame = tk.Frame(card, bg=CARD)
        filter_frame.pack(fill="x", padx=18, pady=18)

        search_var = tk.StringVar()
        tk.Label(
            filter_frame, text="Search", bg=CARD, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 7))

        search = tk.Entry(
            filter_frame, textvariable=search_var, bg=INPUT,
            fg=TEXT, relief="flat", bd=0,
            font=("Segoe UI", 9), width=30
        )
        search.pack(side="left", ipady=8)

        holder = tk.Frame(card, bg=CARD)
        holder.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        columns = (
            "id", "time", "actor", "action",
            "description"
        )
        tree = ttk.Treeview(
            holder, columns=columns, show="headings",
            selectmode="browse", style="Budget.Treeview"
        )

        headings = {
            "id": "#", "time": "DATE / TIME",
            "actor": "USER", "action": "ACTION",
            "description": "DETAILS"
        }
        widths = {
            "id": 55, "time": 155, "actor": 130,
            "action": 100, "description": 500
        }

        for c in columns:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w")

        self.attach_scrollbar(holder, tree)

        def refresh(*_):
            for item in tree.get_children():
                tree.delete(item)
            logs = database.get_audit_logs()
            search_text = search_var.get().strip().lower()

            shown = 0
            for row in logs:
                # row: id, timestamp, actor, action, description
                haystack = " ".join(str(x) for x in row).lower()
                if search_text and search_text not in haystack:
                    continue
                tree.insert(
                    "", "end",
                    values=(
                        row[0], str(row[1]), row[2],
                        row[3], row[4]
                    )
                )
                shown += 1

            status.set(f"{shown} audit record(s)")

        status = tk.StringVar(value="")
        search.bind("<KeyRelease>", refresh)

        tk.Label(
            card, textvariable=status, bg=CARD, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(0, 15))

        refresh()

    # --------------------------------------------------------
    # Admin
    # --------------------------------------------------------
    def show_admin(self):
        if self.role != "admin":
            messagebox.showerror(
                "Access Denied",
                "Administrator access is required.",
                parent=self.root
            )
            return

        self.clear_content()
        self.page_header(
            "Administration",
            "Manage BudgetBuddy accounts and roles."
        )

        card = self.card(self.content)
        card.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        holder = tk.Frame(card, bg=CARD)
        holder.pack(fill="both", expand=True, padx=18, pady=18)

        columns = ("id", "name", "username", "role", "created")
        tree = ttk.Treeview(
            holder, columns=columns, show="headings",
            selectmode="browse", style="Budget.Treeview"
        )

        headings = {
            "id": "#", "name": "FULL NAME",
            "username": "USERNAME", "role": "ROLE",
            "created": "CREATED"
        }
        widths = {
            "id": 55, "name": 250, "username": 180,
            "role": 130, "created": 180
        }

        for c in columns:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w")

        self.attach_scrollbar(holder, tree)

        def refresh():
            for item in tree.get_children():
                tree.delete(item)
            for row in database.get_all_users():
                tree.insert(
                    "", "end",
                    values=(row[0], row[1], row[2], row[3], str(row[4]))
                )

        def change_role():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Nothing Selected",
                    "Select a user first.",
                    parent=self.root
                )
                return

            values = tree.item(selected[0], "values")
            user_id = int(values[0])
            current_role = values[3]
            new_role = "admin" if current_role == "user" else "user"

            if user_id == self.user["id"]:
                messagebox.showwarning(
                    "Action Not Allowed",
                    "You cannot change your own administrator role.",
                    parent=self.root
                )
                return

            if messagebox.askyesno(
                "Change Role",
                f"Change {values[1]}'s role from {current_role} to {new_role}?",
                parent=self.root
            ):
                try:
                    database.set_user_role(
                        user_id, new_role, self.user["id"]
                    )
                    refresh()
                    messagebox.showinfo(
                        "Role Updated",
                        f"{values[1]} is now a {new_role}.",
                        parent=self.root
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Database Error", str(e), parent=self.root
                    )

        footer = tk.Frame(card, bg=CARD)
        footer.pack(fill="x", padx=18, pady=(0, 18))

        self.action_button(
            footer, "Change Selected Role", change_role,
            PRIMARY, "white"
        ).pack(side="left")

        tk.Label(
            footer,
            text="Admin access is restricted to administrator accounts.",
            bg=CARD, fg=MUTED, font=("Segoe UI", 9)
        ).pack(side="right")

        refresh()

    # --------------------------------------------------------
    # Logout
    # --------------------------------------------------------
    def logout(self):
        if not messagebox.askyesno(
            "Log Out",
            "Log out of BudgetBuddy?",
            parent=self.root
        ):
            return

        for widget in self.root.winfo_children():
            widget.destroy()
        self.auth_window.build_login()


def main():
    try:
        database.initialize_database()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "BudgetBuddy Startup Error",
            f"{e}\n\n"
            "Make sure XAMPP MySQL is running and "
            "the MySQL settings in database.py are correct."
        )
        root.destroy()
        return

    root = tk.Tk()
    AuthWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
