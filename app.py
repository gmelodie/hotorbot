import random
import os
import hashlib
import time
import json

from collections import defaultdict

from flask import Flask, request, render_template
from flask import redirect, session, make_response, url_for
from werkzeug.exceptions import HTTPException

import psycopg2
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px


app = Flask(__name__)


try:
    DATABASE_URL = os.environ['DATABASE_URL']
    SESSION_KEY = os.environ['HOB_SESS_SEED']
    app.secret_key = os.environ['HOB_SESS_SEED'].encode('utf-8')
except KeyError:
    print("Couldn't find some env vars. Are (all of) them set?")
    exit(1)


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


@app.route('/results')
def results():
    count_hots_and_nots_query = "SELECT language, \
                                COUNT(CASE WHEN hot THEN 1 END) as hot, \
                                COUNT(CASE WHEN NOT hot THEN 1 END) as not_hot \
                                FROM votes GROUP BY language \
                                ORDER BY hot DESC, not_hot ASC;"

    with psycopg2.connect(DATABASE_URL, sslmode='require') as conn:
        with conn.cursor() as cursor:
            cursor.execute(count_hots_and_nots_query)
            results = cursor.fetchall()

    return render_template('results.html', graph=gen_res_graph(results))


@app.errorhandler(HTTPException)
def handle_exception(e):
    return render_template('error.html'), random.choice(funny_distractors)


@app.route('/vote', methods=['POST'])
def vote():

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
    with psycopg2.connect(DATABASE_URL, sslmode='require') as conn:
        with conn.cursor() as cursor:
            insert_query = """INSERT INTO votes(language, hot)\
                                VALUES (%s, %s);"""
            cursor.execute(insert_query,(lang, hot));
            conn.commit()

    session['langi'] += 1
    return redirect(url_for('index'))


@app.route('/')
def index():
    if 'userid' not in session:
        ts = str(time.time())
        full_key = (ts+SESSION_KEY).encode('utf-8')
        session['userid'] = hashlib.sha512(full_key).hexdigest()
        session['langi'] = 0

    i = session['langi']
    print(session['userid'], session['langi'])
    if i >= len(langs):
        return render_template('thx.html')

    return render_template('index.html', lang=list(langs)[i])


if __name__ == '__main__':
    random.seed()
    app.run()



