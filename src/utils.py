import os
import logging
from threading import Thread
from subprocess import PIPE, Popen

import jinja2

import settings

log = logging.basicConfig(level=logging.INFO)


class Nginx(Thread):
    def __init__(self, nginxs: list, servers: list, domain: str, update_file: str, queue):
        Thread.__init__(self)
        self.nginxs = nginxs
        self.servers = servers
        self.domain = domain
        self.queue = queue
        self.update_file = update_file
        self.tasks = list()

    def operate_servers(self, action: str):
        if action not in ["down", "up"]:
            action = "up"
        task_file = render(
            'nginx.yml.ja2', '{}.yml'.format(action), action=action,
            domain=self.domain, nginxs=self.nginxs, servers=self.servers
        )
        self.tasks.append(task_file)

    def update_domain(self):
        render(
            "backup.ps1.ja2", "backup.ps1", domain=self.domain,
            smb_username=settings.BACKUP_SERVER_USER,
            smb_passwrod=settings.BACKUP_SERVER_PASSWORD
        )
        render("update.ps1.ja2", "update.ps1", domain=self.domain)
        task_file = render("update.yml.ja2", "update.yml", servers=self.servers, upload_file=self.update_file)
        self.tasks.append(task_file)

    def run(self) -> None:
        self.operate_servers('down')
        self.tasks.append(prepare_update(self.domain, self.servers))
        self.operate_servers('up')
        self.queue.put("生成更新所需要的Task文件成功，准备执行相关Task")
        for task_file in self.tasks:
            if 'down' in task_file:
                self.queue.put("<span style='color:#0066FF'>开始从网关中摘除服务器</span>")
            elif 'update' in task_file:
                self.queue.put("<span style='color:#0066FF'>开始执行更新站点动作</span>")
            elif 'up' in task_file:
                self.queue.put("<span style='color:#0066FF'>更新完成，开始将服务器重新从网关中上线</span>")
            stdout = Popen(["ansible-playbook", task_file], stdout=PIPE, stderr=PIPE).stdout
            for line in stdout:
                try:
                    info = line.decode("utf8").strip("\n").strip("\r")
                except UnicodeDecodeError:
                    info = line.decode("gbk").strip("\n").strip("\r")
                if info:
                    logging.info(info)
                    self.queue.put(info)
        self.queue.put("EOF")


class Slb(Thread):
    def __init__(self, aes_key: str, aes_secret: str, region: str,
                 domain: str, filename: str, servers: list, queue) -> None:
        Thread.__init__(self)
        self.domain = domain
        self.servers = servers
        self.upload_file = filename
        self.queue = queue

    def run(self) -> None:
        task_file = prepare_update(self.domain, self.servers)
        pass


def render(template_name: str, filename: str,  **kwargs) -> str:
    env_yml = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(os.getcwd(), 'templates'))
    )
    template = env_yml.get_template(template_name)
    with open(filename, 'w') as f:
        f.write(template.render(kwargs))
        return filename


# 因为这个函数可以复用，不管是NGINX还是SLB，都要做这一步
def prepare_update(domain: str, servers: list) -> str:
    render(
        "backup.ps1.ja2", "backup.ps1", domain=domain,
        backup_server=settings.BACKUP_SERVER,
        backup_username=settings.BACKUP_SERVER_USER,
        backup_password=settings.BACKUP_SERVER_PASSWORD
    )
    render("update.ps1.ja2", "update.ps1", domain=domain)
    task_file = render("update.yml.ja2", "update.yml", domain=domain, servers=servers)
    return task_file
