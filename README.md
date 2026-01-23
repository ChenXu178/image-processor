# 批量图片处理Web应用

一个基于Flask和ImageMagick的Web端批量图片压缩、图片格式转换工具，支持多种图片格式。

## 功能特性

- ✅ **批量图片压缩**：支持调整压缩质量，跳过小于指定大小的文件
- ✅ **批量图片格式转换**：支持JPG、PNG、WebP、AVIF、HEIC、BMP、GIF、TIFF、PDF等格式
- ✅ **PDF转图片**：支持将PDF文件转换为图片格式
- ✅ **图片合并PDF**：支持将多张图片合并成一个PDF文件，支持PDF加密
- ✅ **文件格式统计**：统计选中文件或文件夹的格式分布和大小
- ✅ **文件后缀修复**：自动将大写后缀改为小写
- ✅ **图片预览**：支持点击预览和鼠标悬浮预览
- ✅ **EXIF信息显示**：支持查看图片的EXIF元数据，包括地理位置转换
- ✅ **多线程处理**：根据CPU核心数动态调整线程数
- ✅ **跨平台支持**：支持Windows和Linux系统
- ✅ **Docker容器化**：提供Dockerfile，支持容器化部署
- ✅ **专用压缩工具**：Linux平台使用jpegoptim、pngquant、cwebp进行压缩，提高压缩效率和质量
- ✅ **文件搜索**：支持按名称搜索文件，支持正则表达式和大小写敏感选项
- ✅ **文件删除**：支持单个文件删除和按格式批量删除文件
- ✅ **清理空文件夹**：支持递归清理指定路径下的空文件夹
- ✅ **实时进度显示**：处理过程中显示实时进度和剩余时间
- ✅ **处理中断**：支持随时停止正在进行的图片处理
- ✅ **文件下载**：支持直接下载选中的图片文件

## 技术栈

- **后端**：Flask
- **WSGI服务器**：Gunicorn
- **图像处理**：Pillow, ImageMagick
- **PDF处理**：pdf2image, pikepdf（用于PDF加密）
- **专用压缩工具**：jpegoptim, pngquant, cwebp (仅Linux平台)
- **前端**：HTML, CSS, JavaScript, Bootstrap
- **并发处理**：concurrent.futures
- **容器化**：Docker
- **辅助库**：
  - geopy：用于地理位置转换
  - natsort：用于自然排序
  - pypinyin：用于中文拼音排序
  - pdf2image：用于PDF转图片
  - pikepdf：用于PDF加密
  - mimetypes：用于文件类型检测

## 系统要求

- Python 3.8+
- ImageMagick 6+
- Docker (可选，用于容器化部署)
- 专用压缩工具（Linux平台）：jpegoptim, pngquant, cwebp (Docker容器中已自动安装)

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
   
   - **开发环境**：
     ```bash
     python app.py
     ```
   
   - **生产环境**（推荐）：
     ```bash
     gunicorn -w 1 -b 0.0.0.0:5000 --preload --timeout 600 app:app
     ```
   
   说明：
   - `-w 1`：启动1个工作进程（可根据CPU核心数调整）
   - `-b 0.0.0.0:5000`：绑定到所有网络接口的5000端口
   - `--preload`：预加载应用，提高性能
   - `--timeout 600`：设置超时时间为600秒，适合处理大文件

5. **访问应用**
   打开浏览器访问 http://localhost:5000

### Docker部署

#### 方法1：从Dockerhub拉取镜像（推荐）

1. **拉取Docker镜像**
   ```bash
   docker pull liziwa/image-processor:latest
   ```

2. **运行Docker容器**
   ```bash
   docker run -d -p 5000:5000 -v /path/to/your/images:/data -e PUID=$(id -u) -e PGID=$(id -g) liziwa/image-processor:latest
   ```

#### 方法2：本地构建并运行

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
   - `-e APP_VERSION=1.0.0`：设置应用版本号，可选

   启动模式说明：
   - 容器会自动检查config.py中的DEBUG配置
   - 当DEBUG=True时，使用python直接启动（开发模式）
   - 当DEBUG=False时，使用gunicorn启动（生产模式，默认）

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
   - 处理进度会显示在进度窗口中，支持实时查看进度和剩余时间
   - 点击"停止处理"按钮可随时中断压缩过程

5. **批量图片格式转换**
   - 选择要转换的图片或文件夹
   - 点击"图片转换"按钮
   - 在弹出的配置窗口中设置：
     - **目标格式**：选择要转换的目标格式
     - **转换质量**：1-100，数值越高质量越好，文件越大
     - **线程数**：根据CPU核心数自动调整，可手动修改
   - 点击"开始转换"按钮开始处理
   - 处理进度会显示在进度窗口中，支持实时查看进度和剩余时间
   - 点击"停止处理"按钮可随时中断转换过程

6. **PDF转图片**
   - 选择要转换的PDF文件
   - 在图片转换功能中选择目标格式
   - 系统会自动将PDF页面转换为图片

7. **图片合并PDF**
   - 选择要合并的图片文件
   - 在图片转换功能中选择PDF作为目标格式
   - 可选择设置PDF密码进行加密
   - 点击"开始转换"按钮开始处理
   - 系统会将所有选中的图片合并成一个PDF文件

8. **文件搜索**
   - 在搜索框中输入搜索关键词
   - 可选择是否使用正则表达式和区分大小写
   - 点击"搜索"按钮开始搜索
   - 搜索结果会显示在文件列表中

9. **文件删除**
   - 按格式删除：选择文件夹，点击"按格式删除"按钮，选择要删除的格式
   - 系统会验证文件路径，防止误删

10. **清理空文件夹**
   - 选择要清理的文件夹
   - 点击"清理空文件夹"按钮
   - 系统会递归清理所有空文件夹，从最里层开始

11. **文件格式统计**
    - 选择要统计的文件或文件夹
    - 点击"统计文件格式"按钮
    - 统计结果会显示在弹出的模态框中，包括各格式的数量、大小和平均大小

12. **修复文件后缀**
    - 选择要修复的文件或文件夹
    - 点击"修复文件后缀"按钮
    - 确认后会将所有图片文件的后缀改为小写

13. **文件下载**
    - 选择要下载的文件
    - 点击"下载"按钮开始下载
    - 支持多种格式的文件下载

### 高级功能

#### EXIF信息显示
- 点击图片预览后，可通过"显示EXIF信息"按钮查看图片的EXIF元数据
- EXIF信息包括拍摄时间、设备型号、光圈、快门速度、ISO等
- 支持中文显示EXIF字段
- 支持将GPS坐标转换为具体地址（使用geopy库）

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
├── entrypoint.sh           # Docker容器入口脚本
├── README.md               # 项目说明文档
├── exif_mapping.py         # EXIF字段映射表
├── optimize_exif_parsing.py # EXIF解析优化模块
├── static/
│   ├── css/
│   │   ├── style.css       # 主样式文件
│   │   └── mobile.css      # 移动端样式文件
│   └── js/
│       └── main.js         # JavaScript文件
└── templates/
    └── index.html          # HTML模板
```

## 性能优化

- 使用多线程处理图片，提高处理速度
- 动态检测CPU核心数，合理分配线程资源
- 跳过小于指定大小的文件，避免不必要的处理
- 转换时跳过相同格式的文件，提高效率
- 使用Pillow和ImageMagick的优化选项，优化输出文件
- Linux平台使用专用压缩工具：
  - JPG/JPEG格式使用jpegoptim，提供更好的压缩效果和速度
  - PNG格式使用pngquant，提供更优的压缩质量和体积
  - WebP格式使用cwebp，提供更高的压缩效率
- EXIF解析优化：
  - 使用优化的EXIF字段映射表，提高解析速度
  - 优化EXIF解析算法，减少内存占用
  - 支持选择性解析EXIF字段，只获取需要的信息

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

- 应用使用Flask开发，生产环境默认使用Gunicorn作为WSGI服务器
- 建议在生产环境中使用反向代理（如Nginx）配合Gunicorn，提供更好的安全性和性能
- 定期更新依赖，修复安全漏洞
- 限制容器的网络访问权限
- Gunicorn配置建议：
  - 合理设置工作进程数（根据CPU核心数调整）
  - 设置适当的超时时间，防止长时间运行的请求阻塞
  - 启用预加载功能，提高性能和内存使用效率
  - 使用--preload参数时，确保应用是线程安全的

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

