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
    0x013e: 'Rational',  # WhitePoint
    0x013f: 'Rational',  # PrimaryChromaticities
    0x0140: 'Rational',  # YCbCrCoefficients
    0x0141: 'Short',     # YCbCrSubSampling
    0x0142: 'Short',     # YCbCrPositioning
    0x0143: 'Short',     # ReferenceBlackWhite
    0x014a: 'Short',     # StripRowCounts
    0x015b: 'Ascii',     # Copyright
    
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
        20: 'D55',
        21: 'D65',
        22: 'D75',
        23: 'D50',
        24: 'ISO  Studio Tungsten',
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
        1: '未知',
        2: '逐行扫描',
        3: '隔行扫描',
        4: '单芯片彩色区域传感器',
        5: '双芯片彩色区域传感器',
        6: '三芯片彩色区域传感器',
        7: '彩色线性传感器',
        8: '三芯片彩色线性传感器',
        9: '彩色三叶镜扫描传感器',
        10: '彩色旋转滤镜传感器',
        11: '彩色区域传感器',
        12: '单色区域传感器',
        13: '彩色线扫描传感器',
        14: '单色线扫描传感器',
        15: 'Foveon X3传感器',
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
        0: '未定义',
        1: '正常',
        2: '低增益',
        3: '高增益',
        4: '低增益自动',
        5: '高增益自动',
        6: '闪光灯增益',
        7: '闪光灯自动增益',
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
        18: 'HMI',
        19: '金属卤化物',
        20: '钠蒸气',
        21: '汞蒸气',
        22: 'LED',
        23: 'CFL',
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
        1: '胶片扫描',
        2: '数字相机',
        3: '视频扫描',
        4: '数字视频帧',
        5: '合成图像',
        6: '其他',
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
        1: 'Y',
        2: 'Cb',
        3: 'Cr',
        4: 'R',
        5: 'G',
        6: 'B',
    },
    
    # 扩展的压缩映射
    'Compression': {
        1: '未压缩',
        2: 'CCITT 1D',
        3: 'Group 3 Fax',
        4: 'Group 4 Fax',
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
        32895: 'Nikon NEF Compression',
        32896: 'PixelTalk',
        32908: 'Kodak DCR Compression',
        32946: 'IT8CTPAD',
        32947: 'IT8LW',
        32948: 'IT8MP',
        32949: 'IT8BL',
        33000: 'Ricoh RDC Compression',
        33001: 'Canon CRW Compression',
        33003: 'Nikon NEF Compression',
        34661: 'Samsung SRW Compression',
        34676: 'CCIRLEW',
        34677: 'Huffman',
        34712: 'JBIG',
        34713: 'SGILog',
        34715: 'SGILog24',
        34718: 'JPEG-LS',
        34719: 'JPEG-LS Lossless',
        34720: 'JPEG 2000',
        34721: 'JPEG 2000 Lossless',
        34722: 'JPEG XR',
        34723: 'JPEG XR Lossless',
        34892: 'MPO Compression',
    },

    'ExposureMode': {
        0: '自动曝光', 
        1: '手动曝光', 
        2: '自动包围曝光'
    },
}
