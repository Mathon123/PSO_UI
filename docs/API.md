# PSO_UI API 文档

本文档提供PSO_UI项目的编程接口说明。

## 核心模块

### modules.pso_optimizer

PSO优化器模块，负责粒子群优化算法实现。

```python
from modules.pso_optimizer import NerveParameterOptimizer, format_params

# 创建优化器实例
optimizer = NerveParameterOptimizer(
    pop_size=30,        # 粒子群大小
    max_iter=100,       # 最大迭代次数
    w=0.7,              # 惯性权重
    c1=1.5,             # 个体学习因子
    c2=1.5              # 群体学习因子
)

# 执行优化
result = optimizer.optimize(data, target_freq)

# 获取辨识参数
params = optimizer.get_identified_params()
print(f"R1: {params['R1']}")
```

#### NerveParameterOptimizer 类

| 方法 | 说明 |
|------|------|
| `optimize(data, target_freq)` | 执行PSO优化 |
| `get_identified_params()` | 获取辨识后的参数 |
| `compute_threshold_current(probability)` | 计算阈值电流 |
| `compute_sd_curve(params, current_range)` | 计算SD曲线 |

#### 返回值 (OptimizationResult)

```python
@dataclass
class OptimizationResult:
    best_params: Dict[str, float]  # 最优参数
    best_fitness: float            # 最优适应度
    convergence_history: List[float] # 收敛历史
    iterations: int               # 迭代次数
    rmse: float                   # RMSE评估指标
    r_squared: float              # R²评估指标
```

---

### modules.data_importer

数据导入模块，处理CSV/Excel文件。

```python
from modules.data_importer import DataImporter, DataInfo

importer = DataImporter()
data_info = importer.import_data(
    stim_file='stim_params.csv',
    emg_file='emg_processed.csv'
)

print(f"数据点数量: {data_info.n_points}")
print(f"频率列表: {data_info.frequencies}")
```

#### DataImporter 类

| 方法 | 说明 |
|------|------|
| `import_data(stim_file, emg_file)` | 导入数据文件 |
| `validate_data(data)` | 验证数据有效性 |
| `get_data_info()` | 获取数据信息 |

#### DataInfo 数据类

```python
@dataclass
class DataInfo:
    n_points: int                    # 数据点数量
    frequencies: List[float]          # 频率列表
    current_range: Tuple[float, float] # 电流范围
    voltage_range: Tuple[float, float] # 电压范围
    sample_rate: float               # 采样率
```

---

### modules.data_processor

数据处理模块，预处理和后处理。

```python
from modules.data_processor import DataProcessor

processor = DataProcessor()
processed_data = processor.process(
    raw_data,
    normalize=True,
    remove_outliers=True
)
```

#### DataProcessor 类

| 方法 | 说明 |
|------|------|
| `process(data, normalize, remove_outliers)` | 处理数据 |
| `normalize(data)` | 归一化 |
| `remove_outliers(data, threshold)` | 移除异常值 |

---

### ui.chart_widgets

UI图表组件，提供各种可视化图表。

```python
from ui.chart_widgets import (
    ResponseCurveWidget,
    ConvergenceCurveWidget,
    SDCurveWidget
)

# 创建响应曲线图
response_widget = ResponseCurveWidget()
response_widget.update_chart(experimental_data, simulated_data)

# 创建收敛曲线图
convergence_widget = ConvergenceCurveWidget()
convergence_widget.update_chart(convergence_history)

# 创建SD曲线图
sd_widget = SDCurveWidget()
sd_widget.update_chart(current_range, probability_data)
```

#### 图表组件列表

| 组件 | 说明 |
|------|------|
| `ResponseCurveWidget` | 响应曲线图 |
| `ComparisonCurveWidget` | 对比曲线图 |
| `ConvergenceCurveWidget` | 收敛曲线图 |
| `ResidualPlotWidget` | 残差分析图 |
| `ParameterBarWidget` | 参数条形图 |
| `SDCurveWidget` | SD曲线图 |
| `ComprehensiveAnalysisWidget` | 综合分析图 |
| `MultiChartWidget` | 多图表组件 |

---

### ui.analysis_workflow

分析工作流模块，协调整个分析流程。

```python
from ui.analysis_workflow import NerveAnalysisWorkflow, NerveDataLoader

workflow = NerveAnalysisWorkflow()
loader = NerveDataLoader()

# 加载数据
data = loader.load_files(
    stim_file='stim_params.csv',
    emg_file='emg_processed.csv'
)

# 执行分析
result = workflow.run_analysis(data, params)
```

---

## 配置文件

### modules.config

```python
from modules.config import (
    APP_NAME,
    APP_VERSION,
    COLORS,
    FONTS,
    CHART_TYPES,
    SUPPORTED_FILE_TYPES
)

print(f"应用程序: {APP_NAME} v{APP_VERSION}")
```

---

## 信号槽

应用程序使用PyQt6信号槽机制进行线程间通信。

### OptimizationThread 信号

```python
class OptimizationThread(QThread):
    # 进度更新信号 (当前迭代, 最大迭代, 消息)
    progress_updated = pyqtSignal(int, int, str)

    # 优化完成信号 (结果字典)
    optimization_finished = pyqtSignal(dict)

    # 错误信号 (错误信息)
    error_occurred = pyqtSignal(str)
```

---

## 常量定义

### COLORS 颜色配置

```python
COLORS = {
    'primary': '#3498db',
    'secondary': '#2ecc71',
    'background': '#ecf0f1',
    'text': '#2c3e50',
    'error': '#e74c3c',
    'warning': '#f39c12',
    'success': '#27ae60',
}
```

### CHART_TYPES 图表类型

```python
CHART_TYPES = [
    'response',      # 响应曲线
    'comparison',    # 对比曲线
    'convergence',   # 收敛曲线
    'residual',      # 残差分析
    'parameter',     # 参数条形
    'sd_curve',      # SD曲线
    'comprehensive', # 综合分析
]
```
