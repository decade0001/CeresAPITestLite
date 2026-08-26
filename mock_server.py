#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mock_server.py —— 本地模拟 API 服务器

【这个文件是干什么的？】
它是 CeresAPITestLite 的“陪练”。run_tests.py 是测试运行器，需要有人提供接口给它测。
但真实后端（比如一个商城系统）可能还没开发好、或者不方便启动，怎么办？
答案就是：用这个文件在本地起一个“假”的 HTTP 服务，假装自己是个后端，
收到请求后返回一些写死的假数据，让 run_tests.py 可以把整个测试流程跑通。

【和 run_tests.py 的关系】
- mock_server.py 负责提供接口（被测对象），监听地址是 http://127.0.0.1:19007
- run_tests.py 负责对这些接口发请求、做断言、出报告（测试方）
两者一个当“服务器”，一个当“客户端”，配合起来就能演示完整的接口自动化测试。

【为什么只用标准库？】
这个文件故意不依赖 requests 等第三方库，只用 Python 自带的 http.server，
这样在任何装了 Python 的电脑上都能直接 `python mock_server.py` 启动，零门槛演示。
"""

# json：标准库，用来把 Python 字典转成 JSON 字符串（接口返回的数据格式通常是 JSON）
import json
# BaseHTTPRequestHandler：处理单个 HTTP 请求的基类，我们继承它来定义“收到请求后怎么响应”
# HTTPServer：一个简单的 HTTP 服务器，负责监听端口、把请求分发给 Handler 处理
from http.server import BaseHTTPRequestHandler, HTTPServer
# parse_qs：把 URL 里的查询字符串（如 ?productId=1001&page=2）解析成字典
# urlparse：把一整条 URL 拆分成路径、查询参数等部分
from urllib.parse import parse_qs, urlparse


class MockHandler(BaseHTTPRequestHandler):
    """
    模拟请求处理器：每收到一个 HTTP 请求，就会创建一个 MockHandler 实例来处理它。

    我们继承 BaseHTTPRequestHandler 后，主要做两件事：
    1. 重写 do_GET / do_POST 等方法，定义“收到 GET/POST 请求时该怎么回复”；
    2. 写几个自己的辅助方法（send_json / read_json），让发 JSON、读 JSON 更方便。

    因为是“模拟”服务器，所以这里的响应数据都是写死的假数据，不连数据库。
    """

    # server_version 会在响应头里显示，标识服务器版本，纯粹是展示用
    server_version = "APIMock/1.0"

    def send_json(self, status, body):
        """
        统一的“发送 JSON 响应”辅助方法。

        不管哪个接口，回复给客户端的格式都是：HTTP 状态码 + JSON 正文。
        这个方法把这三步打包到一起，避免在每个接口里重复写一堆发头、发正文的代码。

        参数：
            status: HTTP 状态码，比如 200（成功）、404（找不到）、401（未登录）
            body:   要返回的 Python 字典，会被转成 JSON 字符串发给客户端
        """
        # 1) 先把 Python 字典序列化成 JSON 字符串，再编码成字节（网络传输的是字节）
        #    ensure_ascii=False 让中文不被转成 \uXXXX，方便人眼阅读
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        # 2) send_response 写状态行（如 "HTTP/1.0 200 OK"）
        self.send_response(status)
        # 3) 依次写响应头：告诉客户端“正文是 JSON、且是 UTF-8 编码”
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # Content-Length 很重要：客户端靠它知道正文有多少字节，读完就停，不会一直卡住等待
        self.send_header("Content-Length", str(len(data)))
        # 4) end_headers 表示“响应头写完了，接下来是正文”
        self.end_headers()
        # 5) 把正文字节写进输出流，真正发给客户端
        self.wfile.write(data)

    def read_json(self):
        """
        读取客户端发来的请求体（POST 请求通常带 JSON 正文）。

        比如 run_tests.py 登录时会 POST 一段 {"phone":"...","password":"..."}，
        服务端需要把这些数据读出来，才能判断账号对不对（虽然是模拟的）。

        返回：解析出的 Python 字典；如果没正文或不是合法 JSON，就返回空字典 {}。
        """
        # 从请求头里拿到 Content-Length（正文长度），没有就当 0
        # 这里用 `or "0"` 是防止拿到空字符串导致 int() 报错
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            # 没有正文，直接返回空字典
            return {}
        # 按 length 从输入流里读取这么多字节，再解码成字符串
        raw = self.rfile.read(length).decode("utf-8")
        try:
            # 尝试把字符串解析成 Python 字典
            return json.loads(raw)
        except Exception:
            # 如果客户端发的不是合法 JSON，也不报错，优雅地返回空字典
            return {}

    def do_GET(self):
        """
        处理所有 GET 请求。

        GET 请求一般用来“查”数据（查商品、查店铺、查购物车等）。
        我们根据请求的路径（path）来决定返回什么假数据：
        - /products 或 /product/getProducts  -> 商品列表
        - /products/detail 或 /product/getById -> 商品详情
        - /shop/getShops                       -> 店铺列表
        - /cart 或 /cart/getCart               -> 购物车（需要带 token，否则返回 401）
        - /order/getAll                        -> 订单列表
        - 其它路径                              -> 404 not found

        这种“看路径分发”的写法，和真实后端框架（如 Flask 的路由）思路是一样的。
        """
        # urlparse 把 self.path（如 "/products/detail?productId=1001"）拆成结构化对象
        parsed = urlparse(self.path)
        # parse_qs 把查询字符串 "?productId=1001" 解析成 {"productId": ["1001"]}
        # 注意：值是列表，因为同一个参数可能出现多次
        query = parse_qs(parsed.query)

        # —— 商品列表接口 ——
        # in (...) 表示这几个路径都走同一个分支，兼容不同风格的接口名
        if parsed.path in ("/products", "/product/getProducts"):
            # 返回 200，并给一个写死的商品列表（2 件商品）
            self.send_json(
                200,
                {
                    "code": 200,           # 业务状态码：200 表示业务成功（和 HTTP 状态码含义不同）
                    "message": "success",
                    "data": {              # data 里放真正的业务数据
                        "total": 2,        # 一共 2 件
                        "list": [          # list 是商品数组
                            {"productId": 1001, "name": "demo product", "price": 99},
                            {"productId": 1002, "name": "sample product", "price": 199},
                        ],
                    },
                },
            )
        # —— 商品详情接口 ——
        # 根据查询参数 productId 返回单个商品信息
        elif parsed.path in ("/products/detail", "/product/getById"):
            # query.get("productId", ["1001"])：如果没传 productId，就默认用 "1001"
            # [0] 是因为 parse_qs 的值是列表，取第一个
            product_id = query.get("productId", ["1001"])[0]
            self.send_json(
                200,
                {
                    "code": 200,
                    "message": "success",
                    # 注意：这里把客户端传来的 product_id 原样回显，方便测试“传什么查到什么”
                    "data": {"productId": product_id, "name": "demo product", "price": 99},
                },
            )
        # —— 店铺列表接口 ——
        elif parsed.path == "/shop/getShops":
            self.send_json(200, {"code": 200, "message": "success", "data": {"list": [{"shopId": 1, "shopName": "demo shop"}]}})
        # —— 购物车接口（需要登录） ——
        # 这里演示了“鉴权”：购物车是私密数据，必须带 token 才能查
        elif parsed.path in ("/cart", "/cart/getCart"):
            # 检查请求头里有没有 Authorization（也就是 token）
            if not self.headers.get("Authorization"):
                # 没带 token -> 返回 401 未授权
                self.send_json(401, {"code": 401, "message": "missing token"})
            else:
                # 带了 token -> 返回空购物车（模拟数据）
                self.send_json(200, {"code": 200, "message": "success", "data": {"items": []}})
        # —— 订单列表接口 ——
        elif parsed.path == "/order/getAll":
            self.send_json(200, {"code": 200, "message": "success", "data": {"total": 0, "list": []}})
        # —— 兜底：没匹配上的路径，一律返回 404 ——
        else:
            self.send_json(404, {"code": 404, "message": "not found"})

    def do_POST(self):
        """
        处理所有 POST 请求。

        POST 请求一般用来“提交”数据（登录、下单、新增等）。
        这里只演示了登录接口：收到账号密码后，返回一个假的 token。

        真实项目里 token 是服务端校验账号密码后生成的，这里为了演示直接写死返回。
        """
        parsed = urlparse(self.path)
        # 用前面定义的 read_json 把请求体读出来（登录请求体里有 phone、password）
        body = self.read_json()
        # —— 登录接口 ——
        # 兼容 /auth/login 和 /app/login 两种路径
        if parsed.path in ("/auth/login", "/app/login"):
            # 只要 phone 和 password 都不为空，就认为登录成功
            # （真实项目里要查数据库比对密码，这里只是模拟，不做真实校验）
            if body.get("phone") and body.get("password"):
                # 登录成功 -> 返回一个写死的 token，run_tests.py 会把它提取出来给后续接口用
                self.send_json(200, {"code": 200, "message": "success", "data": {"token": "mock-token-123", "userId": 1}})
            else:
                # 账号或密码缺失 -> 返回 400（客户端请求有误）
                self.send_json(400, {"code": 400, "message": "phone/password required"})
        else:
            # 未知 POST 路径 -> 404
            self.send_json(404, {"code": 404, "message": "not found"})

    def log_message(self, fmt, *args):
        """
        自定义日志输出。

        BaseHTTPRequestHandler 默认会把每个请求打到 stderr（标准错误流），
        格式比较啰嗦。这里重写成更简洁的一行，打印“谁访问了什么”，方便调试时看到请求。
        """
        # address_string() 是客户端地址；fmt % args 是默认的日志内容
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    """
    程序入口：创建服务器并启动。

    当你执行 `python mock_server.py` 时，就会走到这里。
    服务器启动后会一直运行（serve_forever），直到你按 Ctrl+C 停止它。
    """
    # 创建一个 HTTP 服务器：
    #   ("127.0.0.1", 19007) 表示监听本机的 19007 端口（只本机能访问，外网访问不到，安全）
    #   MockHandler 表示用我们写的处理器来处理请求
    server = HTTPServer(("127.0.0.1", 19007), MockHandler)
    # 打印一行提示，告诉用户服务地址（run_tests.py 里 base_url 要和这里对应）
    print("mock server listening: http://127.0.0.1:19007")
    # 开始无限循环地等待并处理请求，直到进程被结束
    server.serve_forever()


# 这是 Python 的惯用写法：只有直接运行本文件时才执行 main()
# 如果本文件被别的文件 import，就不会自动启动服务器，避免副作用
if __name__ == "__main__":
    main()
