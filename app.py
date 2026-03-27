import sqlite3
from flask import Flask, render_template, request, redirect, jsonify, session

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE = 'books.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_books():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books LIMIT 50").fetchall()
    conn.close()
    return books

def search_books(query):
    conn = get_db_connection()
    books = conn.execute(
        "SELECT * FROM books WHERE title LIKE ? OR authors LIKE ?",
        ('%' + query + '%', '%' + query + '%')
    ).fetchall()
    conn.close()
    return books

# 🔐 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect('/')
        else:
            return "Invalid login ❌"

    return render_template("login.html")

# 🔓 LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 👤 PROFILE    
@app.route('/profile')
def profile():
    if not session.get('user'):
        return redirect('/login')

    conn = get_db_connection()

    # JOIN purchases + books to get title
    purchases = conn.execute("""
        SELECT purchases.*, books.title
        FROM purchases
        JOIN books ON purchases.isbn = books.isbn13
        WHERE purchases.username=?
    """, (session['user'],)).fetchall()

    purchase_count = len(purchases)

    conn.close()

    return render_template(
        "profile.html",
        purchases=purchases,
        purchase_count=purchase_count
    )

# 🛒 BUY BOOK
@app.route('/buy/<isbn>')
def buy_book(isbn):
    if not session.get('user'):
        return redirect('/login')

    conn = get_db_connection()

    book = conn.execute(
        "SELECT * FROM books WHERE isbn13=?", (isbn,)
    ).fetchone()

    conn.execute(
        "INSERT INTO purchases (username, isbn, price, purchase_date) VALUES (?, ?, ?, DATE('now'))",
        (session['user'], isbn, book['price'])
    )

    conn.commit()
    conn.close()

    return redirect('/')

# 🛒 VIEW PURCHASES
@app.route('/purchases')
def purchases():
    if not session.get('user'):
        return redirect('/login')

    conn = get_db_connection()
    data = conn.execute(
        "SELECT * FROM purchases WHERE username=?",
        (session['user'],)
    ).fetchall()
    conn.close()

    return render_template("purchases.html", purchases=data)

# 🔍 SEARCH
@app.route('/search')
def search():
    query = request.args.get('q', '')
    books = search_books(query)
    return jsonify([dict(b) for b in books])

# 🏠 HOME
@app.route('/')
def home():
    books = get_all_books()
    return render_template("index.html", books=books)

#signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()

        # check if user already exists
        existing = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing:
            conn.close()
            return "User already exists ❌"

        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, 'student')",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template("signup.html")    

if __name__ == '__main__':
    app.run(debug=True)