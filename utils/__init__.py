"""
工具模块初始化
==============
导出异常类、日志系统、数据管理器等通用工具

【模块内容】
- exceptions: 自定义异常类
- logger: 日志记录系统
- data_manager: 数据管理器

【使用示例】
from utils import (
    PSOException,
    DataValidationError,
    DataImportError,
    OptimizationError,
    logger,
    get_data_manager,
)

# 记录日志
logger.info("程序启动")

# 使用数据管理器
dm = get_data_manager()

# 捕获异常
try:
    validate_data(data)
except DataValidationError as e:
    logger.error(f"数据验证失败: {e}")
"""

# 导入异常类
from .exceptions import (
    PSOException,
    DataValidationError,
    DataImportError,
    OptimizationError,
    ChartRenderError,
    WorkflowError,
)

# 导入日志系统
from .logger import (
    logger,
    get_logger,
    setup_logger,
    PSOLogger,
)

# 导入数据管理器
from .data_manager import (
    DataManager,
    get_data_manager,
    reset_data_manager,
    OptimizationRecord,
)


# =============================================================
# 模块元信息
# =============================================================

__version__ = "1.0.0"
__author__ = "PSO_UI Team"


# =============================================================
# 导出清单
# =============================================================

__all__ = [
    # 异常类
    'PSOException',
    'DataValidationError',
    'DataImportError',
    'OptimizationError',
    'ChartRenderError',
    'WorkflowError',
    
    # 日志系统
    'logger',
    'get_logger',
    'setup_logger',
    'PSOLogger',
    
    # 数据管理器
    'DataManager',
    'get_data_manager',
    'reset_data_manager',
    'OptimizationRecord',
]
