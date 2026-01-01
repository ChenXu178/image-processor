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

# 检查ImageMagick是否可用
IMAGEMAGICK_AVAILABLE = check_imagemagick()

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

# 检查文件是否为图片
def is_image_file(filename):
    # 使用os.path.splitext获取扩展名，更可靠的方法
    ext = os.path.splitext(filename)[1].lower()[1:]  # [1:] 移除点号
    return ext in SUPPORTED_FORMATS

# 使用ImageMagick压缩图片
def compress_image_with_imagemagick(img_path, quality):
    """
    使用ImageMagick压缩图片
    """
    try:
        # 使用更可靠的命令构建方式，确保中文路径被正确处理
        # 在Linux上，ImageMagick 7+ 也使用 magick 命令，而不是 convert
        if platform.system() == 'Windows':
            cmd = [
                'magick', img_path,
                '-quality', str(quality),
                '-strip',  # 移除元数据
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
                    '-strip',  # 移除元数据
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
                    '-strip',  # 移除元数据
                    '-interlace', 'Plane',  # 渐进式JPEG
                    '-sampling-factor', '4:2:0',  # 色度抽样
                    '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                    img_path
                ]
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"压缩图片失败: {img_path}, 错误: {result.stderr}")
            return False
        
        logger.info(f"压缩完成: {img_path}")
        return True
    except Exception as e:
        logger.error(f"压缩图片失败: {img_path}, 错误: {e}")
        return False

# 使用ImageMagick转换图片格式
def convert_image_with_imagemagick(img_path, target_format, quality):
    """
    使用ImageMagick转换图片格式
    """
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
                    '-strip',  # 移除元数据
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
                        '-strip',  # 移除元数据
                        '-interlace', 'Plane',  # 渐进式JPEG
                        '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                        new_path
                    ]
                except:
                    # 回退到convert命令（ImageMagick 6）
                    cmd = [
                        'convert', img_path,
                        '-quality', str(quality),
                        '-strip',  # 移除元数据
                        '-interlace', 'Plane',  # 渐进式JPEG
                        '-colorspace', 'sRGB',  # 确保sRGB色彩空间
                        new_path
                    ]
            
            # 执行命令
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
    
    # 获取图片信息
    try:
        with Image.open(path) as img:
            width, height = img.size
            format = img.format
            
            # 获取EXIF信息
            exif = {}
            if hasattr(img, '_getexif'):
                exif_data = img._getexif()
                if exif_data:
                    from PIL.ExifTags import TAGS
                    from fractions import Fraction
                    
                    # EXIF字段名中英文映射字典
                    exif_field_map = {
                        # 基本信息
                        'Make': '制造商',
                        'Model': '设备型号',
                        'Software': '软件版本',
                        'DateTime': '拍摄时间',
                        'DateTimeOriginal': '原始拍摄时间',
                        'DateTimeDigitized': '数字化时间',
                        
                        # 拍摄参数
                        'ExposureTime': '曝光时间',
                        'FNumber': '光圈值',
                        'ISOSpeedRatings': 'ISO',
                        'FocalLength': '焦距',
                        'FocalLengthIn35mmFilm': '等效35mm焦距',
                        'ExposureProgram': '曝光程序',
                        'ExposureBiasValue': '曝光补偿',
                        'ExposureMode': '曝光模式',
                        'MeteringMode': '测光模式',
                        'Flash': '闪光灯',
                        'WhiteBalance': '白平衡',
                        'ShutterSpeedValue': '快门速度',
                        'ApertureValue': '光圈值',
                        'BrightnessValue': '亮度值',
                        
                        # 图片信息
                        'ImageWidth': '图像宽度',
                        'ImageHeight': '图像高度',
                        'ExifImageWidth': 'EXIF图像宽度',
                        'ExifImageHeight': 'EXIF图像高度',
                        'Orientation': '方向',
                        'ResolutionUnit': '分辨率单位',
                        'XResolution': '水平分辨率',
                        'YResolution': '垂直分辨率',
                        'ColorSpace': '色彩空间',
                        'YCbCrPositioning': 'YCbCr定位',
                        'SensingMethod': '感应方式',
                        'SceneCaptureType': '场景类型',
                        'SceneType': '场景',
                        'SubjectLocation': '主体位置',
                        
                        # 镜头信息
                        'LensMake': '镜头制造商',
                        'LensModel': '镜头型号',
                        'LensSpecification': '镜头规格',
                        
                        # 其他
                        'OffsetTime': '时间偏移',
                        'OffsetTimeOriginal': '原始时间偏移',
                        'OffsetTimeDigitized': '数字化时间偏移',
                        'SubsecTimeOriginal': '原始拍摄毫秒',
                        'SubsecTimeDigitized': '数字化毫秒',
                        
                        # 新增映射
                        'ComponentsConfiguration': '组件配置',
                        'ExifOffset': 'EXIF偏移',
                        'ExifVersion': 'EXIF版本',
                        'FlashPixVersion': 'FlashPix版本',
                        'FlashMode': '闪光灯模式',
                        'PixelXDimension': '像素宽度',
                        'PixelYDimension': '像素高度',
                        'GainControl': '增益控制',
                        'Contrast': '对比度',
                        'Saturation': '饱和度',
                        'Sharpness': '锐度',
                        'SubjectDistanceRange': '主体距离范围',
                    }
                    
                    # 将EXIF标签ID转换为可读名称
                    for tag, value in exif_data.items():
                        tag_name = TAGS.get(tag, tag)
                        # 过滤掉不需要显示的EXIF字段
                        if tag_name not in ['JPEGThumbnail', 'MakerNote', 'GPSInfo']:
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
                                    serializable_value = datetime.strptime(value, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
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
                            elif tag_name == 'ResolutionUnit':
                                # 分辨率单位：1=无单位，2=英寸，3=厘米
                                unit_map = {1: '无单位', 2: '英寸', 3: '厘米'}
                                serializable_value = unit_map.get(serializable_value, serializable_value)
                            elif tag_name == 'Orientation':
                                # 方向：1=正常，2=水平翻转，3=旋转180，4=垂直翻转，5=顺时针旋转90+水平翻转，6=顺时针旋转90，7=顺时针旋转90+垂直翻转，8=逆时针旋转90
                                orientation_map = {
                                    1: '正常', 2: '水平翻转', 3: '旋转180°', 4: '垂直翻转',
                                    5: '顺时针旋转90°+水平翻转', 6: '顺时针旋转90°',
                                    7: '顺时针旋转90°+垂直翻转', 8: '逆时针旋转90°'
                                }
                                serializable_value = orientation_map.get(serializable_value, serializable_value)
                            elif tag_name == 'SceneCaptureType':
                                # 场景类型：0=标准，1=风景，2=肖像，3=夜景
                                scene_map = {0: '标准', 1: '风景', 2: '肖像', 3: '夜景'}
                                serializable_value = scene_map.get(serializable_value, serializable_value)
                            elif tag_name == 'SensingMethod':
                                # 感应方式：1=未知，2=逐行扫描，3=隔行扫描，4=单芯片彩色区域传感器
                                sensing_map = {1: '未知', 2: '逐行扫描', 3: '隔行扫描', 4: '单芯片彩色区域传感器'}
                                serializable_value = sensing_map.get(serializable_value, serializable_value)
                            elif tag_name == 'ExposureProgram':
                                # 曝光程序：1=手动，2=正常程序，3=光圈优先，4=快门优先，5=创意程序，6=动作程序，7=肖像模式，8=风景模式
                                exposure_map = {
                                    1: '手动', 2: '正常程序', 3: '光圈优先', 4: '快门优先',
                                    5: '创意程序', 6: '动作程序', 7: '肖像模式', 8: '风景模式'
                                }
                                serializable_value = exposure_map.get(serializable_value, serializable_value)
                            elif tag_name == 'ExposureMode':
                                # 曝光模式：0=自动曝光，1=手动曝光，2=自动包围曝光
                                exposure_mode_map = {0: '自动曝光', 1: '手动曝光', 2: '自动包围曝光'}
                                serializable_value = exposure_mode_map.get(serializable_value, serializable_value)
                            elif tag_name == 'MeteringMode':
                                # 测光模式：0=未知，1=平均，2=中央重点平均，3=点测光，4=多点测光，5=评估测光
                                metering_map = {
                                    0: '未知', 1: '平均', 2: '中央重点平均', 3: '点测光',
                                    4: '多点测光', 5: '评估测光'
                                }
                                serializable_value = metering_map.get(serializable_value, serializable_value)
                            elif tag_name == 'Flash':
                                # 闪光灯：0=未使用，1=使用，5=关闭，9=打开，13=红眼关闭，17=红眼打开
                                flash_map = {
                                    0: '未使用', 1: '使用', 5: '关闭', 9: '打开',
                                    13: '红眼关闭', 17: '红眼打开', 24: '自动但未使用', 25: '自动且使用',
                                    29: '自动且关闭', 33: '自动且打开', 37: '自动且红眼关闭', 41: '自动且红眼打开'
                                }
                                serializable_value = flash_map.get(serializable_value, serializable_value)
                            elif tag_name == 'WhiteBalance':
                                # 白平衡：0=自动，1=手动
                                wb_map = {0: '自动', 1: '手动'}
                                serializable_value = wb_map.get(serializable_value, serializable_value)
                            
                            # 只添加非空值
                            if serializable_value is not None:
                                # 使用中文字段名，如果没有映射则使用原字段名
                                chinese_tag_name = exif_field_map.get(tag_name, tag_name)
                                exif[chinese_tag_name] = serializable_value
            
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
    try:
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
        return jsonify({'error': '统计文件格式失败: {e}'}), 500

@app.route('/fix_extensions', methods=['POST'])
def fix_extensions():
    """
    修复文件后缀，将大写扩展名改为小写，并将jpeg改为jpg
    请求方法: POST
    请求参数: selected_paths - 要修复的文件或文件夹路径列表
    返回: JSON格式的修复结果，包括处理的文件数量
    """
    selected_paths = request.json.get('selected_paths', [])
    logger.info(f"开始修复文件后缀，选中路径: {selected_paths}")
    
    if not selected_paths:
        logger.warning("未选中任何文件或文件夹")
        return jsonify({'error': '未选中任何文件或文件夹'}), 400
    
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
                            name_without_ext, ext = os.path.splitext(file)
                            # 标准化扩展名
                            ext_lower = ext.lower()
                            # 检查是否需要修复：1) 包含大写 2) 是jpeg 3) 是heic但扩展名是大写
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
                                    continue
                                # 重命名文件
                                os.rename(old_path, new_path)
                                logger.info(f"重命名文件: {old_path} -> {new_path}")
                                processed += 1
            elif os.path.isfile(path) and is_image_file(path):
                logger.info(f"修复文件: {path}")
                # 获取文件扩展名
                filename = os.path.basename(path)
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
                        continue
                    # 重命名文件
                    os.rename(path, new_path)
                    logger.info(f"重命名文件: {path} -> {new_path}")
                    processed += 1
        
        logger.info(f"修复完成，共处理 {processed} 个文件")
        return jsonify({'processed': processed})
    except Exception as e:
        logger.error(f"修复文件后缀失败: {e}")
        return jsonify({'error': '修复文件后缀失败: {e}'}), 500

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
            
            # 使用ImageMagick压缩图片
            if compress_image_with_imagemagick(img_path, quality):
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
            all_images.extend(filtered_images)
            
            # 将被跳过的文件添加到skipped_files列表
            skipped_files = [f for f in all_files if f not in filtered_images]
            with progress_lock:
                for f in skipped_files:
                    progress_data['skipped_files'].append(f)
                    progress_data['processed'] += 1
        elif os.path.isfile(path) and is_image_file(path):
            total_selected += 1
            ext = os.path.basename(path).lower().split('.')[-1]
            
            # 规范化当前文件格式
            normalized_ext = 'jpg' if ext == 'jpeg' else ext
            
            if normalized_ext != normalized_target:
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