"""
异常处理模块
============
定义项目中使用的所有自定义异常类

【异常层次结构】
PSOException (基类)
├── DataValidationError    - 数据验证失败
├── DataImportError        - 数据导入异常
├── OptimizationError      - 优化过程异常
└── ChartRenderError      - 图表渲染异常

【使用方式】
from utils.exceptions import DataValidationError, OptimizationError

try:
    validate_data(data)
except DataValidationError as e:
    print(f"数据验证失败: {e}")
"""


class PSOException(Exception):
    """
    PSO基础异常类
    
    【说明】
    所有项目自定义异常的基类，继承自Python内置Exception类。
    用于提供统一的异常处理接口。
    
    【属性】
    - message: 异常消息
    - details: 详细错误信息（可选）
    """
    
    def __init__(self, message: str = "PSO分析工具异常", details: str = None):
        """
        初始化异常
        
        Args:
            message: 异常消息
            details: 详细错误信息（可选）
        """
        self.message = message
        self.details = details
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """
        格式化异常消息
        
        Returns:
            格式化的错误消息字符串
        """
        if self.details:
            return f"{self.message}\n详情: {self.details}"
        return self.message


class DataValidationError(PSOException):
    """
    数据验证失败异常
    
    【触发场景】
    - 导入数据格式不符合要求
    - 数据列缺失或类型错误
    - 数据值超出有效范围
    - 数据完整性检验失败
    """
    
    def __init__(self, message: str = "数据验证失败", details: str = None):
        """
        初始化数据验证异常
        
        Args:
            message: 错误消息
            details: 详细错误信息
        """
        super().__init__(message, details)


class DataImportError(PSOException):
    """
    数据导入异常
    
    【触发场景】
    - 文件不存在或路径错误
    - 文件格式不支持
    - 文件读取失败
    - 文件编码问题
    - 解析数据失败
    """
    
    def __init__(self, message: str = "数据导入失败", details: str = None):
        """
        初始化数据导入异常
        
        Args:
            message: 错误消息
            details: 详细错误信息
        """
        super().__init__(message, details)


class OptimizationError(PSOException):
    """
    优化过程异常
    
    【触发场景】
    - PSO优化计算失败
    - 参数边界不合法
    - 适应度函数计算异常
    - 优化器初始化失败
    - 收敛失败或超时
    """
    
    def __init__(self, message: str = "优化过程异常", details: str = None):
        """
        初始化优化异常
        
        Args:
            message: 错误消息
            details: 详细错误信息
        """
        super().__init__(message, details)


class ChartRenderError(PSOException):
    """
    图表渲染异常
    
    【触发场景】
    - 图表创建失败
    - 数据绑定错误
    - 图表保存失败
    - 字体加载失败
    - 图表导出失败
    """
    
    def __init__(self, message: str = "图表渲染异常", details: str = None):
        """
        初始化图表渲染异常
        
        Args:
            message: 错误消息
            details: 详细错误信息
        """
        super().__init__(message, details)


class WorkflowError(PSOException):
    """
    工作流执行异常
    
    【触发场景】
    - 工作流步骤执行失败
    - 步骤依赖不满足
    - 状态转换非法
    - 资源加载失败
    """
    
    def __init__(self, message: str = "工作流执行异常", details: str = None):
        """
        初始化工作流异常
        
        Args:
            message: 错误消息
            details: 详细错误信息
        """
        super().__init__(message, details)
