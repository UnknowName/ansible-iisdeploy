import asyncio
import logging
from queue import Queue, Empty

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


@aiohttp_jinja2.template("show_log.html")
async def deploy(request):
    global LOG_QUEUE
    if request.method == "POST":
        data = await request.multipart()
        field = await data.next()
        # 处理FROM表单不同列的数据
        domain = ""
        upload_file = "update.zip"
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
                if not filename:
                    return web.Response(status=200, text="未检测到更新文件，请上传更新文件")
                LOG_QUEUE.put("开始处理上传的文件")
                # 防止OOM，通过流方式将用户上传的文件写入本地目录
                size = 0
                with open(upload_file, 'wb') as f:
                    while True:
                        # 8192 bytes by default.
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        size += len(chunk)
                        f.write(chunk)
            # 读取下一个field，直到为None
            field = await data.next()
        gateway_type = settings.DOMAINS.get(domain, {}).get("gateway")
        all_servers = settings.DOMAINS.get(domain, {}).get("servers")
        LOG_QUEUE.put("本次部署的站点为{},更新的服务器为{}".format(domain, servers))
        if len(servers) >= len(all_servers):
            return web.Response(status=200, text="不能一次性全部更新，将会导致服务不可用")
        # 后端条件检查
        if gateway_type == "nginx":
            task = Nginx(settings.GATEWAY.get(gateway_type), servers, domain, upload_file, LOG_QUEUE)
            task.start()
            return {"message": "成功加入执行队列"}
        elif gateway_type == "slb":
            print("网关类型为阿里云SLB")
            aes_key = settings.GATEWAY.get('slb').get("aes_key")
            aes_secret = settings.GATEWAY.get('slb').get("aes_secret")
            region = settings.GATEWAY.get('slb').get("region")
            return {"message": "成功加入执行队列"}
        else:
            return web.Response(status=500, text="未实现的网关类型，请联系管理员")
    return web.Response(status=200, text="ok")


async def show_log(request):
    global LOG_QUEUE
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    info = ""
    while info != "EOF":
        await asyncio.sleep(0.5)
        await ws.send_str(info)
        try:
            info = LOG_QUEUE.get(timeout=60)
        except Empty:
            await ws.send_str("<span style='color:red'>任务执行超时,很可能已失败，请联系管理员进一步查看详细日志信息</span>")
            break
    return ws


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader("templates")
    )
    app.add_routes([
        web.get("/", index),
        web.post("/deploy", deploy),
        web.get("/deploy/log", show_log),
    ])
    web.run_app(app, port=8080, access_log=None)
