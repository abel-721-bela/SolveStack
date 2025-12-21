from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
import sys

sys.path.append('D:/major proj demo')

import pyproblem_shelf as your_scraping_module

app = Flask(__name__)
CORS(app)
@app.route('/scrape', methods=['POST'])
def scrape():
    problems = your_scraping_module.scrape_reddit(limit=20)
    your_scraping_module.store_in_db(problems)
    your_scraping_module.export_to_json()
    return jsonify({"message": "Scraping completed"})

@app.route('/problems', methods=['GET'])
def get_problems():
    conn = sqlite3.connect('problems.db')
    df = pd.read_sql_query("SELECT * FROM problem_statements", conn)
    conn.close()
    problems = df.to_dict(orient='records')
    for problem in problems:
        if isinstance(problem['tags'], str):
            problem['tags'] = eval(problem['tags']) if problem['tags'] else []
    return jsonify(problems)

@app.route('/suggest', methods=['GET'])
def get_suggestions():
    tech_input = request.args.get('tech', '')
    conn = sqlite3.connect('problems.db')
    query = "SELECT * FROM problem_statements WHERE suggested_tech LIKE ?"
    suggestions = pd.read_sql_query(query, conn, params=[f'%{tech_input.lower()}%'])
    conn.close()
    return jsonify(suggestions.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)