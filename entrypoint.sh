#!/bin/bash

# 设置默认值
PUID=${PUID:-1000}
PGID=${PGID:-1000}
UMASK=${UMASK:-022}

# 显示当前PUID和PGID
echo "Current PUID: $PUID, PGID: $PGID"

# 处理组
# 先检查指定的PGID是否已被占用
if getent group $PGID > /dev/null 2>&1; then
    # GID已被占用，获取已存在的组名
    existing_group=$(getent group $PGID | cut -d: -f1)
    echo "GID $PGID is already in use by group '$existing_group'"
    
    # 检查appuser组是否存在
    if ! getent group appuser > /dev/null 2>&1; then
        # appuser组不存在，使用已存在的组名和GID
        echo "Creating appuser user without separate group, using existing group '$existing_group'"
        APP_GROUP="$existing_group"
    else
        # appuser组已存在，保持现有组
        echo "Group appuser already exists, using existing group"
        APP_GROUP="appuser"
    fi
else
    # GID未被占用，检查appuser组是否存在
    if ! getent group appuser > /dev/null 2>&1; then
        # 创建appuser组，使用指定的GID
        groupadd -g $PGID appuser
        echo "Created group appuser with GID $PGID"
        APP_GROUP="appuser"
    else
        # appuser组已存在，更新其GID
        groupmod -g $PGID appuser
        echo "Updated group appuser to GID $PGID"
        APP_GROUP="appuser"
    fi
fi

# 处理用户
# 先检查指定的PUID是否已被占用
if getent passwd $PUID > /dev/null 2>&1; then
    # UID已被占用，获取已存在的用户名
    existing_user=$(getent passwd $PUID | cut -d: -f1)
    echo "UID $PUID is already in use by user '$existing_user'"
    
    # 使用已存在的用户，检查其组是否正确
    if ! groups $existing_user | grep -q "$APP_GROUP"; then
        # 将用户添加到APP_GROUP组
        usermod -aG $APP_GROUP $existing_user
        echo "Added user '$existing_user' to group '$APP_GROUP'"
    fi
    # 使用已存在的用户
    APP_USER="$existing_user"
else
    # UID未被占用，检查appuser用户是否存在
    if ! getent passwd appuser > /dev/null 2>&1; then
        # 创建appuser用户，使用APP_GROUP组
        useradd -u $PUID -g $APP_GROUP -m -s /bin/bash appuser
        echo "Created user appuser with UID $PUID and GID $(getent group $APP_GROUP | cut -d: -f3)"
        APP_USER="appuser"
    else
        # appuser用户已存在，更新其UID和GID
        usermod -u $PUID -g $APP_GROUP appuser
        echo "Updated user appuser to UID $PUID and GID $(getent group $APP_GROUP | cut -d: -f3)"
        APP_USER="appuser"
    fi
fi

# 确保/data目录存在并设置权限
mkdir -p /data
# 获取APP_GROUP的实际GID
ACTUAL_GID=$(getent group $APP_GROUP | cut -d: -f3)
chown -R $PUID:$ACTUAL_GID /app

# 使用正确的用户和组运行应用程序
echo "Running application as $APP_USER ($PUID:$ACTUAL_GID), UMASK: $UMASK"
exec gosu $PUID:$ACTUAL_GID bash -c "umask $UMASK && python3 app.py"