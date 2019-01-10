import time
from datetime import datetime, timedelta
import os
import uuid
from flask import g
from flask import redirect, jsonify
from flask import render_template
from flask import request
from werkzeug.utils import secure_filename
from info.models import Videos, Subject, User
from info.modules.profile import profile_blu
from info.utils.common import user_login_data
from info.utils.img_storage import storage
from info.utils.response_code import RET
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask import current_app, flash, url_for
from info import constants, Config, db

tags = Subject.query.all()


class MovieForm(FlaskForm):
    """
    电影表单
    """
    subject_id = SelectField(
        label="分类 ：",
        validators=[
            DataRequired("请选择分类！")
        ],
        coerce=int,
        choices=[(v.id, v.name) for v in tags],
        description="分类",
        render_kw={
            "class": "sel_opt",
            "id": "input_tag_id"
        }
    )
    title = StringField(
        label="简介 ：",
        validators=[
            DataRequired("请输入简介！")
        ],
        description="简介",
        render_kw={
            "class": "input_txt2",
            "id": "input_title",
            "placeholder": "请输入简介！"
        }
    )
    img = FileField(
        label="封面图片 ：",
        validators=[
            DataRequired("请上传封面图片！")
        ],
        description="图片",
    )
    url = FileField(
        label="视频 ：",
        validators=[
            DataRequired("请上传视频！")
        ],
        description="视频",
    )
    submit = SubmitField(
        label="编辑",
        render_kw={
            "class": "input_sub input_sub2",
        }
    )


def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


@profile_blu.route('/video_list')
@user_login_data
def user_video_list():
    # 获取参数
    page = request.args.get("p", 1)

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    user = g.user
    video_list = []
    current_page = 1
    total_page = 1
    try:
        paginate = Videos.query.paginate(page, constants.USER_COLLECTION_MAX_NEWS,
                                         False)
        video_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    video_dict_li = []
    for video in video_list:
        video_dict_li.append(video.to_dict())

    data = {
        "video_dict": video_dict_li,
        "total_page": total_page,
        "current_page": current_page,
    }

    return render_template('videos/user_video_list.html', data=data)


@profile_blu.route('/collection')
@user_login_data
def user_collection():
    # 获取参数
    page = request.args.get("p", 1)

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 查询用户指定页数的收藏的视频
    user = g.user

    video_list = []
    total_page = 1
    current_page = 1
    try:
        paginate = user.collection_videos.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        current_page = paginate.page
        total_page = paginate.pages
        video_list = paginate.items
    except Exception as e:
        current_app.logger.error(e)

    video_dict_li = []
    for video in video_list:
        video_dict_li.append(video.to_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collections": video_dict_li
    }

    return render_template('videos/user_collection.html', data=data)


@profile_blu.route('/pass_info', methods=["GET", "POST"])
@user_login_data
def pass_info():
    if request.method == "GET":
        return render_template('videos/user_pass_info.html')

    # 1. 获取参数
    old_password = request.json.get("old_password")
    news_password = request.json.get("new_password")

    # 2. 校验参数
    if not all([old_password, news_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 判断旧密码是否正确
    user = g.user
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="原密码错误")

    # 4. 设置新密码
    user.password = news_password

    return jsonify(errno=RET.OK, errmsg="保存成功")


@profile_blu.route('/info')
@user_login_data
def user_info():
    user = g.user
    if not user:
        # 代表没有登录，重定向到首页
        return redirect("/")
    data = {"user": user.to_dict()}
    return render_template('videos/user.html', data=data)


@profile_blu.route('/video_release', methods=["get", "post"])
@user_login_data
def video_add():
    form = MovieForm()
    if request.method == "GET":
        return render_template("videos/user_video_release.html", form=form)
    data = form.data
    file_url = secure_filename(form.url.data.filename)
    if not os.path.exists(Config.UP_DIR):
        os.makedirs(Config.UP_DIR)
        # os.chmod(Config.UP_DIR, os.stat.S_IRWXU)
    url = change_filename(file_url)
    form.url.data.save(Config.UP_DIR + url)
    img_url = change_filename(form.img.data.filename)
    with open(Config.UP_DIR+img_url, 'wb') as f:
        f.write(form.img.data.read())
    movie = Videos()
    movie.img_url = img_url,
    movie.intro = data["title"],
    movie.url = url,
    movie.clicks = 0,
    movie.subject_id = int(data["subject_id"])
    try:
        db.session.add(movie)
    except Exception as e:
        flash("添加视频失败！", "error")
        db.session.rollback()
    db.session.commit()
    return redirect(url_for('profile.video_add'))


@profile_blu.route('/video_type', methods=["GET", "POST"])
def video_type():
    if request.method == "GET":
        # 查询分类数据
        try:
            categories = Subject.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('videos/video_type.html', errmsg="查询数据错误")

        category_dict_li = []
        for category in categories:
            # 取到分类的字典
            cate_dict = category.to_dict()
            category_dict_li.append(cate_dict)

        data = {
            "categories": category_dict_li
        }

        return render_template('videos/video_type.html', data=data)

    # 新增或者添加分类
    # 1. 取参数
    cname = request.json.get("name")
    # 如果传了cid，代表是编辑已存在的分类
    cid = request.json.get("id")

    if not cname:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if cid:
        # 有 分类 id 代表查询相关数据
        try:
            cid = int(cid)
            category = Subject.query.get(cid)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        if not category:
            return jsonify(errno=RET.NODATA, errmsg="未查询到分类数据")
        category.name = cname
    else:
        category = Subject()
        category.name = cname
        # TODO 添加cid
        db.session.add(category)

    return jsonify(errno=RET.OK, errmsg="OK")


@profile_blu.route('/user_count')
def user_count():
    # 总人数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 月新增数
    mon_count = 0
    t = time.localtime()
    begin_mon_date_str = '%d-%02d-01' % (t.tm_year, t.tm_mon)
    # 将字符串转成datetime对象
    begin_mon_date = datetime.strptime(begin_mon_date_str, "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > begin_mon_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日新增数
    day_count = 0
    begin_day_date = datetime.strptime(('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday)), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > begin_day_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 拆线图数据

    active_time = []
    active_count = []

    # 取到今天的时间字符串
    today_date_str = ('%d-%02d-%02d' % (t.tm_year, t.tm_mon, t.tm_mday))
    # 转成时间对象
    today_date = datetime.strptime(today_date_str, "%Y-%m-%d")

    for i in range(0, 31):
        # 取到某一天的0点0分
        begin_date = today_date - timedelta(days=i)
        # 取到下一天的0点0分
        end_date = today_date - timedelta(days=(i - 1))
        count = User.query.filter(User.is_admin == False, User.update_time >= begin_date,
                                  User.update_time < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime('%Y-%m-%d'))

    # User.query.filter(User.is_admin == False, User.last_login >= 今天0点0分, User.last_login < 今天24点).count()

    # 反转，让最近的一天显示在最后
    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }

    return render_template('videos/user_count.html', data=data)
