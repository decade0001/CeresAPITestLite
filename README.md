# CeresAPITestLite

一个轻量级、通用的接口自动化测试工具。项目定位不是某个系统的专用脚本，而是面向 Web/API 项目的通用测试运行器：通过外部 JSON 文件维护测试用例，批量执行接口请求，完成断言校验、变量提取、报告生成，并支持 Docker 镜像运行和 GitHub Actions 持续集成。

## 技术栈

- Python 3.11
- Requests：发送 HTTP 请求
- Jinja2：生成 HTML 测试报告
- JSON：维护测试套件和用例数据
- Docker：打包镜像，支持免本机 Python 环境运行
- GitHub Actions：提交代码后自动执行接口测试并上传报告产物

> 如果本地没有安装 Requests/Jinja2，运行器会自动回退到 Python 标准库请求和内置 HTML 模板，方便在干净环境中演示。

## 功能

- 支持 GET / POST / PUT / DELETE 请求
- 支持 Base URL、Query 参数、JSON 请求体、Header、Token 等配置
- 支持 `${变量名}` 形式的变量替换
- 支持从 JSON 响应中提取字段并复用到后续用例
- 支持状态码、响应时间、响应文本、JSON 字段存在、JSON 字段值等断言
- 自动生成 HTML 测试报告和 JSON 摘要
- 提供 `mock_server.py`，无需真实后端即可演示完整流程
- 提供 `Dockerfile` 和 GitHub Actions 工作流示例
- 保留 `cases/cereshop_cases.json`，用于展示如何把通用工具接入具体商城项目

## 目录结构

```text
CeresAPITestLite/
  run_tests.py                  # 兼容 CLI / 导入门面
  ceres_api_test_lite/          # 可维护的核心模块
    config.py                   # JSON 用例与报告读写
    context.py                  # 变量替换与 JSON 点路径取值
    transport.py                # HTTP 请求与响应归一化
    extractors.py               # 跨用例变量提取
    assertions.py               # 内置/自定义断言注册表
    runner.py                   # 测试套编排与汇总
    reporting.py                # HTML/JSON 报告
    cli.py                      # 命令行参数入口
  mock_server.py                # 本地模拟 API 服务
  requirements.txt              # Requests / Jinja2 依赖
  templates/
    report.html.j2              # Jinja2 HTML 报告模板
  cases/
    demo_cases.json             # 通用演示用例
    cereshop_cases.json         # CERESHOP 项目接口用例模板
  reports/                      # 运行后生成报告，默认不提交
  Dockerfile
  .github/workflows/api-test.yml
```

## 快速开始

安装依赖：

```bash
pip install -r requirements.txt
```

启动本地 mock 服务：

```bash
python mock_server.py
```

打开另一个终端执行用例：

```bash
python run_tests.py --case cases/demo_cases.json --report-dir reports
```

运行结束后查看 `reports/` 目录中的 HTML 报告。

## Docker 运行

构建镜像：

```bash
docker build -t ceres-api-test-lite .
```

运行默认演示用例：

```bash
docker run --rm -v ${PWD}/reports:/app/reports ceres-api-test-lite
```

如果需要指定自己的用例文件，可以挂载 `cases/` 和 `reports/` 目录：

```bash
docker run --rm ^
  -v %cd%/cases:/app/cases ^
  -v %cd%/reports:/app/reports ^
  ceres-api-test-lite python run_tests.py --case cases/demo_cases.json --report-dir reports
```

## 用例格式

```json
{
  "name": "Demo API smoke test",
  "base_url": "http://127.0.0.1:19007",
  "variables": {
    "phone": "13800138000",
    "password": "123456"
  },
  "global_headers": {
    "Accept": "application/json"
  },
  "cases": [
    {
      "name": "login and extract token",
      "method": "POST",
      "path": "/auth/login",
      "json": {
        "phone": "${phone}",
        "password": "${password}"
      },
      "extract": {
        "token": "data.token"
      },
      "assertions": [
        {"type": "status_code", "equals": 200},
        {"type": "json_field_not_empty", "path": "data.token"}
      ]
    }
  ]
}
```

## 支持的断言

| 类型 | 说明 |
| --- | --- |
| `status_code` | 校验 HTTP 状态码 |
| `response_time_less_than` | 校验接口响应时间 |
| `contains` | 校验响应文本包含指定内容 |
| `json_field_exists` | 校验 JSON 字段存在 |
| `json_field_equals` | 校验 JSON 字段值等于预期值 |
| `json_field_not_empty` | 校验 JSON 字段非空 |

## 接入真实项目

把真实项目的接口整理成 JSON 用例后，通过 `--base-url` 指定环境地址即可：

```bash
python run_tests.py --case cases/your_project_cases.json --base-url http://127.0.0.1:8080 --report-dir reports
```

`cases/cereshop_cases.json` 是一个接入商城系统的示例模板，覆盖登录、商品查询、店铺查询、购物车、订单等接口。实际使用时需要根据本地环境调整账号、密码、Token 字段路径、商品 ID 和期望返回值。

## 简历描述参考

可描述为：

> 设计并实现轻量级接口自动化测试工具，技术栈为 Python + Requests + Jinja2 + Docker + GitHub Actions。工具支持 JSON 用例管理、GET/POST/PUT/DELETE 请求、Header/Token 配置、变量提取与复用、状态码/响应字段/响应时间断言，并自动生成 HTML/JSON 测试报告；编写 Dockerfile 将项目打包为镜像，实现免本机 Python 环境的一键运行；配置 GitHub Actions 在代码提交后自动执行测试并上传报告产物，可作为通用接口回归测试工具接入不同 Web/API 项目。
