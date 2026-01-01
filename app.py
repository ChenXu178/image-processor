from flask import Flask, render_template, request, jsonify, session
import os
import threading
import time
from datetime import datetime
from PIL import Image
import concurrent.futures
import mimetypes
import logging

# 配置日志记录
from logging.handlers import RotatingFileHandler

# 创建log文件夹（如果不存在）
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
os.makedirs(log_dir, exist_ok=True)

# 创建RotatingFileHandler，设置最大文件大小为10M，最大保留5份日志
file_path = os.path.join(log_dir, 'app.log')
file_handler = RotatingFileHandler(
    file_path,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)

# 配置日志格式
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)

# 创建StreamHandler
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# 配置根日志记录器
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        stream_handler
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 用于session管理

# 加载配置
logger.info("开始加载配置文件")
try:
    with open('config.py', 'r', encoding='utf-8') as f:
        config = {}
        exec(f.read(), config)
        BASE_DIR = config['BASE_DIR']
    logger.info(f"配置加载成功，BASE_DIR: {BASE_DIR}")
except Exception as e:
    logger.error(f"配置加载失败: {e}")
    BASE_DIR = '/data'  # 默认值

# 支持的图片格式
SUPPORTED_FORMATS = {
    'jpg': 'JPEG',
    'jpeg': 'JPEG',
    'png': 'PNG',
    'webp': 'WEBP',
    'avif': 'AVIF',
    'heic': 'HEIC',
    'bmp': 'BMP',
    'gif': 'GIF',
    'tiff': 'TIFF'
}

# 检查格式是否支持写入
def is_format_supported(format_name):
    try:
        # 尝试创建一个简单的图片并保存为指定格式，测试是否支持
        test_img = Image.new('RGB', (1, 1))
        import io
        buffer = io.BytesIO()
        test_img.save(buffer, format=SUPPORTED_FORMATS[format_name])
        return True
    except Exception:
        return False

# 初始化时检查并移除不支持的格式
logger.info("开始检查支持的图片格式")
unsupported_formats = []
for ext, format_name in SUPPORTED_FORMATS.items():
    if not is_format_supported(ext):
        unsupported_formats.append(ext)
        
for ext in unsupported_formats:
    del SUPPORTED_FORMATS[ext]
    logger.warning(f"格式 {ext} 不支持，已从支持列表中移除")
    
logger.info(f"支持的图片格式: {list(SUPPORTED_FORMATS.keys())}")

# 全局进度变量
progress_data = {
    'total': 0,
    'processed': 0,
    'status': 'idle',  # idle, running, completed
    'start_time': None,
    'end_time': None,
    'original_size': 0,
    'final_size': 0,
    'current_file': ''  # 当前正在处理的图片路径
}

progress_lock = threading.Lock()

# 检查文件是否为图片
def is_image_file(filename):
    # 使用os.path.splitext获取扩展名，更可靠的方法
    ext = os.path.splitext(filename)[1].lower()[1:]  # [1:] 移除点号
    return ext in SUPPORTED_FORMATS

# 获取文件大小
def get_file_size(filepath):
    return os.path.getsize(filepath)

# 遍历目录获取所有图片文件
def get_all_images(directory, exclude_formats=None):
    images = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_image_file(file):
                if exclude_formats:
                    # 使用os.path.splitext获取扩展名
                    ext = os.path.splitext(file)[1].lower()[1:]  # [1:] 移除点号
                    if ext not in exclude_formats:
                        images.append(filepath)
                else:
                    images.append(filepath)
    return images

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_files', methods=['POST'])
def get_files():
    """
    获取指定路径下的文件列表
    请求方法: POST
    请求参数: path - 要获取文件的路径，默认为BASE_DIR
    返回: JSON格式的文件列表和当前路径
    """
    path = request.form.get('path', BASE_DIR)
    logger.info(f"获取文件列表，路径: {path}")
    
    # 确保路径在BASE_DIR下，防止目录遍历攻击
    if not os.path.normpath(path).startswith(os.path.normpath(BASE_DIR)):
        logger.warning(f"路径 {path} 不在BASE_DIR下，使用默认路径: {BASE_DIR}")
        path = BASE_DIR
    
    files = []
    try:
        # 遍历目录，获取所有文件和文件夹
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # 目录项
                files.append({
                    'name': item,
                    'path': item_path,
                    'type': 'dir',
                    'size': 0,
                    'mtime': os.path.getmtime(item_path)
                })
            elif is_image_file(item):
                # 图片文件项
                files.append({
                    'name': item,
                    'path': item_path,
                    'type': 'file',
                    'size': get_file_size(item_path),
                    'mtime': os.path.getmtime(item_path)
                })
        # 按类型排序，文件夹在前，文件在后
        files.sort(key=lambda x: (x['type'] != 'dir', x['name']))
        logger.info(f"成功获取 {len(files)} 个文件/文件夹")
        
        return jsonify({
            'files': files,
            'current_path': path
        })
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/preview_image', methods=['POST'])
def preview_image():
    """
    获取图片预览信息
    请求方法: POST
    请求参数: path - 图片文件路径
    返回: JSON格式的图片信息，包括路径、宽高、格式和大小
    """
    path = request.form.get('path')
    logger.info(f"获取图片预览信息，路径: {path}")
    
    # 验证图片文件
    if not path or not os.path.isfile(path) or not is_image_file(path):
        logger.warning(f"无效的图片文件: {path}")
        return jsonify({'error': 'Invalid image file'}), 400
    
    # 获取图片信息
    try:
        with Image.open(path) as img:
            width, height = img.size
            format = img.format
        size = get_file_size(path)
        logger.info(f"成功获取图片信息: {width}x{height}, {format}, {size} bytes")
        
        return jsonify({
            'path': path,
            'width': width,
            'height': height,
            'format': format,
            'size': size
        })
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/preview/<path:filepath>')
def preview_file(filepath):
    """
    预览图片文件
    请求方法: GET
    请求参数: filepath - 图片文件相对路径
    返回: 图片文件内容
    """
    logger.info(f"预览图片文件，相对路径: {filepath}")
    
    # 确保文件在BASE_DIR下，防止目录遍历攻击
    # 使用os.path.join自动处理不同平台的路径分隔符
    full_path = os.path.normpath(os.path.join(BASE_DIR, filepath.replace('/', os.sep)))
    logger.info(f"生成完整路径: {full_path}")
    
    # 验证文件
    if not full_path.startswith(BASE_DIR):
        logger.warning(f"路径 {full_path} 不在BASE_DIR下")
        return 'File not found', 404
    if not os.path.isfile(full_path):
        logger.warning(f"文件不存在: {full_path}")
        return 'File not found', 404
    if not is_image_file(full_path):
        logger.warning(f"不是图片文件: {full_path}")
        return 'File not found', 404
    
    # 返回图片文件
    logger.info(f"返回图片文件: {full_path}")
    from flask import send_file
    return send_file(full_path)

@app.route('/convert_tiff_preview')
def convert_tiff_preview():
    """
    将TIFF格式图片转换为PNG格式以便预览
    请求方法: GET
    请求参数: path - TIFF图片文件路径
    返回: PNG格式图片内容
    """
    full_path = request.args.get('path')
    logger.info(f"转换TIFF图片为PNG，路径: {full_path}")
    
    # 验证文件
    if not full_path:
        logger.warning("未提供图片路径")
        return 'File not found', 404
    if not os.path.isfile(full_path):
        logger.warning(f"文件不存在: {full_path}")
        return 'File not found', 404
    if not full_path.startswith(BASE_DIR):
        logger.warning(f"路径 {full_path} 不在BASE_DIR下")
        return 'File not found', 404
    if not is_image_file(full_path):
        logger.warning(f"不是图片文件: {full_path}")
        return 'File not found', 404
    
    try:
        # 打开TIFF图片并转换为PNG
        logger.info(f"开始转换TIFF图片: {full_path}")
        from flask import send_file
        import io
        
        with Image.open(full_path) as img:
            # 如果是多页TIFF，只取第一页
            if img.mode != 'RGB':
                img = img.convert('RGB')
                logger.info(f"将图片模式从 {img.mode} 转换为 RGB")
            
            # 将图片保存到内存中
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            logger.info(f"TIFF图片转换成功: {full_path}")
            # 返回PNG图片
            return send_file(buffer, mimetype='image/png')
    except Exception as e:
        logger.error(f"转换TIFF图片失败: {e}")
        return 'Error converting TIFF to PNG', 500

@app.route('/count_formats', methods=['POST'])
def count_formats():
    """
    统计文件格式
    请求方法: POST
    请求参数: selected_paths - 要统计的文件或文件夹路径列表
    返回: JSON格式的统计结果，包括各格式的文件数量、大小、总文件数和总大小
    """
    selected_paths = request.json.get('selected_paths', [])
    logger.info(f"开始统计文件格式，选中路径: {selected_paths}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': 'No files selected'}), 400
    
    format_count = {}  # 格式 -> 数量
    format_size = {}   # 格式 -> 总大小
    total_files = 0    # 总文件数
    total_size = 0     # 总大小
    
    try:
        for path in selected_paths:
            if os.path.isdir(path):
                logger.info(f"统计目录: {path}")
                # 遍历目录，统计所有文件
                for root, dirs, files in os.walk(path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        # 获取文件扩展名
                        ext = os.path.splitext(file)[1].lower()[1:]  # [1:] 移除点号
                        # 如果文件没有扩展名，使用'no_extension'
                        if not ext:
                            ext = 'no_extension'
                        
                        # 获取文件大小
                        file_size = get_file_size(filepath)
                        # 更新统计信息
                        format_count[ext] = format_count.get(ext, 0) + 1
                        format_size[ext] = format_size.get(ext, 0) + file_size
                        total_files += 1
                        total_size += file_size
            elif os.path.isfile(path):
                logger.info(f"统计文件: {path}")
                # 处理单个文件，统计所有文件
                filename = os.path.basename(path)
                # 获取文件扩展名
                ext = os.path.splitext(filename)[1].lower()[1:]  # [1:] 移除点号
                # 如果文件没有扩展名，使用'no_extension'
                if not ext:
                    ext = 'no_extension'
                
                # 获取文件大小
                file_size = get_file_size(path)
                # 更新统计信息
                format_count[ext] = format_count.get(ext, 0) + 1
                format_size[ext] = format_size.get(ext, 0) + file_size
                total_files += 1
                total_size += file_size
        
        logger.info(f"统计完成，总文件数: {total_files}, 总大小: {total_size} bytes")
        logger.info(f"格式统计: {format_count}")
        
        return jsonify({
            'format_count': format_count,
            'format_size': format_size,
            'total_files': total_files,
            'total_size': total_size
        })
    except Exception as e:
        logger.error(f"统计文件格式失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/fix_extensions', methods=['POST'])
def fix_extensions():
    """
    修复文件后缀，将大写扩展名改为小写
    请求方法: POST
    请求参数: selected_paths - 要修复的文件或文件夹路径列表
    返回: JSON格式的修复结果，包括处理的文件数量
    """
    selected_paths = request.json.get('selected_paths', [])
    logger.info(f"开始修复文件后缀，选中路径: {selected_paths}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': 'No files selected'}), 400
    
    processed = 0  # 处理的文件数量
    
    try:
        for path in selected_paths:
            if os.path.isdir(path):
                logger.info(f"修复目录: {path}")
                # 遍历目录
                for root, dirs, files in os.walk(path):
                    for file in files:
                        # 检查文件是否为图片
                        if is_image_file(file):
                            # 获取文件扩展名，确保使用正确的分割方法
                            _, ext = os.path.splitext(file)
                            # 检查扩展名是否包含大写
                            if any(c.isupper() for c in ext[1:]):  # ext包含点号，所以从索引1开始
                                old_path = os.path.join(root, file)
                                # 生成新文件名，将扩展名改为小写
                                name_without_ext = os.path.splitext(file)[0]
                                new_name = f"{name_without_ext}{ext.lower()}"
                                new_path = os.path.join(root, new_name)
                                # 重命名文件
                                os.rename(old_path, new_path)
                                logger.info(f"重命名文件: {old_path} -> {new_path}")
                                processed += 1
            elif os.path.isfile(path) and is_image_file(path):
                logger.info(f"修复文件: {path}")
                # 检查文件扩展名是否包含大写
                _, ext = os.path.splitext(path)
                if any(c.isupper() for c in ext[1:]):  # ext包含点号，所以从索引1开始
                    # 生成新文件名，将扩展名改为小写
                    dirname = os.path.dirname(path)
                    name_without_ext = os.path.splitext(os.path.basename(path))[0]
                    new_name = f"{name_without_ext}{ext.lower()}"
                    new_path = os.path.join(dirname, new_name)
                    # 重命名文件
                    os.rename(path, new_path)
                    logger.info(f"重命名文件: {path} -> {new_path}")
                    processed += 1
        
        logger.info(f"修复完成，共处理 {processed} 个文件")
        return jsonify({'processed': processed})
    except Exception as e:
        logger.error(f"修复文件后缀失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/compress_images', methods=['POST'])
def compress_images():
    """
    压缩图片
    请求方法: POST
    请求参数:
        selected_paths - 要压缩的文件或文件夹路径列表
        quality - 压缩质量，1-100，默认80
        min_size - 最小文件大小，小于此大小的文件将被跳过，默认0字节
        max_workers - 最大线程数，默认4
    返回: JSON格式的压缩结果，包括状态
    """
    global progress_data
    
    selected_paths = request.json.get('selected_paths', [])
    quality = request.json.get('quality', 80)
    min_size = request.json.get('min_size', 0)
    max_workers = request.json.get('max_workers', 4)
    
    logger.info(f"开始压缩图片，选中路径: {selected_paths}, 质量: {quality}, 最小大小: {min_size}, 最大线程数: {max_workers}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': 'No files selected'}), 400
    
    # 重置进度
    with progress_lock:
        progress_data = {
            'total': 0,
            'processed': 0,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'original_size': 0,
            'final_size': 0
        }
    
    # 获取所有图片文件
    all_images = []
    for path in selected_paths:
        if os.path.isdir(path):
            logger.info(f"获取目录中的图片: {path}")
            all_images.extend(get_all_images(path))
        elif os.path.isfile(path) and is_image_file(path):
            logger.info(f"添加图片: {path}")
            all_images.append(path)
    
    logger.info(f"共找到 {len(all_images)} 个图片文件")
    
    # 过滤小于指定大小的文件
    if min_size > 0:
        filtered_images = [img for img in all_images if get_file_size(img) > min_size]
        logger.info(f"过滤后剩余 {len(filtered_images)} 个图片文件")
        all_images = filtered_images
    
    with progress_lock:
        progress_data['total'] = len(all_images)
    
    # 如果没有图片需要处理，直接完成
    if len(all_images) == 0:
        logger.info("没有需要处理的图片，直接完成")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
        return jsonify({'status': 'started'})
    
    # 处理图片
    def process_image(img_path):
        """
        处理单个图片压缩
        """
        global progress_data
        try:
            logger.info(f"压缩图片: {img_path}")
            
            # 更新当前正在处理的图片路径
            with progress_lock:
                progress_data['current_file'] = img_path
            
            original_size = get_file_size(img_path)
            
            with Image.open(img_path) as img:
                # 如果图片是JPEG格式且模式是RGBA，转换为RGB模式
                ext = img_path.lower().split('.')[-1]
                if ext in ['jpg', 'jpeg'] and img.mode == 'RGBA':
                    logger.info(f"将图片 {img_path} 从 RGBA 转换为 RGB 模式")
                    img = img.convert('RGB')
                
                # 保存图片，使用指定质量
                img.save(img_path, optimize=True, quality=quality)
            
            final_size = get_file_size(img_path)
            logger.info(f"压缩完成: {img_path}, 原大小: {original_size} bytes, 新大小: {final_size} bytes")
            
            with progress_lock:
                progress_data['processed'] += 1
                progress_data['original_size'] += original_size
                progress_data['final_size'] += final_size
        except Exception as e:
            logger.error(f"处理图片失败: {img_path}, 错误: {e}")
            with progress_lock:
                progress_data['processed'] += 1
    
    # 在新线程中处理图片，避免阻塞主线程
    def process_images_async():
        # 使用多线程处理
        logger.info(f"使用 {max_workers} 个线程开始处理图片")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(process_image, all_images)
        
        logger.info("所有图片处理完成")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            progress_data['current_file'] = ''
    
    # 启动异步处理
    thread = threading.Thread(target=process_images_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/convert_images', methods=['POST'])
def convert_images():
    """
    批量转换图片格式
    请求方法: POST
    请求参数:
        selected_paths - 要转换的文件或文件夹路径列表
        target_format - 目标格式，例如 jpg, png, webp 等
        quality - 转换质量，1-100，默认99
        max_workers - 最大线程数，默认4
    返回: JSON格式的转换结果，包括状态
    """
    global progress_data
    
    selected_paths = request.json.get('selected_paths', [])
    target_format = request.json.get('target_format', 'jpg')
    quality = request.json.get('quality', 99)
    max_workers = request.json.get('max_workers', 4)
    
    logger.info(f"开始转换图片格式，选中路径: {selected_paths}, 目标格式: {target_format}, 质量: {quality}, 最大线程数: {max_workers}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': 'No files selected'}), 400
    
    # 重置进度
    with progress_lock:
        progress_data = {
            'total': 0,
            'processed': 0,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'original_size': 0,
            'final_size': 0
        }
    
    # 获取所有图片文件，排除目标格式
    all_images = []
    target_format_lower = target_format.lower()
    for path in selected_paths:
        if os.path.isdir(path):
            logger.info(f"获取目录中的图片，排除目标格式: {target_format_lower}, 路径: {path}")
            all_images.extend(get_all_images(path, exclude_formats=[target_format_lower]))
        elif os.path.isfile(path) and is_image_file(path):
            ext = os.path.basename(path).lower().split('.')[-1]
            if ext != target_format_lower:
                logger.info(f"添加图片: {path}, 当前格式: {ext}, 目标格式: {target_format_lower}")
                all_images.append(path)
            else:
                logger.info(f"跳过图片: {path}, 当前格式与目标格式相同: {target_format_lower}")
    
    logger.info(f"共找到 {len(all_images)} 个需要转换的图片文件")
    
    with progress_lock:
        progress_data['total'] = len(all_images)
    
    # 如果没有图片需要处理，直接完成
    if len(all_images) == 0:
        logger.info("没有需要处理的图片，直接完成")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
        return jsonify({'status': 'started'})
    
    # 处理图片
    def process_image(img_path):
        """
        处理单个图片转换
        """
        global progress_data
        try:
            logger.info(f"转换图片: {img_path}")
            
            # 更新当前正在处理的图片路径
            with progress_lock:
                progress_data['current_file'] = img_path
            
            original_size = get_file_size(img_path)
            
            # 生成新文件名
            dirname = os.path.dirname(img_path)
            basename = os.path.basename(img_path).split('.')[0]
            new_path = os.path.join(dirname, f"{basename}.{target_format}")
            
            with Image.open(img_path) as img:
                # 如果目标格式是JPEG，且图片模式是RGBA，转换为RGB模式
                if target_format.lower() in ['jpg', 'jpeg'] and img.mode == 'RGBA':
                    logger.info(f"将图片 {img_path} 从 RGBA 转换为 RGB 模式")
                    img = img.convert('RGB')
                
                # 保存图片，使用指定质量
                img.save(new_path, format=SUPPORTED_FORMATS[target_format], quality=quality)
            
            # 删除原文件
            os.remove(img_path)
            
            final_size = get_file_size(new_path)
            logger.info(f"转换完成: {img_path} -> {new_path}, 原大小: {original_size} bytes, 新大小: {final_size} bytes")
            
            with progress_lock:
                progress_data['processed'] += 1
                progress_data['original_size'] += original_size
                progress_data['final_size'] += final_size
        except Exception as e:
            logger.error(f"处理图片失败: {img_path}, 错误: {e}")
            with progress_lock:
                progress_data['processed'] += 1
    
    # 在新线程中处理图片转换，避免阻塞主线程
    def process_images_async():
        # 使用多线程处理
        logger.info(f"使用 {max_workers} 个线程开始处理图片转换")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(process_image, all_images)
        
        logger.info("所有图片转换完成")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            progress_data['current_file'] = ''
    
    # 启动异步处理
    thread = threading.Thread(target=process_images_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/get_progress')
def get_progress():
    with progress_lock:
        return jsonify(progress_data)

@app.route('/get_supported_formats')
def get_supported_formats():
    # 返回支持的格式列表
    return jsonify({'formats': list(SUPPORTED_FORMATS.keys())})

@app.route('/reset_progress', methods=['POST'])
def reset_progress():
    """
    重置进度状态
    请求方法: POST
    返回: JSON格式的重置结果
    """
    global progress_data
    with progress_lock:
        progress_data = {
            'total': 0,
            'processed': 0,
            'status': 'idle',  # idle, running, completed
            'start_time': None,
            'end_time': None,
            'original_size': 0,
            'final_size': 0,
            'current_file': ''  # 当前正在处理的图片路径
        }
        logger.info("进度状态已重置为idle")
    return jsonify({'status': 'success'})

@app.route('/get_config')
def get_config():
    """
    获取系统配置信息
    返回: JSON格式的配置信息，包括基础目录和CPU核心数
    """
    # 获取CPU核心数
    cpu_count = os.cpu_count() or 4  # 默认为4
    logger.info(f"获取CPU核心数: {cpu_count}")
    return jsonify({'base_dir': BASE_DIR, 'cpu_count': cpu_count})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)