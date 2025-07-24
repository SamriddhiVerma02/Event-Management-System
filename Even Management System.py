import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import mysql.connector

# --- MySQL Configuration ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "3Sep2003@"
DB_NAME = "event_db"

# --- Initialize DB and Tables ---
def initialize_database():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS event_db")
    cursor.execute("USE event_db")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            date DATE,
            venue VARCHAR(255)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password VARCHAR(100),
            event_id INT,
            payment_status VARCHAR(50),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            event_id INT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)
    conn.commit()
    conn.close()

# --- Admin Panel ---
def open_admin_panel():
    admin_window = tk.Toplevel(root)
    admin_window.title("Admin Panel")
    admin_window.geometry("600x500")

    def refresh_tree():
        tree.delete(*tree.get_children())
        try:
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events")
            for row in cursor.fetchall():
                tree.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def add_event():
        name, date, venue = entry_name.get(), entry_date.get(), entry_venue.get()
        if not name or not date or not venue:
            messagebox.showerror("Input Error", "Fill all fields")
            return
        try:
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO events (name, date, venue) VALUES (%s, %s, %s)", (name, date, venue))
            conn.commit()
            messagebox.showinfo("Success", "Event added successfully!")
            entry_name.delete(0, tk.END)
            entry_venue.delete(0, tk.END)
            refresh_tree()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            conn.close()

    tk.Label(admin_window, text="Event Name").pack()
    entry_name = tk.Entry(admin_window)
    entry_name.pack()

    tk.Label(admin_window, text="Event Date").pack()
    entry_date = DateEntry(admin_window)
    entry_date.pack()

    tk.Label(admin_window, text="Venue").pack()
    entry_venue = tk.Entry(admin_window)
    entry_venue.pack()

    tk.Button(admin_window, text="Add Event", command=add_event).pack(pady=10)

    tree = ttk.Treeview(admin_window, columns=("ID", "Name", "Date", "Venue"), show="headings")
    for col in ("ID", "Name", "Date", "Venue"):
        tree.heading(col, text=col)
        tree.column(col, width=130)
    tree.pack(fill=tk.BOTH, expand=True, pady=10)
    refresh_tree()

# --- Registration Page ---
def open_registration():
    reg_window = tk.Toplevel(root)
    reg_window.title("Register for Event")
    reg_window.geometry("400x400")

    tk.Label(reg_window, text="Name").pack()
    entry_name = tk.Entry(reg_window)
    entry_name.pack()

    tk.Label(reg_window, text="Email").pack()
    entry_email = tk.Entry(reg_window)
    entry_email.pack()

    tk.Label(reg_window, text="Password").pack()
    entry_password = tk.Entry(reg_window, show='*')
    entry_password.pack()

    tk.Label(reg_window, text="Select Event").pack()
    combo_event = ttk.Combobox(reg_window)
    combo_event.pack()

    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM events")
        events = cursor.fetchall()
        combo_event['values'] = [f"{eid}: {ename}" for eid, ename in events]
    except Exception as e:
        messagebox.showerror("DB Error", str(e))
    finally:
        conn.close()

    tk.Label(reg_window, text="Payment Status (Paid/Unpaid)").pack()
    entry_payment = tk.Entry(reg_window)
    entry_payment.pack()

    def submit_registration():
        name = entry_name.get()
        email = entry_email.get()
        password = entry_password.get()
        payment = entry_payment.get()
        event_str = combo_event.get()

        if not all([name, email, password, payment, event_str]):
            messagebox.showerror("Error", "All fields required")
            return

        try:
            event_id = int(event_str.split(":")[0])
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password, event_id, payment_status) VALUES (%s, %s, %s, %s, %s)",
                           (name, email, password, event_id, payment))
            conn.commit()
            messagebox.showinfo("Success", "Registered successfully!")
            reg_window.destroy()
        except mysql.connector.errors.IntegrityError:
            messagebox.showerror("Error", "Email already registered.")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            conn.close()

    tk.Button(reg_window, text="Submit", command=submit_registration).pack(pady=10)

# --- Login Page ---
def open_login():
    login_window = tk.Toplevel(root)
    login_window.title("Login")
    login_window.geometry("400x300")

    tk.Label(login_window, text="Email").pack()
    entry_email = tk.Entry(login_window)
    entry_email.pack()

    tk.Label(login_window, text="Password").pack()
    entry_password = tk.Entry(login_window, show="*")
    entry_password.pack()

    def do_login():
        email = entry_email.get()
        password = entry_password.get()
        try:
            conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT users.name, events.name, events.date 
                FROM users 
                JOIN events ON users.event_id = events.id 
                WHERE users.email = %s AND users.password = %s
            """, (email, password))
            result = cursor.fetchone()
            if result:
                name, event_name, event_date = result
                messagebox.showinfo("Welcome", f"Hello {name}, you're registered for '{event_name}' on {event_date}")
            else:
                messagebox.showerror("Error", "Invalid login credentials")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
        finally:
            conn.close()

    tk.Button(login_window, text="Login", command=do_login).pack(pady=10)

# --- About Us ---
def open_about():
    about_window = tk.Toplevel(root)
    about_window.title("About Us")
    about_window.geometry("400x200")
    tk.Label(about_window, text="Event Management System\nBy B.Tech Student Bhartiya vidyapeeth collage of engerring pune\nAdmin & User Workflow\n group members saurabh kumar singh\n shreya singh \nsammriddhi verma", font=("Arial", 12)).pack(pady=20)

# --- Main Interface ---
initialize_database()
root = tk.Tk()
root.title("Event Management System")
root.geometry("400x400")

tk.Label(root, text="Event Management System", font=("Helvetica", 16, "bold")).pack(pady=20)
tk.Button(root, text="Admin", width=25, height=2, command=open_admin_panel).pack(pady=10)
tk.Button(root, text="Register for Event", width=25, height=2, com-mand=open_registration).pack(pady=10)
tk.Button(root, text="Login", width=25, height=2, command=open_login).pack(pady=10)
tk.Button(root, text="About Us", width=25, height=2, command=open_about).pack(pady=10)

root.mainloop()

