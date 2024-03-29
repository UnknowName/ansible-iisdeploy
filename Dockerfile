FROM python:3.7-alpine
ENV APP_HOME=/opt/app PATH=${APP_HOME}/bin:$PATH
ADD ./src /opt/app
WORKDIR /opt/app
RUN adduser -D -u 120002 -h /opt/app app \
    && mkdir .ssh \
    && echo "StrictHostKeyChecking=no" > .ssh/config \
    && sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && apk add gcc g++ make libffi-dev openssl-dev openssh-client sshpass \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt\
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ pywinrm ansible \
    && apk del gcc g++ make libffi-dev openssl-dev \
    && rm -rf /var/cache/apk/* \
    && chown -R app:app /opt/app
USER app
EXPOSE 8080
CMD ["python", "-u", "main.py"]