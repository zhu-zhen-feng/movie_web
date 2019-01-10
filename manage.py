from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import db, models, app
from info.models import User

manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.option('-n', '-name', dest="name")
@manager.option('-p', '-password', dest="password")
def superuser(name, password):

    if not all([name, password]):
        print("参数不足")

    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)

    print("添加成功")
# python manage.py superuser -n admin -p 12345678


if __name__ == '__main__':
    manager.run()

