# app.py
from flask import Flask, request, render_template
from search_engine import load_all_chunks, keyword_search_web, fuzzy_search_web

app = Flask(__name__)
chunks = load_all_chunks()

@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    results = []
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        results = keyword_search_web(query, chunks, limit=5)
        if not results:
            results = fuzzy_search_web(query, chunks, limit=5)
    return render_template("index.html", query=query, results=results)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)


