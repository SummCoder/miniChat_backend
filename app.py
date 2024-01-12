from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click

app = Flask(__name__)
app.secret_key = 'miniChat'
WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))


@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


users = {
    'user1': 'password1',
    'user2': 'password2'
}


@app.route('/')
def welcome():
    return 'Welcome to My miniChat Project!'


@app.route('/user/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username in users:
        return jsonify(code=999, msg='该用户名已存在')
    elif not all([username, password]):
        """应该是不会发生的，在前端对于信息是否为空进行检验"""
        return jsonify(code=400, msg='参数不完整')
    else:
        return jsonify(code=201, msg='新用户创建成功！')


@app.route('/user/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username in users and users[username] == password:
        session['username'] = username
        return jsonify(code=200, msg='登录成功！')
    else:
        return jsonify({'message': 'Invalid username or password'})


@app.route("/user/logout")
def logout():
    # 删除 Session 中保存的用户名
    session.pop("username", None)


@app.route("/session", methods=["GET"])
def check_session():

    """登录校验"""
    username = session.get("username")
    if username:
        return jsonify(msg=username)
    else:
        return jsonify(msg="登录校验未通过")


if __name__ == '__main__':
    app.run(debug=False)
