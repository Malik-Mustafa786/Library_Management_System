import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# --- DATABASE LOGIC (CRUD + SEARCH) ---
def connect_db():
    return sqlite3.connect("library_crud.db")

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    # Using standard INTEGER PRIMARY KEY so we can pass our own gapless sequential IDs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,  
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            available INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

# 1. CREATE (Calculates the perfect sequential ID manually)
def add_book_to_db(title, author):
    if not title or not author:
        messagebox.showerror("Error", "All fields are required!")
        return False
    conn = connect_db()
    cursor = conn.cursor()
    
    # Find the current highest ID in the table
    cursor.execute("SELECT MAX(id) FROM books")
    max_id = cursor.fetchone()[0]
    
    # If table is empty, start at 1. Otherwise, add 1 to the highest ID left.
    next_id = 1 if max_id is None else max_id + 1
    
    cursor.execute("INSERT INTO books (id, title, author, available) VALUES (?, ?, ?, 1)", (next_id, title, author))
    conn.commit()
    conn.close()
    return True

# 2. READ (With optional Search filter)
def fetch_books(search_query=""):
    conn = connect_db()
    cursor = conn.cursor()
    if search_query:
        cursor.execute("""
            SELECT * FROM books 
            WHERE title LIKE ? OR author LIKE ?
        """, (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM books")
        
    rows = cursor.fetchall()
    conn.close()
    return rows

# 3. UPDATE
def update_status_in_db(book_id, make_available):
    conn = connect_db()
    cursor = conn.cursor()
    status_value = 1 if make_available else 0
    cursor.execute("UPDATE books SET available = ? WHERE id = ?", (status_value, book_id))
    conn.commit()
    conn.close()

# 4. DELETE (Clean and simple, no hidden sequence updates needed)
def delete_book_from_db(book_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()


# --- GUI INTERACTION LOGIC ---
def refresh_table(event=None):
    search_text = entry_search.get().strip()
    
    for item in tree.get_children():
        tree.delete(item)
        
    for row in fetch_books(search_text):
        status = "Available" if row[3] == 1 else "Checked Out"
        tree.insert("", tk.END, values=(row[0], row[1], row[2], status))

def handle_add():
    title = entry_title.get().strip()
    author = entry_author.get().strip()
    if add_book_to_db(title, author):
        entry_title.delete(0, tk.END)
        entry_author.delete(0, tk.END)
        entry_search.delete(0, tk.END) 
        refresh_table()

def get_selected_book_id():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "Please select a book from the table first.")
        return None
    try:
        return int(tree.item(selected_item, "values")[0])
    except (IndexError, ValueError):
        return None

def handle_borrow():
    book_id = get_selected_book_id()
    if book_id:
        update_status_in_db(book_id, make_available=False)
        refresh_table()

def handle_return():
    book_id = get_selected_book_id()
    if book_id:
        update_status_in_db(book_id, make_available=True)
        refresh_table()

def handle_delete():
    book_id = get_selected_book_id()
    if book_id:
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this book?")
        if confirm:
            delete_book_from_db(book_id)
            refresh_table()

def show_context_menu(event):
    iid = tree.identify_row(event.y)
    if iid:
        tree.selection_set(iid)
        context_menu.post(event.x_root, event.y_root)


# --- GUI WINDOW SETUP ---
root = tk.Tk()
root.title("Library Management System ")
root.geometry("650x530")
root.resizable(True, True)

create_table()

# Top Frame: CREATE
frame_inputs = ttk.LabelFrame(root, text=" Add New Book ", padding=10)
frame_inputs.pack(fill="x", padx=15, pady=10)

tk.Label(frame_inputs, text="Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry_title = tk.Entry(frame_inputs, width=22)
entry_title.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_inputs, text="Author:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
entry_author = tk.Entry(frame_inputs, width=22)
entry_author.grid(row=0, column=3, padx=5, pady=5)

btn_add = tk.Button(frame_inputs, text="Add Book", command=handle_add, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"))
btn_add.grid(row=0, column=4, padx=10, pady=5)

# Interactive Frame: SEARCH BAR
frame_search = tk.Frame(root) 
frame_search.pack(fill="x", padx=15, pady=7) 

tk.Label(frame_search, text="🔍 Search Books (Title/Author):", font=("Arial", 10, "bold")).pack(side="left", padx=5)
entry_search = tk.Entry(frame_search, font=("Arial", 10))
entry_search.pack(side="left", fill="x", expand=True, padx=5)

entry_search.bind("<KeyRelease>", refresh_table)

# Middle Frame: READ
frame_table = ttk.LabelFrame(root, text=" Library Inventory (Right-click row for shortcuts) ", padding=10)
frame_table.pack(fill="both", expand=True, padx=15, pady=5)

columns = ("id", "title", "author", "status")
tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=8)

tree.heading("id", text="ID")
tree.heading("title", text="Title")
tree.heading("author", text="Author")
tree.heading("status", text="Status")

tree.column("id", width=50, anchor="center")
tree.column("title", width=220)
tree.column("author", width=160)
tree.column("status", width=110, anchor="center")
tree.pack(fill="both", expand=True)

# Right-Click Context Menu
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Borrow Book", command=handle_borrow)
context_menu.add_command(label="Return Book", command=handle_return)
context_menu.add_separator()
context_menu.add_command(label="🗑 Delete Book", command=handle_delete, foreground="red")

tree.bind("<Button-3>", show_context_menu) 
tree.bind("<Button-2>", show_context_menu) 

# Bottom Frame: UPDATE / DELETE Buttons
frame_actions = tk.Frame(root) 
frame_actions.pack(fill="x", padx=15, pady=20) 

btn_borrow = tk.Button(frame_actions, text="Borrow Book", command=handle_borrow, bg="#008CBA", fg="white")
btn_borrow.pack(side="left", padx=5)

btn_return = tk.Button(frame_actions, text="Return Book", command=handle_return, bg="#FF9800", fg="white")
btn_return.pack(side="left", padx=5)

btn_delete = tk.Button(frame_actions, text="Delete Book", command=handle_delete, bg="#f44336", fg="white")
btn_delete.pack(side="left", padx=5)

btn_exit = tk.Button(frame_actions, text="Exit App", command=root.quit, bg="#757575", fg="white")
btn_exit.pack(side="right", padx=5)

refresh_table()
root.mainloop()