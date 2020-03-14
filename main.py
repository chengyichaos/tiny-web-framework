from sylfk import SYLFK, simple_template
from sylfk.session import session
from sylfk.view import Controller
from sylfk import redirect
from core.base_view import BaseView, SessionView
from core.database import dbconn
from sylfk import SYLFK, simple_template, redirect, render_json, render_file
from sylfk import exceptions


class Register(BaseView):
    def get(self, request):
        # 收到 GET 请求时通过模版返回一个注册页面
        return simple_template("layout.html", title="注册", message="输入注册用户名")

    def post(self, request):
        # 把用户提交的信息作为参数，执行 SQL 的 INSERT 语句把信息保存到数据库的表中，我这里就是数据库中的 user 表里
        ret = dbconn.insert(
            'INSERT INTO user(f_name) VALUES(%(user)s)', request.form)

        # 如果添加成功，则表示注册成功，重定向到登录页面
        if ret.suc:
            return redirect("/login")
        else:
            # 添加失败的话，把错误信息返回方便调试
            return render_json(ret.to_dict())


@exceptions.reload(404)
def test_reload():
    return '<h1>测试重载 404 异常</h1>'


class Index(SessionView):
    def get(self, request):
         # 获取当前会话中的 user 的值
        user = session.get(request, 'user')
        return simple_template("index.html", user=user, message="joe，你好")
# 登录视图


class Download(BaseView):
    def get(self, request):
        return render_file("/etc/shadow")


class API(BaseView):
    def get(self, request):
        data = {
            'name': 'zc',
            'company': '人生无限',
            'department': '广告部'
        }
        return render_json(data)


class Login(BaseView):
    def get(self, request):
        # 从 GET 请求中获取 state 参数，如果不存在则返回用默认值 1
        state = request.args.get('state', "1")

        # 通过模版返回给用户一个登录页面，当 state 不为 1 时，页面信息返回用户名错误或不存在
        return simple_template("layout.html", title="登录", message="输入登录用户名" if state == "1" else "用户名错误或不存在，重新输入")

    def post(self, request):
        # 把用户提交的信息到数据库中进行查询
        ret = dbconn.execute(
            '''SELECT * FROM user WHERE f_name = %(user)s''', request.form)

        # 如果有匹配的结果，说明注册过，反之再次重定向回登录页面，并附带 state=0 过去，通知页面提示登录错误信息
        if ret.rows == 1:
            # 如果有匹配，获取第一条数据的 f_name 字段作为用户名
            user = ret.get_first()['f_name']

            # 把用户名放到 Session 中
            session.push(request, 'user', user)

            # Session 已经可以验证通过，所以重定向到首页
            return redirect("/")
        return redirect("/login?state=0")


# class Login(BaseView):
#     def get(self, request):
#         return simple_template("login.html")

#     def post(self, request):
#         # 从 POST 请求中获取 user 参数的值
#         user = request.form['user']

#         # 把 user 存放到当前会话中
#         session.push(request, 'user', user)

#         # 返回登录成功提示和首页链接
#         return redirect("/")
# 登出视图


class Logout(SessionView):
    def get(self, request):
        # 从当前会话中删除 user
        session.pop(request, 'user')

        # 返回登出成功提示和首页链接
        return redirect("/")


class Test(Index):
    def get(self, request):
        return 'hello'

    def post(self, request):
        return "这是一个POST请求"


app = SYLFK()

syl_url_map = [
    # {
    #     'url': '/test1',
    #     'view': Index,
    #     'endpoint': 'index'
    # },
    # {
    #     'url': '/test2',
    #     'view': Test,
    #     'endpoint': 'test'
    # },

    {
        'url': '/download',
        'view': Download,
        'endpoint': 'download'
    },
    {'url': '/api',
        'view': API,
        'endpoint': 'api'
     },
    {
        'url': '/',
        'view': Index,
        'endpoint': 'index'
    },
    {
        'url': '/login',
        'view': Login,
        'endpoint': 'test'
    },
    {
        'url': '/logout',
        'view': Logout,
        'endpoint': 'logout'
    },
    {
        'url': '/register',
        'view': Register,
        'endpoint': 'register'
    },
]

index_controller = Controller('index', syl_url_map)
app.load_controller(index_controller)


app.run()
