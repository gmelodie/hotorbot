import random
import os
import hashlib
import time
from collections import defaultdict

from flask import Flask, request, render_template
from flask import redirect, session, make_response, url_for
from werkzeug.exceptions import HTTPException


app = Flask(__name__)


try:
    SESSION_KEY = os.environ['HOB_SESS_SEED']
    app.secret_key = os.environ['HOB_SESS_SEED'].encode('utf-8')
except KeyError:
    print("Couldn't find $HOB_SESS_SEED env var. Is it set?")
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


@app.route('/results')
def results():
    res = defaultdict(lambda: [0, 0])
    with open('results.dat', 'r') as fp:
        for line in fp:
            lang, vote = line.split()
            if vote == 'Hot':
                res[lang][0] += 1
            elif vote == 'Not':
                res[lang][1] += 1
            else:
                print("Neither 'Hot' nor 'Not', got: " + vote)

    res = list(res.items())
    res.sort(key=lambda x:x[1][0], reverse=True)

    return render_template('results.html', res=res)


@app.errorhandler(HTTPException)
def handle_exception(e):
    return render_template('error.html'), random.choice(funny_distractors)


@app.route('/vote', methods=['POST'])
def vote():

    if 'lang' not in request.form or 'hot' not in request.form:
        return handle_exception(None)

    lang = request.form['lang']

    if lang not in langs or \
            request.form['hot'] not in ['Hot', 'Not']:
        return handle_exception(None)

    print(lang, request.form['hot'])

    with open('results.dat', 'a') as fp:
        fp.write(lang + ' ' + request.form['hot'] + '\n')

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



