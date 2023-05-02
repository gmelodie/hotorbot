import random
import os
import hashlib
import time
import json

from collections import defaultdict
from secrets import token_urlsafe

from flask import Flask, request, render_template, send_from_directory
from flask import redirect, session, make_response, url_for
from flask import send_from_directory
from werkzeug.exceptions import HTTPException
from flask_sslify import SSLify

import sqlite3
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px


app = Flask(__name__)
sslify = SSLify(app)


DB_FILE = "database.db"
CREATE_VOTES_TABLE = """ CREATE TABLE IF NOT EXISTS votes (
                            userid VARCHAR(64),
                            language VARCHAR(20),
                            hot BOOL,
                            PRIMARY KEY (userid, language)
                        ); """


# lang, hot, not
langs = set(['Python',
         'Rust',
         'PHP',
         'Objective-C',
         'SQL',
         'Ruby',
         'R',
         'Matlab',
         'Assembly',
         'Perl',
         'Swift',
         'Kotlin',
         'Elixir',
         'Go',
         'C',
         'C++',
         'C#',
         'Java',
         'JavaScript',
        ])

funny_distractors = [100, 200, 201, 203, 300, 303, 400, 404, 401, 500,
                     505, 503, 501, 529]

app.secret_key = token_urlsafe(64)

def run_db_query(query_str, fetch_query=False):
    result = []
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            res = cursor.execute(query_str)
            if fetch_query:
                result = res.fetchall()
            conn.commit()
    except Exception as e:
        print(e)

    return result


def gen_res_graph(results):
    d = {'Who': [row[0] for row in results],
     'Hot': [row[1] for row in results],
     'Not': [row[2] for row in results],}

    df = pd.DataFrame(d)

    fig = go.Figure()
    for col in df.columns[1:2]:
        fig.add_trace(go.Bar(x=df[col].values,
                             y=df['Who'],
                             orientation='h',
                             name=col,
                             customdata=df[col],
                             hovertemplate = "%{y}: %{customdata}"))
    for col in df.columns[2:3]:
        fig.add_trace(go.Bar(x=-df[col],
                             y=df['Who'],
                             orientation='h',
                             name= col,
                             customdata=df[col],
                             hovertemplate = "%{y}: %{customdata}"))

    fig.update_layout(barmode='relative',
                      yaxis_autorange='reversed',
                      bargap=0.02,
                     )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico')


@app.route('/styles.css')
def stylesheet():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'styles.css')


@app.route('/results')
def results():
    count_hots_and_nots_query = "SELECT language, \
                                COUNT(CASE WHEN hot THEN 1 END) as hot, \
                                COUNT(CASE WHEN NOT hot THEN 1 END) as not_hot \
                                FROM votes GROUP BY language \
                                ORDER BY hot DESC, not_hot ASC;"

    results = run_db_query(count_hots_and_nots_query, fetch_query=True)

    return render_template('results.html', graph=gen_res_graph(results))


@app.errorhandler(HTTPException)
def handle_exception(e):
    print(e)
    return render_template('error.html'), random.choice(funny_distractors)


@app.route('/vote', methods=['POST'])
def vote():
    # if user does not have a cookie, give'em one
    if 'userid' not in session:
        return handle_exception(None)

    # Check input (no funky stuff)
    if 'lang' not in request.form or 'hot' not in request.form:
        return handle_exception(None)

    lang = request.form['lang']

    if lang not in langs or \
            request.form['hot'] not in ['Hot', 'Not']:
        return handle_exception(None)

    hot = False
    if request.form['hot'] == 'Hot':
        hot = True

    print(lang, request.form['hot'])

    # Put vote in database
    insert_query = f"""INSERT INTO votes(userid, language, hot)\
                        VALUES ('{session['userid']}', '{lang}', {hot});"""
    print(f"inserting: {insert_query}")
    run_db_query(insert_query)

    session['langi'] += 1
    return redirect(url_for('index'))


@app.route('/')
def index():
    # if user does not have a cookie, give'em one
    if 'userid' not in session:
        ts = str(time.time())
        full_key = (ts+token_urlsafe(64)).encode('utf-8')
        session['userid'] = hashlib.sha512(full_key).hexdigest()
        session['langi'] = 0

    i = session['langi']
    print(session['userid'], session['langi'])
    if i >= len(langs):
        return render_template('thx.html')

    return render_template('index.html', lang=list(langs)[i])


if __name__ == '__main__':
    random.seed()
    run_db_query(CREATE_VOTES_TABLE)
    app.run()



