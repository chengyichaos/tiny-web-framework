import pymysql


class DBResult:
    suc = False
    result = None
    error = None
    rows = None

    def index_of(self, index):
        if self.suc and isinstance(index,
                                   int) and self.rows > index >= -self.rows:
            return self.result[index]
        return None

    def get_first(self):
        return self.index_of(0)

    def get_last(self):
        return self.index_of(-1)

    @staticmethod
    def handler(func):
        def decorator(*args, **options):
            # 实例化
            ret = DBResult()

            # 捕获异常
            try:
                # 为 DBResult 对象的 rows 和 result 成员赋值
                ret.rows, ret.result = func(*args, **options)
                # 修改执行状态为 True 表示成功
                ret.suc = True
            except Exception as e:
                # 如果捕获到异常，将异常放进 DBResult 对象的 error 属性中
                ret.error = e
            # 返回 DBResult 对象
            return ret

        # 返回 decorator 方法，其实就相当于返回 DBResult 对象
        return decorator

    def to_dict(self):
        return {
            'suc': str(self.suc),
            'result': str(self.result),
            'error': str(self.error),
            'rows': str(self.rows)
        }


# 数据库模块


class BaseDB:

    # 实例对象初始化方法
    def __init__(self,
                 user,
                 password,
                 database='',
                 host='127.0.0.1',
                 port=3306,
                 charset='utf8',
                 cursor_class=pymysql.cursors.DictCursor):
        self.user = user  # 连接用户
        self.password = password  # 连接用户密码
        self.database = database  # 选择的数据库
        self.host = host  # 主机名，默认 127.0.0.1
        self.port = port  # 端口号，默认 3306
        self.charset = charset  # 数据库编码，默认 UTF-8
        self.cursor_class = cursor_class  # 数据库游标类型，默认为 DictCursor，返回的每一行数据集都是个字典
        self.conn = self.connect()  # 数据库连接对象
        # 建立连接
        # 数据操作，增，删，改，查

    @DBResult.handler
    def process(self, func, params=None):
        # 获取数据库连接对象上下文
        with self.conn as cursor:

            # 如果参数不为空并且时 Dict 类型时，把存储过程名与参数一起传入 callproc 中调用，反之直接调用 callproc
            rows = cursor.callproc(func, params) if params and isinstance(
                params, dict) else cursor.callproc(func)

            # 获取存储过程执行结果
            result = cursor.fetchall()

        return rows, result

    @DBResult.handler
    def execute(self, sql, params=None):
        # 获取数据库连接对象上下文
        with self.conn as cursor:
            # 如果参数不为空并且时 Dict 类型时，把 SQL 语句与参数一起传入 execute 中调用，反之直接调用 exevute

            # 执行语句并获取影响条目数量
            rows = cursor.execute(
                sql, params) if params else cursor.execute(sql)
            # and isinstance(params, dict)

            # 获取执行结果
            result = cursor.fetchall()

        # 返回影响条目数量和执行结果
        return rows, result

    # def connect(self):
    #     pass

    # # 断开连接
    # def close(self):
    #     pass

    # SQL 语句执行方法
    # def execute(self, sql, params=None):
    #     pass

    # 插入数据并获取最新插入的数据标识，也就是主键索引 ID 字段
    # 插入数据并获取最新插入的数据标识，也就是主键索引 ID 字段
    def insert(self, sql, params=None):
        # 获取 SQL 语句执行之后的 DBResult 对象
        ret = self.execute(sql, params)

        # 为 DBResult 对象的 result 属性重新赋值为插入数据的 ID
        ret.result = self.conn.insert_id()

        # 返回 DBResult 对象
        return ret

        # # 存储过程调用
        # def process(self, func, params=None):
        #     pass

        # 创建数据库
        # def create_db(self, db_name, db_charset='utf8'):
        #     pass

        # # 删除数据库
        # def drop_db(self, db_name):
        #     pass

        # # 选择数据库
        # def choose_db(self, db_name):
        pass

    def connect(self):
        return pymysql.connect(host=self.host,
                               user=self.user,
                               port=self.port,
                               passwd=self.password,
                               db=self.database,
                               charset=self.charset,
                               cursorclass=self.cursor_class)
        # 断开连接

    def close(self):
        # 关闭数据库连接
        self.conn.close()
        # 创建数据库

    def create_db(self, db_name, db_charset='utf8'):
        return self.execute('CREATE DATABASE %s DEFAULT CHARACTER SET %s' %
                            (db_name, db_charset))

    # 删除数据库
    def drop_db(self, db_name):
        return self.execute('DROP DATABASE %s' % db_name)

    # 选择数据库
    @DBResult.handler
    def choose_db(self, db_name):
        # 调用 PyMySQL 的 select_db 方法选择数据库
        self.conn.select_db(db_name)

        # 因为正确执行的话没有影响条数和执行结果，所以返回两个空值 None
        return None, None
