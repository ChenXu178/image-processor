# EXIF标签值类型映射
# 基于 https://exiv2.org/tags.html
EXIF_TAG_TYPES = {
    # Image 0x000b-0x02ff
    0x000b: 'Ascii',    # ProcessingSoftware
    0x00fe: 'Long',      # NewSubfileType
    0x00ff: 'Short',     # SubfileType (deprecated)
    0x0100: 'Long',      # ImageWidth
    0x0101: 'Long',      # ImageLength
    0x0102: 'Short',     # BitsPerSample
    0x0103: 'Short',     # Compression
    0x0106: 'Short',     # PhotometricInterpretation
    0x0107: 'Short',     # Thresholding
    0x0108: 'Short',     # CellWidth
    0x0109: 'Short',     # CellLength
    0x010a: 'Short',     # FillOrder
    0x010d: 'Ascii',     # DocumentName
    0x010e: 'Ascii',     # ImageDescription
    0x010f: 'Ascii',     # Make
    0x0110: 'Ascii',     # Model
    0x0111: 'Long',      # StripOffsets
    0x0112: 'Short',     # Orientation
    0x0115: 'Short',     # SamplesPerPixel
    0x0116: 'Long',      # RowsPerStrip
    0x0117: 'Long',      # StripByteCounts
    0x011a: 'Rational',  # XResolution
    0x011b: 'Rational',  # YResolution
    0x011c: 'Short',     # PlanarConfiguration
    0x011d: 'Ascii',     # PageName
    0x011e: 'Rational',  # XPosition
    0x011f: 'Rational',  # YPosition
    0x0120: 'Rational',  # FreeOffsets
    0x0121: 'Long',      # FreeByteCounts
    0x0122: 'Short',     # GrayResponseUnit
    0x0123: 'Short',     # GrayResponseCurve
    0x0124: 'Short',     # T4Options
    0x0125: 'Short',     # T6Options
    0x0128: 'Short',     # ResolutionUnit
    0x0129: 'Ascii',     # PageNumber
    0x012d: 'Short',     # TransferFunction
    0x0131: 'Ascii',     # Software
    0x0132: 'Ascii',     # DateTime
    0x013b: 'Ascii',     # Artist
    0x013c: 'Ascii',     # HostComputer
    0x013d: 'Short',     # Predictor
    0x013e: 'Rational',  # WhitePoint
    0x013f: 'Rational',  # PrimaryChromaticities
    0x0140: 'Rational',  # YCbCrCoefficients
    0x0141: 'Short',     # YCbCrSubSampling
    0x0142: 'Short',     # YCbCrPositioning
    0x0143: 'Short',     # ReferenceBlackWhite
    0x014a: 'Short',     # StripRowCounts
    0x015b: 'Ascii',     # Copyright
    0x0152: 'Short',     # ExtraSamples
    0x0153: 'Short',     # SampleFormat
    
    # EXIF 0x8298-0x927c
    0x8298: 'Ascii',     # Copyright
    0x829a: 'Rational',  # ExposureTime
    0x829d: 'Rational',  # FNumber
    0x83bb: 'Ascii',     # IPTC/NAA
    0x8769: 'Long',      # ExifOffset
    0x8822: 'Short',     # ExposureProgram
    0x8824: 'Rational',  # SpectralSensitivity
    0x8825: 'Rational',  # ISOSpeedRatings
    0x8827: 'Rational',  # OECF
    0x8829: 'Short',     # Interlace
    0x8830: 'Short',     # SensitivityType
    0x8831: 'Long',      # RecommendedExposureIndex
    0x8832: 'Short',     # ISOSpeedLatitudeyyy
    0x8833: 'Short',     # ISOSpeedLatitudezzz
    0x9000: 'Ascii',     # ExifVersion
    0x9003: 'Ascii',     # DateTimeOriginal
    0x9004: 'Ascii',     # DateTimeDigitized
    0x9101: 'Rational',  # ComponentsConfiguration
    0x9102: 'Rational',  # CompressedBitsPerPixel
    0x9201: 'Rational',  # ShutterSpeedValue
    0x9202: 'Rational',  # ApertureValue
    0x9203: 'Rational',  # BrightnessValue
    0x9204: 'Rational',  # ExposureBiasValue
    0x9205: 'Rational',  # MaxApertureValue
    0x9206: 'Rational',  # SubjectDistance
    0x9207: 'Short',     # MeteringMode
    0x9208: 'Short',     # LightSource
    0x9209: 'Short',     # Flash
    0x920a: 'Rational',  # FocalLength
    0x9214: 'Short',     # SubjectArea
    0x927c: 'Short',     # MakerNote
    0x9286: 'Rational',  # UserComment
    0x9290: 'Rational',  # SubsecTime
    0x9291: 'Rational',  # SubsecTimeOriginal
    0x9292: 'Rational',  # SubsecTimeDigitized
    
    # EXIF 0xa000-0xa438
    0xa000: 'Short',     # FlashPixVersion
    0xa001: 'Short',     # ColorSpace
    0xa002: 'Long',      # ExifImageWidth
    0xa003: 'Long',      # ExifImageLength
    0xa004: 'Short',     # InteroperabilityOffset
    0xa20b: 'Short',     # FlashEnergy
    0xa20c: 'Rational',  # SpatialFrequencyResponse
    0xa20e: 'Rational',  # FocalPlaneXResolution
    0xa20f: 'Rational',  # FocalPlaneYResolution
    0xa210: 'Short',     # FocalPlaneResolutionUnit
    0xa214: 'Short',     # SubjectLocation
    0xa215: 'Rational',  # ExposureIndex
    0xa217: 'Short',     # SensingMethod
    0xa300: 'Short',     # FileSource
    0xa301: 'Short',     # SceneType
    0xa302: 'Short',     # CFAPattern
    0xa401: 'Short',     # CustomRendered
    0xa402: 'Short',     # ExposureMode
    0xa403: 'Short',     # WhiteBalance
    0xa404: 'Rational',  # DigitalZoomRatio
    0xa405: 'Rational',  # FocalLengthIn35mmFilm
    0xa406: 'Short',     # SceneCaptureType
    0xa407: 'Short',     # GainControl
    0xa408: 'Short',     # Contrast
    0xa409: 'Short',     # Saturation
    0xa40a: 'Short',     # Sharpness
    0xa40b: 'Short',     # DeviceSettingDescription
    0xa40c: 'Short',     # SubjectDistanceRange
    0xa420: 'Short',     # ImageUniqueID
    0xa460: 'Short',     # CompositeImage
    
    # GPS 0x0000-0x0031
    0x0000: 'Byte',      # GPSVersionID
    0x0001: 'Ascii',     # GPSLatitudeRef
    0x0002: 'Rational',  # GPSLatitude
    0x0003: 'Ascii',     # GPSLongitudeRef
    0x0004: 'Rational',  # GPSLongitude
    0x0005: 'Byte',      # GPSAltitudeRef
    0x0006: 'Rational',  # GPSAltitude
    0x0007: 'Rational',  # GPSTimeStamp
    0x0008: 'Ascii',     # GPSSatellites
    0x0009: 'Ascii',     # GPSStatus
    0x000a: 'Ascii',     # GPSMeasureMode
    0x000b: 'Rational',  # GPSDOP
    0x000c: 'Ascii',     # GPSSpeedRef
    0x000d: 'Rational',  # GPSSpeed
    0x000e: 'Ascii',     # GPSTrackRef
    0x000f: 'Rational',  # GPSTrack
    0x0010: 'Ascii',     # GPSImgDirectionRef
    0x0011: 'Rational',  # GPSImgDirection
    0x0012: 'Ascii',     # GPSMapDatum
    0x0013: 'Ascii',     # GPSDestLatitudeRef
    0x0014: 'Rational',  # GPSDestLatitude
    0x0015: 'Ascii',     # GPSDestLongitudeRef
    0x0016: 'Rational',  # GPSDestLongitude
    0x0017: 'Ascii',     # GPSDestBearingRef
    0x0018: 'Rational',  # GPSDestBearing
    0x0019: 'Ascii',     # GPSDestDistanceRef
    0x001a: 'Rational',  # GPSDestDistance
    0x001b: 'Ascii',     # GPSProcessingMethod
    0x001c: 'Ascii',     # GPSAreaInformation
    0x001d: 'Ascii',     # GPSDateStamp
    0x001e: 'Short',     # GPSDifferential
    0x001f: 'Rational',  # GPSHPositioningError
    0x0020: 'Rational',  # GPSAltitudeError
    0x0021: 'Rational',  # GPSSpeedError
    0x0022: 'Rational',  # GPSImgDirectionError
    0x0023: 'Rational',  # GPSTrackError
    0x0024: 'Rational',  # GPSDestBearingError
    0x0025: 'Rational',  # GPSDestDistanceError
    0x0026: 'Ascii',     # GPSDateTime
    0x0027: 'Byte',      # GPSProcessingMethodBin
    0x0028: 'Byte',      # GPSAreaInformationBin
    0x0030: 'Byte',      # GPSSatelliteIDs
    0x0031: 'Byte',      # GPSStatusBits

    0xc617: 'Short',     # CFALayout
    0xc6bf: 'Short',     # ColorimetricReference
    0xc6fd: 'Short',     # ProfileEmbedPolicy
    0xc71a: 'Short',     # PreviewColorSpace
    0xc740: 'Short',     # OpcodeList1
    0xc741: 'Short',     # OpcodeList2
    0xc74e: 'Short',     # OpcodeList3
}

# 扩展的标签值映射
extended_value_mappings = {
    # 扩展的曝光程序映射
    'ExposureProgram': {
        0: '未定义',
        1: '手动',
        2: '正常程序',
        3: '光圈优先',
        4: '快门优先',
        5: '创意程序',
        6: '动作程序',
        7: '肖像模式',
        8: '风景模式',
        9: '夜景模式',
        10: '夜景肖像模式',
        11: '剧场模式',
        12: '海滩模式',
        13: '雪景模式',
        14: '烟火模式',
        15: '运动模式',
        16: '聚会模式',
        17: '日落模式',
        18: '微距模式',
        19: '儿童模式',
        20: '宠物模式',
        21: '烛光模式',
        22: '全景模式',
        23: '食物模式',
        24: '文字模式',
        25: 'HDR模式',
        26: '3D模式',
        27: '咖啡模式',
        28: '水彩画模式',
        29: '素描模式',
        30: '卡通模式',
        31: '高对比度黑白模式',
        32: '玩具相机模式',
        33: '微型模型模式',
        34: '怀旧模式',
        35: '高动态范围模式',
        36: '全景模式',
        37: '鱼眼模式',
        38: '微缩景观模式',
        39: '动态光照模式',
        40: '完美人像模式',
        41: '柔焦模式',
        42: '照片效果模式',
        43: '智能自动模式',
        44: '超级肖像模式',
        45: '手持夜景模式',
        46: '夜景HDR模式',
        47: '运动连拍模式',
        48: '高速连拍模式',
        49: '单拍模式',
        50: '定时自拍模式',
        51: '连续定时自拍模式',
        52: '触控快门模式',
        53: '笑脸快门模式',
        54: '眨眼检测模式',
        55: '防抖模式',
        56: '智能防抖模式',
        57: '运动防抖模式',
        58: '三脚架防抖模式',
        59: '多重曝光模式',
        60: '全景扫描模式',
        61: '3D全景扫描模式',
        62: '背景虚化模式',
        63: '创意控制模式',
    },
    
    # 扩展的光源映射
    'LightSource': {
        0: '未知',
        1: '日光',
        2: '荧光灯',
        3: '钨丝灯',
        4: '闪光灯',
        9: '阴天',
        10: '阴影',
        11: '黄昏/黎明',
        12: '日光荧光灯',
        13: '冷白色荧光灯',
        14: '白色荧光灯',
        15: '暖白色荧光灯',
        17: '标准光源A',
        18: '标准光源B',
        19: '标准光源C',
        20: 'D55光源',
        21: 'D65光源',
        22: 'D75光源',
        23: 'D50光源',
        24: 'ISO工作室钨丝灯',
        255: '其他',
    },
    
    # 扩展的测光模式映射
    'MeteringMode': {
        0: '未知',
        1: '平均',
        2: '中央重点平均',
        3: '点测光',
        4: '多点测光',
        5: '评估测光',
        6: '部分测光',
        255: '其他',
    },
    
    # 扩展的感应方式映射
    'SensingMethod': {
        1: '未定义',
        2: '单芯片彩色区域传感器',
        3: '双芯片彩色区域传感器',
        4: '三芯片彩色区域传感器',
        5: '彩色顺序区域传感器',
        7: '三线性传感器',
        8: '彩色顺序线性传感器'
    },
    
    # 扩展的场景类型映射
    'SceneCaptureType': {
        0: '标准',
        1: '风景',
        2: '肖像',
        3: '夜景',
        4: '微距',
        5: '运动',
        6: '日落',
        7: '烟火',
        8: '海滩',
        9: '雪景',
        10: '文档',
        11: '全景',
        12: '夜晚肖像',
        13: '儿童',
        14: '宠物',
        15: '食物',
        16: '烛光',
        17: '博物馆',
        18: '舞台',
        19: '日出',
        20: '植物',
        21: '水族馆',
        22: '街景',
        23: 'HDR',
        24: '文字',
        25: '日落/日出',
        26: '背光',
        27: '多云',
        28: '晴天',
        29: '雨天',
        30: '雾天',
        31: '雪天',
    },
    
    # 扩展的闪光灯映射
    'Flash': {
        0x0000: '未使用',
        0x0001: '使用',
        0x0005: '关闭',
        0x0009: '打开',
        0x000d: '红眼关闭',
        0x0011: '红眼打开',
        0x0018: '自动但未使用',
        0x0019: '自动且使用',
        0x001d: '自动且关闭',
        0x0021: '自动且打开',
        0x0025: '自动且红眼关闭',
        0x0029: '自动且红眼打开',
        0x0030: '外接闪光灯，未使用',
        0x0031: '外接闪光灯，使用',
        0x0035: '外接闪光灯，关闭',
        0x0039: '外接闪光灯，打开',
        0x003d: '外接闪光灯，红眼关闭',
        0x0041: '外接闪光灯，红眼打开',
        0x0048: '外接闪光灯，自动但未使用',
        0x0049: '外接闪光灯，自动且使用',
        0x004d: '外接闪光灯，自动且关闭',
        0x0051: '外接闪光灯，自动且打开',
        0x0055: '外接闪光灯，自动且红眼关闭',
        0x0059: '外接闪光灯，自动且红眼打开',
    },
    
    # 扩展的增益控制映射
    'GainControl': {
        0: '无',
        1: '低增益上调',
        2: '高增益上调',
        3: '低增益下调',
        4: '高增益下调',
        5: '自动',
    },
    
    # 扩展的对比度映射
    'Contrast': {
        0: '标准',
        1: '低',
        2: '高',
    },
    
    # 扩展的饱和度映射
    'Saturation': {
        0: '标准',
        1: '低',
        2: '高',
    },
    
    # 扩展的锐度映射
    'Sharpness': {
        0: '标准',
        1: '低',
        2: '高',
    },
    
    # 扩展的白平平衡映射
    'WhiteBalance': {
        0: '自动',
        1: '手动',
        2: '阴天',
        3: '日光',
        4: '荧光灯',
        5: '荧光灯H',
        6: '荧光灯L',
        7: '荧光灯N',
        8: '白炽灯',
        9: '闪光灯',
        10: '日落',
        11: '日落/日出',
        12: '水下',
        13: '阴影',
        14: '多云',
        15: '黄昏',
        16: '黎明',
        17: '电子闪光',
        18: 'HMI光源',
        19: '金属卤化物灯',
        20: '钠蒸气灯',
        21: '汞蒸气灯',
        22: 'LED灯',
        23: 'CFL灯',
        24: 'TTL闪光灯',
        25: '自定义1',
        26: '自定义2',
        27: '自定义3',
        28: '自定义4',
        29: '自定义5',
        30: '自定义6',
        31: '自定义7',
    },
    
    # 扩展的文件来源映射
    'FileSource': {
        0: '其他',
        1: '胶片扫描',
        2: '反射扫描',
        3: '数码相机',
    },
    
    # 扩展的分辨率单位映射
    'ResolutionUnit': {
        1: '无单位',
        2: '英寸',
        3: '厘米',
    },
    
    # 扩展的YCC定位映射
    'YCbCrPositioning': {
        1: '中心',
        2: '共置',
    },
    
    # 扩展的组件配置映射
    'ComponentsConfiguration': {
        0: '未定义',
        1: 'Y通道',
        2: 'Cb通道',
        3: 'Cr通道',
        4: 'R通道',
        5: 'G通道',
        6: 'B通道',
    },
    
    # 扩展的压缩映射
    'Compression': {
        1: '未压缩',
        2: 'CCITT 1D',
        3: '第三组传真',
        4: '第四组传真',
        5: 'LZW',
        6: 'JPEG',
        7: 'JPEG',
        8: 'Adobe Deflate',
        9: 'JBIG B&W',
        10: 'JBIG Color',
        99: 'PackBits',
        262: 'Deflate',
        32766: 'JBIG',
        32767: 'SGILog',
        32769: 'SGILog24',
        32809: 'JPEG 2000',
        32895: 'Nikon NEF 压缩',
        32896: 'PixelTalk',
        32908: 'Kodak DCR 压缩',
        32946: 'IT8CTPAD',
        32947: 'IT8LW',
        32948: 'IT8MP',
        32949: 'IT8BL',
        33000: 'Ricoh RDC 压缩',
        33001: 'Canon CRW 压缩',
        33003: 'Nikon NEF 压缩',
        34661: 'Samsung SRW 压缩',
        34676: 'CCIRLEW',
        34677: '霍夫曼编码',
        34712: 'JBIG',
        34713: 'SGILog',
        34715: 'SGILog24',
        34718: 'JPEG-LS',
        34719: 'JPEG-LS 无损',
        34720: 'JPEG 2000',
        34721: 'JPEG 2000 无损',
        34722: 'JPEG XR',
        34723: 'JPEG XR 无损',
        34892: 'MPO 压缩',
    },

    'ExposureMode': {
        0: '自动曝光', 
        1: '手动曝光', 
        2: '自动包围曝光'
    },

    'Orientation': {
        1: '水平（正常）',
        2: '水平镜像',
        3: '旋转180°',
        4: '垂直镜像',
        5: '水平镜像并顺时针旋转270°',
        6: '顺时针旋转90°',
        7: '水平镜像并顺时针旋转90°',
        8: '顺时针旋转270°'
    },
    
    # 扩展的子文件类型映射
    'SubfileType': {
        1: '全分辨率图像',
        2: '降分辨率图像',
        3: '多页图像的单页'
    },
    
    # 扩展的新子文件类型映射
    'NewSubfileType': {
        0x0: '全分辨率图像',
        0x1: '降分辨率图像',
        0x2: '多页图像的单页',
        0x3: '多页降分辨率图像的单页',
        0x4: '透明蒙版',
        0x5: '降分辨率图像的透明蒙版',
        0x6: '多页图像的透明蒙版',
        0x7: '多页降分辨率图像的透明蒙版',
        0x8: '深度图',
        0x9: '降分辨率图像的深度图',
        0x10: '增强图像数据',
        0x10001: '备用降分辨率图像',
        0x10004: '语义蒙版',
        0xffffffff: '无效'
    },
    
    # 扩展的预测器映射
    'Predictor': {
        1: '无预测',
        2: '水平差分',
        3: '浮点'
    },
    
    # 扩展的额外样本映射
    'ExtraSamples': {
        0: '未指定',
        1: '关联Alpha',
        2: '非关联Alpha'
    },
    
    # 扩展的安全分类映射
    'SecurityClassification': {
        'C': '机密',
        'R': '受限',
        'S': '秘密',
        'T': '最高机密',
        'U': '非机密'
    },
    
    # 扩展的色彩空间映射
    'ColorSpace': {
        0x1: 'sRGB',
        0x2: 'Adobe RGB',
        0xfffd: '广色域RGB',
        0xfffe: 'ICC配置文件',
        0xffff: '未校准'
    },
    
    # 扩展的合成图像映射
    'CompositeImage': {
        0: '未知',
        1: '非合成图像',
        2: '普通合成图像',
        3: '拍摄时捕获的合成图像'
    },
    
    # 扩展的CFA布局映射
    'CFALayout': {
        1: '矩形',
        2: '偶数列向下偏移1/2行',
        3: '偶数列向上偏移1/2行',
        4: '偶数行向右偏移1/2列',
        5: '偶数行向左偏移1/2列',
        6: '偶数行向上偏移1/2行，偶数列向左偏移1/2列',
        7: '偶数行向上偏移1/2行，偶数列向右偏移1/2列',
        8: '偶数行向下偏移1/2行，偶数列向左偏移1/2列',
        9: '偶数行向下偏移1/2行，偶数列向右偏移1/2列'
    },
    
    # 扩展的色度参考映射
    'ColorimetricReference': {
        0: '场景参考',
        1: '输出参考（ICC配置文件动态范围）',
        2: '输出参考（高动态范围）'
    },
    
    # 扩展的配置文件嵌入策略映射
    'ProfileEmbedPolicy': {
        0: '允许复制',
        1: '使用时嵌入',
        2: '从不嵌入',
        3: '无限制'
    },
    
    # 扩展的预览色彩空间映射
    'PreviewColorSpace': {
        0: '未知',
        1: '灰度伽马2.2',
        2: 'sRGB',
        3: 'Adobe RGB',
        4: 'ProPhoto RGB'
    },
    
    # 扩展的操作码列表1映射
    'OpcodeList1': {
        1: '矩形扭曲',
        2: '鱼眼扭曲',
        3: '径向渐晕修复',
        4: '恒定坏点修复',
        5: '坏点列表修复',
        6: '边界修剪',
        7: '映射表',
        8: '多项式映射',
        9: '增益映射',
        10: '逐行增量',
        11: '逐列增量',
        12: '逐行缩放',
        13: '逐列缩放',
        14: '矩形扭曲2'
    },
    
    # 扩展的操作码列表2映射
    'OpcodeList2': {
        1: '矩形扭曲',
        2: '鱼眼扭曲',
        3: '径向渐晕修复',
        4: '恒定坏点修复',
        5: '坏点列表修复',
        6: '边界修剪',
        7: '映射表',
        8: '多项式映射',
        9: '增益映射',
        10: '逐行增量',
        11: '逐列增量',
        12: '逐行缩放',
        13: '逐列缩放',
        14: '矩形扭曲2'
    },
    
    # 扩展的操作码列表3映射
    'OpcodeList3': {
        1: '矩形扭曲',
        2: '鱼眼扭曲',
        3: '径向渐晕修复',
        4: '恒定坏点修复',
        5: '坏点列表修复',
        6: '边界修剪',
        7: '映射表',
        8: '多项式映射',
        9: '增益映射',
        10: '逐行增量',
        11: '逐列增量',
        12: '逐行缩放',
        13: '逐列缩放',
        14: '矩形扭曲2'
    },
    
    # 扩展的光度解释映射
    'PhotometricInterpretation': {
        0: '白为零',
        1: '黑为零',
        2: 'RGB',
        3: 'RGB调色板',
        4: '透明蒙版',
        5: 'CMYK',
        6: 'YCbCr',
        8: 'CIELab',
        9: 'ICCLab',
        10: 'ITU Lab',
        32803: '彩色滤镜阵列',
        32844: 'Pixar LogL',
        32845: 'Pixar LogLuv',
        32892: '顺序彩色滤镜',
        34892: '线性原始图像',
        51177: '深度图',
        52527: '语义蒙版'
    },
    
    # 扩展的阈值化映射
    'Thresholding': {
        1: '无抖动或半色调',
        2: '有序抖动或半色调',
        3: '随机抖动'
    },
    
    # 扩展的填充顺序映射
    'FillOrder': {
        1: '正常',
        2: '反转'
    },
    
    # 扩展的平面配置映射
    'PlanarConfiguration': {
        1: '块状',
        2: '平面'
    },
    
    # 扩展的灰度响应单位映射
    'GrayResponseUnit': {
        1: '0.1',
        2: '0.001',
        3: '0.0001',
        4: '1e-05',
        5: '1e-06'
    },
    
    # 扩展的互操作索引映射
    'InteropIndex': {
        'R03': 'R03 - DCF选项文件 (Adobe RGB)',
        'R98': 'R98 - DCF基本文件 (sRGB)',
        'THM': 'THM - DCF缩略图文件'
    },
    
    # 扩展的样本位数映射
    'BitsPerSample': {
        8: '8位',
        10: '10位',
        12: '12位',
        14: '14位',
        16: '16位',
        24: '24位',
        32: '32位',
        48: '48位',
        64: '64位'
    },
    
    # 扩展的YCbCr系数映射
    'YCbCrCoefficients': {
        # 通常是三个浮点数的组合，这里只列出常见组合
        (0.299, 0.587, 0.114): '标准YCbCr系数'
    },
    
    # 扩展的YCbCr子采样映射
    'YCbCrSubSampling': {
        1: '1x1 (4:4:4)',
        2: '2x1 (4:2:2)',
        3: '2x2 (4:2:0)',
        4: '3x1 (4:1:1)',
        5: '3x3 (4:1:0)'
    },
    
    # 扩展的ISO感光度映射
    'ISOSpeedRatings': {
        # 这里只列出常见的ISO值，实际应用中会动态处理
        100: 'ISO 100',
        200: 'ISO 200',
        400: 'ISO 400',
        800: 'ISO 800',
        1600: 'ISO 1600',
        3200: 'ISO 3200',
        6400: 'ISO 6400',
        12800: 'ISO 12800',
        25600: 'ISO 25600'
    },
    
    # 扩展的感光度类型映射
    'SensitivityType': {
        1: '标准输出感光度',
        2: '推荐曝光指数',
        3: 'ISO速度',
        4: '标准输出感光度和推荐曝光指数',
        5: '标准输出感光度和ISO速度',
        6: '推荐曝光指数和ISO速度',
        7: '标准输出感光度、推荐曝光指数和ISO速度'
    },
    
    # 扩展的场景类型映射
    'SceneType': {
        1: '直接拍摄'
    },
    
    # 扩展的GPS纬度参考映射
    'GPSLatitudeRef': {
        'N': '北纬',
        'S': '南纬'
    },
    
    # 扩展的GPS经度参考映射
    'GPSLongitudeRef': {
        'E': '东经',
        'W': '西经'
    },
    
    # 扩展的GPS高度参考映射
    'GPSAltitudeRef': {
        0: '海平面以上',
        1: '海平面以下'
    },
    
    # 扩展的GPS速度参考映射
    'GPSSpeedRef': {
        'K': '公里/小时',
        'M': '英里/小时',
        'N': '节'
    },
    
    # 扩展的GPS航向参考映射
    'GPSTrackRef': {
        'T': '真方向',
        'M': '磁方向'
    },
    
    # 扩展的GPS图像方向参考映射
    'GPSImgDirectionRef': {
        'T': '真方向',
        'M': '磁方向'
    },
    
    # 扩展的GPS目标纬度参考映射
    'GPSDestLatitudeRef': {
        'N': '北纬',
        'S': '南纬'
    },
    
    # 扩展的GPS目标经度参考映射
    'GPSDestLongitudeRef': {
        'E': '东经',
        'W': '西经'
    },
    
    # 扩展的GPS目标方位参考映射
    'GPSDestBearingRef': {
        'T': '真方向',
        'M': '磁方向'
    },
    
    # 扩展的GPS目标距离参考映射
    'GPSDestDistanceRef': {
        'K': '公里',
        'M': '英里',
        'N': '节'
    },
    
    # 扩展的GPS差分映射
    'GPSDifferential': {
        0: '无差分校正',
        1: '应用了差分校正'
    },
    
    # 扩展的焦平面分辨率单位映射
    'FocalPlaneResolutionUnit': {
        1: '无单位',
        2: '英寸',
        3: '厘米',
        4: '毫米',
        5: '微米'
    },
    
    # 扩展的自定义渲染映射
    'CustomRendered': {
        0: '正常处理',
        1: '自定义处理',
        2: 'HDR (no original saved)',
        3: 'HDR (original saved)',
        4: 'Original (for HDR)',
        6: 'Panorama',
        7: 'Portrait HDR',
        8: 'Portrait'
    },
    
    # 扩展的数字变焦比映射
    'DigitalZoomRatio': {
        # 通常是数值，这里只列出特殊值
        0: '无数字变焦',
        1: '1x（无变焦）'
    },
    
    # 扩展的等效35mm焦距映射
    'FocalLengthIn35mmFilm': {
        # 通常是数值，这里只列出特殊值
        0: '未知'
    },
    
    # 扩展的主体距离范围映射
    'SubjectDistanceRange': {
        0: '未知',
        1: '微距',
        2: '近距离',
        3: '远距离'
    },
    
    # 扩展的样本格式映射
    'SampleFormat': {
        1: '无符号',
        2: '有符号',
        3: '浮点',
        4: '未定义',
        5: '复数整数',
        6: '复数浮点'
    },
    
    # 扩展的交错映射
    'Interlace': {
        0: '未交错',
        1: '隔行扫描，2行交错',
        2: '隔行扫描，4行交错'
    },
    
    # 扩展的T4选项映射
    'T4Options': {
        0: '无特殊处理',
        1: '使用2D编码',
        2: '未压缩',
        4: '添加填充位'
    },
    
    # 扩展的T6选项映射
    'T6Options': {
        0: '无特殊处理',
        1: '使用2D编码',
        2: '未压缩',
        4: '添加填充位'
    },
}
