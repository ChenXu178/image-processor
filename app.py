from flask import Flask, render_template, request, jsonify, session, send_file
import os
import threading
import time
from datetime import datetime
from PIL import Image
import concurrent.futures
import mimetypes
import logging
import subprocess
import platform
import io
import traceback
from pdf2image import convert_from_path

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

# 配置根日志记录器，设置为DEBUG级别以便查看详细调试信息
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        file_handler,
        stream_handler
    ]
)

logger = logging.getLogger(__name__)

# 导入geopy库用于地址查询
from geopy.geocoders import Nominatim

# 初始化geocoder，使用zh-CN语言
gelocator = Nominatim(user_agent="image-processor", timeout=5)
logger.info("成功加载并初始化geopy库")

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
    'jpeg': 'JPEG',  # JPG和JPEG是同一种格式，只是扩展名不同
    'png': 'PNG',
    'webp': 'WEBP',
    'avif': 'AVIF',
    'heic': 'HEIC',
    'bmp': 'BMP',
    'gif': 'GIF',
    'tiff': 'TIFF',
    'pdf': 'PDF'  # 添加PDF格式支持
}

# 检查ImageMagick是否可用
def check_imagemagick():
    try:
        cmd = ['magick', '--version'] if platform.system() == 'Windows' else ['convert', '--version']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        logger.info(f"ImageMagick版本: {result.stdout.split()[2]}")
        return True
    except Exception as e:
        logger.warning(f"ImageMagick不可用: {e}")
        logger.warning("程序将继续运行，但图片处理功能将不可用")
        return False

# 根据GPS坐标查询地址的API端点
@app.route('/get_address_from_coords', methods=['POST'])
def get_address_from_coords():
    """根据GPS坐标查询地址"""
    try:
        data = request.get_json()
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': '缺少必要的坐标参数'}), 400
        
        logger.debug(f"根据坐标查询地址: lat={lat}, lon={lon}")
        
        # 使用geopy查询地址
        location = gelocator.reverse((lat, lon), language='zh-CN')
        
        if location:
            address = location.address
            logger.info(f"成功查询到地址: {address}")
            return jsonify({'address': address})
        else:
            logger.warning(f"无法查询到地址: lat={lat}, lon={lon}")
            return jsonify({'error': '无法查询到地址'}), 404
    except Exception as e:
            logger.error(f"查询地址失败: {e}", exc_info=True)
            return jsonify({'error': f'查询地址失败: {str(e)}'}), 500

# 检查jpegoptim是否可用
def check_jpegoptim():
    try:
        result = subprocess.run(['jpegoptim', '--version'], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip().split()[1]
        logger.info(f"jpegoptim版本: {version}")
        return True
    except Exception as e:
        logger.info(f"jpegoptim不可用: {e}")
        return False

# 检查pngquant是否可用
def check_pngquant():
    try:
        result = subprocess.run(['pngquant', '--version'], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip().split()[0]
        logger.info(f"pngquant版本: {version}")
        return True
    except Exception as e:
        logger.info(f"pngquant不可用: {e}")
        return False

# 检查cwebp是否可用
def check_cwebp():
    try:
        result = subprocess.run(['cwebp', '-version'], capture_output=True, text=True, timeout=5)
        version = result.stdout.strip().split()[0]
        logger.info(f"cwebp版本: {version}")
        return True
    except Exception as e:
        logger.info(f"cwebp不可用: {e}")
        return False

# 检查ImageMagick是否可用
IMAGEMAGICK_AVAILABLE = check_imagemagick()

# 检查专门压缩工具是否可用
JPEGOPTIM_AVAILABLE = check_jpegoptim()
PNGQUANT_AVAILABLE = check_pngquant()
CWEBP_AVAILABLE = check_cwebp()

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
    'current_file': '',  # 当前正在处理的图片路径
    'failed_files': [],  # 转换/压缩失败的文件列表
    'skipped_files': []  # 已存在而跳过的文件列表
}

progress_lock = threading.Lock()

# 停止处理标记
stop_processing_flag = False
stop_lock = threading.Lock()

# 检查文件是否为图片
def is_image_file(filename):
    """
    检查文件是否为支持的图片格式
    
    Args:
        filename (str): 文件名或文件路径
        
    Returns:
        bool: 如果是支持的图片格式返回True，否则返回False
        
    说明：
        - 使用os.path.splitext获取扩展名，更可靠的方法
        - 将扩展名转换为小写，确保大小写不敏感
        - 检查扩展名是否在SUPPORTED_FORMATS字典中
    """
    # 使用os.path.splitext获取扩展名，更可靠的方法
    ext = os.path.splitext(filename)[1].lower()[1:]  # [1:] 移除点号
    return ext in SUPPORTED_FORMATS

# 使用专门工具压缩图片（仅Linux平台）
def compress_image_with_special_tools(img_path, quality):
    """
    使用专门的压缩工具压缩图片（仅Linux平台）
    - JPG: jpegoptim
    - PNG: pngquant
    - WEBP: cwebp
    
    Args:
        img_path (str): 图片文件路径
        quality (int): 压缩质量，1-100，数值越高质量越好，文件越大
        
    Returns:
        bool: 压缩成功返回True，失败返回False
    """
    try:
        # 获取文件扩展名
        ext = os.path.splitext(img_path)[1].lower()[1:]
        
        # 根据文件格式选择不同的压缩工具
        if ext in ['jpg', 'jpeg']:
            # JPG文件使用jpegoptim压缩
            cmd = [
                'jpegoptim',
                '--max', str(quality),
                '--all-progressive',  # 生成渐进式JPEG
                '--quiet',  # 静默模式
                img_path
            ]
        elif ext == 'png':
            # PNG文件使用pngquant压缩
            # pngquant的质量范围是0-100，与其他工具一致
            cmd = [
                'pngquant',
                '--skip-if-larger',
                '--quality', str(quality),
                '--output', img_path,
                '--force',  # 覆盖原文件
                img_path
            ]
        elif ext == 'webp':
            # WEBP文件使用cwebp压缩
            cmd = [
                'cwebp',
                '-q', str(quality),
                '-metadata', 'all',  # 保留所有元数据
                '-o', img_path,
                img_path
            ]
        else:
            # 其他格式不支持，返回False
            logger.info(f"不支持的格式，无法使用专门工具压缩: {ext}")
            return False
        
        # 执行命令
        logger.info(f"使用{cmd[0]}压缩图片: {img_path}, 质量: {quality}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"使用{cmd[0]}压缩图片失败: {img_path}, 错误: {result.stderr}")
            return False
        
        logger.info(f"压缩完成: {img_path}")
        return True
    except Exception as e:
        logger.error(f"使用专门工具压缩图片失败: {img_path}, 错误: {e}")
        return False

# 使用ImageMagick压缩图片
def compress_image_with_imagemagick(img_path, quality):
    """
    使用ImageMagick压缩图片
    
    Args:
        img_path (str): 图片文件路径
        quality (int): 压缩质量，1-100，数值越高质量越好，文件越大
        
    Returns:
        bool: 压缩成功返回True，失败返回False
        
    说明：
        - 根据操作系统选择合适的ImageMagick命令
        - 在Windows上使用magick命令
        - 在Linux上先尝试magick命令（ImageMagick 7+），失败则回退到convert命令（ImageMagick 6）
        - 保留EXIF元数据
        - 使用-interlace Plane生成渐进式JPEG，提高网页加载体验
        - 使用-sampling-factor 4:2:0进行色度抽样，平衡质量和大小
        - 使用-colorspace sRGB确保输出图片使用sRGB色彩空间，提高兼容性
    """
    try:
        # 使用更可靠的命令构建方式，确保中文路径被正确处理
        # 在Linux上，ImageMagick 7+ 也使用 magick 命令，而不是 convert
        if platform.system() == 'Windows':
            cmd = [
                'magick', img_path,
                '-quality', str(quality),
                '-interlace', 'Plane',  # 渐进式JPEG
                '-sampling-factor', '4:2:0',  # 色度抽样
                '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                img_path
            ]
        else:
            # 检查系统上可用的ImageMagick命令
            try:
                # 先尝试magick命令（ImageMagick 7+）
                subprocess.run(['magick', '--version'], capture_output=True, text=True, timeout=5)
                cmd = [
                    'magick', img_path,
                    '-quality', str(quality),
                    '-interlace', 'Plane',  # 渐进式JPEG
                    '-sampling-factor', '4:2:0',  # 色度抽样
                    '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                    img_path
                ]
            except:
                # 回退到convert命令（ImageMagick 6）
                cmd = [
                    'convert', img_path,
                    '-quality', str(quality),
                    '-interlace', 'Plane',  # 渐进式JPEG
                    '-sampling-factor', '4:2:0',  # 色度抽样
                    '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                    img_path
                ]
        
        # 执行命令
        logger.info(f"使用ImageMagick压缩图片: {img_path}, 质量: {quality}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"使用ImageMagick压缩图片失败: {img_path}, 错误: {result.stderr}")
            return False
        
        logger.info(f"压缩完成: {img_path}")
        return True
    except Exception as e:
        logger.error(f"压缩图片失败: {img_path}, 错误: {e}")
        return False

# 压缩图片的统一入口函数
def compress_image(img_path, quality):
    """
    压缩图片的统一入口函数
    - Linux平台：使用专门的压缩工具（jpegoptim/pngquant/cwebp）
    - Windows平台：使用ImageMagick
    - 保留EXIF元数据
    
    Args:
        img_path (str): 图片文件路径
        quality (int): 压缩质量，1-100，数值越高质量越好，文件越大
        
    Returns:
        bool: 压缩成功返回True，失败返回False
    """
    logger.info(f"开始压缩图片，路径: {img_path}, 质量: {quality}")
    
    # 获取文件扩展名
    ext = os.path.splitext(img_path)[1].lower()[1:]
    logger.debug(f"图片格式: {ext}")
    
    # 检查是否为支持的格式
    if ext not in ['jpg', 'jpeg', 'png', 'webp']:
        logger.info(f"不支持的格式，无法压缩: {ext}")
        return False
    
    # Linux平台优先使用专门的压缩工具
    if platform.system() != 'Windows':
        try:
            # 检查是否安装了相应的压缩工具
            tool_available = False
            if ext in ['jpg', 'jpeg']:
                tool_available = JPEGOPTIM_AVAILABLE
            elif ext == 'png':
                tool_available = PNGQUANT_AVAILABLE
            elif ext == 'webp':
                tool_available = CWEBP_AVAILABLE
            
            # 如果工具可用，使用专门的压缩工具
            if tool_available:
                logger.debug(f"使用专门工具压缩图片，格式: {ext}")
                result = compress_image_with_special_tools(img_path, quality)
                logger.info(f"专门工具压缩结果: {'成功' if result else '失败'}")
                return result
            else:
                # 工具不可用，记录日志并回退到ImageMagick
                tool_name = 'jpegoptim' if ext in ['jpg', 'jpeg'] else 'pngquant' if ext == 'png' else 'cwebp'
                logger.warning(f"{tool_name}不可用，回退到ImageMagick")
        except Exception as e:
            logger.warning(f"专门的压缩工具不可用，回退到ImageMagick: {e}")
    
    # Windows平台或专门工具不可用时，使用ImageMagick
    logger.debug(f"使用ImageMagick压缩图片")
    result = compress_image_with_imagemagick(img_path, quality)
    logger.info(f"ImageMagick压缩结果: {'成功' if result else '失败'}")
    return result

# 使用ImageMagick转换图片格式
def convert_image_with_imagemagick(img_path, target_format, quality):
    """
    使用ImageMagick转换图片格式
    
    Args:
        img_path (str): 图片文件路径
        target_format (str): 目标格式，如'jpg'、'png'、'webp'等
        quality (int): 转换质量，1-100，数值越高质量越好，文件越大
        
    Returns:
        tuple: (success, output_path)
            success (bool): 转换成功返回True，失败返回False
            output_path (str): 转换后的文件路径，如果是PDF文件转换则返回原路径
        
    说明：
        - 支持普通图片格式转换和PDF文件转图片
        - 对于PDF文件，使用pdf2image库处理，支持多页转换
        - 普通图片转换时，生成新的文件名，保留原文件名但更改扩展名
        - 检查转换后的文件是否已存在，如果存在则跳过
        - 对于目标格式为jpeg的情况，自动转换为jpg，保持一致性
        - 保留EXIF元数据
    """
    logger.info(f"开始转换图片，路径: {img_path}, 目标格式: {target_format}, 质量: {quality}")
    try:
        # 获取文件扩展名
        ext = os.path.splitext(img_path)[1].lower()[1:]
        
        # 生成新文件名
        dirname = os.path.dirname(img_path)
        basename = os.path.basename(img_path).split('.')[0]
        
        # 如果是PDF文件，需要特殊处理
        if ext == 'pdf':
            # PDF文件转图片，支持多页，使用pdf2image库
            logger.info(f"PDF文件转图片: {img_path}")
            
            try:
                # 使用pdf2image转换PDF为图片列表
                logger.info(f"开始使用pdf2image转换PDF: {img_path}")
                images = convert_from_path(img_path, dpi=300, fmt=target_format.lower(), thread_count=1)
                logger.info(f"PDF转换完成，共 {len(images)} 页")
                
                # 处理转换后的图片
                for i, img in enumerate(images):
                    # 生成带序号的输出文件名
                    output_filename = os.path.join(dirname, f"{basename}-{i+1:03d}.{target_format}")
                    # 检查文件是否已存在
                    if os.path.exists(output_filename):
                        logger.info(f"文件已存在，跳过: {output_filename}")
                        with progress_lock:
                            progress_data['skipped_files'].append(output_filename)
                        continue
                    # 保存图片
                    img.save(output_filename, quality=quality)
                    logger.info(f"保存图片: {output_filename}")
                
                logger.info(f"PDF转图片完成: {img_path}")
                return True, img_path  # 返回原路径，因为PDF转换会生成多个文件
            except Exception as e:
                logger.error(f"PDF转图片失败: {img_path}, 错误: {e}")
                logger.error(f"异常详情: {traceback.format_exc()}")
                return False, ""
        else:
            # 普通图片转换
            # 处理目标格式，将jpeg转换为jpg，保持一致性
            normalized_target = 'jpg' if target_format.lower() == 'jpeg' else target_format.lower()
            new_path = os.path.join(dirname, f"{basename}.{normalized_target}")
            logger.debug(f"原始文件路径: {img_path}")
            logger.debug(f"转换后文件路径: {new_path}")
            
            # 检查转换后的文件是否已存在，如果存在则跳过
            if os.path.exists(new_path):
                logger.info(f"转换后的文件已存在，跳过: {new_path}")
                with progress_lock:
                    progress_data['skipped_files'].append(new_path)
                return True, new_path
            
            # 使用更可靠的命令构建方式，确保中文路径被正确处理
            # 在Linux上，ImageMagick 7+ 也使用 magick 命令，而不是 convert
            if platform.system() == 'Windows':
                cmd = [
                    'magick', img_path,
                    '-quality', str(quality),
                    # 移除-strip，保留元数据
                    '-interlace', 'Plane',  # 渐进式JPEG
                    '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                    new_path
                ]
            else:
                # 检查系统上可用的ImageMagick命令
                try:
                    # 先尝试magick命令（ImageMagick 7+）
                    subprocess.run(['magick', '--version'], capture_output=True, text=True, timeout=5)
                    cmd = [
                        'magick', img_path,
                        '-quality', str(quality),
                        '-interlace', 'Plane',  # 渐进式JPEG
                        '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                        new_path
                    ]
                except:
                    # 回退到convert命令（ImageMagick 6）
                    cmd = [
                        'convert', img_path,
                        '-quality', str(quality),
                        '-interlace', 'Plane',  # 渐进式JPEG
                        '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                        new_path
                    ]
            
            # 执行命令
            logger.debug(f"执行转换命令: {cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"转换图片失败: {img_path}, 错误: {result.stderr}")
                return False, ""
            
            logger.info(f"转换完成: {img_path} -> {new_path}")
            return True, new_path
    except Exception as e:
        logger.error(f"转换图片失败: {img_path}, 错误: {e}")
        return False, ""

# 获取文件大小
def get_file_size(filepath):
    """
    获取文件大小
    
    Args:
        filepath (str): 文件路径
        
    Returns:
        int: 文件大小，单位为字节
    """
    return os.path.getsize(filepath)

# 遍历目录获取所有图片文件
def get_all_images(directory, exclude_formats=None):
    """
    遍历目录获取所有图片文件，支持排除指定格式
    
    Args:
        directory (str): 要遍历的目录路径
        exclude_formats (list, optional): 要排除的图片格式列表，默认为None
        
    Returns:
        list: 图片文件路径列表
        
    说明：
        - 使用os.walk遍历目录及其子目录
        - 只返回支持的图片格式文件
        - 支持通过exclude_formats参数排除指定格式
        - 排除格式时使用小写扩展名比较，确保大小写不敏感
    """
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
    请求参数: 
        path - 要获取文件的路径，默认为BASE_DIR
        auto_enter - 是否自动进入子文件夹，默认为true
    返回: JSON格式的文件列表和当前路径
    如果路径下只有一个文件夹且auto_enter为true，自动进入该文件夹，直到满足终止条件
    """
    path = request.form.get('path', BASE_DIR)
    auto_enter = request.form.get('auto_enter', 'true').lower() == 'true'
    logger.info(f"获取文件列表，路径: {path}, auto_enter: {auto_enter}")
    
    # 确保路径在BASE_DIR下，防止目录遍历攻击
    if not os.path.normpath(path).startswith(os.path.normpath(BASE_DIR)):
        logger.warning(f"路径 {path} 不在BASE_DIR下，使用默认路径: {BASE_DIR}")
        path = BASE_DIR
    
    # 自动进入子文件夹逻辑
    if auto_enter:
        max_depth = 10  # 防止无限递归
        current_depth = 0
        
        while current_depth < max_depth:
            try:
                # 获取当前目录下的所有项目
                items = os.listdir(path)
                dir_count = 0
                file_count = 0
                single_dir_path = None
                
                # 统计目录和文件数量
                for item in items:
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        dir_count += 1
                        single_dir_path = item_path
                    elif is_image_file(item):
                        file_count += 1
                
                # 如果只有一个目录且没有文件，自动进入该目录
                if dir_count == 1 and file_count == 0:
                    logger.info(f"自动进入子文件夹: {single_dir_path}")
                    path = single_dir_path
                    current_depth += 1
                else:
                    # 满足终止条件，退出循环
                    break
            except Exception as e:
                logger.error(f"自动进入子文件夹失败: {e}")
                break
    
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
        logger.info(f"成功获取 {len(files)} 个文件/文件夹，当前路径: {path}")
        
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
        return jsonify({'error': f'无效的图片文件: {path}'}), 400
    
    # 获取文件扩展名
    ext = os.path.splitext(path)[1].lower()[1:]
    
    # 处理PDF文件
    if ext == 'pdf':
        try:
            size = get_file_size(path)
            logger.info(f"成功获取PDF文件信息: PDF, {size} bytes")
            
            return jsonify({
                'path': path,
                'width': 0,  # PDF文件不返回宽高
                'height': 0,  # PDF文件不返回宽高
                'format': 'PDF',
                'size': size
            })
        except Exception as e:
            logger.error(f"获取PDF文件信息失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    # 处理AVIF格式文件（使用ImageMagick获取信息）
    if ext == 'avif':
        try:
            size = get_file_size(path)
            logger.info(f"成功获取AVIF文件大小: AVIF, {size} bytes")
            
            # 使用ImageMagick获取AVIF图片宽高
            try:
                # 构建命令
                if platform.system() == 'Windows':
                    cmd = ['magick', 'identify', '-format', '%w %h', path]
                else:
                    # 先尝试magick命令（ImageMagick 7+）
                    try:
                        subprocess.run(['magick', '--version'], capture_output=True, text=True, timeout=5)
                        cmd = ['magick', 'identify', '-format', '%w %h', path]
                    except:
                        # ImageMagick 6使用identify命令
                        cmd = ['identify', '-format', '%w %h', path]
                
                # 执行命令
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                logger.debug(f"ImageMagick identify命令输出: {result.stdout}")
                
                if result.returncode == 0:
                    # 解析输出，格式为 "width height"
                    output = result.stdout.strip()
                    if output:
                        parts = output.split()
                        if len(parts) == 2:
                            width = int(parts[0])
                            height = int(parts[1])
                            logger.info(f"成功使用ImageMagick获取AVIF图片信息: AVIF, {width}x{height}, {size} bytes")
                            return jsonify({
                                'path': path,
                                'width': width,
                                'height': height,
                                'format': 'AVIF',
                                'size': size
                            })
            except Exception as magick_error:
                logger.warning(f"使用ImageMagick获取AVIF图片宽高失败: {magick_error}")
                # 如果获取宽高失败，返回基本信息
                logger.info(f"返回AVIF文件基本信息: AVIF, {size} bytes")
                return jsonify({
                    'path': path,
                    'width': 0,  # AVIF文件无法获取宽高
                    'height': 0,  # AVIF文件无法获取宽高
                    'format': 'AVIF',
                    'size': size
                })
        except Exception as e:
            logger.error(f"获取AVIF文件信息失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    # 获取图片信息
    try:
        # 尝试打开图片，如果是截断的图片，使用ImageFile.LOAD_TRUNCATED_IMAGES选项
        from PIL import ImageFile
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        with Image.open(path) as img:
            width, height = img.size
            format = img.format
            
            # 获取EXIF信息
            exif = {}
            if hasattr(img, '_getexif'):
                exif_data = img._getexif()
                if exif_data:
                    from PIL.ExifTags import TAGS, GPSTAGS
                    from fractions import Fraction
                    
                    # 导入EXIF字段名中英文映射字典
                    from exif_mapping import exif_field_map
                    # 导入EXIF标签类型和扩展值映射
                    from optimize_exif_parsing import EXIF_TAG_TYPES, extended_value_mappings
                    # 使用全局的地理编码库配置，避免在请求处理函数内部导入和初始化
                    
                    # 将EXIF标签ID转换为可读名称
                    for tag, value in exif_data.items():
                        # 只处理TAGS字典中已定义的标签，过滤掉未知标签
                        if tag in TAGS:
                            tag_name = TAGS.get(tag, tag)
                            # 确保tag_name始终是字符串类型
                            if isinstance(tag_name, int):
                                tag_name = str(tag_name)
                            
                            # 特殊处理GPSInfo，它是一个嵌套字典，包含多个GPS子标签
                            if tag_name == 'GPSInfo' and isinstance(value, dict):
                                # 遍历GPS子标签
                                for gps_tag, gps_value in value.items():
                                    # 处理GPS子标签，使用GPSTAGS字典
                                    if gps_tag in GPSTAGS:
                                        gps_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                                        if isinstance(gps_tag_name, int):
                                            gps_tag_name = str(gps_tag_name)
                                        
                                        # 转换不可序列化的类型
                                        gps_serializable_value = gps_value
                                        
                                        # 处理PIL的IFDRational和Fraction类型
                                        if hasattr(gps_value, 'numerator') and hasattr(gps_value, 'denominator'):
                                            # 转换为浮点数
                                            try:
                                                gps_serializable_value = float(gps_value)
                                            except:
                                                gps_serializable_value = f"{gps_value.numerator}/{gps_value.denominator}"
                                        # 处理元组类型（GPS坐标通常是元组）
                                        elif isinstance(gps_value, tuple):
                                            # 转换为列表
                                            gps_serializable_value = list(gps_value)
                                            # 递归转换列表中的元素
                                            for i, v in enumerate(gps_serializable_value):
                                                if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                                                    try:
                                                        gps_serializable_value[i] = float(v)
                                                    except:
                                                        gps_serializable_value[i] = f"{v.numerator}/{v.denominator}"
                                        # 处理字节类型
                                        elif isinstance(gps_value, bytes):
                                            # 尝试将字节转换为可读格式
                                            try:
                                                # 过滤掉不可打印的字符
                                                filtered_bytes = bytes([b for b in gps_value if 32 <= b <= 126])
                                                if filtered_bytes:
                                                    gps_serializable_value = filtered_bytes.decode('utf-8', errors='replace')
                                                else:
                                                    # 显示为十六进制
                                                    gps_serializable_value = f"0x{gps_value.hex()}"
                                            except:
                                                gps_serializable_value = f"0x{gps_value.hex()}"
                                        # 格式化GPS日期时间
                                        elif gps_tag_name == 'GPSDateStamp' and isinstance(gps_value, str):
                                            try:
                                                # 格式：YYYY:MM:DD
                                                gps_serializable_value = datetime.strptime(gps_value, '%Y:%m:%d').strftime('%Y-%m-%d')
                                            except:
                                                pass
                                        
                                        # 使用扩展的标签值映射优化GPS字段
                                        if gps_tag_name in extended_value_mappings:
                                            mapping = extended_value_mappings[gps_tag_name]
                                            # 检查gps_serializable_value是否可哈希，避免list等不可哈希类型导致错误
                                            if isinstance(gps_serializable_value, (int, float)):
                                                gps_serializable_value = mapping.get(int(gps_serializable_value), gps_serializable_value)
                                            elif isinstance(gps_serializable_value, (str, bytes, tuple)):
                                                # 只有可哈希类型才能作为字典键
                                                gps_serializable_value = mapping.get(gps_serializable_value, gps_serializable_value)
                                        
                                        # 只添加非空值
                                        is_empty = False
                                        if gps_serializable_value is None:
                                            is_empty = True
                                        elif isinstance(gps_serializable_value, str) and gps_serializable_value.strip() == '':
                                            is_empty = True
                                        elif isinstance(gps_serializable_value, bytes) and len(gps_serializable_value) == 0:
                                            is_empty = True
                                        elif isinstance(gps_serializable_value, (list, tuple)) and len(gps_serializable_value) == 0:
                                            is_empty = True
                                        
                                        if not is_empty:
                                            # 使用中文字段名，如果没有映射则使用原字段名
                                            chinese_gps_tag_name = exif_field_map.get(gps_tag_name, gps_tag_name)
                                            exif[chinese_gps_tag_name] = gps_serializable_value
                            # 处理其他标签
                            elif tag_name not in ['JPEGThumbnail', 'MakerNote']:
                                # 转换不可序列化的类型
                                serializable_value = value
                                
                                # 处理PIL的IFDRational和Fraction类型
                                if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                                    # 转换为浮点数
                                    try:
                                        serializable_value = float(value)
                                    except:
                                        serializable_value = f"{value.numerator}/{value.denominator}"
                                # 处理元组类型
                                elif isinstance(value, tuple):
                                    # 转换为列表
                                    serializable_value = list(value)
                                    # 递归转换列表中的元素
                                    for i, v in enumerate(serializable_value):
                                        if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                                            try:
                                                serializable_value[i] = float(v)
                                            except:
                                                serializable_value[i] = f"{v.numerator}/{v.denominator}"
                                # 处理字节类型
                                elif isinstance(value, bytes):
                                    # 尝试将字节转换为可读格式
                                    try:
                                        # 过滤掉不可打印的字符
                                        filtered_bytes = bytes([b for b in value if 32 <= b <= 126])
                                        if filtered_bytes:
                                            serializable_value = filtered_bytes.decode('utf-8', errors='replace')
                                        else:
                                            # 显示为十六进制
                                            serializable_value = f"0x{value.hex()}"
                                    except:
                                        serializable_value = f"0x{value.hex()}"
                                # 格式化日期时间
                                elif tag_name in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized'] and isinstance(value, str):
                                    try:
                                        # 尝试解析不同的日期时间格式
                                        if ':' in value and ' ' in value:
                                            # 格式：YYYY:MM:DD HH:MM:SS
                                            serializable_value = datetime.strptime(value, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                                        elif ':' in value and len(value) == 10:
                                            # 格式：YYYY:MM:DD
                                            serializable_value = datetime.strptime(value, '%Y:%m:%d').strftime('%Y-%m-%d')
                                        elif '-' in value and len(value) == 10:
                                            # 格式：YYYY-MM-DD
                                            serializable_value = datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d')
                                        elif ' ' not in value and len(value) == 8:
                                            # 格式：YYYYMMDD
                                            serializable_value = datetime.strptime(value, '%Y%m%d').strftime('%Y-%m-%d')
                                    except:
                                        pass
                                
                                # 优化特定字段的显示
                                if tag_name in ['ExposureTime', 'ExposureBiasValue']:
                                    # 优化曝光时间显示，转换为1/xxx秒格式
                                    if isinstance(serializable_value, float) and serializable_value > 0 and serializable_value < 1:
                                        try:
                                            serializable_value = f"1/{int(round(1/serializable_value))}秒"
                                        except:
                                            pass
                                # 使用扩展的标签值映射优化其他字段
                                elif tag_name in extended_value_mappings:
                                    mapping = extended_value_mappings[tag_name]
                                    # 检查serializable_value是否可哈希，避免list等不可哈希类型导致错误
                                    if isinstance(serializable_value, (int, float)):
                                        serializable_value = mapping.get(int(serializable_value), serializable_value)
                                    elif isinstance(serializable_value, (str, bytes, tuple)):
                                        # 只有可哈希类型才能作为字典键
                                        serializable_value = mapping.get(serializable_value, serializable_value)
                                
                                # 只添加非空值
                                is_empty = False
                                if serializable_value is None:
                                    is_empty = True
                                elif isinstance(serializable_value, str) and serializable_value.strip() == '':
                                    is_empty = True
                                elif isinstance(serializable_value, bytes) and len(serializable_value) == 0:
                                    is_empty = True
                                elif isinstance(serializable_value, (list, tuple)) and len(serializable_value) == 0:
                                    is_empty = True
                                
                                if not is_empty:
                                    # 使用中文字段名，如果没有映射则使用原字段名
                                    chinese_tag_name = exif_field_map.get(tag_name, tag_name)
                                    exif[chinese_tag_name] = serializable_value
                    
                    # 解析GPS经纬度为地址
                    gps_latitude = None
                    gps_longitude = None
                    gps_latitude_ref = None
                    gps_longitude_ref = None
                    
                    # 获取GPS经纬度信息
                    for tag_name, value in exif.items():
                        logger.debug(f"EXIF字段: {tag_name} = {value}")
                        if tag_name == 'GPS纬度':
                            gps_latitude = value
                        elif tag_name == 'GPS经度':
                            gps_longitude = value
                        elif tag_name == 'GPS纬度参考':
                            gps_latitude_ref = value
                        elif tag_name == 'GPS经度参考':
                            gps_longitude_ref = value
                    
                    # 如果有完整的GPS信息，解析为地址
                    if gps_latitude and gps_longitude and gps_latitude_ref and gps_longitude_ref:
                        try:
                            # 转换GPS坐标格式：度分秒元组 -> 十进制度数
                            def convert_gps_coordinate(coordinate, ref):
                                decimal_degrees = 0.0
                                
                                # 处理GPS坐标，通常是 (度, 分, 秒) 的元组，每个元素是IFDRational类型
                                if isinstance(coordinate, (list, tuple)) and len(coordinate) >= 3:
                                    # 转换度、分、秒为浮点数
                                    degrees = float(coordinate[0]) if hasattr(coordinate[0], 'numerator') and hasattr(coordinate[0], 'denominator') else float(coordinate[0])
                                    minutes = float(coordinate[1]) if hasattr(coordinate[1], 'numerator') and hasattr(coordinate[1], 'denominator') else float(coordinate[1])
                                    seconds = float(coordinate[2]) if hasattr(coordinate[2], 'numerator') and hasattr(coordinate[2], 'denominator') else float(coordinate[2])
                                    
                                    # 计算十进制度数
                                    decimal_degrees = degrees + minutes/60 + seconds/3600
                                elif isinstance(coordinate, (int, float)):
                                    decimal_degrees = float(coordinate)
                                
                                # 根据参考方向调整符号
                                if ref in ['S', 'W']:
                                    decimal_degrees = -decimal_degrees
                                
                                return decimal_degrees
                            
                            # 转换为十进制度数
                            logger.debug(f"GPS纬度: {gps_latitude}, 参考: {gps_latitude_ref}")
                            logger.debug(f"GPS经度: {gps_longitude}, 参考: {gps_longitude_ref}")
                            
                            lat = convert_gps_coordinate(gps_latitude, gps_latitude_ref)
                            lon = convert_gps_coordinate(gps_longitude, gps_longitude_ref)
                            
                            logger.debug(f"转换后的坐标: 纬度={lat}, 经度={lon}")
                            
                            address = f"坐标: {lat:.6f}, {lon:.6f}"
                            exif['拍摄地址'] = address
                            logger.info(f"显示原始GPS坐标: {address}")
                        except Exception as e:
                            logger.error(f"解析GPS地址失败: {e}", exc_info=True)
                    
        size = get_file_size(path)
        logger.info(f"成功获取图片信息: {width}x{height}, {format}, {size} bytes, EXIF字段: {len(exif)}")
        
        return jsonify({
            'path': path,
            'width': width,
            'height': height,
            'format': format,
            'size': size,
            'exif': exif
        })
    except Exception as e:
        logger.error(f"获取图片信息失败: {e}")
        return jsonify({'error': f'获取图片信息失败: {e}'}), 500

@app.route('/preview/<path:filepath>')
def preview_file(filepath):
    """
    预览图片或PDF文件
    请求方法: GET
    请求参数: filepath - 图片或PDF文件相对路径
    返回: 图片文件内容或PDF第一页的图像
    """
    logger.info(f"预览文件，相对路径: {filepath}")
    
    # 构建完整路径
    # 情况1: 如果filepath是绝对路径（包含:），直接使用
    if ':' in filepath:
        full_path = filepath
    # 情况2: 否则，结合BASE_DIR构建绝对路径
    else:
        # 使用os.path.join自动处理不同平台的路径分隔符
        full_path = os.path.normpath(os.path.join(BASE_DIR, filepath.replace('/', os.sep)))
    
    logger.info(f"生成完整路径: {full_path}")
    logger.debug(f"BASE_DIR: {BASE_DIR}")
    
    # 验证文件
    if not os.path.isfile(full_path):
        logger.warning(f"文件不存在: {full_path}")
        return 'File not found', 404
    if not is_image_file(full_path):
        logger.warning(f"不是支持的文件类型: {full_path}")
        return 'File not found', 404
    
    # 检查文件扩展名
    ext = os.path.splitext(full_path)[1].lower()[1:]
    
    # 只处理普通图片文件，PDF文件由前端直接下载
    logger.info(f"返回图片文件: {full_path}")
    logger.debug(f"文件存在: {os.path.exists(full_path)}")
    logger.debug(f"文件大小: {os.path.getsize(full_path)} bytes")
    logger.debug(f"文件类型: {mimetypes.guess_type(full_path)[0]}")
    
    # 处理AVIF格式文件（只使用ImageMagick获取宽高，不转换）
    if ext == 'avif':
        try:
            # 使用ImageMagick获取AVIF图片宽高信息
            logger.info(f"开始使用ImageMagick获取AVIF宽高: {full_path}")
            
            # 构建命令
            if platform.system() == 'Windows':
                magick_cmd = 'magick'
            else:
                # 先尝试magick命令（ImageMagick 7+）
                try:
                    subprocess.run(['magick', '--version'], capture_output=True, text=True, timeout=5)
                    magick_cmd = 'magick'
                except:
                    # ImageMagick 6使用convert命令
                    magick_cmd = 'convert'
            
            # 获取图片宽高
            identify_cmd = [magick_cmd, 'identify', '-format', '%w %h', full_path]
            result = subprocess.run(identify_cmd, capture_output=True, text=True, timeout=10)
            
            width = 0
            height = 0
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    parts = output.split()
                    if len(parts) == 2:
                        width = int(parts[0])
                        height = int(parts[1])
            
            logger.info(f"成功获取AVIF图片宽高: {width}x{height}")
            
            # 直接返回原始AVIF文件，不进行转换
            response = send_file(full_path)
            logger.debug(f"send_file返回成功，响应头: {dict(response.headers)}")
            return response
        except Exception as e:
            logger.error(f"处理AVIF文件失败: {type(e).__name__}: {str(e)}")
            return f'Image preview failed: {str(e)}', 500
    
    try:
        # 尝试打开图片，如果是截断的图片，使用ImageFile.LOAD_TRUNCATED_IMAGES选项
        from PIL import ImageFile
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        # 打开图片，检查分辨率
        with Image.open(full_path) as img:
            width, height = img.size
            logger.info(f"图片原始分辨率: {width}x{height}")
            
            # 如果图片分辨率超过1920x1080，调整大小
            if width > 1920 or height > 1080:
                logger.info(f"图片分辨率超过1920x1080，需要调整大小")
                
                # 计算调整后的尺寸，保持原始比例
                ratio = min(1920/width, 1080/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                logger.info(f"调整后分辨率: {new_width}x{new_height}")
                
                # 调整图片大小
                resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # 将调整后的图片保存到内存缓冲区
                buffer = io.BytesIO()
                
                # 根据原图格式选择保存格式
                if ext in ['png', 'gif']:
                    # PNG和GIF保持原格式
                    resized_img.save(buffer, format=ext)
                else:
                    # 其他格式保存为JPEG
                    resized_img.save(buffer, format='JPEG', quality=90)
                
                buffer.seek(0)
                
                # 返回调整后的图片
                response = send_file(buffer, mimetype=mimetypes.guess_type(full_path)[0])
                logger.debug(f"send_file返回成功，响应头: {dict(response.headers)}")
                return response
            else:
                # 图片分辨率符合要求，直接返回原图
                response = send_file(full_path)
                logger.debug(f"send_file返回成功，响应头: {dict(response.headers)}")
                return response
    except Exception as e:
        logger.error(f"处理图片失败: {type(e).__name__}: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
        # 尝试直接返回原图，即使处理失败
        try:
            response = send_file(full_path)
            logger.debug(f"send_file返回成功，响应头: {dict(response.headers)}")
            return response
        except:
            return f'Image preview failed: {str(e)}', 500



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
    
    # 检查文件扩展名，确保是TIFF文件
    ext = os.path.splitext(full_path)[1].lower()[1:]
    if ext not in ['tiff', 'tif']:
        logger.warning(f"只有TIFF文件支持预览转换: {full_path}")
        return 'Only TIFF files are supported for preview conversion', 400
    
    try:
        # 尝试打开图片，如果是截断的图片，使用ImageFile.LOAD_TRUNCATED_IMAGES选项
        from PIL import ImageFile
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        # 打开TIFF图片并转换为PNG
        logger.info(f"开始转换TIFF图片: {full_path}")
        
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
            response = send_file(buffer, mimetype='image/png')
            logger.debug(f"send_file返回成功，响应头: {dict(response.headers)}")
            return response
    except Exception as e:
        logger.error(f"转换TIFF图片失败: {type(e).__name__}: {str(e)}")
        logger.error(f"异常详情: {traceback.format_exc()}")
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
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
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
                        # 获取文件扩展名（区分大小写）
                        ext = os.path.splitext(file)[1][1:]  # [1:] 移除点号，保持原始大小写
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
                # 获取文件扩展名（区分大小写）
                ext = os.path.splitext(filename)[1][1:]  # [1:] 移除点号，保持原始大小写
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
        return jsonify({'error': '统计文件格式失败: {e}'}), 500

@app.route('/fix_extensions', methods=['POST'])
def fix_extensions():
    """
    修复文件后缀，将大写扩展名改为小写，并将jpeg改为jpg
    请求方法: POST
    请求参数: selected_paths - 要修复的文件或文件夹路径列表
    返回: JSON格式的修复结果，包括处理的文件数量
    说明: 支持所有文件类型，跳过隐藏文件
    """
    selected_paths = request.json.get('selected_paths', [])
    logger.info(f"开始修复文件后缀，选中路径: {selected_paths}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
    processed = 0  # 处理的文件数量
    skipped_files = []  # 跳过的文件列表
    failed_files = []  # 失败的文件列表
    
    try:
        for path in selected_paths:
            if os.path.isdir(path):
                logger.info(f"修复目录: {path}")
                # 遍历目录，处理所有文件
                for root, dirs, files in os.walk(path):
                    for file in files:
                        # 跳过隐藏文件
                        if file.startswith('.'):
                            continue
                        
                        try:
                            # 获取文件扩展名，确保使用正确的分割方法
                            name_without_ext, ext = os.path.splitext(file)
                            # 标准化扩展名
                            ext_lower = ext.lower()
                            # 检查是否需要修复：1) 包含大写 2) 是jpeg
                            needs_fix = any(c.isupper() for c in ext[1:]) or ext_lower == '.jpeg'
                            
                            if needs_fix:
                                old_path = os.path.join(root, file)
                                # 生成新扩展名：如果是jpeg则改为jpg，否则保留原扩展名的小写
                                new_ext = '.jpg' if ext_lower == '.jpeg' else ext_lower
                                # 生成新文件名
                                new_name = f"{name_without_ext}{new_ext}"
                                new_path = os.path.join(root, new_name)
                                # 检查新文件名是否已存在
                                if os.path.exists(new_path):
                                    logger.info(f"文件已存在，跳过: {new_path}")
                                    skipped_files.append(old_path)
                                    continue
                                # 重命名文件
                                os.rename(old_path, new_path)
                                logger.info(f"重命名文件: {old_path} -> {new_path}")
                                processed += 1
                        except Exception as e:
                            # 记录失败的文件
                            failed_file = os.path.join(root, file)
                            failed_files.append({'path': failed_file, 'error': str(e)})
                            logger.error(f"处理文件失败: {failed_file}, 错误: {e}")
            elif os.path.isfile(path):
                try:
                    logger.info(f"修复文件: {path}")
                    # 获取文件扩展名
                    filename = os.path.basename(path)
                    # 跳过隐藏文件
                    if filename.startswith('.'):
                        continue
                    # 获取文件扩展名
                    name_without_ext, ext = os.path.splitext(filename)
                    # 标准化扩展名
                    ext_lower = ext.lower()
                    # 检查是否需要修复：1) 包含大写 2) 是jpeg
                    needs_fix = any(c.isupper() for c in ext[1:]) or ext_lower == '.jpeg'
                    
                    if needs_fix:
                        # 生成新扩展名：如果是jpeg则改为jpg，否则保留原扩展名的小写
                        new_ext = '.jpg' if ext_lower == '.jpeg' else ext_lower
                        # 生成新文件名
                        new_name = f"{name_without_ext}{new_ext}"
                        dirname = os.path.dirname(path)
                        new_path = os.path.join(dirname, new_name)
                        # 检查新文件名是否已存在
                        if os.path.exists(new_path):
                            logger.info(f"文件已存在，跳过: {new_path}")
                            skipped_files.append(path)
                            continue
                        # 重命名文件
                        os.rename(path, new_path)
                        logger.info(f"重命名文件: {path} -> {new_path}")
                        processed += 1
                except Exception as e:
                    # 记录失败的文件
                    failed_files.append({'path': path, 'error': str(e)})
                    logger.error(f"处理文件失败: {path}, 错误: {e}")
        
        logger.info(f"修复完成，共处理 {processed} 个文件，跳过 {len(skipped_files)} 个文件，失败 {len(failed_files)} 个文件")
        return jsonify({
            'processed': processed,
            'skipped_files': skipped_files,
            'failed_files': failed_files
        })
    except Exception as e:
        logger.error(f"修复文件后缀失败: {e}")
        return jsonify({'error': '修复文件后缀失败: {e}'}), 500

@app.route('/search_files', methods=['POST'])
def search_files():
    """
    搜索文件
    请求方法: POST
    请求参数: selected_paths - 要搜索的文件或文件夹路径列表，pattern - 搜索模式，is_regex - 是否使用正则表达式，case_sensitive - 是否区分大小写
    返回: JSON格式的结果，包括匹配的文件列表
    """
    selected_paths = request.json.get('selected_paths', [])
    pattern = request.json.get('pattern', '')
    is_regex = request.json.get('is_regex', False)
    case_sensitive = request.json.get('case_sensitive', False)
    logger.info(f"开始搜索文件，选中路径: {selected_paths}，模式: {pattern}，正则: {is_regex}，区分大小写: {case_sensitive}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
    if not pattern:
        logger.warning("未指定搜索模式")
        return jsonify({'error': '未指定搜索模式'}), 400
    
    import re
    
    # 编译正则表达式
    try:
        if is_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        else:
            # 普通搜索，转义正则表达式特殊字符
            escaped_pattern = re.escape(pattern)
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(escaped_pattern, flags)
    except re.error as e:
        logger.error(f"正则表达式错误: {e}")
        return jsonify({'error': f'正则表达式错误: {e}'}), 400
    
    matched_files = []
    
    # 遍历所有选中的路径
    for path in selected_paths:
        if os.path.isdir(path):
            # 遍历目录中的所有文件
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 检查文件名是否匹配
                    if regex.search(file):
                        try:
                            # 获取文件大小
                            size = os.path.getsize(file_path)
                            # 获取文件扩展名
                            ext = os.path.splitext(file)[1].lstrip('.') or 'unknown'
                            matched_files.append({
                                "name": file,
                                "path": file_path,
                                "size": size,
                                "ext": ext
                            })
                        except Exception as e:
                            logger.error(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
        elif os.path.isfile(path):
            # 检查单个文件是否匹配
            file = os.path.basename(path)
            if regex.search(file):
                try:
                    # 获取文件大小
                    size = os.path.getsize(path)
                    # 获取文件扩展名
                    ext = os.path.splitext(file)[1].lstrip('.') or 'unknown'
                    matched_files.append({
                        "name": file,
                        "path": path,
                        "size": size,
                        "ext": ext
                    })
                except Exception as e:
                    logger.error(f"获取文件信息失败: {path}, 错误: {str(e)}")
    
    logger.info(f"搜索完成，找到 {len(matched_files)} 个匹配文件")
    return jsonify({"success": True, "files": matched_files})

@app.route('/delete_file', methods=['POST'])
def delete_file():
    """
    删除单个文件
    请求方法: POST
    请求参数: path - 要删除的文件路径
    返回: JSON格式的结果，包括删除是否成功
    """
    file_path = request.json.get('path', '')
    logger.info(f"开始删除单个文件: {file_path}")
    
    if not file_path:
        logger.warning("未指定要删除的文件路径")
        return jsonify({'error': '未指定要删除的文件路径'}), 400
    
    if not os.path.exists(file_path):
        logger.warning(f"文件不存在: {file_path}")
        return jsonify({'error': '文件不存在'}), 404
    
    if not os.path.isfile(file_path):
        logger.warning(f"指定路径不是文件: {file_path}")
        return jsonify({'error': '指定路径不是文件'}), 400
    
    try:
        os.remove(file_path)
        logger.info(f"已成功删除文件: {file_path}")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@app.route('/delete_files_by_format', methods=['POST'])
def delete_files_by_format():
    """
    根据文件格式删除文件
    请求方法: POST
    请求参数: selected_paths - 要处理的文件或文件夹路径列表，format - 要删除的文件格式
    返回: JSON格式的结果，包括删除的文件数量
    """
    selected_paths = request.json.get('selected_paths', [])
    format = request.json.get('format', '')
    logger.info(f"开始删除指定格式文件，选中路径: {selected_paths}，格式: {format}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
    if not format:
        logger.warning("未指定要删除的文件格式")
        return jsonify({'error': '未指定要删除的文件格式'}), 400
    
    deleted_count = 0  # 删除的文件数
    
    try:
        for path in selected_paths:
            if os.path.isdir(path):
                logger.info(f"删除目录中的文件: {path}")
                # 遍历目录，删除所有指定格式的文件
                for root, dirs, files in os.walk(path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        # 跳过隐藏文件
                        if file.startswith('.'):
                            continue
                        
                        # 获取文件扩展名（区分大小写）
                        file_ext = os.path.splitext(file)[1][1:]  # [1:] 移除点号，保持原始大小写
                        # 如果文件没有扩展名，使用'no_extension'
                        if not file_ext:
                            file_ext = 'no_extension'
                        
                        # 检查文件格式是否匹配
                        if file_ext == format:
                            # 删除文件
                            os.remove(filepath)
                            deleted_count += 1
                            logger.info(f"删除文件: {filepath}")
            elif os.path.isfile(path):
                logger.info(f"检查文件: {path}")
                # 检查单个文件
                filename = os.path.basename(path)
                # 获取文件扩展名（区分大小写）
                file_ext = os.path.splitext(filename)[1][1:]  # [1:] 移除点号，保持原始大小写
                # 如果文件没有扩展名，使用'no_extension'
                if not file_ext:
                    file_ext = 'no_extension'
                
                # 检查文件格式是否匹配
                if file_ext == format:
                    # 删除文件
                    os.remove(path)
                    deleted_count += 1
                    logger.info(f"删除文件: {path}")
        
        logger.info(f"删除完成，共删除 {deleted_count} 个文件")
        return jsonify({'deleted_count': deleted_count})
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        return jsonify({'error': f'删除文件失败: {e}'}), 500

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
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
    # 检查ImageMagick是否可用
    if not IMAGEMAGICK_AVAILABLE:
        logger.error("ImageMagick不可用，无法压缩图片")
        return jsonify({'error': 'ImageMagick不可用'}), 500
    
    # 重置进度
    with progress_lock:
        progress_data = {
            'total': 0,
            'processed': 0,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'original_size': 0,
            'final_size': 0,
            'current_file': '',
            'failed_files': [],
            'skipped_files': []
        }
    
    # 获取所有图片文件
    all_images = []
    total_selected = 0
    for path in selected_paths:
        if os.path.isdir(path):
            logger.info(f"获取目录中的图片: {path}")
            dir_images = get_all_images(path)
            all_images.extend(dir_images)
            total_selected += len(dir_images)
        elif os.path.isfile(path) and is_image_file(path):
            logger.info(f"添加图片: {path}")
            all_images.append(path)
            total_selected += 1
    
    logger.info(f"共找到 {len(all_images)} 个图片文件")
    
    # 过滤小于指定大小的文件
    if min_size > 0:
        filtered_images = [img for img in all_images if get_file_size(img) > min_size]
        logger.info(f"过滤后剩余 {len(filtered_images)} 个图片文件")
        all_images = filtered_images
    
    with progress_lock:
        progress_data['total'] = len(all_images) or total_selected or 1
    
    # 如果没有图片需要处理，直接完成
    if len(all_images) == 0:
        logger.info("没有需要处理的图片，直接完成")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            # 确保进度条显示100%，使用实际选择的文件数
            progress_data['total'] = total_selected
            progress_data['processed'] = total_selected
        return jsonify({'status': 'started'})
    
    # 处理图片
    def process_image(img_path):
        """
        处理单个图片压缩
        """
        global progress_data
        try:
            # 检查是否需要停止处理
            with stop_lock:
                if stop_processing_flag:
                    logger.info(f"停止处理，跳过图片: {img_path}")
                    with progress_lock:
                        progress_data['processed'] += 1
                    return
            
            # 检查文件扩展名，如果是PDF则跳过压缩
            ext = os.path.splitext(img_path)[1].lower()[1:]
            if ext == 'pdf':
                logger.info(f"跳过PDF文件压缩: {img_path}")
                with progress_lock:
                    progress_data['processed'] += 1
                return
            
            logger.info(f"压缩图片: {img_path}")
            
            # 更新当前正在处理的图片路径
            with progress_lock:
                progress_data['current_file'] = img_path
            
            original_size = get_file_size(img_path)
            
            # 使用统一压缩函数（会自动选择合适的压缩工具）
            if compress_image(img_path, quality):
                final_size = get_file_size(img_path)
                logger.info(f"压缩完成: {img_path}, 原大小: {original_size} bytes, 新大小: {final_size} bytes")
                with progress_lock:
                    progress_data['processed'] += 1
                    progress_data['original_size'] += original_size
                    progress_data['final_size'] += final_size
            else:
                final_size = original_size
                logger.error(f"压缩失败: {img_path}")
                with progress_lock:
                    progress_data['processed'] += 1
                    progress_data['original_size'] += original_size
                    progress_data['final_size'] += final_size
                    progress_data['failed_files'].append(img_path)
        except Exception as e:
            logger.error(f"处理图片失败: {img_path}, 错误: {e}")
            with progress_lock:
                progress_data['processed'] += 1
    
    # 在新线程中处理图片，避免阻塞主线程
    def process_images_async():
        # 使用多线程处理
        logger.info(f"使用 {max_workers} 个线程开始处理图片")
        
        # 检查是否需要停止处理
        def should_stop():
            with stop_lock:
                return stop_processing_flag
        
        # 如果已经停止，直接返回
        if should_stop():
            logger.info("处理已停止，不再处理新图片")
            with progress_lock:
                progress_data['status'] = 'completed'
                progress_data['end_time'] = datetime.now().isoformat()
                progress_data['current_file'] = ''
            return
        
        # 使用concurrent.futures处理图片，并支持中途停止
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务并检查停止标记
            futures = []
            for path in all_images:
                # 检查是否需要停止处理
                if should_stop():
                    logger.info("收到停止请求，不再提交新任务")
                    break
                
                # 提交单个任务
                future = executor.submit(process_image, path)
                futures.append(future)
            
            # 等待所有已提交的任务完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"处理图片时发生异常: {e}")
        
        logger.info("图片处理完成或已停止")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            progress_data['current_file'] = ''
        
        # 重置停止标记
        with stop_lock:
            global stop_processing_flag
            stop_processing_flag = False
    
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
    skip_pdf = request.json.get('skip_pdf', False)
    
    logger.info(f"开始转换图片格式，选中路径: {selected_paths}, 目标格式: {target_format}, 质量: {quality}, 最大线程数: {max_workers}, 跳过PDF: {skip_pdf}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
    # 检查ImageMagick是否可用
    if not IMAGEMAGICK_AVAILABLE:
        logger.error("ImageMagick不可用，无法转换图片")
        return jsonify({'error': 'ImageMagick不可用'}), 500
    
    # 检查是否包含PDF文件且目标格式不是jpg
    has_pdf = False
    for path in selected_paths:
        if os.path.isfile(path) and path.lower().endswith('.pdf'):
            has_pdf = True
            break
        elif os.path.isdir(path):
            # 检查目录中是否包含PDF文件
            import glob
            pdf_files = glob.glob(os.path.join(path, '*.pdf'), recursive=True)
            if pdf_files:
                has_pdf = True
                break
    
    if has_pdf and target_format.lower() != 'jpg':
        if skip_pdf:
            logger.info(f"检测到PDF文件，目标格式不是jpg，已选择跳过PDF文件处理")
        else:
            logger.warning(f"PDF文件只能转换为jpg格式，请求的格式: {target_format}")
            return jsonify({'error': 'PDF文件只能转换为jpg格式'}), 400
    
    # 重置进度
    with progress_lock:
        progress_data = {
            'total': 0,
            'processed': 0,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'original_size': 0,
            'final_size': 0,
            'current_file': '',
            'failed_files': [],
            'skipped_files': []
        }
    
    # 获取所有图片文件，排除目标格式
    all_images = []
    total_selected = 0
    target_format_lower = target_format.lower()
    
    # 处理目标格式，将jpeg转换为jpg，保持一致性
    normalized_target = 'jpg' if target_format_lower == 'jpeg' else target_format_lower
    
    for path in selected_paths:
        if os.path.isdir(path):
            # 先获取所有图片文件（包括目标格式），用于统计总数
            all_files = get_all_images(path)
            total_selected += len(all_files)
            
            # 构建排除格式列表，包含jpg和jpeg如果目标是其中之一
            exclude_formats = [normalized_target]
            if normalized_target == 'jpg':
                exclude_formats.append('jpeg')
            
            logger.info(f"获取目录中的图片，排除目标格式: {normalized_target}, 路径: {path}")
            filtered_images = get_all_images(path, exclude_formats=exclude_formats)
            
            # 如果需要跳过PDF文件，过滤掉PDF文件
            if skip_pdf:
                filtered_images = [f for f in filtered_images if not f.lower().endswith('.pdf')]
                
                # 更新skipped_files列表，添加被跳过的PDF文件
                pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]
                with progress_lock:
                    for f in pdf_files:
                        progress_data['skipped_files'].append(f)
                        progress_data['processed'] += 1
            
            all_images.extend(filtered_images)
            
            # 将被跳过的文件添加到skipped_files列表
            skipped_files = [f for f in all_files if f not in filtered_images and not (skip_pdf and f.lower().endswith('.pdf'))]
            with progress_lock:
                for f in skipped_files:
                    progress_data['skipped_files'].append(f)
                    progress_data['processed'] += 1
        elif os.path.isfile(path) and is_image_file(path):
            total_selected += 1
            ext = os.path.basename(path).lower().split('.')[-1]
            
            # 规范化当前文件格式
            normalized_ext = 'jpg' if ext == 'jpeg' else ext
            
            # 如果是PDF文件且需要跳过，添加到skipped_files列表
            if skip_pdf and path.lower().endswith('.pdf'):
                logger.info(f"跳过PDF文件: {path}")
                with progress_lock:
                    progress_data['skipped_files'].append(path)
                    progress_data['processed'] += 1
            elif normalized_ext != normalized_target:
                logger.info(f"添加图片: {path}, 当前格式: {ext}, 目标格式: {normalized_target}")
                all_images.append(path)
            else:
                logger.info(f"跳过图片: {path}, 当前格式与目标格式相同: {ext} -> {normalized_target}")
                with progress_lock:
                    progress_data['skipped_files'].append(path)
                    progress_data['processed'] += 1
    
    logger.info(f"共找到 {len(all_images)} 个需要转换的图片文件，总选择文件数: {total_selected}")
    
    # 设置总文件数为实际选择的文件数
    with progress_lock:
        progress_data['total'] = total_selected
    
    # 如果没有图片需要处理，直接完成
    if len(all_images) == 0:
        logger.info("没有需要处理的图片，直接完成")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            # 确保进度条显示100%，使用实际选择的文件数
            progress_data['processed'] = total_selected
        return jsonify({'status': 'started'})
    
    # 处理图片
    def process_image(img_path):
        """
        处理单个图片转换
        """
        global progress_data
        try:
            # 检查是否需要停止处理
            with stop_lock:
                if stop_processing_flag:
                    logger.info(f"停止处理，跳过图片: {img_path}")
                    # 直接返回，不再处理新的图片
                    with progress_lock:
                        progress_data['processed'] += 1
                    return
            
            logger.info(f"转换图片: {img_path}")
            
            # 更新当前正在处理的图片路径
            with progress_lock:
                progress_data['current_file'] = img_path
            
            original_size = get_file_size(img_path)
            
            # 使用ImageMagick转换图片格式
            success, new_path = convert_image_with_imagemagick(img_path, target_format, quality)
            
            if success:
                # 获取文件扩展名
                ext = os.path.splitext(img_path)[1].lower()[1:]
                
                if ext == 'pdf':
                    # PDF文件转换，不删除原文件，因为会生成多个图片文件
                    logger.info(f"PDF转图片完成，保留原文件: {img_path}")
                    # 计算转换后所有图片的总大小
                    dirname = os.path.dirname(img_path)
                    basename = os.path.basename(img_path).split('.')[0]
                    # 查找所有生成的图片文件
                    import glob
                    output_files = glob.glob(os.path.join(dirname, f"{basename}-*.{target_format}"))
                    final_size = sum(get_file_size(f) for f in output_files)
                    logger.info(f"PDF转图片生成 {len(output_files)} 个文件，总大小: {final_size} bytes")
                    with progress_lock:
                        progress_data['processed'] += 1
                        progress_data['original_size'] += original_size
                        progress_data['final_size'] += final_size
                else:
                    if new_path != img_path:  # 只有当新路径和原路径不同时才删除原文件
                        # 检查转换后的文件是否是新创建的（不是跳过的）
                        if os.path.exists(new_path):
                            # 检查原文件是否与新文件不同
                            if os.path.abspath(new_path) != os.path.abspath(img_path):
                                # 删除原文件
                                os.remove(img_path)
                                final_size = get_file_size(new_path)
                                logger.info(f"转换完成: {img_path} -> {new_path}, 原大小: {original_size} bytes, 新大小: {final_size} bytes")
                                with progress_lock:
                                    progress_data['processed'] += 1
                                    progress_data['original_size'] += original_size
                                    progress_data['final_size'] += final_size
                            else:
                                final_size = original_size
                                logger.info(f"转换后的文件与原文件相同，跳过删除: {img_path}")
                                with progress_lock:
                                    progress_data['processed'] += 1
                                    progress_data['original_size'] += original_size
                                    progress_data['final_size'] += final_size
                                    progress_data['skipped_files'].append(img_path)
                        else:
                            final_size = original_size
                            logger.error(f"转换失败: {img_path}")
                            with progress_lock:
                                progress_data['processed'] += 1
                                progress_data['original_size'] += original_size
                                progress_data['final_size'] += final_size
                                progress_data['failed_files'].append(img_path)
                    else:
                        final_size = original_size
                        logger.info(f"转换后的文件与原文件路径相同，跳过: {img_path}")
                        with progress_lock:
                            progress_data['processed'] += 1
                            progress_data['original_size'] += original_size
                            progress_data['final_size'] += final_size
                            progress_data['skipped_files'].append(img_path)
            else:
                final_size = original_size
                logger.error(f"转换失败: {img_path}")
                with progress_lock:
                    progress_data['processed'] += 1
                    progress_data['original_size'] += original_size
                    progress_data['final_size'] += final_size
                    progress_data['failed_files'].append(img_path)
        except Exception as e:
            logger.error(f"处理图片失败: {img_path}, 错误: {e}")
            with progress_lock:
                progress_data['processed'] += 1
    
    # 在新线程中处理图片转换，避免阻塞主线程
    def process_images_async():
        # 使用多线程处理
        logger.info(f"使用 {max_workers} 个线程开始处理图片转换")
        
        # 检查是否需要停止处理
        def should_stop():
            with stop_lock:
                return stop_processing_flag
        
        # 如果已经停止，直接返回
        if should_stop():
            logger.info("处理已停止，不再处理新图片")
            with progress_lock:
                progress_data['status'] = 'completed'
                progress_data['end_time'] = datetime.now().isoformat()
                progress_data['current_file'] = ''
            return
        
        # 使用concurrent.futures处理图片，并支持中途停止
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务并检查停止标记
            futures = []
            for path in all_images:
                # 检查是否需要停止处理
                if should_stop():
                    logger.info("收到停止请求，不再提交新任务")
                    break
                
                # 提交单个任务
                future = executor.submit(process_image, path)
                futures.append(future)
            
            # 等待所有已提交的任务完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"处理图片时发生异常: {e}")
        
        logger.info("图片转换完成或已停止")
        with progress_lock:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            progress_data['current_file'] = ''
        
        # 重置停止标记
        with stop_lock:
            global stop_processing_flag
            stop_processing_flag = False
    
    # 启动异步处理
    thread = threading.Thread(target=process_images_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/get_progress')
def get_progress():
    with progress_lock:
        return jsonify(progress_data)

@app.route('/stop_processing', methods=['POST'])
def stop_processing():
    """
    停止当前正在进行的图片处理
    请求方法: POST
    返回: JSON格式的停止结果
    """
    global stop_processing_flag
    with stop_lock:
        stop_processing_flag = True
    logger.info("收到停止处理请求")
    return jsonify({'status': 'stopping'})

@app.route('/get_supported_formats')
def get_supported_formats():
    """
    返回支持的格式列表，将jpg和jpeg合并为一种格式
    """
    # 获取所有格式键，并转换为小写，确保大小写不敏感
    all_formats = [fmt.lower() for fmt in SUPPORTED_FORMATS.keys()]
    
    # 去重处理，将jpg和jpeg视为同一种格式，只保留jpg
    unique_formats = []
    seen = set()
    
    for fmt in all_formats:
        # 将jpeg转换为jpg，保持格式一致性
        normalized_fmt = 'jpg' if fmt == 'jpeg' else fmt
        if normalized_fmt not in seen:
            seen.add(normalized_fmt)
            unique_formats.append(normalized_fmt)
    
    return jsonify({'formats': unique_formats})

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
            'current_file': '',  # 当前正在处理的图片路径
            'failed_files': [],
            'skipped_files': []
        }
        logger.info("进度状态已重置为idle")
    return jsonify({'status': 'success'})

@app.route('/download', methods=['GET'])
def download_file():
    """
    下载文件
    请求方法: GET
    请求参数: path - 文件路径
    返回: 文件内容
    """
    file_path = request.args.get('path')
    logger.info(f"下载文件: {file_path}")
    
    if not file_path or not os.path.isfile(file_path):
        logger.warning(f"无效的文件路径: {file_path}")
        return 'Invalid file path', 400
    
    try:
        logger.info(f"返回文件: {file_path}")
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"下载文件失败: {type(e).__name__}: {str(e)}")
        return f'Download failed: {str(e)}', 500

@app.route('/clean_empty_folders', methods=['POST'])
def clean_empty_folders():
    """
    清理空文件夹
    请求方法: POST
    请求参数: selected_paths - 要清理的文件或文件夹路径列表
    返回: JSON格式的清理结果，包括删除的文件夹数量
    说明: 从最里层开始删除空文件夹，支持嵌套空文件夹清理
    """
    selected_paths = request.json.get('selected_paths', [])
    logger.info(f"开始清理空文件夹，选中路径: {selected_paths}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
    deleted_count = 0  # 删除的文件夹数量
    
    def clean_empty_dirs_recursive(directory):
        """
        递归清理空文件夹，从最里层开始
        """
        nonlocal deleted_count
        
        if not os.path.isdir(directory):
            return False
        
        # 先清理所有子文件夹
        subdirs = [os.path.join(directory, d) for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
        for subdir in subdirs:
            clean_empty_dirs_recursive(subdir)
        
        # 检查当前文件夹是否为空
        try:
            files = os.listdir(directory)
            if not files:  # 空文件夹
                os.rmdir(directory)
                logger.info(f"删除空文件夹: {directory}")
                deleted_count += 1
                return True
            return False
        except Exception as e:
            logger.error(f"检查或删除文件夹失败: {directory}, 错误: {e}")
            return False
    
    try:
        for path in selected_paths:
            if os.path.isdir(path):
                logger.info(f"清理目录下的空文件夹: {path}")
                clean_empty_dirs_recursive(path)
            elif os.path.isfile(path):
                # 如果是文件，跳过
                logger.info(f"跳过文件: {path}")
                continue
        
        logger.info(f"清理空文件夹完成，共删除 {deleted_count} 个空文件夹")
        return jsonify({'deleted_count': deleted_count})
    except Exception as e:
        logger.error(f"清理空文件夹失败: {e}")
        return jsonify({'error': f'清理空文件夹失败: {e}'}), 500

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