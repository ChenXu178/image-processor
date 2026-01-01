#!/bin/bash

# 设置默认值
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# 显示当前PUID和PGID
echo "Current PUID: $PUID, PGID: $PGID"

# 创建组
if ! getent group appuser > /dev/null 2>&1; then
    groupadd -g $PGID appuser
    echo "Created group appuser with GID $PGID"
else
    echo "Group appuser already exists"
fi

# 创建用户
if ! getent passwd appuser > /dev/null 2>&1; then
    useradd -u $PUID -g $PGID -m -s /bin/bash appuser
    echo "Created user appuser with UID $PUID and GID $PGID"
else
    echo "User appuser already exists, updating UID and GID"
    usermod -u $PUID -g $PGID appuser
fi

# 确保/data目录存在并设置权限
mkdir -p /data
chown -R $PUID:$PGID /data
chown -R $PUID:$PGID /app

# 使用appuser用户运行应用程序
echo "Running application as appuser ($PUID:$PGID)"
exec gosu $PUID:$PGID python app.py