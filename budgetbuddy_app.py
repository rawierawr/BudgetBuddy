import calendar
import csv
import functools
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
import customtkinter as ctk
import database


THEMES = {
    "light": dict(BG="#F3FAF6", CARD="#FFFFFF", INPUT="#F0FAF4", TEXT="#0F2E22",
                  MUTED="#4A5F54", BORDER="#DCEBE2", GRID="#DCEBE2", HEAD="#E2F4EA",
                  MINT="#CFEEDD", SEL="#B9E4CC", GREEN="#1F6F4A", GREEN_H="#185A3C",
                  ON_GREEN="#FFFFFF", PEACH="#F4A261", PEACH_H="#E08D4F",
                  ON_PEACH="#0F2E22", WARN="#B4501A", WARN_H="#9A4215", ON_WARN="#FFFFFF"),
    "dark": dict(BG="#0E1A15", CARD="#16251E", INPUT="#1F3329", TEXT="#EAF7EF",
                 MUTED="#9DB5A7", BORDER="#27403A", GRID="#27403A", HEAD="#1C2F26",
                 MINT="#1F3A2D", SEL="#2F5A47", GREEN="#4CBF8F", GREEN_H="#3AA77A",
                 ON_GREEN="#0B1F16", PEACH="#F4A261", PEACH_H="#E08D4F",
                 ON_PEACH="#0F2E22", WARN="#F4A261", WARN_H="#E08D4F", ON_WARN="#1A1208"),
}
T = dict(THEMES["light"])
CATEGORIES = ["Food", "Transportation", "Education", "Entertainment",
              "Shopping", "Bills", "Health", "Other"]
FONT = "Segoe UI"
ADMIN_CODE = os.environ.get("BUDGETBUDDY_ADMIN_CODE", "onlybudgetadmins")  # Override with an environment variable before deployment


def set_theme(name):
    T.clear()
    T.update(THEMES[name])
    ctk.set_appearance_mode(name)


def money(v):
    return f"₱{float(v or 0):,.2f}"


def font(size=12, bold=False):
    return (FONT, size, "bold" if bold else "normal")


def to_date(v):
    return v if isinstance(v, date) else datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def group_rows(rows):
    """{year: {month: [rows]}} sorted by date - used to separate exports by year and month."""
    g = {}
    for r in sorted(rows, key=lambda r: to_date(r[1])):
        d = to_date(r[1])
        g.setdefault(d.year, {}).setdefault(d.month, []).append(r)
    return g


def fresh_role(user):
    """Role is always read from the database, so an admin keeps the admin role after logging back in."""
    try:
        for u in database.get_all_users():
            if u[0] == user["id"]:
                return str(u[3]).lower()
    except Exception:
        pass
    return str(user.get("role", "user")).lower()


def pdf_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    fp = next((f for f in [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf",
                           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"] if os.path.exists(f)), None)
    if not fp:
        raise RuntimeError("No Unicode font found (Arial or DejaVu Sans) - needed for the peso sign.")
    if "BBFont" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("BBFont", fp))
    return "BBFont"


# ------------------------------------------------------------
# widget 
# ------------------------------------------------------------
def label(p, text="", size=12, bold=False, color="TEXT", **kw):
    return ctk.CTkLabel(p, text=text, text_color=T[color], font=font(size, bold), **kw)


def card(p, **kw):
    return ctk.CTkFrame(p, corner_radius=20, fg_color=T["CARD"],
                        border_width=1, border_color=T["BORDER"], **kw)


def button(p, text, cmd, kind="primary", **kw):
    fg, hv, tc = {
        "primary": (T["GREEN"], T["GREEN_H"], T["ON_GREEN"]),
        "peach": (T["PEACH"], T["PEACH_H"], T["ON_PEACH"]),
        "mint": (T["MINT"], T["SEL"], T["TEXT"]),
        "danger": (T["WARN"], T["WARN_H"], T["ON_WARN"]),
        "ghost": ("transparent", T["MINT"], T["TEXT"]),
    }[kind]
    return ctk.CTkButton(p, text=text, command=cmd, fg_color=fg, hover_color=hv,
                         text_color=tc, corner_radius=14, font=font(12, True),
                         height=kw.pop("height", 38), **kw)


def link(p, text, cmd, **kw):
    return ctk.CTkButton(p, text=text, command=cmd, fg_color="transparent",
                         hover_color=T["MINT"], text_color=T["GREEN"],
                         font=font(12, True), corner_radius=12, height=28, **kw)


def entry(p, ph="", show=None, **kw):
    return ctk.CTkEntry(p, placeholder_text=ph, show=show, height=40, corner_radius=14,
                        fg_color=T["INPUT"], border_color=T["BORDER"], text_color=T["TEXT"],
                        placeholder_text_color=T["MUTED"], font=font(12), **kw)


def combo(p, values, var=None, width=150, cmd=None):
    return ctk.CTkComboBox(p, values=values, variable=var, width=width, height=40,
                           corner_radius=14, state="readonly", command=cmd, font=font(12),
                           fg_color=T["INPUT"], border_color=T["BORDER"],
                           button_color=T["GREEN"], button_hover_color=T["GREEN_H"],
                           text_color=T["TEXT"], dropdown_fg_color=T["CARD"],
                           dropdown_text_color=T["TEXT"], dropdown_hover_color=T["MINT"])


def checkbox(p, text, var, cmd, width=110):
    return ctk.CTkCheckBox(p, text=text, variable=var, command=cmd, text_color=T["TEXT"],
                           fg_color=T["GREEN"], hover_color=T["GREEN_H"], border_color=T["MUTED"],
                           checkmark_color=T["ON_GREEN"], font=font(11), width=width,
                           checkbox_width=18, checkbox_height=18)


def dialog(root, title, w, h):
    d = ctk.CTkToplevel(root)
    d.title(title)
    d.geometry(f"{w}x{h}")
    d.resizable(False, False)
    d.configure(fg_color=T["BG"])
    d.transient(root)
    d.after(150, d.grab_set)
    return d


def style_tree():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("B.Treeview", background=T["CARD"], fieldbackground=T["CARD"],
                foreground=T["TEXT"], rowheight=36, borderwidth=1, relief="solid", font=font(10))
    s.configure("B.Treeview.Heading", background=T["HEAD"], foreground=T["TEXT"],
                font=font(10, True), relief="solid", borderwidth=1, padding=8)
    s.map("B.Treeview.Heading", background=[("active", T["HEAD"])])
    s.map("B.Treeview", background=[("selected", T["SEL"])],
          foreground=[("selected", T["TEXT"])])
    s.configure("Vertical.TScrollbar", background=T["HEAD"], troughcolor=T["CARD"],
                bordercolor=T["CARD"], arrowcolor=T["TEXT"])


def make_tree(p, cols, height=10):
    t = ttk.Treeview(p, columns=[c[0] for c in cols], show="headings",
                     style="B.Treeview", selectmode="browse", height=height)
    for key, head, w, anchor in cols:
        t.heading(key, text=head)
        t.column(key, width=w, anchor=anchor)
    sb = ttk.Scrollbar(p, orient="vertical", command=t.yview)
    t.configure(yscrollcommand=sb.set)
    t.tag_configure("row_a", background=T["CARD"])
    t.tag_configure("row_b", background=T["BG"])
    t.tag_configure("hover", background=T["MINT"], foreground=T["TEXT"])
    hover_state = {"item": None}
    def on_motion(event):
        row_id = t.identify_row(event.y)
        old_id = hover_state["item"]
        if old_id and old_id in t.get_children(""):
            tags = tuple(tag for tag in t.item(old_id, "tags") if tag != "hover")
            t.item(old_id, tags=tags)
        if row_id:
            tags = tuple(tag for tag in t.item(row_id, "tags") if tag != "hover") + ("hover",)
            t.item(row_id, tags=tags)
        hover_state["item"] = row_id
    def on_leave(_event):
        old_id = hover_state["item"]
        if old_id and old_id in t.get_children(""):
            t.item(old_id, tags=tuple(tag for tag in t.item(old_id, "tags") if tag != "hover"))
        hover_state["item"] = None
    t.bind("<Motion>", on_motion, add="+")
    t.bind("<Leave>", on_leave, add="+")
    t.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return t


def fill_tree(tree, rows):
    tree.delete(*tree.get_children())
    for i, r in enumerate(rows):
        tree.insert("", "end", values=tuple(r), tags=("row_a" if i % 2 == 0 else "row_b",))


FULL_COLS = [("id", "#", 50, "center"), ("date", "DATE", 110, "center"),
             ("desc", "DESCRIPTION", 320, "w"), ("cat", "CATEGORY", 170, "w"),
             ("amt", "AMOUNT", 130, "e")]
RECENT_COLS = FULL_COLS[1:]


# ------------------------------------------------------------
# Login / register / admin login
# ------------------------------------------------------------
class Auth:
    def __init__(self, root):
        self.root = root
        root.geometry("980x750")
        root.minsize(860, 580)
        self.show("login")

    def show(self, mode):
        self.mode = mode
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title("BudgetBuddy - Login")
        self.root.configure(fg_color=T["BG"])

        wrap = ctk.CTkFrame(self.root, fg_color=T["CARD"], corner_radius=28,
                            border_width=1, border_color=T["BORDER"])
        wrap.pack(fill="both", expand=True, padx=36, pady=32)

        left = ctk.CTkFrame(wrap, width=330, corner_radius=24, fg_color=T["GREEN"])
        left.pack(side="left", fill="y", padx=10, pady=10)
        left.pack_propagate(False)
        label(left, "₱ BudgetBuddy", 26, True, "ON_GREEN").pack(anchor="w", padx=30, pady=(70, 14))
        label(left, "Spend smart.\nSave more.", 20, False, "ON_GREEN", justify="left").pack(anchor="w", padx=30)
        label(left, "Track expenses, set your budget,\nand understand your spending.",
              12, False, "ON_GREEN", justify="left").pack(anchor="w", padx=30, pady=(16, 0))
        ctk.CTkLabel(left, text="  Every peso counts  ", fg_color=T["PEACH"], text_color=T["ON_PEACH"],
                     corner_radius=14, font=font(11, True), height=30).pack(anchor="w", padx=30, pady=(28, 0))

        right = ctk.CTkFrame(wrap, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        if mode in ("admin", "admin_register"):
            top = button(right, "← User login", lambda: self.show("login"), "peach", width=120, height=34)
        else:
            top = button(right, "Admin", lambda: self.show("admin"), "peach", width=90, height=34)
        top.place(relx=1, x=-22, y=18, anchor="ne")

        titles = {"login": ("Welcome back!", "Log in to see how your budget is doing."),
                  "admin": ("Admin log in", "Enter your administrator details."),
                  "register": ("Create an account", "Start tracking your expenses today."),
                  "admin_register": ("Admin sign up", "Create an administrator account.")}
        form = ctk.CTkFrame(right, fg_color="transparent")
        form.place(relx=0.5, rely=0.52, anchor="center", relwidth=0.78)
        label(form, titles[mode][0], 28, True).pack(anchor="w")
        label(form, titles[mode][1], 12, False, "MUTED").pack(anchor="w", pady=(4, 22))

        reg = mode in ("register", "admin_register")
        if reg:
            self.fn = entry(form, "Full name")
            self.fn.pack(fill="x", pady=(0, 10))
        self.un = entry(form, "Username")
        self.un.pack(fill="x", pady=(0, 10))
        self.pw = entry(form, "Password", "•")
        self.pw.pack(fill="x", pady=(0, 10))
        if reg:
            self.cf = entry(form, "Confirm password", "•")
            self.cf.pack(fill="x", pady=(0, 10))
            admin_reg = mode == "admin_register"
            if admin_reg:
                self.code = entry(form, "Admin access code", "•")
                self.code.pack(fill="x", pady=(0, 10))
            button(form, "Create admin account" if admin_reg else "Create account",
                   self.register, height=44).pack(fill="x", pady=(14, 0))
            link(form, "Back to admin log in" if admin_reg else "Back to log in",
                 lambda: self.show("admin" if admin_reg else "login")).pack(pady=(16, 0))
        else:
            link(form, "Forgot password?", self.forgot).pack(anchor="e")
            button(form, "Log in", self.login, height=44).pack(fill="x", pady=(8, 0))
            self.pw.bind("<Return>", lambda _: self.login())
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(pady=(18, 0))
            if mode == "login":
                label(row, "New here?", 12, False, "MUTED").pack(side="left")
                link(row, "Create new account", lambda: self.show("register")).pack(side="left")
            else:
                label(row, "Need an admin account?", 12, False, "MUTED").pack(side="left")
                link(row, "Sign up", lambda: self.show("admin_register")).pack(side="left")

    def login(self):
        u, p = self.un.get().strip(), self.pw.get()
        if not u or not p:
            return messagebox.showwarning("Missing Information", "Please enter your username and password.")
        try:
            user = database.authenticate_user(u, p)
        except Exception as e:
            return messagebox.showerror("Database Error", str(e))
        if not user:
            return messagebox.showerror("Login Failed", "Incorrect username or password.")
        role = fresh_role(user)  # always from the database, never lost between logins
        if self.mode == "admin" and role != "admin":
            return messagebox.showerror("Access Denied", "This account is not an administrator.")
        user["role"] = role
        for w in self.root.winfo_children():
            w.destroy()
        App(self.root, user, self)  # admin accounts always open the admin menus

    def register(self):
        name, u, p, c = self.fn.get().strip(), self.un.get().strip(), self.pw.get(), self.cf.get()
        if not (name and u and p and c):
            return messagebox.showwarning("Missing Information", "Please complete all fields.")
        if p != c:
            return messagebox.showerror("Passwords Do Not Match", "Please make sure both passwords match.")
        admin = self.mode == "admin_register"
        if admin and self.code.get() != ADMIN_CODE:
            return messagebox.showerror("Access Denied", "Incorrect admin access code.")
        try:
            if admin:
                # Database enforces first-admin bootstrap and preserves role='admin'.
                database.create_admin_account(name, u, p, actor_admin_id=None, secret_code=self.code.get())
            else:
                database.register_user(name, u, p)
            messagebox.showinfo("Account Created",
                                "Your admin account is ready." if admin else "Your BudgetBuddy account is ready.")
            self.show("admin" if admin else "login")
        except ValueError as e:
            messagebox.showwarning("Registration Problem", str(e))
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def forgot(self):
        d = dialog(self.root, "Change Password", 420, 470)
        label(d, "Change password", 22, True).pack(anchor="w", padx=30, pady=(26, 2))
        label(d, "Enter your account details and a new password.", 11, False, "MUTED").pack(anchor="w", padx=30, pady=(0, 14))
        box = card(d)
        box.pack(fill="both", expand=True, padx=26, pady=(0, 26))
        u = entry(box, "Username")
        c = entry(box, "Current password", "•")
        n = entry(box, "New password (6+ characters)", "•")
        for e in (u, c, n):
            e.pack(fill="x", padx=20, pady=(16, 0))

        def save():
            if len(n.get()) < 6:
                return messagebox.showwarning("Weak Password", "New password must be at least 6 characters.", parent=d)
            try:
                user = database.authenticate_user(u.get().strip(), c.get())
                if not user:
                    return messagebox.showerror("Failed", "Incorrect username or current password.", parent=d)
                database.change_password(user["id"], c.get(), n.get())
                messagebox.showinfo("Password Changed", "Your password has been changed.", parent=d)
                d.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=d)

        button(box, "Save password", save, height=42).pack(fill="x", padx=20, pady=22)


# ------------------------------------------------------------
# Role guards (checked in code, not only by hiding buttons)
# ------------------------------------------------------------
def user_only(fn):
    @functools.wraps(fn)
    def wrapper(self, *a, **k):
        if self.admin:
            return messagebox.showerror("Not Available", "Administrator accounts do not have personal expense pages.", parent=self.root)
        return fn(self, *a, **k)
    return wrapper


def admin_only(fn):
    @functools.wraps(fn)
    def wrapper(self, *a, **k):
        if self.require_admin():
            return fn(self, *a, **k)
    return wrapper


# ------------------------------------------------------------
# Main application
# ------------------------------------------------------------
class App:
    def __init__(self, root, user, auth):
        self.root, self.user, self.auth = root, user, auth
        self.role = str(user.get("role", "user")).lower()
        self.admin = self.role == "admin"
        self.dark = T["BG"] == THEMES["dark"]["BG"]
        self.page, self.nav = (self.admin_home, "Overview") if self.admin else (self.dashboard, "Home")
        self.dashboard_month = datetime.now().month
        self.dashboard_year = datetime.now().year
        self.menu = None
        root.bind("<Button-1>", self.outside_click, add="+")
        root.bind("<Escape>", lambda e: self.close_menu(), add="+")
        root.title(f"BudgetBuddy - {user['full_name']}")
        root.geometry("1350x950")
        root.minsize(1050, 680)
        self.build()
        if not self.admin:  # admins do not keep a personal budget
            root.after(250, self.ensure_monthly_budget)

    def require_admin(self):
        if not self.admin or fresh_role(self.user) != "admin":
            messagebox.showerror("Access Denied", "Administrator access is required.", parent=self.root)
            self.root.after(50, lambda: self.auth.show("login"))
            return False
        return True

    def build(self):
        self.menu = None
        for w in self.root.winfo_children():
            w.destroy()
        self.root.configure(fg_color=T["BG"])
        style_tree()
        self.topbar()
        self.body = ctk.CTkFrame(self.root, fg_color="transparent")
        self.body.pack(fill="both", expand=True)
        self.page()

    def go(self, page, nav):
        self.page, self.nav = page, nav
        self.build()

    def topbar(self):
        bar = ctk.CTkFrame(self.root, fg_color=T["CARD"], corner_radius=0, height=70)
        bar.pack(fill="x")
        ctk.CTkLabel(bar, text="₱", width=40, height=40, corner_radius=12, fg_color=T["GREEN"],
                     text_color=T["ON_GREEN"], font=font(16, True)).pack(side="left", padx=(24, 8), pady=15)
        label(bar, "BudgetBuddy", 18, True).pack(side="left", padx=(0, 20))
        if self.admin:  # admin: overview, users, audit trail and reports only
            items = [("Overview", lambda: self.go(self.admin_home, "Overview")),
                     ("Users", lambda: self.go(self.admin_users, "Users")),
                     ("Audit Trail", lambda: self.go(self.audit_page, "Audit Trail")),
                     ("Reports", lambda: self.go(self.admin_reports, "Reports"))]
        else:
            items = [("Home", lambda: self.go(self.dashboard, "Home")),
                     ("Add Expense", self.open_form),
                     ("Expenses", lambda: self.go(lambda: self.expenses("view"), "Expenses")),
                     ("Edit Expense", lambda: self.go(lambda: self.expenses("edit"), "Edit Expense")),
                     ("Delete Expense", lambda: self.go(lambda: self.expenses("delete"), "Delete Expense")),
                     ("Budget", self.open_budget),
                     ("Reports", self.open_reports)]
        for name, cmd in items:
            button(bar, name, cmd, "primary" if name == self.nav else "ghost",
                   width=max(66, len(name) * 7 + 20), height=34).pack(side="left", padx=2)
        ctk.CTkLabel(bar, text="Administrator" if self.admin else "User", fg_color=T["MINT"],
                     text_color=T["TEXT"], corner_radius=14, font=font(10, True), width=76,
                     height=30).pack(side="right", padx=(4, 10))
        self.gear = button(bar, "⚙ Settings ▾", self.open_settings_menu, "peach", width=118, height=34)
        self.gear.pack(side="right", padx=(4, 8))

    def toggle(self):
        self.dark = not self.dark
        set_theme("dark" if self.dark else "light")
        self.build()

    def header(self, title, sub, right=""):
        h = ctk.CTkFrame(self.body, fg_color="transparent")
        h.pack(fill="x", padx=28, pady=(22, 12))
        l = ctk.CTkFrame(h, fg_color="transparent")
        l.pack(side="left")
        label(l, title, 28, True).pack(anchor="w")
        label(l, sub, 12, False, "MUTED").pack(anchor="w")
        if right:
            ctk.CTkLabel(h, text=right, fg_color=T["CARD"], text_color=T["MUTED"], corner_radius=14,
                         font=font(11, True)).pack(side="right", ipadx=10, ipady=4)

    # ---------------- Dashboard ----------------
    @user_only
    def dashboard(self):
        uid = self.user["id"]
        try:
            selected_month = self.dashboard_month
            selected_year = self.dashboard_year
            budget = float(database.get_budget(uid, year=selected_year, month=selected_month)) if selected_month else float(database.get_year_budget_total(uid, selected_year))
            total = float(database.get_total_expenses(uid, month=selected_month, year=selected_year))
            count = database.get_transaction_count(uid, month=selected_month, year=selected_year)
            recent = database.get_recent_expenses(uid, limit=3) if selected_month == datetime.now().month and selected_year == datetime.now().year else database.get_expenses(uid, month=selected_month, year=selected_year)[:3]
            cats = database.get_category_totals(uid, month=selected_month, year=selected_year)
        except Exception as e:
            return messagebox.showerror("Database Error", str(e), parent=self.root)
        rem = budget - total
        first = self.user["full_name"].split()[0]
        self.header("Dashboard", f"Good day, {first}! Take control of your money, one expense at a time.",
                    datetime.now().strftime("%a • %b %d • %I:%M %p"))

        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", padx=22)
        stats = [("Monthly Budget", money(budget), "GREEN"), ("Total Spent", money(total), "WARN"),
                 ("Remaining", money(rem), "GREEN" if rem >= 0 else "WARN"), ("Transactions", str(count), "TEXT")]
        for i, (t, v, c) in enumerate(stats):
            row.columnconfigure(i, weight=1, uniform="s")
            cd = card(row)
            cd.grid(row=0, column=i, sticky="nsew", padx=6)
            label(cd, t, 12, True, "MUTED").pack(anchor="w", padx=20, pady=(16, 2))
            label(cd, v, 24, True, c).pack(anchor="w", padx=20, pady=(0, 16))

        mid = ctk.CTkFrame(self.body, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=22, pady=12)
        ov = card(mid)
        ov.pack(side="left", fill="both", expand=True, padx=(6, 8))
        chart_top = ctk.CTkFrame(ov, fg_color="transparent")
        chart_top.pack(fill="x", padx=22, pady=(18, 0))
        label(chart_top, "Spending Overview", 16, True).pack(side="left")
        month_names = [datetime(2000, m, 1).strftime("%B") for m in range(1, 13)]
        month_options = ["All months"] + month_names
        year_options = [str(y) for y in range(datetime.now().year - 8, datetime.now().year + 1)]
        self.chart_month_var = tk.StringVar(value=month_names[self.dashboard_month - 1] if self.dashboard_month else "All months")
        self.chart_year_var = tk.StringVar(value=str(self.dashboard_year))
        combo(chart_top, month_options, self.chart_month_var, 125,
              lambda v: self.update_dashboard_period(v, self.chart_year_var.get())).pack(side="right", padx=(6, 0))
        combo(chart_top, year_options, self.chart_year_var, 95,
              lambda v: self.update_dashboard_period(self.chart_month_var.get(), v)).pack(side="right", padx=(6, 0))
        label(ov, "Spending by category for the selected period", 11, False, "MUTED").pack(anchor="w", padx=22, pady=(2, 4))
        cv = tk.Canvas(ov, bg=T["CARD"], highlightthickness=0, height=230)
        cv.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.chart(cv, cats)

        qa = card(mid, width=270)
        qa.pack(side="right", fill="y", padx=(8, 6))
        qa.pack_propagate(False)
        label(qa, "Quick Actions", 16, True).pack(anchor="w", padx=22, pady=(18, 12))
        for text, cmd, kind in [("+  Add Expense", self.open_form, "primary"),
                                ("₱  Set Monthly Budget", self.open_budget, "peach"),
                                ("▤  View Expenses", lambda: self.go(lambda: self.expenses("view"), "Expenses"), "mint"),
                                ("✎  Edit Expense", lambda: self.go(lambda: self.expenses("edit"), "Edit Expense"), "mint")]:
            button(qa, text, cmd, kind, anchor="w", height=44).pack(fill="x", padx=18, pady=5)

        rc = card(self.body)
        rc.pack(fill="x", padx=28, pady=(0, 22))
        top = ctk.CTkFrame(rc, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(16, 8))
        label(top, "Recent Transactions", 16, True).pack(side="left")
        link(top, "View All →", lambda: self.go(lambda: self.expenses("view"), "Expenses")).pack(side="right")
        holder = tk.Frame(rc, bg=T["CARD"])
        holder.pack(fill="x", padx=22, pady=(0, 18))
        tree = make_tree(holder, RECENT_COLS, height=3)
        for r in recent:
            tree.insert("", "end", values=(str(r[1]), r[2], r[3], money(r[4])))

    def update_dashboard_period(self, month_value, year_value):
        try:
            self.dashboard_year = int(year_value)
            self.dashboard_month = None if month_value == "All months" else datetime.strptime(month_value, "%B").month
            self.build()
        except (ValueError, TypeError):
            messagebox.showwarning("Invalid period", "Choose a valid month and year.", parent=self.root)

    def ensure_monthly_budget(self):
        """Ask for a budget on first use of an account/month, before normal use continues."""
        try:
            has_budget = database.has_monthly_budget(self.user["id"])
        except Exception as exc:
            messagebox.showerror("Budget Check Failed", str(exc), parent=self.root)
            return
        if not has_budget:
            self.open_budget(required=True)

    def chart(self, cv, cats):
        def draw(_=None):
            if not cv.winfo_exists():
                return
            cv.delete("all")
            w, h = max(cv.winfo_width(), 500), max(cv.winfo_height(), 200)
            if not cats:
                cv.create_text(w / 2, h / 2, text="No spending recorded this month.", fill=T["MUTED"], font=font(11))
                return
            items = list(cats.items())
            top_v = max(float(v) for _, v in items) or 1
            left, right, bottom, top = 70, w - 25, h - 40, 24
            slot = (right - left) / len(items)
            bw = min(70, slot * 0.55)
            for i in range(5):
                y = bottom - (bottom - top) * i / 4
                cv.create_line(left, y, right, y, fill=T["GRID"])
                cv.create_text(left - 8, y, text=money(top_v * i / 4), anchor="e", fill=T["MUTED"], font=font(8))
            for i, (name, v) in enumerate(items):
                v = float(v)
                cx = left + slot * (i + 0.5)
                y1 = bottom - (bottom - top) * v / top_v
                color = T["GREEN"] if i % 2 == 0 else T["PEACH"]
                cv.create_rectangle(cx - bw / 2, y1, cx + bw / 2, bottom, fill=color, outline="")
                cv.create_text(cx, bottom + 16, text=name[:12], fill=T["TEXT"], font=font(8, True))
                cv.create_text(cx, max(y1 - 10, 10), text=money(v), fill=T["TEXT"], font=font(8, True))
        cv.bind("<Configure>", draw)
        cv.after(80, draw)

    # ---------------- View / Edit / Delete ----------------
    @user_only
    def expenses(self, mode):
        titles = {"view": ("View Expenses", "Browse your complete expense history and filter it by month or year."),
                  "edit": ("Edit Expense", "Search the list, select one row, then edit its details."),
                  "delete": ("Delete Expense", "Search the list, select one row, then delete it.")}
        self.header(*titles[mode])
        cd = card(self.body)
        cd.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        bar = ctk.CTkFrame(cd, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=16)
        search = entry(bar, "Search description or category", width=260)
        search.pack(side="left", padx=(0, 10))
        mv, yv = tk.StringVar(value="All Months"), tk.StringVar(value="All Years")
        months = ["All Months"] + [datetime(2000, m, 1).strftime("%B") for m in range(1, 13)]
        yr = date.today().year
        years = ["All Years"] + [str(y) for y in range(yr - 5, yr + 2)]
        combo(bar, months, mv, 150, lambda _: refresh()).pack(side="left", padx=(0, 10))
        combo(bar, years, yv, 120, lambda _: refresh()).pack(side="left")

        holder = tk.Frame(cd, bg=T["CARD"])
        holder.pack(fill="both", expand=True, padx=18)
        tree = make_tree(holder, FULL_COLS, height=14)
        foot = ctk.CTkFrame(cd, fg_color="transparent")
        foot.pack(fill="x", padx=18, pady=16)
        status = label(foot, "", 11, False, "MUTED")
        status.pack(side="left")

        def refresh(*_):
            m = None if mv.get() == "All Months" else datetime.strptime(mv.get(), "%B").month
            y = None if yv.get() == "All Years" else int(yv.get())
            try:
                rows = database.get_expenses(self.user["id"], search=search.get().strip(), month=m, year=y)
            except Exception as e:
                return messagebox.showerror("Database Error", str(e), parent=self.root)
            tree.delete(*tree.get_children())
            for i, r in enumerate(rows):
                tree.insert("", "end", values=(r[0], str(r[1]), r[2], r[3], money(r[4])),
                            tags=("row_a" if i % 2 == 0 else "row_b",))
            status.configure(text=f"{len(rows)} expense(s) found")

        def selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Nothing Selected", "Select an expense from the table first.", parent=self.root)
                return None
            return tree.item(sel[0], "values")

        def edit():
            v = selected()
            if v:
                self.open_form(int(v[0]))

        def delete():
            v = selected()
            if v and messagebox.askyesno("Delete Expense?", f"Delete '{v[2]}' for {v[4]}?\n\nThis cannot be undone.",
                                         parent=self.root):
                try:
                    database.delete_expense(self.user["id"], int(v[0]))
                    refresh()
                except Exception as e:
                    messagebox.showerror("Database Error", str(e), parent=self.root)

        search.bind("<KeyRelease>", refresh)
        if mode == "view":
            button(foot, "Add Expense", self.open_form, width=140).pack(side="right")
        elif mode == "edit":
            tree.bind("<Double-1>", lambda _: edit())
            button(foot, "Edit Selected", edit, width=140).pack(side="right")
        else:
            button(foot, "Delete Selected", delete, "danger", width=150).pack(side="right")
        refresh()

    # ---------------- Dialogs ----------------
    @user_only
    def open_form(self, expense_id=None):
        exp = None
        if expense_id is not None:
            exp = database.get_expense(self.user["id"], expense_id)
            if not exp:
                return messagebox.showerror("Error", "Expense not found.", parent=self.root)
        d = dialog(self.root, "Edit Expense" if exp else "Add Expense", 470, 590)
        label(d, "Edit Expense" if exp else "Add Expense", 24, True).pack(anchor="w", padx=30, pady=(24, 2))
        label(d, "Enter the details of your expense.", 11, False, "MUTED").pack(anchor="w", padx=30, pady=(0, 12))
        box = card(d)
        box.pack(fill="both", expand=True, padx=26, pady=(0, 26))

        def field(name, widget):
            label(box, name, 11, True).pack(anchor="w", padx=22, pady=(14, 4))
            widget.pack(fill="x", padx=22)
            return widget
        desc = field("Description", entry(box))
        cat = field("Category", combo(box, CATEGORIES, None, 200))
        amt = field("Amount", entry(box))
        dt = field("Date (YYYY-MM-DD)", entry(box))
        if exp:
            desc.insert(0, exp[2]); cat.set(exp[3]); amt.insert(0, str(exp[4])); dt.insert(0, str(exp[1]))
        else:
            cat.set("Food"); dt.insert(0, str(date.today()))

        def save():
            try:
                amount = float(amt.get().strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                return messagebox.showwarning("Invalid Amount", "Enter an amount greater than 0.", parent=d)
            try:
                when = datetime.strptime(dt.get().strip(), "%Y-%m-%d").date()
            except ValueError:
                return messagebox.showwarning("Invalid Date", "Date must use YYYY-MM-DD.", parent=d)
            if not desc.get().strip():
                return messagebox.showwarning("Missing Information", "Please enter a description.", parent=d)
            try:
                args = (self.user["id"],) + ((expense_id,) if exp else ()) + (desc.get().strip(), cat.get(), amount, when)
                (database.update_expense if exp else database.add_expense)(*args)
            except Exception as e:
                return messagebox.showerror("Database Error", str(e), parent=d)
            d.destroy()
            self.build()

        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=22)
        button(row, "Save", save, width=110).pack(side="left", padx=(0, 8))
        button(row, "Cancel", d.destroy, "mint", width=110).pack(side="left")

    @user_only
    def open_budget(self, required=False):
        d = dialog(self.root, "Set Monthly Budget", 430, 330)
        if required:
            d.protocol("WM_DELETE_WINDOW", lambda: messagebox.showwarning(
                "Budget Required", "Please set this month's budget before continuing.", parent=d))
        label(d, "Monthly Budget", 24, True).pack(anchor="w", padx=30, pady=(24, 2))
        label(d, f"Set your budget for {datetime.now().strftime('%B %Y')}.", 11, False, "MUTED").pack(anchor="w", padx=30, pady=(0, 12))
        box = card(d)
        box.pack(fill="both", expand=True, padx=26, pady=(0, 26))
        label(box, "Budget Amount", 11, True).pack(anchor="w", padx=22, pady=(22, 4))
        e = entry(box)
        e.pack(fill="x", padx=22)
        try:
            e.insert(0, f"{float(database.get_budget(self.user['id'])):.2f}")
        except Exception:
            e.insert(0, "0.00")

        def save():
            try:
                amount = float(e.get().strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                return messagebox.showwarning("Invalid Budget", "Enter a budget greater than zero.", parent=d)
            try:
                database.set_budget(self.user["id"], amount)
            except Exception as ex:
                return messagebox.showerror("Database Error", str(ex), parent=d)
            d.destroy()
            self.build()

        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=22)
        button(row, "Save Budget", save, width=130).pack(side="left", padx=(0, 8))
        if not required:
            button(row, "Cancel", d.destroy, "mint", width=100).pack(side="left")

    # ---------------- Settings dropdown and account settings ----------------
    def close_menu(self):
        m = self.menu
        self.menu = None
        if m is not None and m.winfo_exists():
            m.destroy()

    def outside_click(self, e):
        m = self.menu
        if m is None or not m.winfo_exists():
            self.menu = None
            return
        w = e.widget
        while w is not None and not isinstance(w, str):
            if w is m or w is getattr(self, "gear", None):
                return  # click inside the dropdown (or on its button) is handled there
            w = getattr(w, "master", None)
        self.close_menu()

    def open_settings_menu(self):
        """Dropdown panel that opens right under the Settings button, inside the main window."""
        if self.menu is not None and self.menu.winfo_exists():
            return self.close_menu()
        panel = ctk.CTkFrame(self.root, fg_color=T["CARD"], corner_radius=16, border_width=1, border_color=T["BORDER"])
        self.menu = panel
        ctk.CTkFrame(panel, width=310, height=1, fg_color="transparent").pack()  # fixes the panel width

        head = ctk.CTkFrame(panel, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(14, 6))
        initials = "".join(w[0] for w in self.user["full_name"].split()[:2]).upper() or "?"
        ctk.CTkLabel(head, text=initials, width=44, height=44, corner_radius=22, fg_color=T["GREEN"],
                     text_color=T["ON_GREEN"], font=font(14, True)).pack(side="left")
        who = ctk.CTkFrame(head, fg_color="transparent")
        who.pack(side="left", padx=10)
        label(who, self.user["full_name"], 14, True).pack(anchor="w")
        label(who, f"@{self.user.get('username', '')}  •  {'Administrator' if self.admin else 'User'}", 10, False, "MUTED").pack(anchor="w")
        ctk.CTkFrame(panel, height=1, fg_color=T["BORDER"]).pack(fill="x", padx=14, pady=6)

        def act(cmd):
            self.close_menu()
            self.root.after(20, cmd)

        def row(icon, title, sub, cmd, danger=False):
            r = ctk.CTkFrame(panel, fg_color="transparent", corner_radius=12)
            r.pack(fill="x", padx=8, pady=1)
            chip = ctk.CTkLabel(r, text=icon, width=38, height=38, corner_radius=19, fg_color=T["MINT"],
                                text_color=T["WARN"] if danger else T["TEXT"], font=font(14, True))
            chip.pack(side="left", padx=(8, 10), pady=6)
            col = ctk.CTkFrame(r, fg_color="transparent")
            col.pack(side="left", fill="x", expand=True)
            t = label(col, title, 13, True, "WARN" if danger else "TEXT")
            t.pack(anchor="w")
            sub_l = label(col, sub, 10, False, "MUTED")
            sub_l.pack(anchor="w")
            parts = (r, chip, col, t, sub_l)
            for w in parts:
                w.bind("<Button-1>", lambda e, c=cmd: act(c))
                w.bind("<Enter>", lambda e: r.configure(fg_color=T["MINT"]))
                w.bind("<Leave>", lambda e: r.configure(fg_color="transparent"))

        row("✎", "Edit name / username", "Update how you appear in BudgetBuddy", self.edit_profile)
        row("✱", "Change password", "Keep your account secure", self.change_password_dialog)
        row("☀" if self.dark else "☾", "Light mode" if self.dark else "Dark mode", "Switch the app appearance", self.toggle)
        ctk.CTkFrame(panel, height=1, fg_color=T["BORDER"]).pack(fill="x", padx=14, pady=6)
        row("✕", "Delete my account", "Permanently remove your data", self.delete_account_dialog, danger=True)
        row("↩", "Log out", "Sign out of BudgetBuddy", self.logout)
        ctk.CTkFrame(panel, height=8, fg_color="transparent").pack()

        self.root.update_idletasks()
        g = self.gear
        x = g.winfo_rootx() - self.root.winfo_rootx() + g.winfo_width() - 312
        y = g.winfo_rooty() - self.root.winfo_rooty() + g.winfo_height() + 6
        panel.place(x=max(8, x), y=y)
        panel.lift()

    def edit_profile(self):
        d = dialog(self.root, "Edit Profile", 440, 370)
        label(d, "Edit your profile", 23, True).pack(anchor="w", padx=28, pady=(24, 4))
        label(d, "Your username must remain unique.", 11, False, "MUTED").pack(anchor="w", padx=28, pady=(0, 14))
        box = card(d); box.pack(fill="both", expand=True, padx=22, pady=(0, 22))
        label(box, "Full name", 11, True).pack(anchor="w", padx=20, pady=(18, 4))
        name_e = entry(box, "Full name"); name_e.pack(fill="x", padx=20); name_e.insert(0, self.user["full_name"])
        label(box, "Username", 11, True).pack(anchor="w", padx=20, pady=(12, 4))
        user_e = entry(box, "Username"); user_e.pack(fill="x", padx=20); user_e.insert(0, self.user["username"])
        def save():
            name, username = name_e.get().strip(), user_e.get().strip()
            if not name or not username:
                return messagebox.showwarning("Missing Information", "Enter both your name and username.", parent=d)
            try:
                database.update_user_profile(self.user["id"], name, username)
            except Exception as exc:
                return messagebox.showerror("Profile Update Failed", str(exc), parent=d)
            self.user["full_name"], self.user["username"] = name, username
            d.destroy(); self.build()
            messagebox.showinfo("Profile Updated", "Your account details were updated.", parent=self.root)
        row = ctk.CTkFrame(box, fg_color="transparent"); row.pack(fill="x", padx=20, pady=18)
        button(row, "Save changes", save, width=140).pack(side="left", padx=(0, 8))
        button(row, "Cancel", d.destroy, "mint", width=100).pack(side="left")

    def change_password_dialog(self):
        d = dialog(self.root, "Change Password", 430, 390)
        label(d, "Change password", 23, True).pack(anchor="w", padx=28, pady=(24, 4))
        box = card(d); box.pack(fill="both", expand=True, padx=22, pady=(12, 22))
        old = entry(box, "Current password", "•"); old.pack(fill="x", padx=20, pady=(22, 10))
        new = entry(box, "New password (8+ characters)", "•"); new.pack(fill="x", padx=20, pady=10)
        confirm = entry(box, "Confirm new password", "•"); confirm.pack(fill="x", padx=20, pady=10)
        def save():
            if len(new.get()) < 8:
                return messagebox.showwarning("Weak Password", "Use at least 8 characters.", parent=d)
            if new.get() != confirm.get():
                return messagebox.showerror("Mismatch", "The new passwords do not match.", parent=d)
            try:
                database.change_password(self.user["id"], old.get(), new.get())
            except Exception as exc:
                return messagebox.showerror("Password Change Failed", str(exc), parent=d)
            d.destroy(); messagebox.showinfo("Success", "Your password has been changed.", parent=self.root)
        button(box, "Save password", save).pack(fill="x", padx=20, pady=18)

    def delete_account_dialog(self):
        d = dialog(self.root, "Delete Account", 430, 300)
        label(d, "Delete your account?", 23, True, "WARN").pack(anchor="w", padx=28, pady=(24, 6))
        label(d, "This permanently removes your account and its expense records. This cannot be undone.", 11, False, "MUTED", wraplength=360, justify="left").pack(anchor="w", padx=28, pady=(0, 12))
        pw = entry(d, "Confirm with your password", "•"); pw.pack(fill="x", padx=28, pady=8)
        def delete():
            if self.admin:  # never leave the system without an administrator
                try:
                    if sum(1 for u in database.get_all_users() if str(u[3]).lower() == "admin") <= 1:
                        return messagebox.showwarning("Not Allowed", "You are the last administrator. Promote another admin first.", parent=d)
                except Exception as exc:
                    return messagebox.showerror("Database Error", str(exc), parent=d)
            if not messagebox.askyesno("Final confirmation", "Permanently delete this account?", parent=d):
                return
            try:
                database.delete_user_account(self.user["id"], pw.get())
            except Exception as exc:
                return messagebox.showerror("Account Not Deleted", str(exc), parent=d)
            d.destroy(); self.auth.show("login")
            messagebox.showinfo("Account Deleted", "Your account has been deleted.", parent=self.root)
        button(d, "Delete account permanently", delete, "danger").pack(fill="x", padx=28, pady=12)

    # ---------------- User reports: preview table + multi month/year filter + export ----------------
    def open_reports(self):
        self.go(self.reports_page, "Reports")

    @user_only
    def reports_page(self):
        self.header("Summary Reports", "Choose months and years, preview your expenses, then export them as CSV or PDF.")
        box = card(self.body)
        box.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        try:
            allrows = list(database.get_expenses(self.user["id"]))
        except Exception as exc:
            label(box, f"Could not load your expenses:\n{exc}", 12, False, "WARN", justify="left").pack(anchor="w", padx=22, pady=22)
            return
        today = date.today()
        years = sorted({to_date(r[1]).year for r in allrows} | {today.year})
        all_var = tk.BooleanVar(value=True)
        mvars = {i: tk.BooleanVar(value=False) for i in range(1, 13)}
        yvars = {y: tk.BooleanVar(value=False) for y in years}

        def any_selected():
            return any(v.get() for v in mvars.values()) or any(v.get() for v in yvars.values())

        def on_pick():  # ticking a month or year turns off "All dates"; clearing everything turns it back on
            all_var.set(not any_selected())
            show()

        def on_all():
            if all_var.get() or not any_selected():
                all_var.set(True)
                for v in list(mvars.values()) + list(yvars.values()):
                    v.set(False)
            show()

        top = ctk.CTkFrame(box, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(18, 4))
        checkbox(top, "All dates", all_var, on_all, 100).pack(side="left", padx=(0, 16))
        label(top, "Or tick several months and years - results show months AND years you picked.", 11, False, "MUTED").pack(side="left")
        panel = ctk.CTkFrame(box, fg_color=T["INPUT"], corner_radius=14)
        panel.pack(fill="x", padx=22, pady=(6, 8))
        label(panel, "Months", 11, True, "MUTED").grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        for i in range(1, 13):
            checkbox(panel, calendar.month_name[i], mvars[i], on_pick, 105).grid(row=1 + (i - 1) // 6, column=(i - 1) % 6, padx=12, pady=4, sticky="w")
        label(panel, "Years", 11, True, "MUTED").grid(row=3, column=0, sticky="w", padx=12, pady=(6, 0))
        yrow = ctk.CTkFrame(panel, fg_color="transparent")
        yrow.grid(row=4, column=0, columnspan=6, sticky="w", padx=6, pady=(0, 8))
        for y in years:
            checkbox(yrow, str(y), yvars[y], on_pick, 80).pack(side="left", padx=6)

        cards = ctk.CTkFrame(box, fg_color="transparent")
        cards.pack(fill="x", padx=17, pady=(0, 8))
        vals = {}
        for i, t in enumerate(["Total Spent", "Transactions", "Average Transaction"]):
            cards.columnconfigure(i, weight=1, uniform="r")
            c = card(cards)
            c.grid(row=0, column=i, sticky="nsew", padx=5)
            label(c, t, 11, True, "MUTED").pack(anchor="w", padx=16, pady=(10, 0))
            vals[t] = label(c, "", 17, True)
            vals[t].pack(anchor="w", padx=16, pady=(0, 10))
        holder = tk.Frame(box, bg=T["CARD"])
        holder.pack(fill="both", expand=True, padx=22, pady=(0, 8))
        foot = ctk.CTkFrame(box, fg_color="transparent")
        foot.pack(fill="x", padx=22, pady=(4, 16))
        status = label(foot, "", 11, False, "MUTED")
        status.pack(side="left")
        cur = {"rows": []}

        def pick():
            if all_var.get():
                return list(allrows)
            ms = {i for i, v in mvars.items() if v.get()} or set(range(1, 13))
            ys = {y for y, v in yvars.items() if v.get()} or set(years)
            return [r for r in allrows if to_date(r[1]).month in ms and to_date(r[1]).year in ys]

        def title():
            if all_var.get():
                return "All dates"
            ms = [calendar.month_name[i] for i, v in mvars.items() if v.get()] or ["All months"]
            ys = [str(y) for y, v in yvars.items() if v.get()] or ["All years"]
            return f"{', '.join(ms)} / {', '.join(ys)}"

        def show():
            rows = pick()
            cur["rows"] = rows
            total = sum(float(r[4]) for r in rows)
            vals["Total Spent"].configure(text=money(total))
            vals["Transactions"].configure(text=str(len(rows)))
            vals["Average Transaction"].configure(text=money(total / len(rows) if rows else 0))
            status.configure(text=f"Showing: {title()}")
            for w in holder.winfo_children():
                w.destroy()
            tree = make_tree(holder, [("d", "DATE", 110, "center"), ("p", "MONTH / YEAR", 150, "w"),
                                      ("s", "DESCRIPTION", 300, "w"), ("c", "CATEGORY", 160, "w"),
                                      ("a", "AMOUNT", 130, "e")], height=9)
            fill_tree(tree, [(str(r[1]), f"{calendar.month_name[to_date(r[1]).month]} {to_date(r[1]).year}", r[2], r[3], money(r[4]))
                             for r in sorted(rows, key=lambda r: to_date(r[1]), reverse=True)])

        def have_rows():
            if not cur["rows"]:
                messagebox.showinfo("Nothing to Export", "There are no expenses in the selected period.", parent=self.root)
                return False
            return True

        def export_csv():
            if not have_rows():
                return
            path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
                                                initialfile="BudgetBuddy_Summary_Report.csv")
            if not path:
                return
            try:
                grand = 0.0
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["BudgetBuddy Summary Report", title()])
                    w.writerow(["User", self.user["full_name"], "Generated", datetime.now().strftime("%Y-%m-%d %H:%M")])
                    for y, ms in group_rows(cur["rows"]).items():  # separated by year, then month
                        w.writerow([])
                        w.writerow([f"YEAR {y}"])
                        ytotal = 0.0
                        for m, rs in ms.items():
                            w.writerow([])
                            w.writerow([f"{calendar.month_name[m]} {y}"])
                            w.writerow(["ID", "Date", "Description", "Category", "Amount (PHP)"])
                            for r in rs:
                                w.writerow([r[0], str(r[1]), r[2], r[3], f"{float(r[4]):.2f}"])
                            t = sum(float(r[4]) for r in rs)
                            ytotal += t
                            w.writerow(["", "", "", f"Total {calendar.month_name[m]} {y}", f"{t:.2f}"])
                        w.writerow(["", "", "", f"Total {y}", f"{ytotal:.2f}"])
                        grand += ytotal
                    w.writerow([])
                    w.writerow(["", "", "", "GRAND TOTAL", f"{grand:.2f}"])
            except Exception as exc:
                return messagebox.showerror("Export Failed", str(exc), parent=self.root)
            messagebox.showinfo("Report Exported", f"CSV saved to:\n{path}\n\nIncluded {len(cur['rows'])} expense record(s).", parent=self.root)

        def export_pdf():
            if not have_rows():
                return
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            except ImportError:
                return messagebox.showerror("PDF Export Unavailable", "Install ReportLab:\npython -m pip install reportlab", parent=self.root)
            path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".pdf", filetypes=[("PDF file", "*.pdf")],
                                                initialfile="BudgetBuddy_Summary_Report.pdf")
            if not path:
                return
            try:
                fn = pdf_font()
                st = getSampleStyleSheet()
                story = [Paragraph("BudgetBuddy - Summary Report", st["Title"]),
                         Paragraph(f"{title()} - {self.user['full_name']} - generated {datetime.now():%Y-%m-%d %H:%M}", st["Normal"])]
                grand = 0.0
                for y, ms in group_rows(cur["rows"]).items():
                    story += [Spacer(1, 14), Paragraph(f"Year {y}", st["Heading1"])]
                    ytotal = 0.0
                    for m, rs in ms.items():
                        t = sum(float(r[4]) for r in rs)
                        ytotal += t
                        data = [["Date", "Description", "Category", "Amount"]] + \
                               [[str(r[1]), str(r[2]), str(r[3]), money(r[4])] for r in rs] + [["", "", "Month total", money(t)]]
                        story.append(Paragraph(f"{calendar.month_name[m]} {y}", st["Heading3"]))
                        tb = Table(data, colWidths=[75, 210, 100, 90], repeatRows=1)
                        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F6F4A")),
                                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                                ("FONTNAME", (0, 0), (-1, -1), fn), ("FONTSIZE", (0, 0), (-1, -1), 8),
                                                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BFE3CD")),
                                                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2F4EA")),
                                                ("ALIGN", (-1, 0), (-1, -1), "RIGHT")]))
                        story += [tb, Spacer(1, 8)]
                    story.append(Paragraph(f"Total for {y}: {money(ytotal)}", st["Heading4"]))
                    grand += ytotal
                story += [Spacer(1, 12), Paragraph(f"Grand total: {money(grand)}", st["Heading2"])]
                SimpleDocTemplate(path, pagesize=A4, leftMargin=36, rightMargin=36).build(story)
            except Exception as exc:
                return messagebox.showerror("Export Failed", str(exc), parent=self.root)
            messagebox.showinfo("Report Exported", f"PDF saved to:\n{path}\n\nIncluded {len(cur['rows'])} expense record(s).", parent=self.root)

        button(foot, "Export PDF", export_pdf, "danger", width=130).pack(side="right")
        button(foot, "Export CSV", export_csv, "peach", width=130).pack(side="right", padx=8)
        show()

    # ---------------- Admin: overview ----------------
    def admin_count(self, users):
        return sum(1 for u in users if str(u[3]).lower() == "admin")

    def system_stats(self):
        users = database.get_all_users()
        tx, spent, cats = 0, 0.0, {}
        for u in users:  # totals only - individual expense rows are never read
            tx += int(database.get_transaction_count(u[0]))
            spent += float(database.get_total_expenses(u[0]))
            for k, v in database.get_category_totals(u[0]).items():
                cats[k] = cats.get(k, 0) + float(v)
        return users, tx, spent, cats

    @admin_only
    def admin_home(self):
        try:
            users, tx, spent, cats = self.system_stats()
            logs = sorted(database.get_audit_logs(), key=lambda r: str(r[1]), reverse=True)[:5]
        except Exception as exc:
            return messagebox.showerror("Database Error", str(exc), parent=self.root)
        self.header("Admin Overview", "System-wide statistics only. Personal expense details are not shown here.",
                    datetime.now().strftime("%a • %b %d • %I:%M %p"))
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", padx=22)
        stats = [("Registered Users", str(len(users)), "GREEN"), ("Administrators", str(self.admin_count(users)), "TEXT"),
                 ("Transactions (current month)", str(tx), "GREEN"), ("Total Spent (all users)", money(spent), "WARN")]
        for i, (t, v, c) in enumerate(stats):
            row.columnconfigure(i, weight=1, uniform="a")
            cd = card(row)
            cd.grid(row=0, column=i, sticky="nsew", padx=6)
            label(cd, t, 12, True, "MUTED").pack(anchor="w", padx=20, pady=(16, 2))
            label(cd, v, 24, True, c).pack(anchor="w", padx=20, pady=(0, 16))
        mid = ctk.CTkFrame(self.body, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=22, pady=12)
        ov = card(mid)
        ov.pack(side="left", fill="both", expand=True, padx=(6, 8))
        label(ov, "Spending by Category", 16, True).pack(anchor="w", padx=22, pady=(18, 0))
        label(ov, "Combined totals for all users, current month", 11, False, "MUTED").pack(anchor="w", padx=22, pady=(2, 4))
        cv = tk.Canvas(ov, bg=T["CARD"], highlightthickness=0, height=220)
        cv.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.chart(cv, cats)
        qa = card(mid, width=270)
        qa.pack(side="right", fill="y", padx=(8, 6))
        qa.pack_propagate(False)
        label(qa, "Quick Access", 16, True).pack(anchor="w", padx=22, pady=(18, 12))
        for text, page, nav, kind in [("Manage Users", self.admin_users, "Users", "primary"),
                                      ("Audit Trail", self.audit_page, "Audit Trail", "peach"),
                                      ("Reports", self.admin_reports, "Reports", "mint")]:
            button(qa, text, lambda p=page, n=nav: self.go(p, n), kind, anchor="w", height=44).pack(fill="x", padx=18, pady=5)
        rc = card(self.body)
        rc.pack(fill="x", padx=28, pady=(0, 22))
        label(rc, "Recent System Activity", 16, True).pack(anchor="w", padx=22, pady=(16, 8))
        holder = tk.Frame(rc, bg=T["CARD"])
        holder.pack(fill="x", padx=22, pady=(0, 18))
        tree = make_tree(holder, [("t", "DATE / TIME", 170, "w"), ("u", "USER", 130, "w"),
                                  ("a", "ACTION", 120, "w"), ("d", "DETAILS", 560, "w")], height=5)
        fill_tree(tree, [(str(r[1]), r[2], r[3], r[4]) for r in logs])

    # ---------------- Admin: users ----------------
    @admin_only
    def admin_users(self):
        self.header("User Management", "Search accounts, review details and manage roles. Accounts cannot be deleted here.")
        cd = card(self.body)
        cd.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        bar = ctk.CTkFrame(cd, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=16)
        search = entry(bar, "Search name or username", width=260)
        search.pack(side="left", padx=(0, 10))
        rv = tk.StringVar(value="All Roles")
        combo(bar, ["All Roles", "user", "admin"], rv, 150, lambda _: refresh()).pack(side="left")
        holder = tk.Frame(cd, bg=T["CARD"])
        holder.pack(fill="both", expand=True, padx=18)
        tree = make_tree(holder, [("id", "#", 50, "center"), ("name", "FULL NAME", 260, "w"),
                                  ("user", "USERNAME", 200, "w"), ("role", "ROLE", 120, "w"),
                                  ("created", "CREATED", 200, "w")], height=14)
        foot = ctk.CTkFrame(cd, fg_color="transparent")
        foot.pack(fill="x", padx=18, pady=16)
        status = label(foot, "", 11, False, "MUTED")
        status.pack(side="left")

        def refresh(*_):
            try:
                users = database.get_all_users()
            except Exception as exc:
                return messagebox.showerror("Database Error", str(exc), parent=self.root)
            q = search.get().strip().lower()
            rows = [(u[0], u[1], u[2], u[3], str(u[4])) for u in users
                    if (not q or q in f"{u[1]} {u[2]}".lower()) and (rv.get() == "All Roles" or str(u[3]).lower() == rv.get())]
            fill_tree(tree, rows)
            status.configure(text=f"{len(rows)} account(s) shown")

        def selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Nothing Selected", "Select a user first.", parent=self.root)
                return None
            return tree.item(sel[0], "values")

        def details():
            v = selected()
            if not v:
                return
            d = dialog(self.root, "Account Details", 420, 380)
            label(d, "Account details", 22, True).pack(anchor="w", padx=30, pady=(24, 10))
            box = card(d)
            box.pack(fill="both", expand=True, padx=26, pady=(0, 26))
            for name, val in zip(["ID", "Full name", "Username", "Role", "Created"], v):
                r = ctk.CTkFrame(box, fg_color="transparent")
                r.pack(fill="x", padx=22, pady=(12, 0))
                label(r, name, 11, True, "MUTED").pack(anchor="w")
                label(r, str(val), 13, True).pack(anchor="w")

        def change_role():
            if not self.require_admin():
                return
            v = selected()
            if not v:
                return
            uid, name, role = int(v[0]), v[1], str(v[3]).lower()
            if uid == self.user["id"]:
                return messagebox.showwarning("Not Allowed", "You cannot change your own role.", parent=self.root)
            try:
                if role == "admin" and sum(1 for u in database.get_all_users() if str(u[3]).lower() == "admin") <= 1:
                    return messagebox.showwarning("Not Allowed", "The last administrator cannot be demoted.", parent=self.root)
                new = "user" if role == "admin" else "admin"
                note = "\n\nThis grants full administrator access." if new == "admin" else ""
                if messagebox.askyesno("Confirm Role Change", f"Change {name}'s role from {role} to {new}?{note}", parent=self.root):
                    database.set_user_role(uid, new, self.user["id"])
                    refresh()
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=self.root)

        search.bind("<KeyRelease>", refresh)
        button(foot, "Change Role", change_role, "danger", width=130).pack(side="right")
        button(foot, "Details", details, "mint", width=100).pack(side="right", padx=8)
        refresh()

    # ---------------- Admin: audit trail with USER dropdown + search ----------------
    def user_dropdown(self, anchor, options, on_pick):
        m = tk.Toplevel(self.root)
        m.overrideredirect(True)
        m.configure(bg=T["BORDER"])
        box = ctk.CTkFrame(m, fg_color=T["CARD"], corner_radius=14)
        box.pack(padx=1, pady=1)
        q = entry(box, "Search users...", width=240)
        q.pack(padx=10, pady=(10, 6))
        lst = ctk.CTkScrollableFrame(box, width=228, height=240, fg_color="transparent")
        lst.pack(padx=6, pady=(0, 8))

        def choose(name):
            m.destroy()
            on_pick(name)

        def fill(*_):
            for w in lst.winfo_children():
                w.destroy()
            text = q.get().strip().lower()
            for name in ["All users"] + [o for o in options if text in o.lower()]:
                ctk.CTkButton(lst, text=name, anchor="w", height=32, corner_radius=10, fg_color="transparent",
                              hover_color=T["MINT"], text_color=T["TEXT"], font=font(12, name == "All users"),
                              command=lambda n=name: choose(None if n == "All users" else n)).pack(fill="x", pady=1)
            if text and len(lst.winfo_children()) == 1:
                label(lst, "No matching users", 11, False, "MUTED").pack(pady=8)
        q.bind("<KeyRelease>", fill)
        fill()
        m.update_idletasks()
        m.geometry(f"+{anchor.winfo_rootx()}+{anchor.winfo_rooty() + anchor.winfo_height() + 4}")
        m.focus_force()
        q.focus_set()
        m.bind("<Escape>", lambda e: m.destroy())
        m.bind("<FocusOut>", lambda e: m.after(200, lambda: m.winfo_exists() and m.focus_displayof() is None and m.destroy()))

    @admin_only
    def audit_page(self):
        self.header("Audit Trail", "Review recorded account, expense, budget, and administrative activity. Records are read-only.")
        box = card(self.body)
        box.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        try:
            logs = [tuple(str(x) for x in r[:5]) for r in database.get_audit_logs()]
            users = database.get_all_users()
        except Exception as exc:
            label(box, f"Could not load the audit trail:\n{exc}", 12, False, "WARN", justify="left").pack(anchor="w", padx=22, pady=22)
            return
        actors = sorted({r[2] for r in logs} | {str(u[2]) for u in users}, key=str.lower)
        state = {"user": None}
        bar = ctk.CTkFrame(box, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=(16, 8))
        search = entry(bar, "Search action or details", width=280)
        search.pack(side="left", padx=(0, 12))
        chip = label(bar, "User: all users", 12, True, "MUTED")
        chip.pack(side="left")
        clear = link(bar, "✕ Clear", lambda: pick_user(None))
        holder = tk.Frame(box, bg=T["CARD"])
        holder.pack(fill="both", expand=True, padx=18)
        cols = [("id", "ID", 60, "center"), ("time", "TIMESTAMP", 170, "w"), ("user", "USER", 190, "w"),
                ("action", "ACTION", 150, "w"), ("desc", "DESCRIPTION", 520, "w")]
        tree = make_tree(holder, cols, height=15)
        status = label(box, "", 11, False, "MUTED")
        status.pack(anchor="w", padx=18, pady=14)

        def refresh(*_):
            q = search.get().strip().lower()
            rows = [r for r in logs if (state["user"] is None or r[2] == state["user"])
                    and (not q or q in f"{r[3]} {r[4]}".lower())]
            fill_tree(tree, rows)
            status.configure(text=f"{len(rows)} of {len(logs)} audit record(s)")

        def pick_user(name):
            state["user"] = name
            chip.configure(text=f"User: {name}" if name else "User: all users")
            if name:
                clear.pack(side="left", padx=6)
            else:
                clear.pack_forget()
            refresh()

        # the dropdown arrow sits inside the USER column header
        arrow = tk.Button(tree, text="▾", bd=0, relief="flat", cursor="hand2", font=font(11, True), bg=T["HEAD"],
                          fg=T["GREEN"], activebackground=T["MINT"], activeforeground=T["GREEN"])
        arrow.configure(command=lambda: self.user_dropdown(arrow, actors, pick_user))

        def place_arrow(_=None):
            if arrow.winfo_exists():
                x = int(tree.column("id", "width")) + int(tree.column("time", "width")) + int(tree.column("user", "width")) - 30
                arrow.place(x=x, y=6, width=24, height=24)
        tree.bind("<Configure>", lambda e: tree.after_idle(place_arrow), add="+")
        tree.bind("<ButtonRelease-1>", lambda e: tree.after_idle(place_arrow), add="+")
        search.bind("<KeyRelease>", refresh)
        refresh()

    # ---------------- Admin: reports ----------------
    def admin_report_data(self, kind):
        users = database.get_all_users()
        if kind == "User accounts":
            return ["ID", "Full name", "Username", "Role", "Created"], [(u[0], u[1], u[2], u[3], str(u[4])) for u in users]
        logs = [tuple(str(x) for x in r[:5]) for r in database.get_audit_logs()]
        if kind == "Audit trail":
            return ["ID", "Date / Time", "User", "Action", "Details"], logs
        admins = sum(1 for u in users if str(u[3]).lower() == "admin")
        rows = [("Registered users", len(users)), ("Administrators", admins), ("Standard users", len(users) - admins),
                ("Audit records", len(logs))]
        counts = {}
        for r in logs:
            counts[r[3]] = counts.get(r[3], 0) + 1
        rows += [(f"Audit action: {k}", v) for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
        return ["Metric", "Value"], rows

    @admin_only
    def admin_reports(self):
        self.header("Reports", "System reports for oversight. Individual users' expenses are never listed here.")
        cd = card(self.body)
        cd.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        bar = ctk.CTkFrame(cd, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=16)
        kinds = ["User accounts", "Audit trail", "System summary"]
        kv = tk.StringVar(value=kinds[0])
        combo(bar, kinds, kv, 200, lambda _: show()).pack(side="left")
        holder = tk.Frame(cd, bg=T["CARD"])
        holder.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        state = {}

        def show():
            for w in holder.winfo_children():
                w.destroy()
            try:
                heads, rows = self.admin_report_data(kv.get())
            except Exception as exc:
                return messagebox.showerror("Database Error", str(exc), parent=self.root)
            state["data"] = (heads, rows)
            tree = make_tree(holder, [(f"c{i}", h.upper(), 780 // len(heads), "w") for i, h in enumerate(heads)], height=14)
            fill_tree(tree, rows)

        def ask(ext, kind):
            return filedialog.asksaveasfilename(parent=self.root, title=f"Save {kind} report", defaultextension=ext,
                                                filetypes=[(f"{kind} files", f"*{ext}")])

        def export_csv():
            if not self.require_admin():
                return
            path = ask(".csv", "CSV")
            if not path:
                return
            heads, rows = state["data"]
            try:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow([f"BudgetBuddy - {kv.get()}"])
                    w.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M"), "By", self.user["full_name"]])
                    w.writerow([])
                    w.writerow(heads)
                    w.writerows(rows)
            except Exception as exc:
                return messagebox.showerror("Export Failed", str(exc), parent=self.root)
            messagebox.showinfo("Export Complete", f"CSV saved to:\n{path}", parent=self.root)

        def export_pdf():
            if not self.require_admin():
                return
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            except ImportError:
                return messagebox.showerror("PDF Export Unavailable", "Install ReportLab:\npython -m pip install reportlab", parent=self.root)
            path = ask(".pdf", "PDF")
            if not path:
                return
            try:
                fn = pdf_font()
                heads, rows = state["data"]
                st = getSampleStyleSheet()
                story = [Paragraph(f"BudgetBuddy - {kv.get()}", st["Title"]),
                         Paragraph(f"Generated {datetime.now():%Y-%m-%d %H:%M} by {self.user['full_name']}", st["Normal"]), Spacer(1, 12)]
                tb = Table([heads] + [[str(c) for c in r] for r in rows], repeatRows=1)
                tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F6F4A")),
                                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                        ("FONTNAME", (0, 0), (-1, -1), fn), ("FONTSIZE", (0, 0), (-1, -1), 8),
                                        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BFE3CD")),
                                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0FAF4")])]))
                story.append(tb)
                SimpleDocTemplate(path, pagesize=A4, leftMargin=30, rightMargin=30).build(story)
            except Exception as exc:
                return messagebox.showerror("Export Failed", str(exc), parent=self.root)
            messagebox.showinfo("Export Complete", f"PDF saved to:\n{path}", parent=self.root)

        button(bar, "Export PDF", export_pdf, "danger", width=120).pack(side="right")
        button(bar, "Export CSV", export_csv, "peach", width=120).pack(side="right", padx=8)
        show()

    def logout(self):
        if messagebox.askyesno("Log Out", "Log out of BudgetBuddy?", parent=self.root):
            self.auth.show("login")


def main():
    try:
        database.initialize_database()
    except Exception as e:
        tmp = tk.Tk()
        tmp.withdraw()
        messagebox.showerror("BudgetBuddy Startup Error",
                             f"{e}\n\nMake sure XAMPP MySQL is running and the settings in database.py are correct.")
        tmp.destroy()
        return
    set_theme("light")
    root = ctk.CTk()
    Auth(root)
    root.mainloop()


if __name__ == "__main__":
    main()
