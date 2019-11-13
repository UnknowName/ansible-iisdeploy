DOMAINS = {
        "test.aaa.com": {
          "servers": ["128.0.255.27", "128.0.255.28"],
          "gateway": "nginx"
        },
        "test.bbb.com": {
          "servers": ["128.0.255.27", "128.0.255.28"],
          "gateway": "slb"
        }
}

GATEWAY = {
    "nginx": ["128.0.255.10", "128.0.255.3"],
    "slb": {
        "aes_key": "aes_key",
        "aes_secret": "aes_secret",
        "region": "shengzheng",
        "id": "slb_id",
    },
}

BACKUP_SERVER = r"\\128.0.100.170\backups"

BACKUP_SERVER_USER = r"admin"

BACKUP_SERVER_PASSWORD = r"admin"

