# app.py
from flask import Flask, request, render_template, redirect, url_for, session
from search_engine import load_all_chunks, keyword_search_web, fuzzy_search_web

app = Flask(__name__)
app.secret_key = "super-secret-key"  # change this later for security
PASSWORD = "Hopscotch"

print("Flask app is launching...")

chunks = load_all_chunks()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/search", methods=["GET", "POST"])
def index():
    if not session.get("authenticated"):
        return redirect(url_for("login"))

    query = ""
    results = []
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        results = keyword_search_web(query, chunks, limit=5)
        if not results:
            results = fuzzy_search_web(query, chunks, limit=5)
    return render_template("index.html", query=query, results=results)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=10000)

