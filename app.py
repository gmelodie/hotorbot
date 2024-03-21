import random
import os
import hashlib
import time
import json
import logging

from secrets import token_urlsafe

from flask import Flask, request, render_template, send_from_directory
from flask import redirect, session, make_response, url_for
from flask_session import Session
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

import sqlite3
import pandas as pd
import plotly
import plotly.graph_objects as go

app = Flask(__name__)

app.config['DEBUG'] = os.environ.get('DEBUG', False)
app.logger.setLevel(logging.ERROR)

# tell flask it's behind a proxy (nginx)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


DB_FILE = "database.db"
CREATE_VOTES_TABLE = """ CREATE TABLE IF NOT EXISTS votes (
                            userid VARCHAR(64),
                            language VARCHAR(20),
                            hot BOOL,
                            PRIMARY KEY (userid, language)
                        ); """


# lang, hot, bot
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

def run_db_query(query_str, parameters=(), fetch_query=False):
    result = []
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        res = cursor.execute(query_str, parameters)
        if fetch_query:
            result = res.fetchall()
        conn.commit()

    return result

def gen_res_graph(results):
    d = {'Who': [row[0] for row in results],
         'Bot': [row[1] for row in results],
         'Hot': [row[2] for row in results],}

    df = pd.DataFrame(d)

    fig = go.Figure()
    for col in df.columns[1:2]:
        fig.add_trace(go.Bar(x=df[col].values,
                             y=df['Who'],
                             orientation='h',
                             name=col,
                             customdata=df[col],
                             hovertemplate = "%{y}: %{customdata}",
                             showlegend=False,
                             marker=dict(color='#F6AA1C')
                             ))
    for col in df.columns[2:3]:
        fig.add_trace(go.Bar(x=-df[col],
                             y=df['Who'],
                             orientation='h',
                             name= col,
                             customdata=df[col],
                             hovertemplate = "%{y}: %{customdata}",
                             showlegend=False,
                             marker=dict(color='#FF4D4D')
                             ))

    fig.update_layout(barmode='relative',
                      yaxis_autorange='reversed',
                      bargap=0.02,
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)',
                      hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                      xaxis=dict(showticklabels=False),
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
    count_hots_and_bots_query = "SELECT language, \
                                COUNT(CASE WHEN NOT hot THEN 1 END) as not_hot, \
                                COUNT(CASE WHEN hot THEN 1 END) as hot \
                                FROM votes GROUP BY language \
                                ORDER BY hot DESC, not_hot ASC;"

    results = run_db_query(count_hots_and_bots_query, fetch_query=True)

    return render_template('results.html', graph=gen_res_graph(results))


@app.errorhandler(HTTPException)
def handle_exception(e):
    app.logger.error(e)
    return render_template('error.html'), random.choice(funny_distractors)


@app.route('/vote', methods=['POST'])
def vote():
    # if user does not have a cookie, give'em one
    if 'userid' not in session:
        return handle_exception(HTTPException("userid not in session"))

    # Check input (no funky stuff)
    if 'lang' not in request.form or 'hot' not in request.form:
        return handle_exception(None)

    lang = request.form['lang']

    if lang not in langs or \
            request.form['hot'] not in ['Hot', 'Bot']:
        return handle_exception(None)

    hot = False
    if request.form['hot'] == 'Hot':
        hot = True

    print(lang, request.form['hot'])

    # Put vote in database
    insert_query = "INSERT INTO votes(userid, language, hot) VALUES (?, ?, ?);"
    print(f"inserting: {insert_query}")
    run_db_query(insert_query, parameters=(session['userid'], lang, hot), fetch_query=False)

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



random.seed()

# if database file does not exist, create it:
if not os.path.isfile(DB_FILE):
    open(DB_FILE, 'w')
run_db_query(CREATE_VOTES_TABLE)



if __name__ == '__main__':
    app.run(port=5001)



