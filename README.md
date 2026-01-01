# 批量图片处理Web应用

一个基于Flask和Pillow的Web端批量图片压缩、图片格式转换工具，支持多种图片格式，包括HEIC。

## 功能特性

- ✅ **批量图片压缩**：支持调整压缩质量，跳过小于指定大小的文件
- ✅ **批量图片格式转换**：支持JPG、PNG、WebP、AVIF、HEIC、BMP、GIF、TIFF、PDF等格式
- ✅ **文件格式统计**：统计选中文件或文件夹的格式分布和大小
- ✅ **文件后缀修复**：自动将大写后缀改为小写
- ✅ **图片预览**：支持点击预览和鼠标悬浮预览
- ✅ **EXIF信息显示**：支持查看图片的EXIF元数据
- ✅ **多线程处理**：根据CPU核心数动态调整线程数
- ✅ **跨平台支持**：支持Windows和Linux系统
- ✅ **Docker容器化**：提供Dockerfile，支持容器化部署

## 技术栈

- **后端**：Flask
- **图像处理**：Pillow, ImageMagick
- **前端**：HTML, CSS, JavaScript, Bootstrap
- **并发处理**：concurrent.futures
- **容器化**：Docker

## 系统要求

- Python 3.8+
- ImageMagick 6+
- Docker (可选，用于容器化部署)

## 快速开始

### 本地运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/ChenXu178/image-processor.git
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
   - `-e UMASK=022`：设置文件创建的默认权限，可选

3. **访问应用**
   打开浏览器访问 http://localhost:5000

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

3. **图片预览**
   - **点击预览**：点击图片可查看大图预览，支持EXIF信息显示
   - **悬浮预览**：鼠标悬浮在图片上1秒可显示小图预览
   - **HEIC格式**：HEIC格式图片点击直接下载，不支持悬浮预览

4. **批量图片压缩**
   - 选择要压缩的图片或文件夹
   - 点击"图片压缩"按钮
   - 在弹出的配置窗口中设置：
     - **压缩质量**：1-100，数值越高质量越好，文件越大
     - **最小文件大小**：跳过小于指定大小的文件（单位：KB）
     - **线程数**：根据CPU核心数自动调整，可手动修改
   - 点击"开始压缩"按钮开始处理
   - 处理进度会显示在进度窗口中

5. **批量图片格式转换**
   - 选择要转换的图片或文件夹
   - 点击"图片转换"按钮
   - 在弹出的配置窗口中设置：
     - **目标格式**：选择要转换的目标格式
     - **转换质量**：1-100，数值越高质量越好，文件越大
     - **线程数**：根据CPU核心数自动调整，可手动修改
   - 点击"开始转换"按钮开始处理
   - 处理进度会显示在进度窗口中

6. **文件格式统计**
   - 选择要统计的文件或文件夹
   - 点击"统计文件格式"按钮
   - 统计结果会显示在弹出的模态框中，包括各格式的数量、大小和平均大小

7. **修复文件后缀**
   - 选择要修复的文件或文件夹
   - 点击"修复文件后缀"按钮
   - 确认后会将所有图片文件的后缀改为小写

### 高级功能

#### EXIF信息显示
- 点击图片预览后，可通过"显示EXIF信息"按钮查看图片的EXIF元数据
- EXIF信息包括拍摄时间、设备型号、光圈、快门速度、ISO等
- 支持中文显示EXIF字段

#### HEIC格式支持
- 支持HEIC格式图片的压缩和转换
- 支持HEIC格式图片的直接下载
- 支持HEIC格式图片的EXIF信息提取

#### 多线程处理
- 根据CPU核心数自动调整线程数，默认使用70%核心数
- 可手动调整线程数，平衡处理速度和系统资源占用

#### 支持的图片格式

应用支持多种图片格式，包括：
- JPG/JPEG
- PNG
- WebP
- AVIF
- HEIC/HEIF
- BMP
- GIF
- TIFF/TIF
- PDF（支持PDF转图片）

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
- `PUID`：容器内运行应用的用户UID，用于Docker部署
- `PGID`：容器内运行应用的用户GID，用于Docker部署
- `UMASK`：容器内文件创建的默认权限，用于Docker部署，默认为022

## 目录结构

```
image-processor/
├── app.py                  # 主应用程序
├── config.py               # 配置文件（需创建）
├── requirements.txt        # 依赖列表
├── Dockerfile              # Dockerfile
├── entrypoint.sh          # Docker容器入口脚本
├── README.md              # 项目说明文档
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
- 使用Pillow和ImageMagick的优化选项，优化输出文件

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

5. **HEIC格式无法处理**
   - 检查是否安装了libheif库
   - 检查ImageMagick是否支持HEIC格式

### 日志查看

- **服务器日志**：查看`log/app.log`文件
- **Docker容器日志**：`docker logs <container-id>`

## 安全说明

- 应用使用Flask开发，建议在生产环境中使用WSGI服务器（如Gunicorn）和反向代理（如Nginx）
- 定期更新依赖，修复安全漏洞
- 限制容器的网络访问权限

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

