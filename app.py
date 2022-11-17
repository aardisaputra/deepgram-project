from flask import Flask, request, send_from_directory, abort, render_template, url_for, redirect, session
from mutagen.mp3 import MP3
from authlib.integrations.flask_client import OAuth
from functools import wraps
import requests
import os
import shutil
import json

app = Flask(__name__)
app.secret_key = "12345!"
app.config['SESSION_TYPE'] = 'filesystem'
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="1043743947045-u0dgak3rc2n0ea4l9ncfmpjddh4o71sq.apps.googleusercontent.com",
    client_secret="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",
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
)

ALLOWED_EXTENSIONS = ['mp3', 'wav']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(session)
        user = dict(session).get('profile', None)
        if user:
            return f(*args, **kwargs)
        return 'You need to be logged in'
    return decorated_function


@app.route("/")
@login_required
def home():
    email = dict(session)['profile']['email']
    return render_template('index.html')


@app.route("/post", methods=["POST"])
@login_required
def post():

    if 'file' not in request.files:
        return json.dumps({'success': "False", "error": "Invalid file type"}, indent=4)

    musicFile = request.files['file']

    if musicFile.filename == '':
        return json.dumps({'success': "False", "error": "File not selected"}, indent=4)
    if musicFile and allowed_file(musicFile.filename):
        musicFile.save(os.path.join(
            './storage/', musicFile.filename))
        return json.dumps({'success': "True"}, indent=4)


@app.route("/download", methods=["GET"])
async def download():
    args = request.args
    print(args)
    test = os.path.exists('./storage/' + args['name'])
    print(test)

    if not test:
        return json.dumps({'success': "False", "error": "File not found"}, indent=4)
    else:
        shutil.copyfile(
            './storage/' + args['name'], './downloads/' + args['name'])
        return json.dumps({'success': "True"}, indent=4)


@app.route("/list", methods=["GET"])
@login_required
def listAll():
    args = request.args
    if "maxduration" in args and args["maxduration"] != "":
        maxDur = args["maxduration"]
    else:
        maxDur = -1

    res = []
    for f in os.listdir("./storage"):
        mp3File = MP3("./storage/" + f)
        if maxDur == -1:
            res.append(f)
        else:
            if mp3File.info.length <= float(maxDur):
                res.append(f)
    print(res)
    return json.dumps({'songs': res}, indent=4)


@app.route("/info", methods=["GET"])
@login_required
def info():
    args = request.args
    test = os.path.exists('./storage/' + args['name'])

    if not test:
        return json.dumps({'success': "False", "error": "File not found"}, indent=4)
    else:
        mp3File = MP3("./storage/" + args['name'])
        return json.dumps({'name': args['name'], 'channels': mp3File.info.channels, 'bitrate': mp3File.info.bitrate, 'sample_rate': mp3File.info.sample_rate}, indent=4)
    return


@app.route('/login/')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/alt')
def login2():
    args = request.args
    session["profile"] = {"email": args["email"]}
    print(session["profile"])
    return json.dumps({'success': "True"}, indent=4)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    user = oauth.google.userinfo()
    print(user)
    return redirect('/')


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')


app.run()
