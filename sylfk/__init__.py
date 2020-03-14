from werkzeug.serving import run_simple
from werkzeug.wrappers import Response
from sylfk.wsgi_adapter import wsgi_app
import os
from sylfk.session import create_session_id, session
import sylfk.exceptions as exceptions
from sylfk.helper import parse_static_key
from sylfk.route import Route
from sylfk.view import View
from sylfk.template_engine import replace_template
from sylfk.session import create_session_id
import json
import sylfk.exceptions as exceptions
# 定义常见服务异常的响应体
from werkzeug.wrappers import Response
content_type = 'text/html; charset=UTF-8'
ERROR_MAP = {
    '2': Response('<h1>E2 Not Found File</h1>', content_type=content_type, status=500),
    '13': Response('<h1>E13 No Read Permission</h1>', content_type=content_type, status=500),
    '401': Response('<h1>401 Unknown Or Unsupported Method</h1>', content_type=content_type, status=401),
    '404': Response('<h1>404 Source Not Found<h1>', content_type=content_type, status=404),
    '503': Response('<h1>503 Unknown Function Type</h1>', content_type=content_type, status=503)
}

# 定义文件类型
TYPE_MAP = {
    'css': 'text/css',
    'js': 'text/js',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg'

}


def render_json(data):
  content_type = "text/plain"
  if isinstance(data, dict) or isinstance(data, list):
    data = json.dumps(data)
    content_type = "application/json"
  return Response(data, content_type="%s; charset=UTF-8" % content_type, status=200)


@exceptions.capture
def render_file(file_path, file_name=None):
  if os.path.exists(file_path):
    if not os.access(file_path, os.R_OK):
      raise exceptions.RequireReadPermissionError
    with open(file_path, 'rb') as f:
      content = f.read()
    if file_name is None:
      file_name = file_path.split("/")[-1]
      # 封装响应报头，指定为附件类型，并定义下载的文件名
    headers = {
        'Content-Disposition': 'attachment; filename="%s"' % file_name
    }
    return Response(content, headers=headers, status=200)

  raise exceptions.FileNotExistsError


class SYLFK:
   # 类属性，模版文件本地存放目录
  template_folder = None

  # 添加视图规则
  def bind_view(self, url, view_class, endpoint):
    self.add_url_rule(url, func=view_class.get_func(
        endpoint), func_type='view')

  @exceptions.capture
  def add_url_rule(self, url, func, func_type, endpoint=None, **options):
    if endpoint is None:
      endpoint = func.__name__
    if url in self.url_map:
      raise exceptions.URLExistsError
    if endpoint in self.function_map and func_type != 'static':
      raise exceptions.EndpointExistsError
    self.url_map[url] = endpoint
    self.function_map[endpoint] = ExecFunc(func, func_type, **options)

  # 实例化方法
  def __init__(self, static_folder='static', template_folder='template', session_path=".session"):
    self.host = '127.0.0.1'
    self.route = Route(self)  # 路由装饰器
    self.port = 8086
    self.url_map = {}  # 这里我们存放url和节点的映射
    self.static_map = {}  # 这里我们存放静态资源url与静态资源的映射
    self.function_map = {}  # 这里我们存放节点名和ExecFunc实例的映射
    self.static_folder = static_folder
    self.session_path = session_path
    self.template_folder = template_folder  # 模版文件本地存放路径，默认放在应用所在目录的 template 目录下
    # 为类的 template_folder 也初始化，供上面的置换模版引擎调用
    SYLFK.template_folder = self.template_folder
  # 静态资源路由

  @exceptions.capture
  def dispatch_static(self, static_path):
    if os.path.exists(static_path):
      key = parse_static_key(static_path)
      doc_type = TYPE_MAP.get(key, 'text/plain')
      with open(static_path, 'rb') as f:
        rep = f.read()
      return Response(rep, content_type=doc_type)
    else:
      # 返回 404 页面为找到对应的响应体
      raise exceptions.PageNotFoundError

  @exceptions.capture
  def dispatch_request(self, request):
    cookies = request.cookies  # 是一个字典
    # 如果 session_id 这个键不在 cookies 中，则通知客户端设置 Cookie
    if 'session_id' not in cookies:
      headers = {
          # 定义 Set-Cookie属性，通知客户端记录 Cookie，create_session_id 是生成一个无规律唯一字符串的方法
          'Set-Cookie': 'session_id=%s' % create_session_id(),
          'Server': 'Framework'   # 定义响应报头的 Server 属性
      }
    else:
      headers = {'Server': 'Framework'}
    # 去掉 URL 中 域名部分，也就从 http://xxx.com/path/file?xx=xx 中提取 path/file 这部分
    url = "/" + "/".join(request.url.split("/")[3:]).split("?")[0]
    if url.startswith('/' + self.static_folder + '/'):
      endpoint = 'static'
      url = url[1:]
    else:
      endpoint = self.url_map.get(url, None)
    headers = {'Server': 'Web 0.1'}
    if endpoint is None:
      raise exceptions.PageNotFoundError

    exec_function = self.function_map[endpoint]  # Exec实例
    if exec_function.func_type == 'route':  # 路由
      if request.method in exec_function.options.get('methods'):  # 方法支持
        argcount = exec_function.func.__code__.co_argcount
        if argcount > 0:
          rep = exec_function.func(request)

        else:
          rep = exec_function.func()   # 不需要附带请求体进行结果处理
      else:  # 未知请求方法
        raise exceptions.InvalidRequestMethodError
    elif exec_function.func_type == 'view':
      rep = exec_function.func(request)  # 所有视图处理函数都需要附带请求体
    elif exec_function.func_type == 'static':
      '''静态处理逻辑'''

      return exec_function.func(url)
    else:
      '''未知类型'''
      raise exceptions.UnknownFuncError

    status = 200
    content_type = 'text/html'
    if isinstance(rep, Response):
      return rep

    headers = {'Server': 'Framework'}
    return Response(rep, content_type='%s;charset=UTF-8' % content_type, headers=headers, status=status)

    # 控制器加载
  def load_controller(self, controller):

      # 获取控制器名字
    name = controller.__name__()

    # 遍历控制器的 `url_map` 成员
    for rule in controller.url_map:
          # 绑定 URL 与 视图对象，最后的节点名格式为 `控制器名` + "." + 定义的节点名
      self.bind_view(rule['url'], rule['view'], name + '.' + rule['endpoint'])
  # 启动入口

  def run(self, host=None, port=None, **options):
    for key, value in options.items():
      if value is not None:
        self.__setattr__(key, value)
    if host:
      self.host = host
    if port:
      self.port = port
    self.function_map['static'] = ExecFunc(
        func=self.dispatch_static, func_type='static')
    if not os.path.exists(self.session_path):
      os.mkdir(self.session_path)
    session.set_storage_path(self.session_path)
    session.load_local_session()
    run_simple(hostname=self.host, port=self.port, application=self, **options)

 # 框架被 WSGI 调用入口的方法
  def __call__(self, environ, start_response):
    return wsgi_app(self, environ, start_response)


class ExecFunc:
  def __init__(self, func, func_type, **options):
    self.func = func  # 处理函数
    self.options = options  # 附带的参数
    self.func_type = func_type  # 函数类型


# 这里我们需要绑定三个映射，第一个是绑定url与处理函数节点名，
# 第二个是绑定节点名和ExecFunc的实例，第三个我们需要绑定静态资源文件内容和静态资源url
def simple_template(path, **options):
  return replace_template(SYLFK, path, **options)
  # URL 重定向方法


def redirect(url, status_code=302):
    # 定义一个响应体
  response = Response('', status=status_code)

  # 为响应体的报头中的 Location 参数与 URL 进行绑定 ，通知客户端自动跳转
  response.headers['Location'] = url

  # 返回响应体
  return response
