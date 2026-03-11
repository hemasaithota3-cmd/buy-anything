from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "devsecretkey")

# ----------------- DATABASE -----------------
def init_db():
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    # CREATE DEFAULT ADMIN IF NOT EXISTS
cursor.execute("SELECT * FROM users WHERE email='admin@gmail.com'")
admin = cursor.fetchone()

if not admin:
    admin_password = generate_password_hash("admin123")
    cursor.execute(
        "INSERT INTO users (name, email, password, is_admin) VALUES (?, ?, ?, ?)",
        ("Admin", "admin@gmail.com", admin_password, 1)
    )

    # USERS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # ORDERS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            items TEXT,
            total INTEGER,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    # PRODUCTS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL,
            image_url TEXT,
            category TEXT,
            stock INTEGER DEFAULT 100
        )
    ''')
    
    # SEED INITIAL PRODUCTS IF EMPTY
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        initial_products = [
            ("Eggs", "Eggs - ₹10 each. -2% discount you won", 10.0, "images/Brown-eggs.webp", "Dairy"),
            ("Rice", "Sona Masoori 25kg bag - ₹2000. -20% discount you won", 2000.0, "images/rice.webp", "Grains"),
            ("Sasi Milk", "Sasi Milk 1 litre pack - ₹35. -2% discount you won", 35.0, "images/sasi_milk.png", "Dairy"),
            ("Sasi Ghee", "Sasi Ghee 1 litre pack - ₹3000. -10% discount you won", 3000.0, "https://ueirorganic.com/cdn/shop/files/purecowghee.jpg?v=1689066451", "Dairy"),
            ("Palm Oil", "Sasi Refined Palm Oil 1 litre - ₹180. -5% discount you won", 180.0, "https://media.istockphoto.com/id/626118394/photo/group-of-plastic-bottles-with-palm-oil.jpg?s=612x612&w=0&k=20&c=YcWUxXkgWRvBW_7eQUKlblxmqtRzcVPnZpBVL9tlQ9Y=", "Oils")
        ]
        cursor.executemany('''
            INSERT INTO products (name, description, price, image_url, category)
            VALUES (?, ?, ?, ?, ?)
        ''', initial_products)

        # Remove incorrect records just in case they were seeded incorrectly in the previous run
        cursor.execute("UPDATE products SET image_url='images/Brown-eggs.webp' WHERE name='Eggs'")
        cursor.execute("UPDATE products SET image_url='images/rice.webp' WHERE name='Rice'")
        cursor.execute("UPDATE products SET image_url='images/sasi_milk.png' WHERE name='Sasi Milk'")

    conn.commit()
    conn.close()

init_db()

# ----------------- HOME -----------------
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template('product.html', user=session.get('user_name'), products=products, session=session)

# ----------------- CART -----------------
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('cart.html')

# ----------------- REGISTER -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()
        except:
            conn.close()
            return render_template("register.html", error="Email already exists")

        conn.close()
        return redirect('/login')

    return render_template('register.html')

# ----------------- LOGIN -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['is_admin'] = user[4]
            return redirect('/')
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")

# ----------------- LOGOUT -----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ----------------- PLACE ORDER -----------------
@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect('/login')

    total = request.form.get('total')
    items = request.form.get('items')
    user_id = session['user_id']

    # Simulated Payment Success
    payment_status = "Success"

    if payment_status == "Success":
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO orders (user_id, items, total) VALUES (?, ?, ?)",
            (user_id, items, total)
        )

        conn.commit()
        conn.close()

        print(f"📧 Email sent to {session['user_name']} - Order Confirmed!")

        return render_template("order_success.html")

    return "Payment Failed"

# ----------------- USER ORDER HISTORY -----------------
@app.route('/my_orders')
def my_orders():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, items, total, status, created_at FROM orders WHERE user_id=? ORDER BY created_at DESC",
        (session['user_id'],)
    )

    orders = cursor.fetchall()
    conn.close()

    return render_template('my_orders.html', orders=orders)

# ----------------- ADMIN DASHBOARD -----------------
    # DELETED DUPLICATE /admin ROUTE

# ----------------- UPDATE ORDER STATUS (ADMIN) -----------------
@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')

    new_status = request.form.get('status')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()

    return redirect('/admin')


@app.route('/password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        print("Email entered:", email) 

        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        print("User found:", user)
        

        conn.close()
        

        if user:
            session['reset_user'] = email
            return redirect(url_for('reset_password'))
        else:
            return "User not found"

    return render_template('password.html')
@app.route('/reset_password', methods=['GET','POST'])
def reset_password():

    if 'reset_user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hashed_password, session['reset_user'])
        )

        conn.commit()
        conn.close()

        session.pop('reset_user', None)

        return redirect('/login')

    return render_template('reset_password.html')
conn = sqlite3.connect('orders.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name, email FROM users")
print(cursor.fetchall())

conn.close()
@app.route('/admin_users')
def admin_users():

    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()

    conn.close()

    return render_template("admin_users.html", users=users)
@app.route("/admin")
def admin():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')

    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # get users
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    # get orders
    cur.execute('''
        SELECT orders.id, users.name, users.email, orders.items, orders.total, orders.status, orders.created_at
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
    ''')
    orders = cur.fetchall()

    # get products
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = cur.fetchall()

    conn.close()

    return render_template("admin.html", users=users, orders=orders, products=products)

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')

    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    image_url = request.form.get('image_url')
    category = request.form.get('category')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, description, price, image_url, category) 
        VALUES (?, ?, ?, ?, ?)
    ''', (name, description, price, image_url, category))
    conn.commit()
    conn.close()

    return redirect('/admin')

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    return redirect('/admin')


# ----------------- RUN -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(host='0.0.0.0', port=port)
