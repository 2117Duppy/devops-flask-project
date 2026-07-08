from flask import Flask, render_template
import pymysql
import os

app = Flask(__name__)


def get_users():
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

    cursor = connection.cursor()

    cursor.execute("SELECT name FROM Users")

    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return users


@app.route("/")
def home():
    users = get_users()
    return render_template("index.html", messages=users)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
