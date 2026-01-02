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
// 是否正在进行图片处理（压缩或转换）
let isProcessing = false;
// 是否正在发送停止请求
let isStopping = false;
// 模态框预览是否正在加载
let isModalPreviewLoading = false;
// 鼠标悬停预览
let hoverTimeout = null;
// 保存每个目录的滚动位置
let scrollPositions = {};
// 文件列表元素
let fileListElement = null;
// 目录历史记录
let history = [];
// 当前历史记录索引
let historyIndex = -1;
// 历史记录最大长度
const MAX_HISTORY_LENGTH = 20;

$(document).ready(function() {
    // 初始化文件列表元素
    fileListElement = $('#file-list');
    
    // 添加滚动事件监听器，保存滚动位置
    fileListElement.on('scroll', function() {
        // 保存当前目录的滚动位置
        scrollPositions[currentPath] = $(this).scrollTop();
    });
    
    // 添加全局鼠标事件监听，捕获所有鼠标事件
    // 使用mousedown事件监听鼠标侧键，这是最可靠的方式
    $(document).on('mousedown', function(e) {
        // 鼠标侧键通常会产生button值为3（后退）和4（前进）
        // 检查是否是侧键事件
        if (e.originalEvent.button === 3) {
            // 后退键 (Mouse4)
            e.preventDefault();
            log('info', '鼠标侧键后退 (mousedown)');
            $('#back-btn').click();
        } else if (e.originalEvent.button === 4) {
            // 前进键 (Mouse5)
            e.preventDefault();
            log('info', '鼠标侧键前进 (mousedown)');
            goForward();
        }
    });
    
    // 添加全局mouseup事件监听，确保所有侧键事件都能被捕获
    $(document).on('mouseup', function(e) {
        // 鼠标侧键通常会产生button值为3（后退）和4（前进）
        // 检查是否是侧键事件
        if (e.originalEvent.button === 3) {
            // 后退键 (Mouse4)
            e.preventDefault();
            log('info', '鼠标侧键后退 (mouseup)');
        } else if (e.originalEvent.button === 4) {
            // 前进键 (Mouse5)
            e.preventDefault();
            log('info', '鼠标侧键前进 (mouseup)');
        }
    });
    
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
        log('info', '返回上级按钮点击，当前路径: ' + currentPath + ', 基础目录: ' + baseDir);
        if (currentPath !== baseDir) {
            // 同时处理Windows和Unix路径分隔符
            const lastSeparatorIndex = Math.max(
                currentPath.lastIndexOf('/'),
                currentPath.lastIndexOf('\\')
            );
            if (lastSeparatorIndex > 0) {
                const parentPath = currentPath.substring(0, lastSeparatorIndex);
                log('info', '当前路径: ' + currentPath + ', 父路径: ' + parentPath);
                
                // 检查当前索引是否大于0
                if (historyIndex > 0) {
                    // 如果有前进历史记录，直接减少索引
                    historyIndex--;
                    log('info', '历史记录索引减少: ' + historyIndex);
                } else {
                    // 如果当前是第一个记录，保持索引为0
                    log('info', '历史记录索引保持为0');
                }
                
                // 设置当前路径为父路径
                currentPath = parentPath;
                
                // 立即更新当前路径显示
                $('#current-path').text(currentPath);
            } else {
                // 如果已经是根目录，保持不变
                currentPath = baseDir;
                historyIndex = 0;
            }
            // 回到上级目录时不自动进入子文件夹，并且从历史记录加载
            log('info', '加载父路径: ' + currentPath + ', fromHistory: true, 新索引: ' + historyIndex);
            loadFiles(false, true);
        } else {
            log('info', '已经是根目录，无法返回上级');
        }
    });
    
    // 前进功能
    function goForward() {
        log('info', '前进功能调用，当前历史记录: ' + JSON.stringify(history) + ', 长度: ' + history.length + ', 当前索引: ' + historyIndex);
        // 检查历史记录长度和当前索引
        if (history.length === 0) {
            log('info', '历史记录为空');
            return;
        }
        
        if (historyIndex < history.length - 1) {
            // 如果有前进历史记录
            historyIndex++;
            // 获取前进路径
            const forwardPath = history[historyIndex];
            log('info', '前进到: ' + forwardPath + ', 新索引: ' + historyIndex);
            // 设置当前路径
            currentPath = forwardPath;
            // 立即更新当前路径显示
            $('#current-path').text(currentPath);
            // 加载文件列表，不自动进入子文件夹
            loadFiles(false, true);
        } else {
            log('info', '没有前进历史记录，当前已经是最新记录');
            log('info', '历史记录详情: 索引范围 0-' + (history.length - 1) + ', 当前索引: ' + historyIndex);
        }
    }
    
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
                resultHtml += '<th>操作</th>';
                resultHtml += '</tr>';
                resultHtml += '</thead>';
                resultHtml += '<tbody>';
                
                for (const [format, count] of Object.entries(response.format_count)) {
                    const size = response.format_size[format] || 0;
                    const avgSize = count > 0 ? size / count : 0;
                    resultHtml += '<tr>';
                    resultHtml += '<td>' + format + '</td>';
                    resultHtml += '<td>' + count + '</td>';
                    resultHtml += '<td>' + formatFileSize(size) + '</td>';
                    resultHtml += '<td>' + formatFileSize(avgSize) + '</td>';
                    resultHtml += '<td><button class="btn btn-danger btn-sm delete-format-btn" data-format="' + format + '" title="删除所有该格式文件">删除</button></td>';
                    resultHtml += '</tr>';
                }
                
                resultHtml += '</tbody>';
                resultHtml += '</table>';
                resultHtml += '</div>';
                
                // 更新模态框内容并显示
                $('#statistics-result').html(resultHtml);
                $('#statistics-modal').modal('show');
                
                // 为删除按钮添加点击事件
                $('.delete-format-btn').on('click', function() {
                    const format = $(this).data('format');
                    const count = response.format_count[format];
                    
                    // 显示确认对话框
                    if (confirm(`确定要删除所有${format.toUpperCase()}格式的文件吗？共${count}个文件将被删除，此操作不可恢复！`)) {
                        // 显示加载动画
                        $('#loading').show();
                        
                        // 发送删除请求
                        $.ajax({
                            url: '/delete_files_by_format',
                            type: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify({
                                selected_paths: selectedFiles,
                                format: format
                            }),
                            success: function(response) {
                                $('#loading').hide();
                                alert(`成功删除${response.deleted_count}个${format.toUpperCase()}格式的文件`);
                                // 刷新文件列表
                                loadFiles();
                                // 关闭统计模态框
                                $('#statistics-modal').modal('hide');
                            },
                            error: function(xhr, status, error) {
                                $('#loading').hide();
                                alert('删除失败: ' + error);
                            }
                        });
                    }
                });
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
        
        if (!confirm('确定要修复选中路径下所有文件的后缀名吗？这将把所有大写后缀改为小写（例如PNG->png, Jpg->jpg），并将jpeg改为jpg。')) {
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
                
                // 调试信息
                console.log('修复结果响应:', response);
                
                // 准备结果数据，确保是数组类型
                const processed = response.processed || 0;
                const skippedFiles = Array.isArray(response.skipped_files) ? response.skipped_files : [];
                const failedFiles = Array.isArray(response.failed_files) ? response.failed_files : [];
                
                // 调试信息
                console.log('处理的文件数:', processed);
                console.log('跳过的文件数:', skippedFiles.length);
                console.log('失败的文件数:', failedFiles.length);
                
                // 更新结果摘要
                let summaryHtml = `<p><strong>修复完成，共处理 ${processed} 个文件</strong></p>`;
                if (skippedFiles.length > 0) {
                    summaryHtml += `<p class="text-warning">跳过 ${skippedFiles.length} 个文件（文件已存在）</p>`;
                }
                if (failedFiles.length > 0) {
                    summaryHtml += `<p class="text-danger">修复失败 ${failedFiles.length} 个文件</p>`;
                }
                $('#fix-result-summary').html(summaryHtml);
                
                // 为模态框添加关闭事件，清除之前的列表内容
                $('#fix-result-modal').off('hidden.bs.modal').on('hidden.bs.modal', function() {
                    // 清除摘要信息
                    $('#fix-result-summary').html('');
                    
                    // 清除跳过列表
                    $('#fix-skipped-files-list').html('');
                    $('#fix-skipped-count').text('0');
                    $('#fix-skipped-files-section').hide();
                    
                    // 清除失败列表
                    $('#fix-failed-files-list').html('');
                    $('#fix-failed-count').text('0');
                    $('#fix-failed-files-section').hide();
                    
                    // 调试信息
                    console.log('修复结果模态框已关闭，已清除所有内容');
                });
                
                // 显示结果模态框
                $('#fix-result-modal').modal('show');
                
                // 延迟设置内部元素显示状态，确保模态框已经显示
                setTimeout(function() {
                    // 显示跳过的文件列表
                    if (skippedFiles.length > 0) {
                        $('#skipped-count').text(skippedFiles.length);
                        
                        // 生成HTML，使用带分割线的样式
                    let skippedHtml = '';
                    for (let i = 0; i < skippedFiles.length; i++) {
                        const file = skippedFiles[i];
                        skippedHtml += `<div style="padding: 8px 0; border-bottom: 1px solid #e9ecef; word-break: break-all; word-wrap: break-word;">${file}</div>`;
                    }
                    
                    // 设置文件列表内容
                    $('#fix-skipped-files-list').html(skippedHtml);
                        
                        // 显示section
                        $('#fix-skipped-files-section').show();
                    } else {
                        // 隐藏跳过文件section
                        $('#fix-skipped-files-section').hide();
                    }
                    
                    // 显示失败的文件列表
                    if (failedFiles.length > 0) {
                        $('#failed-count').text(failedFiles.length);
                        
                        // 生成HTML，使用带分割线的样式
                    let failedHtml = '';
                    for (let i = 0; i < failedFiles.length; i++) {
                        const file = failedFiles[i];
                        const filePath = file.path || '未知路径';
                        const fileError = file.error || '未知错误';
                        failedHtml += `<div style="padding: 8px 0; border-bottom: 1px solid #e9ecef; word-break: break-all; word-wrap: break-word;"><strong>${filePath}</strong>: ${fileError}</div>`;
                    }
                    
                    // 设置文件列表内容
                    $('#fix-failed-files-list').html(failedHtml);
                        
                        // 显示section
                        $('#fix-failed-files-section').show();
                    } else {
                        // 隐藏失败文件section
                        $('#fix-failed-files-section').hide();  
                    }
                }, 100);
                
                // 调试信息：显示模态框调用
                console.log('显示修复结果模态框');
                
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
        
        // 更新进度标题
        $('#progress-title').text('图片压缩');
        
        // 设置处理标志位为true
        isProcessing = true;
        
        // 关闭可能已经显示的悬浮预览
        hideHoverPreview();
        
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
                // 设置处理标志位为false
                isProcessing = false;
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
        
        // 更新进度标题
        $('#progress-title').text(`图片转换成${targetFormat}`);
        
        // 设置处理标志位为true
        isProcessing = true;
        
        // 关闭可能已经显示的悬浮预览
        hideHoverPreview();
        
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
                // 设置处理标志位为false
                isProcessing = false;
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
    
    // 停止处理按钮
    $('#stop-progress').on('click', function() {
        // 如果正在发送停止请求，不允许再次点击
        if (isStopping) {
            return;
        }
        
        if (confirm('确定要停止当前处理吗？已开始处理的图片会继续完成，未开始的图片将被取消。')) {
            // 设置停止请求标记
            isStopping = true;
            
            // 将按钮置灰，不允许再次点击
            $(this).prop('disabled', true).text('停止中...');
            
            // 发送停止请求
            $.ajax({
                url: '/stop_processing',
                type: 'POST',
                success: function(response) {
                    log('info', '停止处理请求已发送');
                    // 重置停止请求标记
                    isStopping = false;
                    // 停止请求成功后，保持停止按钮显示，但禁用并修改文本
                    $('#stop-progress').prop('disabled', true).text('已停止');
                    // 不要立即显示关闭按钮，等待处理完成后由updateProgress自动处理
                },
                error: function(xhr, status, error) {
                    log('error', '发送停止请求失败', error);
                    // 重置停止请求标记
                    isStopping = false;
                    // 恢复按钮状态
                    $('#stop-progress').prop('disabled', false).text('停止处理');
                    alert('停止请求失败: ' + error);
                }
            });
        }
    });
    
    // 关闭进度按钮
    $('#close-progress').on('click', function() {
        // 重置进度相关DOM元素
        $('#total-files').text('0');
        $('#processed-files').text('0');
        $('#current-file').text('');
        $('#progress-bar').css('width', '0%').attr('aria-valuenow', '0');
        
        // 重置进度标题
        $('#progress-title').text('处理进度');
        
        // 隐藏文件列表
        $('#failed-files-section').hide();
        $('#skipped-files-section').hide();
        
        // 隐藏弹窗
        $('#progress-overlay').hide();
        $('#statistics').hide();
        $('#close-progress').hide();
        
        // 设置处理标志位为false
        isProcessing = false;
        
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
 * @param {boolean} autoEnter - 是否自动进入子文件夹，默认为true
 * @param {boolean} fromHistory - 是否从历史记录加载，默认为false
 */
function loadFiles(autoEnter = true, fromHistory = false) {
    log('info', '开始加载文件列表，路径: ' + currentPath + ', autoEnter: ' + autoEnter + ', fromHistory: ' + fromHistory);
    // 立即清除悬浮预览的延迟
    if (hoverTimeout) {
        clearTimeout(hoverTimeout);
        hoverTimeout = null;
    }

    // 关闭当前可能显示的悬浮预览
    hideHoverPreview();
    
    $.ajax({
        url: '/get_files',
        type: 'POST',
        data: { 
            path: currentPath,
            auto_enter: autoEnter
        },
        success: function(response) {
            log('info', '文件列表加载成功，路径: ' + response.current_path, response);
            
            currentPath = response.current_path;
            $('#current-path').text(currentPath);
            
            // 更新历史记录
            if (!fromHistory) {
                // 如果不是从历史记录加载，更新历史记录
                log('info', '更新历史记录前 - 当前索引: ' + historyIndex + ', 历史记录长度: ' + history.length);
                
                // 检查当前路径是否已经是历史记录的最后一个元素
                if (history.length === 0 || history[history.length - 1] !== currentPath) {
                    // 如果当前路径不在历史记录中或不是最新记录
                    // 检查当前索引是否是历史记录的最后一个索引
                    if (historyIndex < history.length - 1) {
                        // 如果当前不是最新历史记录，删除当前索引之后的所有历史记录
                        log('info', '进入新目录分支，删除多余历史记录');
                        history = history.slice(0, historyIndex + 1);
                        log('info', '历史记录裁剪后: ' + JSON.stringify(history));
                    }
                    
                    // 添加当前路径到历史记录
                    history.push(currentPath);
                    // 更新历史记录索引
                    historyIndex = history.length - 1;
                    
                    // 检查历史记录长度，如果超过最大长度，删除最旧的记录
                    if (history.length > MAX_HISTORY_LENGTH) {
                        log('info', '历史记录超过最大长度，删除最旧记录');
                        history.shift(); // 删除第一个元素
                        historyIndex--;
                        log('info', '历史记录裁剪后: ' + JSON.stringify(history));
                    }
                    
                    log('info', '历史记录更新: ' + JSON.stringify(history) + ', 当前索引: ' + historyIndex);
                }
            }
            
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
            
            // 恢复滚动位置
            setTimeout(function() {
                const savedScroll = scrollPositions[currentPath] || 0;
                log('debug', '恢复滚动位置: ' + savedScroll + ' for path: ' + currentPath);
                fileListElement.scrollTop(savedScroll);
            }, 0);
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
        const filename = $(this).find('.filename').text();
        
        // 立即清除悬浮预览的延迟，避免两种预览同时出现
        if (hoverTimeout) {
            clearTimeout(hoverTimeout);
            hoverTimeout = null;
        }
        
        // 如果点击的不是复选框，处理不同类型
        if (!e.target.classList.contains('checkbox')) {
            if (type === 'dir') {
                // 进入文件夹
                log('info', '点击文件夹: ' + filename + ', 路径: ' + path);
                if (filename === '..') {
                    // 如果是返回上级目录(..)，使用返回上级功能
                    $('#back-btn').click();
                } else {
                    // 进入新文件夹，历史记录管理由loadFiles函数处理
                    currentPath = path;
                    loadFiles(true);
                }
            } else {
                // 预览图片
                previewImage(path);
            }
        }
    });
    
    // 点击复选框
    $('.file-list-item .checkbox').on('click', function(e) {
        e.stopPropagation(); // 阻止事件冒泡到父元素
        
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
        
        // 更新已选择列表和按钮状态
        updateSelectedFilesList();
        updateButtons();
    });
    
    
    // 鼠标进入事件
    $('.file-list-item').on('mouseenter', function(e) {
        // 如果模态框预览正在加载，不显示悬浮预览
        if (isModalPreviewLoading) {
            return;
        }

        const path = $(this).data('path');
        const type = $(this).data('type');
        
        // 保存当前鼠标位置
        const mouseX = e.pageX;
        const mouseY = e.pageY;
        
        // 只有文件类型且不是PDF才触发预览
        if (type === 'file') {
            // 正确提取文件名，处理Linux和Windows路径
            const lastSlashIndex = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
            const filename = lastSlashIndex === -1 ? path : path.substring(lastSlashIndex + 1);
            const ext = filename.toLowerCase().split('.').pop();
            
            // 检查是否是PDF文件
            if (ext === 'pdf') {
                return; // PDF文件不进行预览
            }
            
            // 1.5秒后显示预览，传递鼠标位置
            hoverTimeout = setTimeout(function() {
                showHoverPreview(path, mouseX, mouseY);
            }, 1500);
        }
    });
    
    // 鼠标离开事件
    $('.file-list-item').on('mouseleave', function() {
        // 清除延迟预览
        if (hoverTimeout) {
            clearTimeout(hoverTimeout);
            hoverTimeout = null;
        }
        
        // 隐藏预览
        hideHoverPreview();
    });
}

// 显示悬停预览
function showHoverPreview(path, mouseX, mouseY) {
    // 如果弹窗预览已经打开，不显示悬浮预览
    if (isModalPreviewOpen) {
        return;
    }
    
    // 如果正在进行图片处理，不显示悬浮预览
    if (isProcessing) {
        return;
    }
    
    // 如果模态框预览正在加载，不显示悬浮预览
    if (isModalPreviewLoading) {
        return;
    }
    
    // 检查是否是PDF或HEIC文件
    const filename = path.substring(Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\') + 1));
    const ext = filename.toLowerCase().split('.').pop();
    
    if (ext === 'pdf' || ext === 'heic' || ext === 'heif') {
        return; // PDF和HEIC/HEIF文件不进行预览
    }
    
    // 获取预览URL
    let previewUrl = '';
    if (ext === 'tiff' || ext === 'tif') {
        // TIFF格式需要转换
        previewUrl = '/convert_tiff_preview?path=' + encodeURIComponent(path);
    } else {
        // 其他图片格式，构建预览URL
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
        previewUrl = '/preview/' + encodeURIComponent(previewPath);
    }
    
    // 计算预览框位置
    const previewWidth = $('#hover-preview').outerWidth();
    const previewHeight = $('#hover-preview').outerHeight();
    const winWidth = $(window).width();
    const winHeight = $(window).height();
    
    // 计算预览位置，避免超出窗口
    let left = mouseX + 10;
    let top = mouseY + 10;
    
    if (left + previewWidth > winWidth) {
        left = mouseX - previewWidth - 10;
    }
    if (top + previewHeight > winHeight) {
        top = mouseY - previewHeight - 10;
    }
    
    // 设置初始位置（但保持隐藏）
    $('#hover-preview').css({
        left: left + 'px',
        top: top + 'px',
        display: 'none' // 先隐藏，等图片加载完成后再显示
    });
    
    // 清空预览图片
    $('#hover-preview-image').attr('src', '');
    
    // 创建新的图片元素，避免直接替换src导致的闪烁
    const img = new Image();
    img.onload = function() {
        // 图片加载完成后，设置图片并显示预览框
        $('#hover-preview-image').attr('src', this.src);
        // 显示预览框
        $('#hover-preview').show();
    };
    img.onerror = function() {
        // 图片加载失败，不显示预览框
        log('error', '预览图片加载失败: ' + previewUrl);
    };
    img.src = previewUrl;
    
    // 绑定鼠标移动事件，更新预览框位置
    $(document).on('mousemove.hoverPreview', function(e) {
        // 重新计算预览位置
        let left = e.pageX + 10;
        let top = e.pageY + 10;
        
        if (left + previewWidth > winWidth) {
            left = e.pageX - previewWidth - 10;
        }
        if (top + previewHeight > winHeight) {
            top = e.pageY - previewHeight - 10;
        }
        
        // 更新预览位置
        $('#hover-preview').css({
            left: left + 'px',
            top: top + 'px'
        });
    });
}

// 隐藏悬停预览
function hideHoverPreview() {
    // 移除鼠标移动事件监听
    $(document).off('mousemove.hoverPreview');
    
    // 隐藏预览
    $('#hover-preview').hide();
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

// 用于跟踪弹窗预览是否打开的标志位
let isModalPreviewOpen = false;

// 预览图片
function previewImage(path) {
    // 设置模态框预览加载标志，防止悬浮预览冲突
    isModalPreviewLoading = true;
    
    // 立即清除悬浮预览的延迟
    if (hoverTimeout) {
        clearTimeout(hoverTimeout);
        hoverTimeout = null;
    }

    // 关闭当前可能显示的悬浮预览
    hideHoverPreview();
    
    // 检查文件扩展名
    const ext = path.split('.').pop().toLowerCase();
    
    // 如果是PDF或HEIC/HEIF文件，直接下载而不预览
    if (ext === 'pdf' || ext === 'heic' || ext === 'heif') {
        console.log('直接下载文件:', path);
        // 创建临时链接下载文件
        const link = document.createElement('a');
        link.href = '/download?path=' + encodeURIComponent(path);
        link.download = path.substring(Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')) + 1);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        // 清除加载标志
        isModalPreviewLoading = false;
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
                log('debug', '图片预览URL:', previewUrl);
                $('#preview-image').attr('src', previewUrl);
            }
            
            // 显示图片信息
            let infoHtml = '';
            // 正确提取文件名，处理Linux和Windows路径
            const lastSlashIndex = Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'));
            const filename = lastSlashIndex === -1 ? path : path.substring(lastSlashIndex + 1);
            infoHtml += '<p><strong>文件名:</strong> ' + filename + '</p>';
            infoHtml += '<p><strong>尺寸:</strong> ' + response.width + ' × ' + response.height + ' 像素</p>';
            infoHtml += '<p><strong>格式:</strong> ' + response.format + '</p>';
            infoHtml += '<p><strong>大小:</strong> ' + formatFileSize(response.size) + '</p>';
            
            // 显示EXIF信息（如果有）
            infoHtml += '<div class="mt-3">';
            if (response.exif && Object.keys(response.exif).length > 0) {
                // 有EXIF信息时，添加显示/隐藏按钮和EXIF信息容器
                infoHtml += '<button id="toggle-exif-btn" class="btn btn-sm btn-outline-secondary" style="margin-bottom: 10px;">显示EXIF信息</button>';
                infoHtml += '<div id="exif-info-container" style="display: none;">';
                infoHtml += '<h5 style="margin-top: 15px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">EXIF信息</h5>';
                infoHtml += '<div class="exif-info" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 14px;">';
                
                // 遍历EXIF数据，显示每个字段
                for (const [key, value] of Object.entries(response.exif)) {
                    // 跳过空值
                    if (value === null || value === undefined) continue;
                    // 跳过过长的值
                    const displayValue = typeof value === 'string' && value.length > 50 ? value.substring(0, 50) + '...' : value;
                    infoHtml += `<div class="exif-item" style="background: #f8f9fa; padding: 8px; border-radius: 4px;">`;
                    
                    // 为拍摄地址添加查询按钮到标题旁边
                    if (key === '拍摄地址') {
                        // 尝试提取经纬度
                        const coordsMatch = displayValue.match(/坐标: ([\d.-]+), ([\d.-]+)/);
                        if (coordsMatch) {
                            const lat = parseFloat(coordsMatch[1]);
                            const lon = parseFloat(coordsMatch[2]);
                            infoHtml += `<strong style="color: #495057; margin-bottom: 2px; display: inline-block;">${key}:</strong>`;
                            infoHtml += `<button class="query-address-btn btn btn-sm btn-outline-primary" 
                                        style="margin-left: 8px; margin-bottom: 4px; display: inline-flex; align-items: center; gap: 4px;" 
                                        data-lat="${lat}" data-lon="${lon}" title="查询详细地址">
                                        <span>查询地址</span>
                                        </button>`;
                        } else {
                            infoHtml += `<strong style="display: block; color: #495057; margin-bottom: 2px;">${key}:</strong>`;
                        }
                    } else {
                        infoHtml += `<strong style="display: block; color: #495057; margin-bottom: 2px;">${key}:</strong>`;
                    }
                    
                    infoHtml += `<span style="color: #6c757d; display: block;">${displayValue}</span>`;
                    infoHtml += `</div>`;
                }
                
                infoHtml += '</div>';
                infoHtml += '</div>'; // 关闭exif-info-container
            }
            infoHtml += '</div>'; // 关闭外层div
            
            $('#image-info').html(infoHtml);
            
            // 绑定EXIF信息显示/隐藏按钮事件（只有当按钮存在时才绑定）
            if (response.exif && Object.keys(response.exif).length > 0) {
                // 先移除旧的事件监听器，避免重复绑定
                $('#toggle-exif-btn').off('click');
                $('#toggle-exif-btn').on('click', function() {
                    const exifContainer = $('#exif-info-container');
                    if (exifContainer.is(':hidden')) {
                        exifContainer.show();
                        $(this).text('隐藏EXIF信息');
                    } else {
                        exifContainer.hide();
                        $(this).text('显示EXIF信息');
                    }
                });
                
                // 为查询地址按钮绑定点击事件
                // 先移除旧的事件监听器，避免重复绑定
                $('#image-info').off('click', '.query-address-btn');
                $('#image-info').on('click', '.query-address-btn', function() {
                    const lat = $(this).data('lat');
                    const lon = $(this).data('lon');
                    const button = $(this);
                    const originalText = button.text();
                    
                    // 显示加载状态
                    button.text('查询中...').prop('disabled', true);
                    
                    // 调用API查询地址
                    $.ajax({
                        url: '/get_address_from_coords',
                        type: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify({ lat: lat, lon: lon }),
                        success: function(response) {
                            if (response.address) {
                                // 更新显示的地址
                                const exifItem = button.closest('.exif-item');
                                exifItem.find('span').text(response.address);
                                // 隐藏查询按钮
                                button.hide();
                            } else {
                                alert('无法查询到地址');
                            }
                        },
                        error: function(xhr, status, error) {
                            log('error', '查询地址失败:', error);
                            let errorMsg = '查询地址失败';
                            if (xhr.responseJSON && xhr.responseJSON.error) {
                                errorMsg = '查询地址失败: ' + xhr.responseJSON.error;
                                log('error', '查询地址详细错误:', xhr.responseJSON.error);
                            }
                            alert(errorMsg);
                        },
                        complete: function() {
                            // 恢复按钮状态
                            button.text(originalText).prop('disabled', false);
                        }
                    });
                });
            }
            
            // 关闭悬浮预览
            hideHoverPreview();
            
            // 设置弹窗预览标志位为true
            isModalPreviewOpen = true;
            
            // 显示模态框
            $('#image-preview-modal').modal('show');
            
            // 确保事件只被绑定一次，使用one方法绑定一次性事件
            $('#image-preview-modal').off('hidden.bs.modal').on('hidden.bs.modal', function() {
                isModalPreviewOpen = false;
            });
            
            // 清除加载标志
            isModalPreviewLoading = false;
        },
        error: function(xhr, status, error) {
            alert('预览图片失败: ' + error);
            // 清除加载标志
            isModalPreviewLoading = false;
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
                // 显示停止按钮，隐藏关闭按钮
                $('#stop-progress').show();
                // 只有在isStopping为false时才恢复停止按钮状态，避免覆盖停止中的状态
                if (!isStopping && $('#stop-progress').text() !== '已停止') {
                    // 恢复停止按钮状态
                    $('#stop-progress').prop('disabled', false).text('停止处理');
                    // 重置停止请求标记
                    isStopping = false;
                }
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
                // 隐藏停止按钮，显示关闭按钮
                $('#stop-progress').hide();
                // 处理完成后，重置停止按钮状态，确保下次显示时是正常状态
                $('#stop-progress').prop('disabled', false).text('停止处理');
                // 重置停止请求标记
                isStopping = false;
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
                
                // 处理失败文件列表
                const failedFiles = response.failed_files || [];
                const failedCount = failedFiles.length;
                if (failedCount > 0) {
                    $('#failed-files-section').show();
                    $('#failed-files-count').text(failedCount);
                    let failedHtml = '';
                    for (const file of failedFiles) {
                        const truncated = truncatePath(file, 100);
                        failedHtml += `<div style="margin: 5px 0; padding: 5px; background-color: rgba(220, 53, 69, 0.8); color: white; border-radius: 4px;">${truncated}</div>`;
                    }
                    $('#failed-files').html(failedHtml);
                } else {
                    $('#failed-files-section').hide();
                    $('#failed-files-count').text('');
                }
                
                // 处理跳过文件列表
                const skippedFiles = response.skipped_files || [];
                const skippedCount = skippedFiles.length;
                if (skippedCount > 0) {
                    $('#skipped-files-section').show();
                    $('#skipped-files-count').text(skippedCount);
                    let skippedHtml = '';
                    for (const file of skippedFiles) {
                        const truncated = truncatePath(file, 100);
                        skippedHtml += `<div style="margin: 5px 0; padding: 5px; background-color: rgba(255, 193, 7, 0.8); color: black; border-radius: 4px;">${truncated}</div>`;
                    }
                    $('#skipped-files').html(skippedHtml);
                } else {
                    $('#skipped-files-section').hide();
                    $('#skipped-files-count').text('');
                }
                
                log('debug', '统计信息更新完成:', {
                    totalTime: totalTime,
                    originalSize: originalSize,
                    finalSize: finalSize,
                    compressionRate: compressionRate + '%',
                    failedFiles: failedFiles.length,
                    skippedFiles: skippedFiles.length
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
            
            // 初始化历史记录，添加基础目录到历史记录
            history = [baseDir];
            historyIndex = 0;
            log('info', '历史记录初始化: ' + JSON.stringify(history) + ', 当前索引: ' + historyIndex);
            
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