from flask import Flask, request, jsonify, session

app = Flask(__name__)


@app.route('/')
def welcome():
    return 'Welcome to My miniChat Project!'


@app.route('/user/register', methods=['POST'])
def register():
    return 'register'


@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    return 'Welcome to My Watchlist!'


if __name__ == '__main__':
    app.run(debug=False)
