from queue import Queue

import jinja2
import aiohttp_jinja2
from aiohttp import web

import settings
from utils import Nginx

LOG_QUEUE = Queue()


@aiohttp_jinja2.template("index.html")
async def index(request):
    domains = settings.DOMAINS
    return {"domains": domains}


async def deploy(request):
    global LOG_QUEUE
    if request.method == "POST":
        data = await request.multipart()
        field = await data.next()
        # 处理FROM表单不同列的数据
        domain = ""
        upload_file = ""
        servers = list()
        while field:
            name = field.name
            if name != "filename":
                value = await field.read(decode=True)
                if name == "domain":
                    domain = value.decode("utf8")
                else:
                    servers.append(value.decode("utf8"))
            else:
                filename = field.filename
                LOG_QUEUE.put("开始处理上传的文件")
                # 防止OOM，通过流方式将用户上传的文件写入本地目录
                size = 0
                with open(filename, 'wb') as f:
                    while True:
                        # 8192 bytes by default.
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        size += len(chunk)
                        f.write(chunk)
                upload_file = filename
            # 读取下一个field，直到为None
            field = await data.next()
        gateway_type = settings.DOMAINS.get(domain, {}).get("gateway")
        all_servers = settings.DOMAINS.get(domain, {}).get("servers")
        if len(servers) >= len(all_servers):
            return web.Response(status=200, text="不能一次性全部更新，将会导致服务不可用")
        # 后端条件检查
        if not upload_file:
            return web.Response(status=200, text="未检测到更新文件，请上传更新文件")
        if gateway_type == "nginx":
            task = Nginx(settings.GATEWAY.get(gateway_type), servers, domain, upload_file, LOG_QUEUE)
            task.start()
        elif gateway_type == "slb":
            print("网关类型为阿里云SLB")
            aes_key = settings.GATEWAY.get('slb').get("aes_key")
            aes_secret = settings.GATEWAY.get('slb').get("aes_secret")
            region = settings.GATEWAY.get('slb').get("region")
            pass
        else:
            return web.Response(status=500, text="未实现的网关类型，请联系管理员")
    return web.Response(status=200, text="ok")


if __name__ == '__main__':
    app = web.Application()
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader("templates")
    )
    app.add_routes([
        web.get("/", index),
        web.get("/deploy/log", deploy),
        web.post("/deploy", deploy),
    ])
    web.run_app(app, port=8080)
