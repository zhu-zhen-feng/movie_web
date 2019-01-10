import logging
import os
from flask import Flask
# 可以用来指定 session 保存的位置
from flask import g
from flask import render_template
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from pymysql import install_as_MySQLdb

from info import constants

install_as_MySQLdb()


class Config(object):
    """项目的配置"""

    SECRET_KEY = "iECgbYWReMNxkRprrzMo5KAQYnb2UeZ3bwvReTSt+VSESW0OB8zbglT+6rEcDW9X"

    # 为数据库添加配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/videos"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 在请求结束时候，如果指定此配置为 True ，那么 SQLAlchemy 会自动执行一次 db.session.commit()操作
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    UP_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")
    # Redis的配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # Session保存配置
    SESSION_TYPE = "redis"
    # 开启session签名
    SESSION_USE_SIGNER = True
    # 指定 Session 保存的 redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 设置需要过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2

    # 设置日志等级
    LOG_LEVEL = logging.DEBUG


# 初始化数据库


# https://www.cnblogs.com/xieqiankun/p/type_hints_in_python3.html
# redis_store = None  # type: StrictRedis


# 创建Flask对象
app = Flask(__name__)
# 加载配置
app.config.from_object(Config)
# 通过app初始化
db = SQLAlchemy(app)
# 初始化 redis 存储对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT,
                          decode_responses=True)
# 开启当前项目 CSRF 保护，只做服务器验证功能
# 帮我们做了：从cookie中取出随机值，从表单中取出随机，然后进行校验，并且响应校验结果
# 我们需要做：1. 在返回响应的时候，往cookie中添加一个csrf_token，2. 并且在表单中添加一个隐藏的csrf_token
# 而我们现在登录或者注册不是使用的表单，而是使用 ajax 请求，所以我们需要在 ajax 请求的时候带上 csrf_token 这个随机值就可以了
CSRFProtect(app)
# 设置session保存指定位置
Session(app)

from info.utils.common import user_login_data


@app.errorhandler(404)
@user_login_data
def page_not_fount(e):
    user = g.user
    data = {"user": user.to_dict() if user else None}
    return render_template('videos/404.html', data=data)


@app.after_request
def after_request(response):
    # 生成随机的csrf_token的值
    csrf_token = generate_csrf()
    # 设置一个cookie
    response.set_cookie("csrf_token", csrf_token)
    return response


# 注册蓝图
from info.modules.index import index_blu

app.register_blueprint(index_blu)
from info.modules.passport import passport_blu

app.register_blueprint(passport_blu)
from info.modules.videos import videos_blu

app.register_blueprint(videos_blu)
from info.modules.profile import profile_blu

app.register_blueprint(profile_blu)
