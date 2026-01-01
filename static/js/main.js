// 日志配置
const LOG_LEVEL = 'info'; // 日志级别：debug, info, warn, error

// 日志函数
function log(level, message, data) {
    const timestamp = new Date().toISOString();
    if (level === 'error' || 
        level === 'warn' || 
        (level === 'info' && ['info', 'debug'].includes(LOG_LEVEL)) || 
        (level === 'debug' && LOG_LEVEL === 'debug')) {
        const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
        if (data) {
            console.log(logMessage, data);
        } else {
            console.log(logMessage);
        }
    }
}

// 已选择的文件列表
let selectedFiles = [];
// 当前目录路径
let currentPath = '';
// 配置的基础目录
let baseDir = '';
// 支持的图片格式
let supportedFormats = ['jpg', 'jpeg', 'png', 'webp', 'avif', 'heic', 'bmp', 'gif', 'tiff'];
// 进度轮询定时器
let progressInterval = null;

$(document).ready(function() {
    // 加载配置信息
    loadConfig();
    
    // 加载支持的格式列表
    loadSupportedFormats();
    
    // 初始检查一次进度
    updateProgress();
    
    // 添加调试信息，确保DOM元素存在
    log('debug', 'DOM元素检查:');
    log('debug', 'total-files exists:', $('#total-files').length > 0);
    log('debug', 'processed-files exists:', $('#processed-files').length > 0);
    log('debug', 'progress-bar exists:', $('#progress-bar').length > 0);
    log('debug', 'progress-overlay exists:', $('#progress-overlay').length > 0);
    log('debug', 'statistics exists:', $('#statistics').length > 0);
    log('debug', 'close-progress exists:', $('#close-progress').length > 0);
    
    // 压缩率滑块
    $('#compression-quality').on('input', function() {
        $('#quality-value').text($(this).val());
    });
    
    // 线程数滑块
    $('#thread-count').on('input', function() {
        $('#thread-value').text($(this).val());
    });
    
    // 转换压缩率滑块
    $('#convert-quality').on('input', function() {
        $('#convert-quality-value').text($(this).val());
    });
    
    // 转换线程数滑块
    $('#convert-thread-count').on('input', function() {
        $('#convert-thread-value').text($(this).val());
    });
    
    // 返回上级按钮
    $('#back-btn').on('click', function() {
        if (currentPath !== baseDir) {
            // 同时处理Windows和Unix路径分隔符
            const lastSeparatorIndex = Math.max(
                currentPath.lastIndexOf('/'),
                currentPath.lastIndexOf('\\')
            );
            if (lastSeparatorIndex > 0) {
                const parentPath = currentPath.substring(0, lastSeparatorIndex);
                currentPath = parentPath;
            } else {
                // 如果已经是根目录，保持不变
                currentPath = baseDir;
            }
            loadFiles();
        }
    });
    
    // 全选按钮 - 选中当前路径下所有图片
    $('#select-all-btn').on('click', function() {
        // 选中当前目录下的所有图片文件
        const fileItems = $('.file-list-item');
        let selectedCount = 0;
        
        fileItems.each(function() {
            const checkbox = $(this).find('.checkbox');
            // 检查是否有复选框
            if (checkbox.length === 0) {
                return; // 跳过没有复选框的项目（如返回上级项）
            }
            
            // 强制设置为选中状态
            checkbox.prop('checked', true);
                
            // 获取路径
            const path = $(this).data('path');
            // 检查是否已经在selectedFiles列表中
            if (!selectedFiles.includes(path)) {
                // 添加到selectedFiles列表
                selectedFiles.push(path);
                // 更新已选择文件列表
                updateSelectedFilesList();
                // 更新按钮状态
                updateButtons();
                selectedCount++;
            }
        });
        
        // 如果没有选中任何项目，可能是因为所有项目都是文件夹
        if (selectedCount === 0) {
            alert('当前目录下没有可选中的文件');
        }
    });
    
    // 取消全选按钮 - 清空右侧选中列表
    $('#deselect-all-btn').on('click', function() {
        // 清空selectedFiles列表
        selectedFiles = [];
        // 更新已选择文件列表
        updateSelectedFilesList();
        // 更新左侧文件列表中的所有复选框
        const checkboxes = $('.file-list-item .checkbox');
        checkboxes.prop('checked', false);
        // 更新按钮状态
        updateButtons();
    });
    
    // 统计文件格式按钮
    $('#count-formats-btn').on('click', function() {
        if (selectedFiles.length === 0) {
            alert('请先选择文件或文件夹');
            return;
        }
        
        // 显示加载动画
        $('#loading').show();
        
        // 发送请求统计文件格式
        $.ajax({
            url: '/count_formats',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ selected_paths: selectedFiles }),
            success: function(response) {
                $('#loading').hide();
                
                // 生成统计结果HTML
                let resultHtml = '<h3>文件格式统计</h3>';
                resultHtml += '<div class="mb-3">';
                resultHtml += '<p><strong>总文件数:</strong> ' + response.total_files + '</p>';
                resultHtml += '<p><strong>总大小:</strong> ' + formatFileSize(response.total_size) + '</p>';
                resultHtml += '</div>';
                resultHtml += '<div class="table-responsive">';
                resultHtml += '<table class="table table-bordered">';
                resultHtml += '<thead class="thead-light">';
                resultHtml += '<tr>';
                resultHtml += '<th>格式</th>';
                resultHtml += '<th>数量</th>';
                resultHtml += '<th>总大小</th>';
                resultHtml += '<th>平均大小</th>';
                resultHtml += '</tr>';
                resultHtml += '</thead>';
                resultHtml += '<tbody>';
                
                for (const [format, count] of Object.entries(response.format_count)) {
                    const size = response.format_size[format] || 0;
                    const avgSize = count > 0 ? size / count : 0;
                    resultHtml += '<tr>';
                    resultHtml += '<td>' + format.toUpperCase() + '</td>';
                    resultHtml += '<td>' + count + '</td>';
                    resultHtml += '<td>' + formatFileSize(size) + '</td>';
                    resultHtml += '<td>' + formatFileSize(avgSize) + '</td>';
                    resultHtml += '</tr>';
                }
                
                resultHtml += '</tbody>';
                resultHtml += '</table>';
                resultHtml += '</div>';
                
                // 更新模态框内容并显示
                $('#statistics-result').html(resultHtml);
                $('#statistics-modal').modal('show');
            },
            error: function(xhr, status, error) {
                $('#loading').hide();
                alert('统计失败: ' + error);
            }
        });
    });
    
    // 修复文件后缀按钮
    $('#fix-extensions-btn').on('click', function() {
        if (selectedFiles.length === 0) {
            alert('请先选择文件或文件夹');
            return;
        }
        
        if (!confirm('确定要修复选中路径下所有图片文件的后缀名吗？这将把所有大写后缀改为小写，例如PNG->png, Jpg->jpg。')) {
            return;
        }
        
        // 显示加载动画
        $('#loading').show();
        
        // 发送请求修复文件后缀
        $.ajax({
            url: '/fix_extensions',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ selected_paths: selectedFiles }),
            success: function(response) {
                $('#loading').hide();
                alert('修复完成，共处理 ' + response.processed + ' 个文件');
                // 刷新文件列表
                loadFiles();
            },
            error: function(xhr, status, error) {
                $('#loading').hide();
                alert('修复失败: ' + error);
            }
        });
    });
    
    // 图片压缩按钮
    $('#compress-btn').on('click', function() {
        // 显示压缩配置模态框
        $('#compress-modal').modal('show');
    });
    
    // 图片转换按钮
    $('#convert-btn').on('click', function() {
        // 显示转换配置模态框
        $('#convert-modal').modal('show');
    });
    
    // 开始压缩按钮
    $('#start-compress-btn').on('click', function() {
        if (selectedFiles.length === 0) {
            alert('请先选择文件或文件夹');
            return;
        }
        
        // 获取配置
        const quality = parseInt($('#compression-quality').val());
        const minSize = parseInt($('#min-file-size').val()) * 1024; // 转换为字节
        const maxWorkers = parseInt($('#thread-count').val());
        
        // 隐藏配置模态框
        $('#compress-modal').modal('hide');
        
        // 显示进度
        $('#progress-overlay').show();
        
        // 发送请求开始压缩
        $.ajax({
            url: '/compress_images',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                selected_paths: selectedFiles,
                quality: quality,
                min_size: minSize,
                max_workers: maxWorkers
            }),
            success: function(response) {
                // 清空已选择列表
                selectedFiles = [];
                updateSelectedFilesList();
                updateButtons();
                
                // 立即调用一次updateProgress
                updateProgress();
                
                // 增加一个快速轮询，直到total值不为0
                let quickPollCount = 0;
                const maxQuickPolls = 10;
                const quickPollInterval = setInterval(function() {
                    quickPollCount++;
                    updateProgress();
                    
                    // 检查total值是否已更新，或者达到最大轮询次数
                    if ($('#total-files').text() !== '0' || quickPollCount >= maxQuickPolls) {
                        clearInterval(quickPollInterval);
                        log('info', '快速轮询结束，总文件数已更新为: ' + $('#total-files').text());
                    }
                }, 200); // 每200毫秒轮询一次
            },
            error: function(xhr, status, error) {
                $('#progress-overlay').hide();
                alert('压缩失败: ' + error);
            }
        });
    });
    
    // 开始转换按钮
    $('#start-convert-btn').on('click', function() {
        if (selectedFiles.length === 0) {
            alert('请先选择文件或文件夹');
            return;
        }
        
        // 获取配置
        const targetFormat = $('#target-format').val();
        const quality = parseInt($('#convert-quality').val());
        const maxWorkers = parseInt($('#convert-thread-count').val());
        
        // 隐藏配置模态框
        $('#convert-modal').modal('hide');
        
        // 显示进度
        $('#progress-overlay').show();
        
        // 发送请求开始转换
        $.ajax({
            url: '/convert_images',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                selected_paths: selectedFiles,
                target_format: targetFormat,
                quality: quality,
                max_workers: maxWorkers
            }),
            success: function(response) {
                // 清空已选择列表
                selectedFiles = [];
                updateSelectedFilesList();
                updateButtons();
                
                // 立即调用一次updateProgress
                updateProgress();
                
                // 增加一个快速轮询，直到total值不为0
                let quickPollCount = 0;
                const maxQuickPolls = 10;
                const quickPollInterval = setInterval(function() {
                    quickPollCount++;
                    updateProgress();
                    
                    // 检查total值是否已更新，或者达到最大轮询次数
                    if ($('#total-files').text() !== '0' || quickPollCount >= maxQuickPolls) {
                        clearInterval(quickPollInterval);
                        log('info', '快速轮询结束，总文件数已更新为: ' + $('#total-files').text());
                    }
                }, 200); // 每200毫秒轮询一次
            },
            error: function(xhr, status, error) {
                $('#progress-overlay').hide();
                // 显示友好的错误信息
                let errorMessage = '转换失败: ';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage += xhr.responseJSON.error;
                } else {
                    errorMessage += error;
                }
                alert(errorMessage);
            }
        });
    });
    
    // 关闭进度按钮
    $('#close-progress').on('click', function() {
        // 重置进度相关DOM元素
        $('#total-files').text('0');
        $('#processed-files').text('0');
        $('#current-file').text('');
        $('#progress-bar').css('width', '0%').attr('aria-valuenow', '0');
        
        // 隐藏弹窗
        $('#progress-overlay').hide();
        $('#statistics').hide();
        $('#close-progress').hide();
        
        // 关闭进度后，重置后端进度状态
        $.ajax({
            url: '/reset_progress',
            type: 'POST',
            success: function(response) {
                log('info', '进度状态已重置');
            },
            error: function(xhr, status, error) {
                log('error', '重置进度状态失败', error);
            }
        });
    });
});

/**
 * 加载文件列表
 * 向服务器发送请求，获取指定路径下的文件列表
 * 然后生成HTML并显示在页面上
 */
function loadFiles() {
    log('info', '开始加载文件列表，路径: ' + currentPath);
    
    $.ajax({
        url: '/get_files',
        type: 'POST',
        data: { path: currentPath },
        success: function(response) {
            log('info', '文件列表加载成功，路径: ' + currentPath, response);
            
            currentPath = response.current_path;
            $('#current-path').text(currentPath);
            
            // 生成文件列表HTML
            let fileListHtml = '';
            
            // 添加返回上级目录项（如果不是根目录）
            if (currentPath !== baseDir) {
                log('debug', '添加返回上级目录项');
                const lastSeparatorIndex = Math.max(
                    currentPath.lastIndexOf('/'),
                    currentPath.lastIndexOf('\\')
                );
                const parentPath = lastSeparatorIndex > 0 ? currentPath.substring(0, lastSeparatorIndex) : baseDir;
                fileListHtml += '<li class="file-list-item" data-path="' + parentPath + '" data-type="dir">';
                fileListHtml += '<span class="icon">📁</span>';
                fileListHtml += '<span class="filename">..</span>';
                fileListHtml += '</li>';
            }
            
            // 添加文件和文件夹
            log('info', '共加载 ' + response.files.length + ' 个文件/文件夹');
            for (const file of response.files) {
                log('debug', '添加文件/文件夹: ' + file.name, file);
                
                fileListHtml += '<li class="file-list-item" data-path="' + file.path + '" data-type="' + file.type + '">';
                
                // 复选框
                fileListHtml += '<input type="checkbox" class="checkbox" ' + (selectedFiles.includes(file.path) ? 'checked' : '') + '>';
                
                // 图标
                if (file.type === 'dir') {
                    fileListHtml += '<span class="icon">📁</span>';
                } else {
                    fileListHtml += '<span class="icon">🖼️</span>';
                }
                
                // 文件名
                fileListHtml += '<span class="filename">' + file.name + '</span>';
                
                // 文件大小
                if (file.type === 'file') {
                    const size = formatFileSize(file.size);
                    fileListHtml += '<span class="filesize">' + size + '</span>';
                }
                
                fileListHtml += '</li>';
            }
            
            // 更新文件列表
            log('info', '更新文件列表HTML');
            $('#file-list').html(fileListHtml);
            
            // 绑定文件列表事件
            bindFileListEvents();
        },
        error: function(xhr, status, error) {
            log('error', '文件列表加载失败', error);
            alert('加载文件失败: ' + error);
        }
    });
}

// 绑定文件列表事件
function bindFileListEvents() {
    // 点击文件列表项
    $('.file-list-item').on('click', function(e) {
        const path = $(this).data('path');
        const type = $(this).data('type');
        
        // 如果点击的是文件名，处理不同类型
        if (e.target.classList.contains('filename') || e.target.classList.contains('icon')) {
            if (type === 'dir') {
                // 进入文件夹
                currentPath = path;
                loadFiles();
            } else {
                // 预览图片
                previewImage(path);
            }
        }
    });
    
    // 点击复选框
    $('.file-list-item .checkbox').on('click', function(e) {
        e.stopPropagation(); // 阻止事件冒泡
        
        const fileItem = $(this).closest('.file-list-item');
        const path = fileItem.data('path');
        
        if ($(this).is(':checked')) {
            // 添加到已选择列表
            if (!selectedFiles.includes(path)) {
                selectedFiles.push(path);
            }
        } else {
            // 从已选择列表中移除
            const index = selectedFiles.indexOf(path);
            if (index > -1) {
                selectedFiles.splice(index, 1);
            }
        }
        
        // 更新已选择列表
            updateSelectedFilesList();
            // 更新按钮状态
            updateButtons();
    });
}

// 更新已选择文件列表
function updateSelectedFilesList() {
    if (selectedFiles.length === 0) {
        $('#selected-files-list').html('<p class="no-selection">未选择任何文件</p>');
    } else {
        let selectedHtml = '';
        for (const path of selectedFiles) {
            const filename = path.substring(Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')) + 1);
            // 检测是否为文件夹，通过查找文件列表中的数据类型
            let isDir = false;
            // 在文件列表中查找对应的项，检查其数据类型
            const fileItem = $('.file-list-item[data-path="' + path.replace(/"/g, '\\"') + '"]');
            if (fileItem.length > 0) {
                isDir = fileItem.data('type') === 'dir';
            } else {
                // 如果找不到对应的项，尝试通过文件名判断
                // 文件夹通常没有扩展名，或者是已知的目录名
                const hasExtension = filename.includes('.');
                isDir = !hasExtension;
            }
            // 添加图标，文件夹显示📁，文件显示🖼️
            const icon = isDir ? '📁' : '🖼️';
            selectedHtml += '<div class="selected-file-item" data-path="' + path + '">';
            selectedHtml += '<span class="file-icon">' + icon + '</span>';
            selectedHtml += '<span class="filename">' + filename + '</span>';
            selectedHtml += '<button class="remove-btn" title="移除">&times;</button>';
            selectedHtml += '</div>';
        }
        $('#selected-files-list').html(selectedHtml);
        
        // 绑定移除按钮事件
        $('.remove-btn').on('click', function() {
            const fileItem = $(this).closest('.selected-file-item');
            const path = fileItem.data('path');
            
            // 从已选择列表中移除
            const index = selectedFiles.indexOf(path);
            if (index > -1) {
                selectedFiles.splice(index, 1);
            }
            
            // 更新UI
            fileItem.remove();
            if (selectedFiles.length === 0) {
                $('#selected-files-list').html('<p class="no-selection">未选择任何文件</p>');
            }
            
            // 更新按钮状态
            updateButtons();
            
            // 更新左侧文件列表中的复选框
            $('.file-list-item').each(function() {
                if ($(this).data('path') === path) {
                    $(this).find('.checkbox').prop('checked', false);
                }
            });
        });
    }
}

// 更新按钮状态
function updateButtons() {
    if (selectedFiles.length > 0) {
        $('#compress-btn').removeAttr('disabled');
        $('#convert-btn').removeAttr('disabled');
    } else {
        $('#compress-btn').attr('disabled', 'disabled');
        $('#convert-btn').attr('disabled', 'disabled');
    }
}

// 预览图片
function previewImage(path) {
    // 检查文件扩展名
    const ext = path.split('.').pop().toLowerCase();
    
    // 如果是PDF文件，直接下载而不预览
    if (ext === 'pdf') {
        console.log('直接下载PDF文件:', path);
        // 创建临时链接下载文件
        const link = document.createElement('a');
        link.href = '/download?path=' + encodeURIComponent(path);
        link.download = path.substring(Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')) + 1);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        return;
    }
    
    // 发送请求获取图片信息
    $.ajax({
        url: '/preview_image',
        type: 'POST',
        data: { path: path },
        success: function(response) {
            // 显示图片预览
            if (ext === 'tiff' || ext === 'tif') {
                // TIFF格式浏览器可能不支持直接显示，转换为PNG显示
                $('#preview-image').attr('src', '/convert_tiff_preview?path=' + encodeURIComponent(path));
            } else {
                // 其他图片格式，直接构建预览URL
                let previewPath = path;
                // 替换Windows路径分隔符为Unix风格
                previewPath = previewPath.replace(/\\/g, '/');
                // 移除base_dir前缀（如果存在）
                if (baseDir && previewPath.startsWith(baseDir)) {
                    previewPath = previewPath.substring(baseDir.length);
                    // 如果预览路径以/开头，移除它，因为路由已经包含了/preview/
                    if (previewPath.startsWith('/')) {
                        previewPath = previewPath.substring(1);
                    }
                }
                // 确保预览URL格式正确
                const previewUrl = '/preview/' + encodeURIComponent(previewPath);
                console.log('图片预览URL:', previewUrl);
                $('#preview-image').attr('src', previewUrl);
            }
            
            // 显示图片信息
            let infoHtml = '';
            const filename = path.substring(Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')) + 1);
            infoHtml += '<p><strong>文件名:</strong> ' + filename + '</p>';
            infoHtml += '<p><strong>尺寸:</strong> ' + response.width + ' × ' + response.height + ' 像素</p>';
            infoHtml += '<p><strong>格式:</strong> ' + response.format + '</p>';
            infoHtml += '<p><strong>大小:</strong> ' + formatFileSize(response.size) + '</p>';
            
            $('#image-info').html(infoHtml);
            
            // 显示模态框
            $('#image-preview-modal').modal('show');
        },
        error: function(xhr, status, error) {
            alert('预览图片失败: ' + error);
        }
    });
}

// 处理长路径显示，只显示路径的后半部分，前面用省略号代替
function truncatePath(path, maxLength = 80) {
    if (!path) return '';
    if (path.length <= maxLength) return path;
    
    // 找到所有分隔符，确定所有路径段
    const isWindowsPath = path.includes('\\');
    const separator = isWindowsPath ? '\\' : '/';
    const allSeparators = [];
    
    // 收集所有分隔符位置
    let index = path.indexOf(separator);
    while (index !== -1) {
        allSeparators.push(index);
        index = path.indexOf(separator, index + 1);
    }
    
    // 没有分隔符，直接返回文件名
    if (allSeparators.length === 0) {
        return path;
    }
    
    // 确定文件名
    const lastSep = allSeparators[allSeparators.length - 1];
    const filename = path.slice(lastSep + 1);
    
    // 如果文件名本身超过最大长度，只显示文件名后半部分
    if (filename.length > maxLength - 3) {
        return '...' + filename.slice(-maxLength + 3);
    }
    
    // 从后往前尝试包含更多路径段，直到总长度不超过maxLength
    let bestResult = '...' + filename;
    
    // 从最后一个路径段开始，向前添加
    for (let i = allSeparators.length - 1; i >= 0; i--) {
        const currentSep = allSeparators[i];
        const currentPath = '...' + path.slice(currentSep + 1);
        
        if (currentPath.length <= maxLength) {
            bestResult = currentPath;
        } else {
            break;
        }
    }
    
    return bestResult;
}

// 更新进度
function updateProgress() {
    log('debug', '开始调用updateProgress');
    log('debug', '当前progressInterval状态:', progressInterval ? 'running' : 'stopped');
    
    $.ajax({
        url: '/get_progress',
        type: 'GET',
        success: function(response) {
            log('debug', 'get_progress响应:', response);
            
            // 无论进度状态如何，都更新总文件数和已处理文件数
            $('#total-files').text(response.total);
            $('#processed-files').text(response.processed);
            
            // 更新当前正在处理的图片路径，处理长路径显示
            const currentFile = response.current_file || '';
            let truncatedPath = '';
            if (response.status === 'running') {
                truncatedPath = truncatePath(currentFile, 80); // 设置最大显示长度为80个字符
                $('#current-file').text(truncatedPath);
            } else {
                // 当处理完成或空闲时，清空当前文件显示
                $('#current-file').text('');
            }
            
            // 计算并更新进度条，精确到0.1%
            const progress = response.total > 0 ? parseFloat(((response.processed / response.total) * 100).toFixed(1)) : 0;
            $('#progress-bar').css('width', progress + '%').attr('aria-valuenow', progress);
            $('#progress-percentage').text(progress + '%');
            
            log('debug', 'UI更新完成:', {
                total: response.total,
                processed: response.processed,
                current_file: currentFile,
                truncated_path: truncatedPath,
                progress: progress + '%',
                status: response.status
            });
            
            // 处理进度状态
            if (response.status === 'running') {
                log('debug', '进度状态为running，显示进度窗口');
                // 处理运行中，显示进度窗口
                $('#progress-overlay').show();
                // 隐藏统计信息和关闭按钮
                $('#statistics').hide();
                $('#close-progress').hide();
                
                // 确保轮询定时器正在运行
                if (!progressInterval) {
                    progressInterval = setInterval(updateProgress, 1000);
                    log('info', '开始进度轮询');
                    log('debug', '创建了新的进度轮询定时器:', progressInterval);
                }
            } else if (response.status === 'completed') {
                log('debug', '进度状态为completed，显示统计信息');
                // 显示统计信息
                $('#statistics').show();
                $('#close-progress').show();
                $('#progress-overlay').show();
                
                // 计算总耗时
                const startTime = new Date(response.start_time);
                const endTime = new Date(response.end_time);
                const totalTime = Math.round((endTime - startTime) / 1000);
                
                // 计算大小（MB）
                const originalSize = (response.original_size / (1024 * 1024)).toFixed(2);
                const finalSize = (response.final_size / (1024 * 1024)).toFixed(2);
                
                // 计算压缩率
                const compressionRate = response.original_size > 0 ? Math.round((1 - response.final_size / response.original_size) * 100) : 0;
                
                // 更新统计信息
                $('#total-time').text(totalTime);
                $('#original-size').text(originalSize);
                $('#final-size').text(finalSize);
                $('#compression-rate').text(compressionRate);
                
                log('debug', '统计信息更新完成:', {
                    totalTime: totalTime,
                    originalSize: originalSize,
                    finalSize: finalSize,
                    compressionRate: compressionRate + '%'
                });
                
                // 图片处理完成后，刷新文件列表
                loadFiles();
                
                // 停止轮询
                if (progressInterval) {
                    clearInterval(progressInterval);
                    progressInterval = null;
                    log('info', '停止进度轮询');
                    log('debug', '停止了进度轮询定时器');
                }
            } else if (response.status === 'idle') {
                log('debug', '进度状态为idle');
                // 停止轮询
                if (progressInterval) {
                    clearInterval(progressInterval);
                    progressInterval = null;
                    log('info', '停止进度轮询');
                    log('debug', '停止了进度轮询定时器');
                }
            } else {
                log('debug', '未知进度状态:', response.status);
            }
        },
        error: function(xhr, status, error) {
            log('error', '获取进度失败:', {
                xhr: xhr,
                status: status,
                error: error
            });
        }
    });
}

// 格式化文件大小，根据数值动态改变单位
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1);
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 加载配置信息
 * 从后端获取配置的BASE_DIR路径和CPU核心数
 * 设置当前路径并更新线程数滑块的最大值和默认值
 * 然后加载文件列表
 */
function loadConfig() {
    log('info', '开始加载配置信息');
    
    $.ajax({
        url: '/get_config',
        type: 'GET',
        success: function(response) {
            log('info', '配置加载成功', response);
            baseDir = response.base_dir;
            // 设置当前路径为baseDir
            currentPath = baseDir;
            
            // 获取CPU核心数并更新线程数滑块
            const cpuCount = response.cpu_count || 4;
            log('info', '获取CPU核心数:', cpuCount);
            
            // 计算默认线程数：CPU核心数的70%
            const defaultThreads = Math.max(1, Math.floor(cpuCount * 0.7));
            log('info', '计算默认线程数:', defaultThreads);
            
            // 更新压缩任务的线程数滑块
            $('#thread-count').attr('max', cpuCount);
            $('#thread-count').val(defaultThreads);
            $('#thread-value').text(defaultThreads);
            
            // 更新转换任务的线程数滑块
            $('#convert-thread-count').attr('max', cpuCount);
            $('#convert-thread-count').val(defaultThreads);
            $('#convert-thread-value').text(defaultThreads);
            
            // 加载文件列表
            log('info', '设置当前路径为', baseDir);
            loadFiles();
        },
        error: function(xhr, status, error) {
            log('error', '配置加载失败', error);
            // 加载失败时使用默认值
            baseDir = '/data';
            currentPath = baseDir;
            log('warn', '使用默认路径', baseDir);
            loadFiles();
        }
    });
}

// 加载支持的格式列表
function loadSupportedFormats() {
    log('info', '开始加载支持的图片格式列表');
    
    $.ajax({
        url: '/get_supported_formats',
        type: 'GET',
        success: function(response) {
            const formats = response.formats;
            const targetFormatSelect = $('#target-format');
            
            // 清空现有选项
            targetFormatSelect.empty();
            
            // 添加支持的格式选项
            for (const format of formats) {
                const option = $('<option>').val(format).text(format.toUpperCase());
                targetFormatSelect.append(option);
            }
            
            // 更新支持的格式全局变量
            supportedFormats = formats;
            log('info', '支持的图片格式列表加载成功', formats);
        },
        error: function(xhr, status, error) {
            log('error', '加载支持的图片格式列表失败', error);
        }
    });
}