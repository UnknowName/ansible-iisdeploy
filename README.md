# Aiohttp+Ansible更新IIS站点

## 特性

- `Aiohttp`提供前端页面与逻辑处理
- `Ansilbe`配合`Powershell`执行相关`Task`
- 更新前备份，格式为`YYYMMDDHH`如`2019111209`

## Prepare

- Windows主机已开启`Ansible`支持。详情请参考[Ansible WindowsGuides](https://docs.ansible.com/ansible/latest/user_guide/windows.html)
- IIS站点(Site)名称，应用池(ApplicationPool),网站根目录均为域名。如站点名称为test.aaa.com,应用池名也为test.aaa.com,网站的根目录文件也为
test.aaaa.com
- IIS站点文件不能放在C盘
- 提供一台内部文件共享服务，如`Samba`或者`Windows共享`
- 网关为`NGINX`时,站点配置文件请放在`/etc/conf.d/`目录下,且文件名为`域名.conf`如`test.aaa.com.conf`

## Deploy

### 1.准备`Ansible`的主机清单文件

```yaml
[windows]
128.0.255.27 ansible_password=password
128.0.255.28 ansible_password=password

[nginxs]
128.0.255.2 ansible_user=root ansible_password=password
128.0.255.3 ansible_user=root ansible_password=password

[windows:vars]
ansible_user=administrator
ansible_connection=winrm
ansible_winrm_transport=basic
ansible_port=5986
ansible_winrm_scheme=https
ansible_winrm_server_cert_validation=ignore
```

### 2.准备配置文件

```python
DOMAINS = {
        # 要部署的站点
        "test.aaa.com": {
          # 站点下的服务器
          "servers": ["128.0.255.27", "128.0.255.28"],
          # 前面的网关类型
          "gateway": "nginx"
        },
        "test.bbb.com": {
          "servers": ["128.0.255.27", "128.0.255.28"],
          "gateway": "slb"
        }
}

GATEWAY = {
    # NGINX的服务器地址
    "nginx": ["128.0.255.10", "128.0.255.3"],
    # 阿里云SLB
    "slb": {
        # 阿里云的AES KEY
        "aes_key": "aes_key",
        # 阿里云的AES SECRET
        "aes_secret": "aes_secret",
        # SLB所在的区域
        "region": "shengzheng",
        # SLB的ID
        "id": "slb_id",
    },
}

# 文件共享的用户名与密码
BACKUP_SERVER = r"\\128.0.100.170\backups"

BACKUP_SERVER_USER = r"share"

BACKUP_SERVER_PASSWORD = r"share"
```


### 3.All Ready

```shell
docker-compose up -d
```