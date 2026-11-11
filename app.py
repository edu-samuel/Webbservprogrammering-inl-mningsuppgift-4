
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "change_this_secret_key"


@app.route("/")
def home():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, inlägg, tidpunkt, användarnamn
            FROM posts
            ORDER BY tidpunkt DESC
        """)
        posts = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    return render_template("index.html", posts=posts)


@app.route("/create_post", methods=["POST"])
def create_post():

    if "user_id" not in session:
        flash("Du måste logga in först.")
        return redirect(url_for("login"))

    inlägg = request.form.get("inlägg", "").strip()

    if not inlägg:
        flash("Du måste skriva något.")
        return redirect(url_for("home"))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO posts (inlägg, tidpunkt, användarnamn)
            VALUES (%s, NOW(), %s)
        """, (inlägg, session["användarnamn"]))

        connection.commit()

        flash("Ditt inlägg har publicerats!")

    except Exception as error:
        connection.rollback()
        print("POST ERROR:", repr(error))
        flash("Det gick inte att publicera inlägget.")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("home"))



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        namn = request.form["namn"].strip()
        användarnamn = request.form["användarnamn"].strip()
        lösenord = request.form["lösenord"]

        if not namn or not användarnamn or not lösenord:
            flash("Alla fält måste fyllas i.")
            return redirect(url_for("register"))

        if len(lösenord) < 8:
            flash("Lösenordet måste innehålla minst 8 tecken.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(lösenord)

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO users (namn, användarnamn, lösenord)
                VALUES (%s, %s, %s)
            """, (namn, användarnamn, hashed_password))

            connection.commit()

            print("REGISTER SUCCESS: User saved!")

            flash("Ditt konto har skapats! Du kan nu logga in.")
            return redirect(url_for("login"))

        except Exception as error:

            if connection:
                connection.rollback()

            print("REGISTER ERROR:", repr(error))

            flash(f"Registreringen misslyckades: {error}")
            return redirect(url_for("register"))

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    print("LOGIN ROUTE:", request.method)

    if request.method == "POST":

        print("POST REQUEST RECEIVED!")

        print("FORM DATA:", request.form)

        användarnamn = request.form.get("användarnamn", "").strip()
        lösenord = request.form.get("lösenord", "")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, namn, användarnamn, lösenord
            FROM users
            WHERE användarnamn = %s
        """, (användarnamn,))

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        print("USER FOUND:", user is not None)

        if user and check_password_hash(user["lösenord"], lösenord):

            session.clear()
            session["user_id"] = user["id"]
            session["användarnamn"] = user["användarnamn"]
            session["namn"] = user["namn"]

            print("LOGIN SUCCESS!")

            flash("Du är nu inloggad!")
            return redirect(url_for("home"))

        else:
            print("LOGIN FAILED!")

            flash("Fel användarnamn eller lösenord.")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash("Du har loggat ut.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)