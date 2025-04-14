from flask import Flask, request, redirect, url_for, render_template, flash
import mysql.connector
from mysql.connector import Error

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this for production

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    port=3307,
    user="root",
    password="Ragdeep123$",
    database="Lib_manage"
)
cursor = db.cursor(dictionary=True)# Use dictionary cursor for easier data handling
def get_borrowing(book_id):
    """Helper function to get current borrowing record"""
    cursor.execute("""
        SELECT * FROM borrowings 
        WHERE book_id = %s AND return_date IS NULL
        LIMIT 1
    """, (book_id,))
    return cursor.fetchone()
# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# In add_user route
@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    role = request.form['role']
    phone = request.form.get('phone', '')  # Get phone (optional field)
    
    cursor.execute("INSERT INTO users (name, role, phone) VALUES (%s, %s, %s)", 
                  (name, role, phone))
    db.commit()
    return redirect(url_for('view_users'))

# In view_users route (modify query)
@app.route('/users')
def view_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template('users.html', users=users)
# Delete User
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    return redirect(url_for('view_users'))

# View Books
@app.route('/books')
def view_books():
    # Get all books with their average ratings
    cursor.execute("""
        SELECT b.*, AVG(r.rating) as avg_rating
        FROM books b
        LEFT JOIN ratings r ON b.id = r.book_id
        GROUP BY b.id
    """)
    books = cursor.fetchall()
    
    # Determine availability by checking borrowings
    for book in books:
        cursor.execute("""
            SELECT 1 FROM borrowings 
            WHERE book_id = %s AND return_date IS NULL
            LIMIT 1
        """, (book['id'],))
        book['available'] = not cursor.fetchone()  # True if no active borrowing
    
    return render_template('books.html', books=books)

# Add Book
@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    genre = request.form['genre']
    cursor.execute("INSERT INTO books (title, author, genre) VALUES (%s, %s, %s)", (title, author, genre))
    db.commit()
    return redirect(url_for('view_books'))

# Edit Book
@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        cursor.execute("UPDATE books SET title = %s, author = %s, genre = %s WHERE id = %s", 
                      (title, author, genre, book_id))
        db.commit()
        return redirect(url_for('view_books'))
    
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    return render_template('edit_book.html', book=book)

# Delete Book
@app.route('/delete_book/<int:book_id>')
def delete_book(book_id):
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
    db.commit()
    return redirect(url_for('view_books'))

# Borrow Book
@app.route('/borrow_book', methods=['POST'])
def borrow_book():
    try:
        user_id = request.form['user_id']
        book_id = request.form['book_id']
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            flash('Error: User ID does not exist', 'danger')
            return redirect(url_for('view_borrowings'))
        
        # Check if book exists
        cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
        if not cursor.fetchone():
            flash('Error: Book ID does not exist', 'danger')
            return redirect(url_for('view_borrowings'))
        
        # Check if book is already borrowed and not returned
        cursor.execute("""
            SELECT id FROM borrowings 
            WHERE book_id = %s AND return_date IS NULL
        """, (book_id,))
        if cursor.fetchone():
            flash('Error: This book is already borrowed', 'danger')
            return redirect(url_for('view_borrowings'))
        
        # If all checks pass, create the borrowing record
        cursor.execute("""
            INSERT INTO borrowings (user_id, book_id, borrow_date) 
            VALUES (%s, %s, CURDATE())
        """, (user_id, book_id))
        db.commit()
        flash('Book borrowed successfully!', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('view_borrowings'))

# View Borrowings
@app.route('/borrowings')
def view_borrowings():
    cursor.execute("""
        SELECT b.id, u.name as user_name, bo.title as book_title, 
               b.borrow_date, b.return_date
        FROM borrowings b
        JOIN users u ON b.user_id = u.id
        JOIN books bo ON b.book_id = bo.id
    """)
    borrowings = cursor.fetchall()
    return render_template('borrowings.html', borrowings=borrowings)

# Return Book
# ... (keep previous imports and setup)

@app.route('/return_book/<int:borrowing_id>', methods=['GET', 'POST'])
def return_book(borrowing_id):
    try:
        if request.method == 'POST':
            user_id = request.form['user_id']
            rating = request.form['rating']
            book_id = request.form['book_id']
            
            # Verify the borrowing record exists
            cursor.execute("""
                SELECT user_id FROM borrowings 
                WHERE id = %s AND return_date IS NULL
            """, (borrowing_id,))
            record = cursor.fetchone()
            
            if not record:
                flash('Error: This borrowing record does not exist or is already returned', 'danger')
                return redirect(url_for('view_borrowings'))
            
            if int(record['user_id']) != int(user_id):
                flash('Error: You can only return books you borrowed', 'danger')
                return redirect(url_for('view_borrowings'))
            
            # Process return
            cursor.execute("""
                UPDATE borrowings SET return_date = CURDATE() 
                WHERE id = %s
            """, (borrowing_id,))
            
            # Handle rating
            cursor.execute("SELECT id FROM ratings WHERE user_id = %s AND book_id = %s", 
                         (user_id, book_id))
            existing_rating = cursor.fetchone()
            
            if existing_rating:
                cursor.execute("UPDATE ratings SET rating = %s WHERE id = %s", 
                              (rating, existing_rating['id']))
            else:
                cursor.execute("""
                    INSERT INTO ratings (user_id, book_id, rating) 
                    VALUES (%s, %s, %s)
                """, (user_id, book_id, rating))
            
            db.commit()
            flash('Book returned and rated successfully!', 'success')
            return redirect(url_for('view_borrowings'))
        
        # GET request - show return form
        cursor.execute("""
            SELECT b.id, b.book_id, u.name as user_name, bo.title as book_title
            FROM borrowings b
            JOIN users u ON b.user_id = u.id
            JOIN books bo ON b.book_id = bo.id
            WHERE b.id = %s AND b.return_date IS NULL
        """, (borrowing_id,))
        borrowing = cursor.fetchone()
        
        if not borrowing:
            flash('Error: Invalid borrowing record', 'danger')
            return redirect(url_for('view_borrowings'))
        
        return render_template('return_book.html', borrowing=borrowing)
        
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('view_borrowings'))

# Rate Book
@app.route('/rate_book/<int:book_id>', methods=['POST'])
def rate_book(book_id):
    user_id = request.form['user_id']
    rating = request.form['rating']
    
    # Check if user already rated this book
    cursor.execute("SELECT id FROM ratings WHERE user_id = %s AND book_id = %s", 
                  (user_id, book_id))
    existing_rating = cursor.fetchone()
    
    if existing_rating:
        cursor.execute("UPDATE ratings SET rating = %s WHERE id = %s", 
                      (rating, existing_rating['id']))
    else:
        cursor.execute("INSERT INTO ratings (user_id, book_id, rating) VALUES (%s, %s, %s)", 
                      (user_id, book_id, rating))
    
    db.commit()
    return redirect(url_for('view_books'))

@app.route('/top_books')
def top_books():
    # Get top rated books
    cursor.execute("""
        SELECT b.*, 
               AVG(r.rating) as avg_rating,
               COUNT(r.rating) as rating_count
        FROM books b
        LEFT JOIN ratings r ON b.id = r.book_id
        GROUP BY b.id
        HAVING avg_rating IS NOT NULL
        ORDER BY avg_rating DESC
        LIMIT 5
    """)
    top_books = cursor.fetchall()
    
    # Calculate availability for each book
    for book in top_books:
        cursor.execute("""
            SELECT 1 FROM borrowings 
            WHERE book_id = %s AND return_date IS NULL
            LIMIT 1
        """, (book['id'],))
        book['available'] = not cursor.fetchone()
    
    return render_template('top_books.html', top_books=top_books)

if __name__ == "__main__":
    app.run(debug=True)
