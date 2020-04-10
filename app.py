import random

from flask import Flask
from flask import request
from flask import render_template
from werkzeug.exceptions import HTTPException


app = Flask(__name__)

# lang, hot, not
langs = {'Python 2': [0, 0],
         'Python 3': [0, 0],
         'Rust': [0, 0],
         'PHP': [0, 0],
         'Objective-C': [0, 0],
         'SQL': [0, 0],
         'Ruby': [0, 0],
         'R': [0, 0],
         'Matlab': [0, 0],
         'Assembly': [0, 0],
         'Perl': [0, 0],
         'Swift': [0, 0],
         'Kotlin': [0, 0],
         'Elixir': [0, 0],
         'Go': [0, 0],
         'C': [0, 0],
         'C++': [0, 0],
         'C#': [0, 0],
         'Java': [0, 0],
         'JavaScript': [0, 0],
        }

funny_distractors = [100, 200, 201, 203, 300, 303, 400, 404, 401, 500,
                     505, 503, 501, 529]


@app.route('/results')
def results():
    hots = list(langs.items())
    hots.sort(key=lambda x:x[1][0], reverse=True)

    return render_template('results.html', hots=hots)


@app.errorhandler(HTTPException)
def handle_exception(e):
    return render_template('error.html'), random.choice(funny_distractors)


@app.route('/vote', methods=['POST'])
def vote():

    if 'lang' not in request.form or 'hot' not in request.form:
        return handle_exception(None)

    lang = request.form['lang']

    hot = False
    if request.form['hot'] == 'Hot':
        hot = True

    if lang not in langs or \
            request.form['hot'] not in ['Hot', 'Not']:
        return handle_exception(None)

    print(lang, hot)

    if hot:
        langs[lang][0] += 1
    else:
        langs[lang][1] += 1

    return render_template('index.html', lang=random.choice(list(langs.keys())))


@app.route('/')
def index():
    return render_template('index.html', lang=random.choice(list(langs.keys())))


if __name__ == '__main__':
    random.seed()
    app.run()



