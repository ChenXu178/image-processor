# 批量图片处理Web应用

一个基于Flask和Pillow的Web端批量图片压缩、图片格式转换工具。

## 功能特性

- ✅ **批量图片压缩**：支持调整压缩质量，跳过小于指定大小的文件
- ✅ **批量图片格式转换**：支持JPG、PNG、WebP、AVIF、BMP、GIF、TIFF等格式
- ✅ **文件格式统计**：统计选中文件或文件夹的格式分布和大小
- ✅ **文件后缀修复**：自动将大写后缀改为小写
- ✅ **多线程处理**：根据CPU核心数动态调整线程数，默认使用70%核心数
- ✅ **跨平台支持**：支持Windows和Linux系统
- ✅ **Docker容器化**：提供Dockerfile，支持容器化部署
- ✅ **CI/CD集成**：提供GitHub Workflow配置，自动构建和推送Docker镜像

## 技术栈

- **后端**：Flask
- **图像处理**：Pillow
- **前端**：HTML、CSS、JavaScript、Bootstrap
- **并发处理**：concurrent.futures
- **容器化**：Docker
- **CI/CD**：GitHub Actions

## 系统要求

- Python 3.8+
- Docker (可选，用于容器化部署)

## 快速开始

### 本地运行

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd image-processor
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置BASE_DIR**
   创建`config.py`文件，配置图片存储目录：
   ```python
   BASE_DIR = '/path/to/your/images'
   ```

4. **运行应用**
   ```bash
   python app.py
   ```

5. **访问应用**
   打开浏览器访问 http://localhost:5000

### Docker部署

#### 方法1：本地构建并运行

1. **构建Docker镜像**
   ```bash
   docker build -t image-processor .
   ```

2. **运行Docker容器**
   ```bash
   docker run -d -p 5000:5000 -v /path/to/your/images:/data -e PUID=$(id -u) -e PGID=$(id -g) image-processor
   ```
   
   参数说明：
   - `-d`：后台运行容器
   - `-p 5000:5000`：将容器的5000端口映射到主机的5000端口
   - `-v /path/to/your/images:/data`：将主机的图片目录挂载到容器的/data目录
   - `-e PUID=$(id -u)`：使用当前用户的UID，避免权限问题
   - `-e PGID=$(id -g)`：使用当前用户的GID，避免权限问题
   
   > 注意：PUID和PGID用于指定容器内运行应用程序的用户ID和组ID，确保容器内的进程对挂载目录有正确的读写权限。建议使用当前用户的UID和GID，可通过`id -u`和`id -g`命令获取。

3. **访问应用**
   打开浏览器访问 http://localhost:5000

#### 方法2：使用Docker Hub镜像

1. **拉取Docker镜像**
   ```bash
   docker pull your-dockerhub-username/image-processor
   ```

2. **运行Docker容器**
   ```bash
   docker run -d -p 5000:5000 -v /path/to/your/images:/data -e PUID=$(id -u) -e PGID=$(id -g) your-dockerhub-username/image-processor
   ```
   
   参数说明：
   - `-e PUID=$(id -u)`：使用当前用户的UID，避免权限问题
   - `-e PGID=$(id -g)`：使用当前用户的GID，避免权限问题

3. **访问应用**
   打开浏览器访问 http://localhost:5000

## GitHub Workflow配置

### 配置步骤

1. **创建GitHub仓库**
   将项目推送到GitHub仓库。

2. **配置Docker Hub访问令牌**
   - 登录到Docker Hub：https://hub.docker.com/
   - 进入**Account Settings** > **Security** > **New Access Token**
   - 创建一个新的访问令牌，权限选择`Read & Write`
   - 复制生成的令牌，妥善保存

3. **配置GitHub Secrets**
   - 进入GitHub仓库的**Settings** > **Secrets and variables** > **Actions**
   - 点击**New repository secret**，添加以下两个Secret：
     - `DOCKER_HUB_USERNAME`：你的Docker Hub用户名
     - `DOCKER_HUB_TOKEN`：刚刚生成的Docker Hub访问令牌

4. **修改Workflow配置**
   - 打开`.github/workflows/docker-push.yml`文件
   - 将第31行的`your-dockerhub-username`替换为你的Docker Hub用户名：
     ```yaml
     images: your-dockerhub-username/image-processor
     ```

5. **触发自动构建**
   - 将修改推送到GitHub仓库的main分支
   - GitHub Actions会自动触发构建，构建过程可在**Actions**标签页查看
   - 构建完成后，镜像会自动推送到Docker Hub

### Workflow说明

- **触发条件**：推送到main分支时触发
- **运行环境**：Ubuntu 22.04
- **主要步骤**：
  1. 检出代码
  2. 设置Docker Buildx
  3. 登录到Docker Hub
  4. 提取Docker镜像标签和元数据
  5. 构建并推送Docker镜像
- **缓存机制**：使用GitHub Actions缓存，提高构建速度

## 使用指南

### 基本操作

1. **文件浏览**
   - 应用启动后，会显示配置的BASE_DIR目录下的文件和文件夹
   - 点击文件夹进入子目录，点击图片查看预览
   - 点击"返回上级"按钮返回父目录

2. **文件选择**
   - 勾选文件或文件夹前的复选框进行选择
   - 点击"全选"按钮选择当前目录下所有图片
   - 点击"取消全选"按钮清空选择
   - 选中的文件会显示在右侧"已选择文件"列表中

3. **批量图片压缩**
   - 选择要压缩的图片或文件夹
   - 点击"图片压缩"按钮
   - 在弹出的配置窗口中设置：
     - **压缩质量**：1-100，数值越高质量越好，文件越大
     - **最小文件大小**：跳过小于指定大小的文件（单位：KB）
     - **线程数**：根据CPU核心数自动调整，可手动修改
   - 点击"开始压缩"按钮开始处理
   - 处理进度会显示在进度窗口中

4. **批量图片格式转换**
   - 选择要转换的图片或文件夹
   - 点击"图片转换"按钮
   - 在弹出的配置窗口中设置：
     - **目标格式**：选择要转换的目标格式
     - **转换质量**：1-100，数值越高质量越好，文件越大
     - **线程数**：根据CPU核心数自动调整，可手动修改
   - 点击"开始转换"按钮开始处理
   - 处理进度会显示在进度窗口中

5. **文件格式统计**
   - 选择要统计的文件或文件夹
   - 点击"统计文件格式"按钮
   - 统计结果会显示在弹出的模态框中，包括各格式的数量、大小和平均大小

6. **修复文件后缀**
   - 选择要修复的文件或文件夹
   - 点击"修复文件后缀"按钮
   - 确认后会将所有图片文件的后缀改为小写

### 高级功能

#### 自定义线程数

- 应用会自动检测系统CPU核心数，并将线程数滑块的最大值设置为核心数
- 默认线程数为CPU核心数的70%，以平衡性能和系统资源占用
- 可根据实际需求手动调整线程数

#### 支持的图片格式

应用启动时会自动检测系统支持的图片格式，并移除不支持的格式。常见支持的格式包括：
- JPG/JPEG
- PNG
- WebP
- AVIF
- BMP
- GIF
- TIFF

> 注意：HEIC格式通常需要额外安装libheif库，部分系统可能不支持

## 配置文件

### config.py

应用启动时会读取`config.py`文件，配置图片存储目录：

```python
# 图片存储目录
BASE_DIR = '/path/to/your/images'
```

### 环境变量

- `FLASK_APP`：Flask应用入口文件，默认为app.py
- `FLASK_ENV`：Flask运行环境，默认为production

## 日志管理

### 服务器日志

- **日志文件**：`app.log`
- **日志级别**：INFO
- **日志格式**：包含时间戳、日志级别、消息内容
- **日志输出**：同时输出到文件和控制台
- **日志轮转**：
  - 最大文件大小：10MB
  - 最大保留日志文件数：5份
  - 日志文件命名：`app.log`、`app.log.1`、`app.log.2`...`app.log.5`
  - 当`app.log`达到10MB时，会自动重命名为`app.log.1`，原`app.log.1`重命名为`app.log.2`，以此类推，`app.log.5`会被删除

### 客户端日志

- **日志级别**：可在`main.js`中配置，默认为INFO
- **日志输出**：控制台
- **日志格式**：包含时间戳、日志级别、消息内容

## 目录结构

```
image-processor/
├── app.py                  # 主应用程序
├── config.py               # 配置文件（需创建）
├── requirements.txt        # 依赖列表
├── Dockerfile              # Dockerfile
├── README.md              # 项目说明文档
├── .github/
│   └── workflows/
│       └── docker-push.yml # GitHub Actions配置
├── static/
│   ├── css/
│   │   └── style.css      # 样式文件
│   └── js/
│       └── main.js        # JavaScript文件
└── templates/
    └── index.html         # HTML模板
```

## 性能优化

- 使用多线程处理图片，提高处理速度
- 动态检测CPU核心数，合理分配线程资源
- 跳过小于指定大小的文件，避免不必要的处理
- 转换时跳过相同格式的文件，提高效率
- 使用Pillow的optimize选项，优化输出文件

## 故障排除

### 常见问题

1. **应用无法启动**
   - 检查Python版本是否符合要求
   - 检查依赖是否正确安装
   - 检查config.py文件是否正确配置

2. **图片无法显示**
   - 检查图片路径是否正确
   - 检查BASE_DIR配置是否正确
   - 检查文件权限

3. **格式转换失败**
   - 检查目标格式是否支持
   - 检查图片是否损坏
   - 查看日志文件获取详细错误信息

4. **Docker容器无法访问**
   - 检查容器是否正在运行：`docker ps`
   - 检查端口映射是否正确
   - 检查挂载的卷路径是否正确

### 日志查看

- **服务器日志**：查看app.log文件
- **Docker容器日志**：`docker logs <container-id>`
- **GitHub Actions日志**：在GitHub仓库的Actions标签页查看

## 安全说明

- 应用使用Flask开发，建议在生产环境中使用WSGI服务器（如Gunicorn）和反向代理（如Nginx）
- 定期更新依赖，修复安全漏洞
- 使用强密码保护Docker Hub账户
- 限制容器的网络访问权限

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues：<repository-url>/issues

---

**Enjoy using the Image Processor Web App!** 🎉