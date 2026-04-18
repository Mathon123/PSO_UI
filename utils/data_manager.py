"""
数据管理器模块
==============
统一管理应用程序中的所有数据状态，解决数据分散在多处的问题。

【设计目的】
- 集中管理实验数据、优化结果、图表数据
- 提供统一的数据访问接口
- 支持数据序列化和反序列化
- 支持优化历史记录

【使用方式】
from utils.data_manager import DataManager, get_data_manager

# 获取单例
dm = get_data_manager()

# 设置数据
dm.set_experiment_data(data)

# 获取数据
data = dm.get_experiment_data()

【数据结构】
┌─────────────────────────────────────────┐
│           DataManager (单例)             │
├─────────────────────────────────────────┤
│ 实验数据 (experiment_data)               │
│  - NerveExperimentData                  │
│  - 电流、响应、频率、脉宽等              │
├─────────────────────────────────────────┤
│ 原始数据 (current_data_info)            │
│  - DataInfo                             │
│  - 导入时的原始信息                      │
├─────────────────────────────────────────┤
│ 优化器 (optimizer)                       │
│  - NerveParameterOptimizer               │
│  - 当前优化器实例                        │
├─────────────────────────────────────────┤
│ 优化结果 (optimization_result)          │
│  - OptimizationResult                   │
│  - 最佳参数、RMSE、收敛状态等           │
├─────────────────────────────────────────┤
│ 辨识参数 (identified_params)             │
│  - Dict[str, float]                    │
│  - 8个神经响应参数                       │
├─────────────────────────────────────────┤
│ 优化历史 (optimization_history)          │
│  - List[OptimizationRecord]             │
│  - 多次优化的历史记录                    │
└─────────────────────────────────────────┘
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OptimizationRecord:
    """
    优化记录数据类
    
    【属性说明】
    - timestamp: 优化时间戳
    - params: 辨识的参数 {'R1': value, ...}
    - rmse: 最终RMSE值
    - r2: 决定系数
    - elapsed: 耗时(秒)
    - message: 结果消息
    - frequencies: 分析的频率列表
    - pulse_width_us: 脉宽(微秒)
    
    【使用场景】
    - 保存每次优化的结果
    - 历史记录对比
    - 结果导出和报告
    """
    timestamp: datetime
    params: Dict[str, float]
    rmse: float
    r2: float
    elapsed: float
    message: str
    frequencies: List[float] = field(default_factory=list)
    pulse_width_us: float = 200.0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            可序列化的字典
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'params': self.params,
            'rmse': self.rmse,
            'r2': self.r2,
            'elapsed': self.elapsed,
            'message': self.message,
            'frequencies': self.frequencies,
            'pulse_width_us': self.pulse_width_us,
        }
    
    def __str__(self) -> str:
        """友好字符串表示"""
        time_str = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return f"优化记录[{time_str}]: RMSE={self.rmse:.6f}, R²={self.r2:.4f}"


class DataManager:
    """
    数据管理器 - 单例模式
    
    【核心职责】
    1. 管理实验数据 (experiment_data)
    2. 管理优化结果 (optimization_result, identified_params)
    3. 管理优化历史 (optimization_history)
    4. 管理优化器实例 (optimizer)
    
    【设计原则】
    - 单例模式确保全局唯一数据源
    - 属性使用 @property 封装，保证数据访问安全
    - 清晰的命名区分不同数据类型
    - 支持状态重置和清空
    
    【线程安全说明】
    - 该类非线程安全，所有操作应在主线程中进行
    - 多线程场景下，通过信号槽与主线程通信
    """
    
    _instance: Optional['DataManager'] = None
    
    def __new__(cls):
        """
        单例模式实现
        
        【实现方式】
        重写 __new__ 方法，确保全局只有一个实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化数据管理器
        
        【初始化内容】
        - 清空所有数据
        - 重置优化历史
        - 重置状态标志
        """
        if self._initialized:
            return
            
        self._initialized = True
        
        # ========== 实验数据 ==========
        # NerveExperimentData对象，包含电流、响应、频率等
        self._experiment_data: Optional[Any] = None
        
        # ========== 导入的原始数据 ==========
        # DataInfo对象，导入时的原始数据信息
        self._current_data_info: Optional[Any] = None
        self._current_file: Optional[str] = None
        
        # ========== 优化相关 ==========
        # NerveParameterOptimizer实例
        self._optimizer: Optional[Any] = None
        # OptimizationResult对象
        self._optimization_result: Optional[Any] = None
        # 辨识的参数 {'R1': 1e4, 'R2': 1e3, ...}
        self._identified_params: Dict[str, float] = {}
        
        # ========== 优化历史记录 ==========
        # 保存多次优化的结果，用于对比分析
        self._optimization_history: List[OptimizationRecord] = []
        
        # ========== 状态标志 ==========
        # 优化是否正在运行
        self._is_optimization_running: bool = False
        # 最后的错误信息
        self._last_error: Optional[str] = None
        
        # ========== 频率相关 ==========
        # 当前选中的分析频率(Hz)
        self._selected_frequency: float = 10.0
    
    # ================================================================
    # 实验数据管理
    # ================================================================
    
    @property
    def experiment_data(self) -> Optional[Any]:
        """
        获取实验数据
        
        【说明】
        返回NerveExperimentData对象，包含完整的实验数据
        
        Returns:
            NerveExperimentData对象或None
        """
        return self._experiment_data
    
    def set_experiment_data(self, data: Any) -> None:
        """
        设置实验数据
        
        【说明】
        当设置新的实验数据时，同时更新频率信息
        
        Args:
            data: NerveExperimentData对象
        """
        self._experiment_data = data
        self._last_error = None
        
        # 更新频率信息（使用第一个频率作为默认）
        if data and hasattr(data, 'frequencies') and data.frequencies:
            self._selected_frequency = data.frequencies[0]
    
    def has_experiment_data(self) -> bool:
        """
        检查是否有实验数据
        
        Returns:
            True表示有数据，False表示无数据
        """
        return self._experiment_data is not None
    
    def get_experiment_data_summary(self) -> str:
        """
        获取实验数据摘要信息
        
        Returns:
            格式化的数据摘要字符串
        """
        if not self._experiment_data:
            return "无实验数据"
        
        data = self._experiment_data
        freq_str = ', '.join(map(str, data.frequencies)) if data.frequencies else '无'
        return (
            f"文件: {data.filename}\n"
            f"数据点数: {data.n_points}\n"
            f"电流范围: {data.currents_mA.min():.1f} - {data.currents_mA.max():.1f} mA\n"
            f"脉宽: {data.pulse_width_us:.0f} us\n"
            f"频率: {freq_str} Hz"
        )
    
    # ================================================================
    # 原始数据管理
    # ================================================================
    
    @property
    def current_data_info(self) -> Optional[Any]:
        """
        获取导入的原始数据信息
        
        【说明】
        返回DataInfo对象，包含导入文件时的原始信息
        
        Returns:
            DataInfo对象或None
        """
        return self._current_data_info
    
    def set_current_data_info(self, data_info: Any) -> None:
        """
        设置原始数据信息
        
        Args:
            data_info: DataInfo对象
        """
        self._current_data_info = data_info
    
    @property
    def current_file(self) -> Optional[str]:
        """
        获取当前文件路径
        
        Returns:
            文件路径字符串或None
        """
        return self._current_file
    
    def set_current_file(self, file_path: str) -> None:
        """
        设置当前文件路径
        
        Args:
            file_path: 文件路径
        """
        self._current_file = file_path
    
    # ================================================================
    # 优化器管理
    # ================================================================
    
    @property
    def optimizer(self) -> Optional[Any]:
        """
        获取优化器实例
        
        Returns:
            NerveParameterOptimizer对象或None
        """
        return self._optimizer
    
    def set_optimizer(self, optimizer: Any) -> None:
        """
        设置优化器实例
        
        Args:
            optimizer: NerveParameterOptimizer对象
        """
        self._optimizer = optimizer
    
    @property
    def optimization_result(self) -> Optional[Any]:
        """
        获取优化结果
        
        Returns:
            OptimizationResult对象或None
        """
        return self._optimization_result
    
    def set_optimization_result(self, result: Any) -> None:
        """
        设置优化结果
        
        【说明】
        当设置新的优化结果时，会自动添加到历史记录
        
        Args:
            result: OptimizationResult对象
        """
        self._optimization_result = result
        
        # 如果有参数，同时保存到历史记录
        if result and hasattr(result, 'best_rmse'):
            self._add_to_history()
    
    @property
    def identified_params(self) -> Dict[str, float]:
        """
        获取辨识的参数
        
        【参数说明】
        - R1: 等效串联电阻 (Ω)
        - R2: 等效并联电阻 (Ω)
        - R3: 膜电阻 (Ω)
        - L: 等效电感 (H)
        - C: 膜电容 (F)
        - alpha: 激活系数
        - beta: 能量指数
        - V_th: 阈值电压 (V)
        
        Returns:
            参数字典
        """
        return self._identified_params.copy()
    
    def set_identified_params(self, params: Dict[str, float]) -> None:
        """
        设置辨识的参数
        
        Args:
            params: 参数字典
        """
        self._identified_params = params.copy()
    
    def format_params_for_display(self) -> str:
        """
        格式化参数用于显示
        
        Returns:
            格式化的参数字符串
        """
        if not self._identified_params:
            return "暂无参数结果"
        
        lines = []
        for name, value in self._identified_params.items():
            lines.append(f"{name}: {value:.6f}")
        return "\n".join(lines)
    
    # ================================================================
    # 优化历史管理
    # ================================================================
    
    @property
    def optimization_history(self) -> List[OptimizationRecord]:
        """
        获取优化历史记录
        
        【说明】
        返回历史记录的副本，不包含原始引用
        
        Returns:
            OptimizationRecord列表
        """
        return self._optimization_history.copy()
    
    def _add_to_history(self) -> None:
        """
        添加当前优化结果到历史记录
        
        【执行条件】
        - 有优化结果
        - 有参数
        """
        if self._optimization_result is None:
            return
        
        record = OptimizationRecord(
            timestamp=datetime.now(),
            params=self._identified_params.copy() if self._identified_params else {},
            rmse=getattr(self._optimization_result, 'best_rmse', 0.0),
            r2=self._calculate_r2(),
            elapsed=getattr(self._optimization_result.history, 'optimization_time', 0.0) 
                    if self._optimization_result else 0.0,
            message=getattr(self._optimization_result, 'message', ''),
            frequencies=self._experiment_data.frequencies if self._experiment_data else [],
            pulse_width_us=getattr(self._experiment_data, 'pulse_width_us', 200.0) 
                          if self._experiment_data else 200.0,
        )
        self._optimization_history.append(record)
    
    def _calculate_r2(self) -> float:
        """
        计算R²值
        
        【计算公式】
        R² = 1 - SS_res / SS_tot
        其中:
        - SS_res = Σ(观测值 - 预测值)²
        - SS_tot = Σ(观测值 - 均值)²
        
        Returns:
            R²值，默认为0
        """
        try:
            if (self._experiment_data is None or 
                self._optimizer is None or 
                self._optimization_result is None):
                return 0.0
                
            currents = self._experiment_data.currents_A
            freq_key = f'Freq_{int(self._selected_frequency)}Hz'
            responses_exp = self._experiment_data.responses.get(freq_key, [])
            
            if len(responses_exp) == 0:
                return 0.0
                
            responses_sim = self._optimizer.compute_response_curve()[1]
            
            ss_res = sum((a - b) ** 2 for a, b in zip(responses_exp, responses_sim[:len(responses_exp)]))
            ss_tot = sum((a - sum(responses_exp) / len(responses_exp)) ** 2 for a in responses_exp)
            
            return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        except Exception:
            return 0.0
    
    def clear_history(self) -> None:
        """
        清空优化历史
        
        【使用场景】
        - 开始新的分析项目时
        - 用户手动清空历史时
        """
        self._optimization_history.clear()
    
    def get_latest_record(self) -> Optional[OptimizationRecord]:
        """
        获取最新的优化记录
        
        Returns:
            最新的OptimizationRecord或None
        """
        if self._optimization_history:
            return self._optimization_history[-1]
        return None
    
    def get_best_record(self) -> Optional[OptimizationRecord]:
        """
        获取最优的优化记录（RMSE最小）
        
        Returns:
            最优的OptimizationRecord或None
        """
        if not self._optimization_history:
            return None
        return min(self._optimization_history, key=lambda r: r.rmse)
    
    def get_history_summary(self) -> str:
        """
        获取历史记录摘要
        
        Returns:
            格式化的历史摘要字符串
        """
        if not self._optimization_history:
            return "无优化历史"
        
        lines = ["优化历史记录:", "-" * 40]
        for i, record in enumerate(self._optimization_history, 1):
            time_str = record.timestamp.strftime('%m-%d %H:%M')
            lines.append(
                f"{i}. [{time_str}] RMSE={record.rmse:.6f}, "
                f"R²={record.r2:.4f}, 耗时={record.elapsed:.1f}s"
            )
        
        return "\n".join(lines)
    
    # ================================================================
    # 状态管理
    # ================================================================
    
    @property
    def is_optimization_running(self) -> bool:
        """
        检查优化是否正在运行
        
        Returns:
            True表示正在运行，False表示未运行
        """
        return self._is_optimization_running
    
    def set_optimization_running(self, running: bool) -> None:
        """
        设置优化运行状态
        
        Args:
            running: 是否正在运行
        """
        self._is_optimization_running = running
    
    @property
    def last_error(self) -> Optional[str]:
        """
        获取最后的错误信息
        
        Returns:
            错误信息字符串或None
        """
        return self._last_error
    
    def set_last_error(self, error: str) -> None:
        """
        设置错误信息
        
        Args:
            error: 错误信息
        """
        self._last_error = error
    
    @property
    def selected_frequency(self) -> float:
        """
        获取选中的频率
        
        Returns:
            频率值(Hz)
        """
        return self._selected_frequency
    
    def set_selected_frequency(self, freq: float) -> None:
        """
        设置选中的频率
        
        Args:
            freq: 频率值(Hz)
        """
        self._selected_frequency = freq
    
    # ================================================================
    # 数据清空
    # ================================================================
    
    def clear_all(self) -> None:
        """
        清空所有数据
        
        【清空内容】
        - 实验数据
        - 原始数据信息
        - 优化器和结果
        - 辨识参数
        - 错误信息
        
        【保留内容】
        - 优化历史记录
        """
        self._experiment_data = None
        self._current_data_info = None
        self._current_file = None
        self._optimizer = None
        self._optimization_result = None
        self._identified_params = {}
        self._is_optimization_running = False
        self._last_error = None
    
    def clear_optimization_results(self) -> None:
        """
        仅清空优化相关数据
        
        【保留内容】
        - 实验数据
        - 原始数据信息
        - 优化历史
        """
        self._optimizer = None
        self._optimization_result = None
        self._identified_params = {}
        self._is_optimization_running = False
        self._last_error = None
    
    # ================================================================
    # 数据导出
    # ================================================================
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出当前状态
        
        【用途】
        - 保存项目状态
        - 调试和诊断
        - 状态恢复
        
        Returns:
            包含所有数据的字典
        """
        return {
            'experiment_data': self._experiment_data,
            'current_file': self._current_file,
            'optimizer': self._optimizer,
            'optimization_result': self._optimization_result,
            'identified_params': self._identified_params,
            'optimization_history': [r.to_dict() for r in self._optimization_history],
            'selected_frequency': self._selected_frequency,
            'timestamp': datetime.now().isoformat(),
        }
    
    # ================================================================
    # 状态检查方法
    # ================================================================
    
    def can_run_optimization(self) -> tuple:
        """
        检查是否可以运行优化
        
        Returns:
            (可以运行, 原因)
        """
        if not self.has_experiment_data():
            return False, "请先导入实验数据"
        
        if self.is_optimization_running:
            return False, "优化任务正在进行中"
        
        return True, ""
    
    def get_status_summary(self) -> str:
        """
        获取状态摘要
        
        Returns:
            格式化的状态摘要
        """
        status = []
        
        # 数据状态
        if self.has_experiment_data():
            status.append(f"✓ 已加载数据: {self.experiment_data.filename}")
        else:
            status.append("○ 未加载数据")
        
        # 优化状态
        if self.is_optimization_running:
            status.append("⟳ 优化进行中...")
        elif self.optimization_result:
            status.append(f"✓ 已完成优化: RMSE={self.optimization_result.best_rmse:.6f}")
        else:
            status.append("○ 未进行优化")
        
        # 历史记录
        if self.optimization_history:
            status.append(f"📋 历史记录: {len(self.optimization_history)}条")
        
        return " | ".join(status)


# ================================================================
# 单例访问函数
# ================================================================

_data_manager_instance: Optional[DataManager] = None


def get_data_manager() -> DataManager:
    """
    获取数据管理器单例
    
    【使用方式】
    dm = get_data_manager()
    dm.set_experiment_data(data)
    
    Returns:
        DataManager实例
    """
    global _data_manager_instance
    if _data_manager_instance is None:
        _data_manager_instance = DataManager()
    return _data_manager_instance


def reset_data_manager() -> None:
    """
    重置数据管理器（用于测试）
    
    【使用场景】
    - 单元测试
    - 重置应用程序状态
    """
    global _data_manager_instance
    if _data_manager_instance is not None:
        _data_manager_instance.clear_all()
    _data_manager_instance = None
