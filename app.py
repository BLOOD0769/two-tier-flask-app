"""
app.py - Main Flask application

This is a simple two-tier web app:
  - Tier 1: This Flask app (the "web" layer)
  - Tier 2: MySQL database (the "data" layer)

It shows a simple guestbook: visitors can leave a name + message,
and all past entries are displayed on the page.
"""

import os
import time
import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ---------------------------------------------------------------
# Database configuration
# We NEVER hardcode credentials here. Instead, we read them from
# environment variables, which are set in docker-compose.yml.
# ---------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "app_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "app_password")
DB_NAME = os.environ.get("DB_NAME", "guestbook")


def get_db_connection(retries=10, delay=3):
    """
    Try to connect to MySQL, retrying a few times.

    Why we need this: when Docker Compose starts both containers
    together, the 'db' container often isn't fully ready to accept
    connections yet, even though the container itself has started.
    Without retrying, Flask would crash immediately on startup.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
            )
            print(f"[DB] Connected successfully on attempt {attempt}")
            return connection
        except Error as e:
            last_error = e
            print(f"[DB] Attempt {attempt}/{retries} failed: {e}")
            time.sleep(delay)
    # If we get here, all retries failed.
    raise RuntimeError(f"Could not connect to database after {retries} attempts: {last_error}")


@app.route("/health")
def health():
    """
    Simple health check endpoint.
    Jenkins' pipeline will curl this after deploying, to confirm
    the app actually started successfully.
    """
    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    """Show all guestbook entries."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, message, created_at FROM entries ORDER BY created_at DESC")
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("index.html", entries=entries)


@app.route("/add", methods=["POST"])
def add_entry():
    """Add a new guestbook entry, then redirect back to the homepage."""
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()

    if name and message:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entries (name, message) VALUES (%s, %s)",
            (name, message),
        )
        conn.commit()
        cursor.close()
        conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    # This block only runs if you execute `python app.py` directly.
    # In production (inside Docker), gunicorn runs the app instead,
    # so this block is skipped - see the Dockerfile's CMD.
    app.run(host="0.0.0.0", port=5000, debug=False)
