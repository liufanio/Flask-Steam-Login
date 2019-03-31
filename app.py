from flask import Flask, redirect, request, json, g, url_for
from flask_sqlalchemy import SQLAlchemy

import re
from urllib import parse
import urllib.request

app = Flask(__name__)
db = SQLAlchemy(app)

app.debug = True

steam_openid_url = 'https://steamcommunity.com/openid/login'

steam_id_re = re.compile('https://steamcommunity.com/openid/id/(.*?)$')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(40))
    nickname = db.String(80)

    @staticmethod
    def get_or_create(steam_id):
        rv = User.query.filter_by(steam_id=steam_id).first()
        if rv is None:
            rv = User()
            rv.steam_id = steam_id
            db.session.add(rv)
        return rv

def get_user_info(steam_id):
    options = {
        'key': 'Steam Web API',
        'steamids': steam_id
    }
    url = 'https://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0002/?%s' % urllib.parse.urlencode(options)
    rv = json.load(urllib.request.urlopen(url))
    return rv['response']['players'][0] or {}


@app.route("/")
def hello():
    return '<a href="http://localhost:5000/auth">Login with steam</a>'


@app.route("/auth")
def login():
    params = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.mode': 'checkid_setup',
        'openid.return_to': 'http://127.0.0.1:5000/authorize',
        'openid.realm': 'http://127.0.0.1:5000'
    }

    param_string = parse.urlencode(params)
    auth_url = steam_openid_url + "?" + param_string
    return redirect(auth_url)


@app.route("/authorize")
def authorize():
    match = steam_id_re.search(dict(request.args)['openid.identity'])
    g.user = User.get_or_create(match.group(1))
    steam_data = get_user_info(g.user.steam_id)
    g.user.nickname = steam_data['personaname']
    db.session.commit()
    return redirect(url_for('hello'))


if __name__ == "__main__":
    app.run()
