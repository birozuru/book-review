import os

os.environ['DATABASE_URL'] = "postgres://rnvbtygbuvjnxk:62c517826eaac4bab1f7757b48a601bb383e455da2b3a6353beb6b4ee3252eda@ec2-34-230-149-169.compute-1.amazonaws.com:5432/d976k57dmhcech"

from flask import Flask, session, request, render_template, url_for, redirect, jsonify, flash
from flask_bcrypt import Bcrypt
from flask_session import Session
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker
from forms import BookSearchForm
import requests
import bcrypt
import csv

app = Flask(__name__)
app.config["DEBUG"] = True
bcrypt = Bcrypt(app)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return redirect(url_for('dashboard'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    message = None

    if request.method == "POST":
        try: 
            usern = request.form.get("username")
            passw = request.form.get("password")
            pw_hash = bcrypt.generate_password_hash(passw).decode('utf-8')
            first = request.form.get("first_name")
            last  =  request.form.get("last_name")
            email = request.form.get("email")

            result = db.execute("INSERT INTO accounts (username, password, first_name, last_name, email) VALUES (:u, :p, :f, :l, :e)", {"u": usern, "p": pw_hash, "f":first, "l":last, "e":email})
            db.commit()

            if result.rowcount > 0:
                session['user'] = usern
                return redirect(url_for('dashboard'))

        except exc.IntegrityError:
            message = "Username already exists."
            db.execute("ROLLBACK")
            db.commit()

    return render_template("registration.html", message=message)  

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    message = None

    if request.method == "POST":
        usern = request.form.get("username")
        passw = request.form.get("password").encode('utf-8')
        result = db.execute("SELECT * FROM accounts WHERE username = '{}'".format(str(usern))).fetchone()
     

        message = "Username or password is incorrect."

        if result is not None:

            if bcrypt.check_password_hash(list(result)[2], passw) is True:
                session['user'] = usern
                return redirect(url_for('dashboard'))
            else:
                #print(message)
                pass
                
        message = "Username or password is incorrect."
    return render_template("login.html", message=message)  

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    if 'user' in session:
        return render_template("dashboard.html", logged=session['user'])

    if request.method == "POST":
            return redirect(url_for('search'))     


@app.route("/dashboard/search", methods=["POST", "GET"])
def search():
    if 'user' not in session:
        return redirect(url_for('login'))

    #message = None

    if 'user' in session:

        query = request.form.get("search")
        query = '%' + str(query) + '%'
        results = db.execute("SELECT * FROM books WHERE title LIKE :q OR isbn LIKE :q OR author LIKE :q LIMIT 10", {"q": query}).fetchall()
        return render_template("search.html", results=results)

@app.route("/b/<string:isbn>", methods=["GET", "POST"])
def info(isbn):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        comment = request.form.get("comment")
        my_rating = request.form.get("rating")
        book = db.execute("INSERT INTO reviews (acc_id, book_id, comment, rating) VALUES (:a, :b, :c, :r)", {"a": session['user'], "b": isbn, "c": comment, "r": my_rating})
        db.commit()

    book = db.execute("SELECT * FROM books WHERE isbn = :q", {"q": isbn}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :q1", {"q1": isbn}).fetchall()

    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "atFOLd1rrwPS4pv6v3pRg", "isbns": isbn})
    data = response.json()
    gr_rating = (data['books'][0]['average_rating'])

    return render_template("info.html", book_info=book, reviews=reviews, rating=gr_rating)

@app.route("/api/<string:isbn>")
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :q", {"q": isbn}).fetchone()
    
    if book is None:
        return jsonify({"error": "Invalid ISBN"}), 404

    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :q1", {"q1": isbn}).fetchall()
    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "atFOLd1rrwPS4pv6v3pRg", "isbns": isbn})
    data = response.json()['books'][0]
    
    return jsonify({
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "review_count": data['reviews_count'],
        "average_rating": data['average_rating']
    })
    
    
if __name__ == "__main__":
    app.run()














