from flask import Flask, render_template, request, redirect, jsonify, session
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from tempfile import mkdtemp
import sqlite3, datetime
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, apology
import os,binascii

app = Flask(__name__)
app.config['SECRET_KEY'] = 'GetRektMur4tReyiz#'
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DBNAME = "database.db"
REGISTERS = {}
SPORTS = [
    "Basketball",
    "Soccer",
    "Volleyball",
    "Tennis"
]
FORBIDDEN = [
    "script",
    "oç",
    "sik",
    "yarak"
    ]
chatlog = None
db = sqlite3.connect(DBNAME)
N = 20
db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_name TEXT NOT NULL, password_hash TEXT NOT NULL, sport TEXT NOT NULL, date DATETIME NOT NULL, color CHAR(6) NOT NULL)")
db.execute("CREATE TABLE IF NOT EXISTS login_history(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, userid INTEGER REFERENCES users(id) NOT NULL, date DATETIME NOT NULL)")
db.execute("CREATE TABLE IF NOT EXISTS chat_log(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT REFERENCES users(user_name) NOT NULL, message TEXT NOT NULL, date DATETIME NOT NULL, color TEXT not NULL)")
db.close()
@app.route("/", methods=["POST", "GET"])
def index():

    if request.method == "GET":
        if session.get("user_id") is not None:
            return render_template("index.html", sports=SPORTS, login=True, username= session.get("user_name"))
        else:
            return render_template("index.html", sports=SPORTS, login=False)
    if request.method == "POST":
        if session.get("user_id") is not None:
            sport = request.form.get("sport")
            if not sport or sport not in SPORTS:
                return render_template("error.html", message="Invalid sport")
            db = sqlite3.connect(DBNAME)
            user_name = session.get("user_name")
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.execute("UPDATE users SET sport = ?, date = ? WHERE user_name = ?;", (sport, now, user_name,))
            db.commit()
            db.close()
            return render_template("registertosport.html", name=user_name, sport=sport)
        else:
            return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    user_name = request.form.get("username")
    password = request.form.get("password")
    password2 = request.form.get("password2")
    if not password or not password2 or len(str(password)) > 15 or password != password2:
        return render_template("error.html", message="Invalid password or they do not match")
    if not user_name or user_name == "" or len(user_name) > 15 or "all" == user_name :
        return render_template("error.html", message="Invalid name")
    db = sqlite3.connect(DBNAME)
    row = db.execute("SELECT * FROM users WHERE user_name = ?", (user_name,)).fetchall()
    if len(row) != 0:
        return render_template("error.html", message="This username is used")
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute("INSERT INTO users (user_name, password_hash, sport, date, color) VALUES ( ? , ?, 'not defined', ?, ?);", (user_name, generate_password_hash(password), now, str(binascii.b2a_hex(os.urandom(3)))[2:-1], ))
    db.commit()
    row = db.execute("SELECT * FROM users WHERE user_name = ?", (user_name,)).fetchall()
    session["user_id"] = row[0][0]
    session["user_name"] = user_name
    session["color"] = row[0][5]
    db.close()
    return render_template("success.html", message="successfully registered")

@app.route("/list", methods=["GET"])
def list():
    db = sqlite3.connect(DBNAME)
    rows = db.execute("SELECT * FROM users;").fetchall()
    return render_template("list.html", values=rows)

@app.route("/search", methods=["GET"])
def search():
    q = str(request.args.get("q"))
    if q != "None" and q != "":
        db = sqlite3.connect(DBNAME)
        rows = db.execute("SELECT id, user_name, sport, date FROM users WHERE user_name LIKE ? OR sport LIKE ?;", (q, q, )).fetchall()
        db.close()
        return render_template("search.html", query=q, values=rows)
    return render_template("search.html", query=None)

@app.route("/searchjson", methods=["GET"])
def searchjson():
    q = "%" + str(request.args.get("q")) + "%"
    db = sqlite3.connect(DBNAME)
    db.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
    rows = db.execute("SELECT id, user_name, sport, date FROM users WHERE user_name LIKE ? OR sport LIKE ?;", (q, q, )).fetchall()
    db.close()
    return jsonify(rows)

@app.route("/search2", methods=["GET"])
def search2():
    return render_template("search2.html")

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        username = session["user_name"]
        color = session["color"]
        message = request.form.get("message")
        if message and color and username:
            flag = False
            for word in FORBIDDEN:
                if word in message.lower():
                    flag = True
                    break
            if not flag:
                db = sqlite3.connect(DBNAME)
                if session.get("user_name") == "emre":
                    command = message.split()
                    if command[0] == "/clear":
                        try:
                            variable = command[1]
                            if variable == "all":
                                db.execute("DELETE FROM chat_log;")
                            else:
                                try:
                                    val = int(command[2])
                                    db.execute("DELETE FROM chat_log Where username = ? order by id desc limit ?;", (variable, val, ))
                                except:
                                    db.execute("DELETE FROM chat_log Where username = ?;", (variable,))
                        finally:
                            db.commit()
                global chatlog
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.execute("INSERT INTO chat_log (username, color, message, date) VALUES ( ? , ?, ?, ?);", (username, color, message, now, ))
                db.commit()
                db.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
                rows = db.execute("SELECT * FROM (SELECT username, message, date, color FROM chat_log order by id DESC limit ?) ORDER BY date ASC;", (N,)).fetchall()
                db.close()
                chatlog = jsonify(rows)
    return render_template('chat.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id") is not None:
            return redirect("/")
        return render_template("login.html")
    if request.method == "POST":
        user_name = request.form.get("username")
        password = request.form.get("password")
        if not user_name or user_name == "":
            return render_template("error.html", message="Invalid username")
        db = sqlite3.connect(DBNAME)
        row = db.execute("SELECT * FROM users WHERE user_name = ?", (user_name,)).fetchall()
        if len(row) != 1 or not check_password_hash(row[0][2], password):
            db.close()
            return render_template("error.html", message="Invalid username or password", redirect="login")
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute("INSERT INTO login_history (userid, date) VALUES (?, ?)", (row[0][0], row[0][4], ))
        db.commit()
        session["user_id"] = row[0][0]
        session["user_name"] = user_name
        session["color"] = row[0][5]
        db.close()
        return render_template("error.html", message="Logged in")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("error.html", message="Logged out")

@app.route("/chatjson")
def chatjson():
    if session.get("user_id") == None:
        return jsonify({})
    global chatlog
    if chatlog == None:
        db = sqlite3.connect(DBNAME)
        db.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
        rows = db.execute("SELECT * FROM (SELECT username, message, date, color FROM chat_log order by id DESC limit ?) ORDER BY date ASC;", (N,)).fetchall()

        db.close()
        chatlog = jsonify(rows)
    return chatlog
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


