# 使用Ubuntu 22.04 LTS作为基础镜像
FROM ubuntu:22.04

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖和Python 3.13
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    imagemagick \
    libjpeg-turbo8 \
    libwebp7 \
    libtiff5 \
    libpng16-16 \
    libavif13 \
    libgif7 \
    zlib1g \
    poppler-utils \
    file \
    python3 \
    python3-pip \
    jpegoptim \
    pngquant \
    webp \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="PS" \/>/<policy domain="coder" rights="read|write" pattern="PS" \/>/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="PS2" \/>/<policy domain="coder" rights="read|write" pattern="PS2" \/>/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="PS3" \/>/<policy domain="coder" rights="read|write" pattern="PS3" \/>/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="EPS" \/>/<policy domain="coder" rights="read|write" pattern="EPS" \/>/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="XPS" \/>/<policy domain="coder" rights="read|write" pattern="XPS" \/>/' /etc/ImageMagick-6/policy.xml

# 复制requirements.txt文件
COPY requirements.txt .

# 安装依赖，使用python3 -m pip确保使用正确的Python版本
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY . .

# 复制entrypoint脚本
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# 暴露端口5000
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PUID=1000
ENV PGID=1000
ENV UMASK=022

# 使用entrypoint脚本
ENTRYPOINT ["entrypoint.sh"]