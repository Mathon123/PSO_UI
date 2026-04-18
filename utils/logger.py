"""
日志模块
========
统一的日志记录系统

【功能说明】
- 提供项目级日志记录器
- 支持控制台和文件双输出
- 自动记录异常堆栈信息
- 格式化日志输出

【日志级别】
DEBUG   - 调试信息（开发时使用）
INFO    - 一般信息（正常运行信息）
WARNING - 警告信息（潜在问题）
ERROR   - 错误信息（已发生的错误）
CRITICAL - 严重错误（可能导致崩溃）

【使用方式】
from utils.logger import logger

logger.info("程序启动")
logger.warning("内存使用较高")
logger.error("文件读取失败", exc_info=True)
"""

import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional


# =============================================================
# 日志配置常量
# =============================================================

# 默认日志级别
DEFAULT_LOG_LEVEL = logging.INFO

# 日志格式模板
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 日志文件目录
LOG_DIR = Path.home() / '.pso_ui' / 'logs'


# =============================================================
# 日志记录器类
# =============================================================

class PSOLogger:
    """
    PSO_UI专用日志记录器
    
    【功能特性】
    - 单例模式，全局唯一实例
    - 支持控制台和文件双输出
    - 自动创建日志目录
    - 异常信息自动追踪
    
    【使用示例】
    logger = PSOLogger.get_instance()
    logger.info("操作成功")
    logger.error("发生错误", exc_info=True)
    """
    
    _instance: Optional['PSOLogger'] = None
    
    def __new__(cls, name: str = "PSO_UI", level: int = DEFAULT_LOG_LEVEL):
        """
        单例模式实现
        
        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, name: str = "PSO_UI", level: int = DEFAULT_LOG_LEVEL):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        if self._initialized:
            return
            
        self._initialized = True
        self._name = name
        self._level = level
        self._logger: Optional[logging.Logger] = None
        self._file_handler: Optional[logging.FileHandler] = None
        
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """
        配置日志记录器
        
        【配置内容】
        1. 创建根日志记录器
        2. 设置日志级别
        3. 配置控制台处理器
        4. 配置文件处理器（可选）
        """
        # 创建日志记录器
        self._logger = logging.getLogger(self._name)
        self._logger.setLevel(self._level)
        
        # 避免重复添加处理器
        if self._logger.handlers:
            return
        
        # 创建格式化器
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        
        # ========== 控制台处理器 ==========
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._level)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # ========== 文件处理器 ==========
        try:
            self._setup_file_handler(formatter)
        except Exception as e:
            # 文件日志失败不影响程序运行
            console_handler_error = logging.StreamHandler(sys.stderr)
            console_handler_error.setLevel(logging.WARNING)
            console_handler_error.setFormatter(formatter)
            self._logger.addHandler(console_handler_error)
            self._logger.warning(f"无法创建日志文件: {e}")
    
    def _setup_file_handler(self, formatter: logging.Formatter) -> None:
        """
        配置文件日志处理器
        
        Args:
            formatter: 日志格式化器
        """
        # 创建日志目录
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # 生成日志文件名（按日期）
        log_date = datetime.now().strftime('%Y%m%d')
        log_file = LOG_DIR / f'pso_ui_{log_date}.log'
        
        # 创建文件处理器
        self._file_handler = logging.FileHandler(
            log_file,
            mode='a',
            encoding='utf-8'
        )
        self._file_handler.setLevel(self._level)
        self._file_handler.setFormatter(formatter)
        self._logger.addHandler(self._file_handler)
    
    @property
    def logger(self) -> logging.Logger:
        """
        获取日志记录器对象
        
        Returns:
            logging.Logger实例
        """
        return self._logger
    
    # ================================================================
    # 日志记录方法
    # ================================================================
    
    def debug(self, message: str, exc_info: bool = False) -> None:
        """
        记录调试信息
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常堆栈信息
        """
        self._logger.debug(message, exc_info=exc_info)
    
    def info(self, message: str, exc_info: bool = False) -> None:
        """
        记录一般信息
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常堆栈信息
        """
        self._logger.info(message, exc_info=exc_info)
    
    def warning(self, message: str, exc_info: bool = False) -> None:
        """
        记录警告信息
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常堆栈信息
        """
        self._logger.warning(message, exc_info=exc_info)
    
    def error(self, message: str, exc_info: bool = False) -> None:
        """
        记录错误信息
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常堆栈信息
        """
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True) -> None:
        """
        记录严重错误信息
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常堆栈信息（默认True）
        """
        self._logger.critical(message, exc_info=exc_info)
    
    def log_exception(self, message: str, exc: Exception = None) -> None:
        """
        记录异常信息（包含堆栈追踪）
        
        Args:
            message: 日志消息前缀
            exc: 异常对象（可选）
        """
        if exc is not None:
            self._logger.error(
                f"{message}\n异常类型: {type(exc).__name__}\n"
                f"异常消息: {str(exc)}\n"
                f"堆栈追踪:\n{traceback.format_exc()}"
            )
        else:
            self._logger.error(
                f"{message}\n堆栈追踪:\n{traceback.format_exc()}"
            )
    
    def log_ui_event(self, event: str, details: str = None) -> None:
        """
        记录UI事件
        
        Args:
            event: 事件名称
            details: 事件详情（可选）
        """
        msg = f"[UI事件] {event}"
        if details:
            msg += f" - {details}"
        self._logger.info(msg)
    
    def log_optimization_progress(self, iteration: int, rmse: float, 
                                   total_iterations: int = None) -> None:
        """
        记录优化进度
        
        Args:
            iteration: 当前迭代次数
            rmse: 当前RMSE值
            total_iterations: 总迭代次数（可选）
        """
        if total_iterations:
            progress = f"[优化进度] 迭代 {iteration}/{total_iterations}"
        else:
            progress = f"[优化进度] 迭代 {iteration}"
        
        self._logger.info(f"{progress} - RMSE: {rmse:.6f}")
    
    def set_level(self, level: int) -> None:
        """
        设置日志级别
        
        Args:
            level: 日志级别 (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._level = level
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            handler.setLevel(level)
    
    def flush(self) -> None:
        """
        刷新日志缓冲区
        """
        if self._file_handler:
            self._file_handler.flush()


# =============================================================
# 全局日志实例访问
# =============================================================

_logger_instance: Optional[PSOLogger] = None


def get_logger(name: str = "PSO_UI", level: int = DEFAULT_LOG_LEVEL) -> PSOLogger:
    """
    获取日志记录器单例
    
    Args:
        name: 日志记录器名称
        level: 日志级别
    
    Returns:
        PSOLogger实例
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PSOLogger(name, level)
    return _logger_instance


def setup_logger(name: str = "PSO_UI", level: int = DEFAULT_LOG_LEVEL) -> PSOLogger:
    """
    设置并返回日志记录器
    
    【别名】
    此函数为 get_logger 的别名，提供与原代码兼容的接口
    
    Args:
        name: 日志记录器名称
        level: 日志级别
    
    Returns:
        PSOLogger实例
    """
    return get_logger(name, level)


# 导出便捷访问方式
logger = get_logger()
