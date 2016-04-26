from flask import Flask, request, render_template
from src.scoreboard import Scoreboard
from src import extract_data
import numpy as np
import pandas as pd
import sys
# import re
# from jinja2 import evalcontextfilter, Markup, escape
reload(sys)
sys.setdefaultencoding("utf-8")
# _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
app = Flask(__name__)

#home page
@app.route('/')
def index():
    return render_template('index.html', error='')

#recommendation result page
@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    channel = str(request.form.get('channel_id').encode(encoding='ascii', errors='ignore'))
    cat = str(request.form.get('category'))
    cat = cat.replace(' ', '_').replace('&', 'and')
    y = extract_data.get_specific_channel(channel)
    if y.empty:
        return render_template('index.html', error="Please input a real channel ID.")
    df = pd.read_csv('data/YT'+cat+'_data.csv')
    score = Scoreboard()
    score.fit(df, y)
    user = y['title'][0]
    results = score.most_similar(25)
    return render_template('recommend.html', results=results, user=user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
