from datetime import timedelta
from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import click

app = Flask(__name__)

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['JWT_SECRET_KEY'] = 'minichat'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=72)
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))  # 用户名
    password_hash = db.Column(db.String(128))  # 密码散列值

    def set_password(self, password):  # 用于设置密码
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):  # 用于验证密码
        return check_password_hash(self.password_hash, password)

    def reset_password(self, new_password):
        self.set_password(new_password)  # 设置新密码
        db.session.commit()  # 提交到数据库


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator = db.Column(db.Integer)
    avatar = db.Column(db.Integer)
    name = db.Column(db.String(20))
    desc = db.Column(db.String(300))
    whetherPublic = db.Column(db.String)


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer)
    chat = db.Column(db.Integer)
    role = db.Column(db.Integer)


@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


def replace_you_with_me(input_string):
    output_string = input_string.replace("你", "我")
    return output_string


@app.route('/')
def welcome():
    return 'Welcome to My miniChat Project!'


# 注册
@app.route('/user/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify(code=999, msg='该用户名已存在')
    elif not all([username, password]):
        """应该是不会发生的，在前端对于信息是否为空进行检验"""
        return jsonify(code=400, msg='参数不完整')
    else:
        user_new = User(username=username)
        user_new.set_password(password)
        db.session.add(user_new)
        db.session.commit()
        access_token = create_access_token(identity=username)
        return jsonify(code=201, data='Bearer ' + access_token, msg='新用户创建成功！', userid=user_new.id)


# 登录
@app.route('/user/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.validate_password(password):
        access_token = create_access_token(identity=username)
        return jsonify(code=200, data='Bearer ' + access_token, msg='登录成功！', userid=user.id)
    else:
        return jsonify(code=999, msg='用户名或密码错误')


# 重置密码
@app.route('/user/reset', methods=['POST'])
@jwt_required()
def reset_password():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    if user:
        new_password = request.form['password']
        user.reset_password(new_password)
        return jsonify(code=200, msg='密码重置成功')
    else:
        return jsonify(code=404, msg='用户不存在')


@app.route("/session", methods=["GET"])
@jwt_required()
def check_session():
    current_user = get_jwt_identity()
    return jsonify(current_user)


# 创建机器人
@app.route("/create", methods=["POST"])
@jwt_required()
def create_robot():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    avatar = request.form['avatar']
    name = request.form['name']
    desc = request.form['desc']
    desc = replace_you_with_me(desc)
    whetherpublic = request.form['whetherPublic']
    robot_new = Chat(creator=user.id, avatar=avatar, name=name, desc=desc, whetherPublic=whetherpublic)
    db.session.add(robot_new)
    db.session.commit()
    robot_id = robot_new.id
    link_new = Link(user=user.id, chat=robot_id, role=0)
    db.session.add(link_new)
    db.session.commit()
    return jsonify(code=201, msg='机器人创建成功')


# 获取拥有的机器人
@app.route("/user/getrobots", methods=["GET"])
@jwt_required()
def get_robots():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    links = Link.query.filter_by(user=user.id).all()
    robots = []
    for link in links:
        robot = Chat.query.filter_by(id=link.chat).first()
        robot_data = {
            'id': robot.id,
            'name': robot.name,
            'desc': robot.desc,
            'avatar': robot.avatar,
            'whetherPublic': robot.whetherPublic
        }
        robots.append(robot_data)

    return jsonify(code=200, data=robots, msg='启用的机器人获取成功')


# 获取公共机器人
@app.route("/getpublic", methods=["GET"])
@jwt_required()
def get_public():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    links = Link.query.filter_by(user=user.id, role=1).all()
    robot_ids = []
    for link in links:
        robot_ids.append(link.chat)
    robots = []
    robotlist = Chat.query.filter_by(whetherPublic=1).all()
    for robot in robotlist:
        if user.id != robot.creator:
            if robot.id in robot_ids:
                robot_data = {
                    'id': robot.id,
                    'name': robot.name,
                    'desc': robot.desc,
                    'avatar': robot.avatar,
                    'whetherPublic': 1
                }
            else:
                robot_data = {
                    'id': robot.id,
                    'name': robot.name,
                    'desc': robot.desc,
                    'avatar': robot.avatar,
                    'whetherPublic': 0
                }
            robots.append(robot_data)

    return jsonify(code=200, data=robots, msg='获取公共的机器人获取成功')


# 添加机器人
@app.route("/add/<int:robot>", methods=["POST"])
@jwt_required()
def add_public(robot):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    link_new = Link(user=user.id, chat=robot, role=1)
    db.session.add(link_new)
    db.session.commit()
    return jsonify(code=201, msg='添加机器人成功！')


@app.route("/delete/<int:robot>", methods=["DELETE"])
@jwt_required()
def delete_link(robot):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    link_to_delete = Link.query.filter_by(chat=robot, user=user.id).first()
    if link_to_delete:
        db.session.delete(link_to_delete)
        db.session.commit()
        return jsonify(code=200, msg='机器人删除成功')
    else:
        return jsonify(code=404, msg='机器人未找到或无权限删除')


@app.route("/search/<search_term>", methods=["GET"])
@jwt_required()
def search(search_term):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    links = Link.query.filter_by(user=user.id, role=1).all()
    robot_ids = []
    for link in links:
        robot_ids.append(link.chat)
    robots = []
    robotlist = Chat.query.filter(Chat.whetherPublic == 1, Chat.name.like(f'%{search_term}%')).all()
    for robot in robotlist:
        if user.id != robot.creator:
            if robot.id in robot_ids:
                robot_data = {
                    'id': robot.id,
                    'name': robot.name,
                    'desc': robot.desc,
                    'avatar': robot.avatar,
                    'whetherPublic': 1
                }
            else:
                robot_data = {
                    'id': robot.id,
                    'name': robot.name,
                    'desc': robot.desc,
                    'avatar': robot.avatar,
                    'whetherPublic': 0
                }
            robots.append(robot_data)

    return jsonify(code=200, data=robots, msg='获取公共的机器人获取成功')


if __name__ == '__main__':
    app.run(debug=True)
