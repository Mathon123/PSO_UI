"""
图表组件模块
============

【模块说明】
本模块定义了各种图表组件，用于在PyQt6界面中展示Matplotlib图表。

【组件层次结构】
┌─────────────────────────────────────────────────────┐
│                   ChartWidget (基类)                  │
│  - 提供通用功能: 工具栏、画布管理、图表保存           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────────┐  ResponseCurveWidget          │
│  │               │  - 响应曲线（电流-概率）         │
│  ├───────────────┤                                 │
│  │               │  ComparisonCurveWidget           │
│  │  ChartWidget   │  - 实验vs仿真对比               │
│  ├───────────────┤                                 │
│  │               │  ConvergenceCurveWidget         │
│  │  (基类)       │  - PSO收敛曲线                  │
│  ├───────────────┤                                 │
│  │               │  ResidualPlotWidget             │
│  │               │  - 残差分析图                   │
│  ├───────────────┤                                 │
│  │               │  ParameterBarWidget             │
│  │               │  - 参数柱状图                   │
│  ├───────────────┤                                 │
│  │               │  SDCurveWidget                  │
│  │               │  - SD刺激剂量曲线               │
│  ├───────────────┤                                 │
│  │               │  ComprehensiveAnalysisWidget    │
│  │               │  - 综合分析仪表板               │
│  └───────────────┘                                 │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │              MultiChartWidget                   │ │
│  │  - 管理多个ChartWidget                          │ │
│  │  - 支持动态添加/删除图表                        │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │              ChartControlPanel                  │ │
│  │  - 图表控制面板                                 │ │
│  │  - 类型选择、显示选项、导出设置                  │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘

【使用方式】
# 创建图表组件
widget = ResponseCurveWidget()
widget.plot(currents, responses)

# 切换到图表Tab
chart_tabs.addTab(widget, "响应曲线")
"""

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QToolBar, QSizePolicy, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from modules.visualization import ChartFactory
from modules.config import COLORS, FONTS, BORDER_RADIUS


class ChartWidget(QWidget):
    """
    图表部件基类
    
    【功能】
    - 集成Matplotlib图表到PyQt6
    - 提供工具栏（保存、缩放、重置、全屏）
    - 管理图表的创建和销毁
    
    【信号】
    - chartSaved: 图表保存时发射，携带文件路径
    """

    # 信号: 图表保存完成
    chartSaved = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = None
        self.canvas = None
        self._zoom_mode = False
        self._chart_layout = None
        self._setup_ui()

    def _get_chart_layout(self):
        """返回主布局，便于子类插入控件"""
        return self._chart_layout

    def _setup_ui(self):
        """
        设置UI布局
        
        【布局说明】
        - 垂直布局管理器
        - 顶部工具栏
        - 底部画布容器
        """
        # QVBoxLayout: 垂直布局
        self._chart_layout = QVBoxLayout(self)
        self._chart_layout.setContentsMargins(0, 0, 0, 0)  # 无外边距
        self._chart_layout.setSpacing(0)  # 无间距
        layout = self._chart_layout

        # ===== 工具栏 =====
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {COLORS['bg_hover']};
                border-bottom: 1px solid {COLORS['border']};
                padding: 4px 8px;
                spacing: 8px;
            }}
        """)

        # 工具栏按钮
        self.btn_save = QPushButton("保存")
        self.btn_save.setToolTip("保存图表")
        self.btn_zoom = QPushButton("缩放")
        self.btn_zoom.setToolTip("启用缩放")
        self.btn_reset = QPushButton("重置")
        self.btn_reset.setToolTip("重置视图")
        self.btn_fullscreen = QPushButton("全屏")
        self.btn_fullscreen.setToolTip("全屏查看")
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setToolTip("放大")
        self.btn_zoom_in.setFixedWidth(32)
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setToolTip("缩小")
        self.btn_zoom_out.setFixedWidth(32)

        # 按钮样式
        btn_style = f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['sm']}px;
                padding: 6px 14px;
                color: {COLORS['text_primary']};
                font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
                border-color: {COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """
        for btn in [self.btn_save, self.btn_zoom, self.btn_reset, self.btn_fullscreen]:
            btn.setStyleSheet(btn_style)
            btn.setFixedWidth(70)

        zoom_btn_style = f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['sm']}px;
                padding: 4px 8px;
                color: {COLORS['text_primary']};
                font-size: {FONTS['size_md']}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_light']};
                border-color: {COLORS['primary']};
            }}
        """
        self.btn_zoom_in.setStyleSheet(zoom_btn_style)
        self.btn_zoom_out.setStyleSheet(zoom_btn_style)

        # 添加分隔线和按钮组
        toolbar.addWidget(self.btn_save)
        toolbar.addWidget(self.btn_zoom)
        toolbar.addWidget(self.btn_zoom_in)
        toolbar.addWidget(self.btn_zoom_out)
        toolbar.addWidget(self.btn_reset)
        toolbar.addWidget(self.btn_fullscreen)

        # 连接信号
        self.btn_zoom.clicked.connect(self._toggle_zoom_mode)
        self.btn_zoom_in.clicked.connect(self._zoom_in)
        self.btn_zoom_out.clicked.connect(self._zoom_out)
        self.btn_reset.clicked.connect(self._reset_view)
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)

        # 缩放状态
        self._zoom_mode = False

        layout.addWidget(toolbar)

        # ===== 画布容器 =====
        # 用于承载Matplotlib图表的容器
        self.canvas_container = QWidget()
        self.canvas_container.setVisible(True)  # 默认可见
        self.canvas_container.setStyleSheet(f"""
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
        """)
        self.canvas_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # 画布布局 - 使用QVBoxLayout并添加stretch factor让画布区域填充剩余空间
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(8, 8, 8, 8)  # 8px边距
        self.canvas_layout.setSpacing(0)
        # 添加stretch factor使画布区域自动扩展填满容器
        self.canvas_layout.addStretch(1)

        layout.addWidget(self.canvas_container)

    def set_figure(self, figure: Figure):
        """设置图表Figure"""
        while self.canvas_layout.count():
            item = self.canvas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.figure = figure
        self.canvas = FigureCanvas(figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.canvas_layout.insertStretch(0, 1)
        self.canvas_layout.addWidget(self.canvas)

        # 保存原始坐标轴范围，用于重置功能
        self._original_limits = {}
        if self.figure and self.figure.axes:
            for i, ax in enumerate(self.figure.axes):
                self._original_limits[i] = {
                    'xlim': ax.get_xlim(),
                    'ylim': ax.get_ylim()
                }

    def save_chart(self, file_path: str = None):
        """保存图表"""
        if self.figure:
            if file_path is None:
                from PyQt6.QtWidgets import QFileDialog
                from pathlib import Path

                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "保存图表",
                    str(Path.home() / "chart.png"),
                    "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
                )
                if path:
                    ChartFactory().save_figure(self.figure, path)
                    self.chartSaved.emit(path)
            else:
                ChartFactory().save_figure(self.figure, file_path)

    def clear(self):
        """清空图表"""
        if self.figure:
            self.figure.clf()  # clf: 清除当前figure

    def _toggle_zoom_mode(self):
        """切换缩放模式"""
        self._zoom_mode = not self._zoom_mode
        self.btn_zoom.setChecked(self._zoom_mode)
        if self._zoom_mode and self.canvas:
            try:
                if hasattr(self.canvas, '_id_release'):
                    self.canvas.mpl_disconnect(self.canvas._id_release)
                if hasattr(self.canvas, '_id_press'):
                    self.canvas.mpl_disconnect(self.canvas._id_press)
            except Exception:
                pass

    def _zoom_in(self):
        """放大图表"""
        if self.figure and hasattr(self.figure, 'axes'):
            for ax in self.figure.axes:
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                x_range = (xlim[1] - xlim[0]) * 0.4
                y_range = (ylim[1] - ylim[0]) * 0.4
                ax.set_xlim([xlim[0] + x_range, xlim[1] - x_range])
                ax.set_ylim([ylim[0] + y_range, ylim[1] - y_range])
            self.canvas.draw()

    def _zoom_out(self):
        """缩小图表"""
        if self.figure and hasattr(self.figure, 'axes'):
            for ax in self.figure.axes:
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                x_range = (xlim[1] - xlim[0]) * 0.6
                y_range = (ylim[1] - ylim[0]) * 0.6
                ax.set_xlim([xlim[0] - x_range, xlim[1] + x_range])
                ax.set_ylim([ylim[0] - y_range, ylim[1] + y_range])
            self.canvas.draw()

    def _reset_view(self):
        """重置视图"""
        if self.figure and hasattr(self.figure, 'axes'):
            for i, ax in enumerate(self.figure.axes):
                if i in self._original_limits:
                    ax.set_xlim(self._original_limits[i]['xlim'])
                    ax.set_ylim(self._original_limits[i]['ylim'])
                else:
                    ax.relim()
                    ax.autoscale_view()
            self.canvas.draw()

    def _toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()


class ResponseCurveWidget(ChartWidget):
    """
    响应曲线图表部件

    【功能】
    显示胫神经电刺激的电流-响应概率曲线

    【数据格式】
    - currents: 电流数组 (mA)
    - responses: 响应概率字典 {频率: 数据}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间
        self.currents = None  # 电流数据
        self.responses_exp = {}  # 实验响应数据
        self.responses_sim = None  # 仿真响应数据

    def plot(self, currents: np.ndarray, responses_exp: dict = None,
             responses_sim: np.ndarray = None, title: str = "响应曲线"):
        """
        绘制响应曲线
        
        Args:
            currents: 电流数组 (mA)
            responses_exp: 实验响应数据 {频率: 数组}
            responses_sim: 仿真响应数据
            title: 图表标题
        """
        self.currents = currents
        self.responses_exp = responses_exp or {}
        self.responses_sim = responses_sim

        # 使用ChartFactory创建图表
        figure = ChartFactory().create_response_curve(
            currents, responses_exp, responses_sim, title
        )
        self.set_figure(figure)

    def update_title(self, title: str):
        """更新标题并重绘"""
        if self.currents is not None:
            self.plot(self.currents, self.responses_exp,
                     self.responses_sim, title)


class ComparisonCurveWidget(ChartWidget):
    """
    实验vs仿真对比曲线部件

    【功能】
    同时显示实验数据和仿真拟合曲线，便于对比分析

    【特性】
    - 支持频率选择器
    - 支持单频率/多频率显示
    - 自动计算RMSE/MAE指标
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间
        self.currents = None
        self.responses_exp = None
        self.responses_sim = None
        self.freq_label = "10Hz"

        # 添加频率选择器
        self._add_controls()

    def _add_controls(self):
        """
        添加控制组件

        【布局】
        [频率:] [下拉框]

        下拉选项: 10Hz, 20Hz, All
        """
        main_layout = self._get_chart_layout()
        if main_layout is None:
            return

        # QHBoxLayout: 水平布局
        control_layout = QHBoxLayout()

        # 频率标签
        control_layout.addWidget(QLabel("频率:"))

        # QComboBox: 下拉选择框
        self.freq_selector = QComboBox()
        self.freq_selector.addItems(["10Hz", "20Hz", "All"])
        control_layout.addWidget(self.freq_selector)

        # currentTextChanged: 选择改变时触发
        self.freq_selector.currentTextChanged.connect(self._on_freq_changed)

        # insertLayout: 插入到工具栏下方
        main_layout.insertLayout(1, control_layout)

    def _on_freq_changed(self, text: str):
        """
        频率切换处理
        
        Args:
            text: 选择的频率文本
        """
        if text == "All":
            self.plot_all()  # 显示所有频率
        else:
            self.plot_single(self.currents, text)  # 显示单频率

    def plot(self, currents: np.ndarray, responses_exp: np.ndarray,
             responses_sim: np.ndarray, freq_label: str = "10Hz"):
        """
        绘制对比曲线
        
        Args:
            currents: 电流数组
            responses_exp: 实验响应
            responses_sim: 仿真响应
            freq_label: 频率标签
        """
        self.currents = currents
        self.responses_exp = responses_exp
        self.responses_sim = responses_sim
        self.freq_label = freq_label

        figure = ChartFactory().create_comparison_curve(
            currents, responses_exp, responses_sim, freq_label
        )
        self.set_figure(figure)

    def plot_single(self, currents: np.ndarray, freq_label: str):
        """
        绘制单频率对比
        
        Args:
            currents: 电流数组
            freq_label: 频率标签
        """
        if self.responses_sim is not None:
            # 处理实验数据（可能是字典）
            # freq_label 可能是 "10Hz" 或 "Freq_10Hz"，需要统一处理
            freq_key = freq_label if freq_label.startswith('Freq_') else f'Freq_{int(freq_label.replace("Hz", ""))}Hz'
            
            if isinstance(self.responses_exp, dict) and freq_key in self.responses_exp:
                resp_exp = self.responses_exp[freq_key]
            else:
                resp_exp = self.responses_exp

            figure = ChartFactory().create_comparison_curve(
                currents, resp_exp, self.responses_sim, freq_label
            )
            self.set_figure(figure)

    def plot_all(self):
        """绘制所有频率"""
        if self.responses_exp and self.responses_sim is not None:
            # 如果 responses_exp 是字典，传递给多频率绘制函数
            if isinstance(self.responses_exp, dict):
                figure = ChartFactory().create_multi_frequency_response(
                    self.currents, self.responses_exp, self.responses_sim
                )
            else:
                # 如果是单个数组，包装成字典
                responses_exp_dict = {'Freq_10Hz': self.responses_exp}
                figure = ChartFactory().create_multi_frequency_response(
                    self.currents, responses_exp_dict, self.responses_sim
                )
            self.set_figure(figure)


class ConvergenceCurveWidget(ChartWidget):
    """
    收敛曲线图表部件

    【功能】
    显示PSO优化过程中RMSE的收敛过程

    【图表组成】
    - 左图: 线性坐标收敛曲线
    - 右图: 对数坐标收敛曲线
    - 标注: 最优点位置和数值
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, fitness_history: list, target_rmse: float = None,
             title: str = "PSO优化收敛曲线"):
        """绘制收敛曲线"""
        figure = ChartFactory().create_convergence_curve(
            fitness_history, target_rmse, title
        )
        self.set_figure(figure)


class ResidualPlotWidget(ChartWidget):
    """
    残差分析图表部件

    【功能】
    显示实验值与仿真值之间的残差分布

    【分析方法】
    - 残差散点图: 观察残差分布模式
    - 误差带: 显示±2σ范围
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, currents: np.ndarray, residuals: dict = None,
             responses_exp: np.ndarray = None, responses_sim: np.ndarray = None,
             title: str = "残差分析"):
        """
        绘制残差图
        
        Args:
            currents: 电流数组
            residuals: 残差字典 {频率: 数组}
            responses_exp: 实验响应（用于自动计算残差）
            responses_sim: 仿真响应（用于自动计算残差）
            title: 标题
        """
        if residuals is None:
            # 自动计算残差
            if responses_exp is not None and responses_sim is not None:
                residuals = {"残差": responses_exp - responses_sim}

        figure = ChartFactory().create_residual_plot(currents, residuals, title)
        self.set_figure(figure)

    def plot_histogram(self, residuals: np.ndarray, title: str = "残差分布"):
        """绘制残差直方图"""
        figure = ChartFactory().create_residual_histogram(residuals, title)
        self.set_figure(figure)


class ParameterBarWidget(ChartWidget):
    """
    参数柱状图部件
    
    【功能】
    以柱状图形式展示辨识的8个物理参数
    
    【参数列表】
    - R1, R2, R3: 电阻参数
    - L: 电感
    - C: 电容
    - alpha, beta: 激活系数
    - V_th: 阈值电压
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, params: dict, param_units: dict = None,
             title: str = "参数分布"):
        """绘制参数柱状图"""
        figure = ChartFactory().create_parameter_bar(params, param_units, title)
        self.set_figure(figure)


class SDCurveWidget(ChartWidget):
    """
    刺激-剂量曲线部件
    
    【功能】
    显示达到目标响应概率所需电流与脉宽的关系
    
    【应用场景】
    临床电刺激参数选择
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, pulse_widths: np.ndarray, currents: np.ndarray,
             target_p: float = 0.5, title: str = "刺激-剂量曲线"):
        """绘制SD曲线"""
        figure = ChartFactory().create_sd_curve(
            pulse_widths, currents, target_p, title
        )
        self.set_figure(figure)


class ComprehensiveAnalysisWidget(ChartWidget):
    """
    综合分析图表部件
    
    【功能】
    在一个图表中展示多种分析结果
    
    【子图布局】
    ┌─────┬─────┬─────┐
    │响应曲线│残差图 │直方图 │
    ├─────┼─────┼─────┤
    │统计表 │频率RMSE│摘要  │
    └─────┴─────┴─────┘
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, currents: np.ndarray, responses_exp: dict,
             responses_sim: np.ndarray, residuals: dict = None,
             metrics: dict = None, title: str = "综合分析"):
        """绘制综合分析图"""
        if residuals is None:
            residuals = {}
            for freq, resp in responses_exp.items():
                if responses_sim is not None:
                    residuals[freq] = resp - responses_sim[:len(resp)]

        if metrics is None:
            metrics = {"rmse": 0, "mae": 0, "r2": 0, "mape": 0}

        figure = ChartFactory().create_comprehensive_analysis(
            currents, responses_exp, responses_sim, residuals, metrics, title
        )
        self.set_figure(figure)


class MultiChartWidget(QWidget):
    """
    多图表管理部件
    
    【功能】
    在一个容器中管理多个图表Tab
    
    【使用场景】
    当需要在主界面之外显示额外图表时使用
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.charts = {}  # 图表字典
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)

        # QTabWidget: 管理多个图表
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
                padding: 0px;
                background-color: {COLORS['bg_card']};
            }}
            QTabBar::tab {{
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: {BORDER_RADIUS['md']}px;
                border-top-right-radius: {BORDER_RADIUS['md']}px;
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-size: {FONTS['size_sm']}px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                font-weight: bold;
                color: {COLORS['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['border_light']};
            }}
        """)
        layout.addWidget(self.tab_widget)

    def add_chart(self, name: str, widget: ChartWidget):
        """
        添加图表
        
        Args:
            name: 图表名称（Tab标题）
            widget: ChartWidget实例
        """
        self.charts[name] = widget
        self.tab_widget.addTab(widget, name)

    def get_chart(self, name: str) -> ChartWidget:
        """获取图表"""
        return self.charts.get(name)

    def clear_all(self):
        """清空所有图表"""
        self.tab_widget.clear()
        self.charts.clear()

    def remove_chart(self, name: str):
        """移除图表"""
        if name in self.charts:
            index = self.tab_widget.indexOf(self.charts[name])
            if index >= 0:
                self.tab_widget.removeTab(index)
            del self.charts[name]

    def get_current_chart(self) -> ChartWidget:
        """获取当前图表"""
        return self.tab_widget.currentWidget()


class ChartControlPanel(QWidget):
    """
    图表控制面板
    
    【功能】
    提供图表显示和导出的控制选项
    
    【控制项】
    - 图表类型选择
    - 显示选项（网格、图例、统计）
    - 导出设置（DPI、格式）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)  # 控件间距12px

        # ===== 图表类型选择 =====
        type_group = QGroupBox("图表类型")
        type_layout = QVBoxLayout(type_group)

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "响应曲线",
            "实验vs仿真对比",
            "收敛曲线",
            "残差分析",
            "残差直方图",
            "刺激-剂量曲线",
            "参数柱状图",
            "综合分析"
        ])
        type_layout.addWidget(QLabel("选择图表:"))
        type_layout.addWidget(self.chart_type_combo)
        layout.addWidget(type_group)

        # ===== 显示选项 =====
        display_group = QGroupBox("显示选项")
        display_layout = QVBoxLayout(display_group)

        # QCheckBox: 复选框
        self.show_grid = QCheckBox("显示网格")
        self.show_grid.setChecked(True)  # 默认选中
        display_layout.addWidget(self.show_grid)

        self.show_legend = QCheckBox("显示图例")
        self.show_legend.setChecked(True)
        display_layout.addWidget(self.show_legend)

        self.show_stats = QCheckBox("显示统计信息")
        self.show_stats.setChecked(True)
        display_layout.addWidget(self.show_stats)

        layout.addWidget(display_group)

        # ===== 导出设置 =====
        export_group = QGroupBox("导出设置")
        export_layout = QVBoxLayout(export_group)

        export_layout.addWidget(QLabel("图片格式:"))
        self.export_format = QComboBox()
        self.export_format.addItems(["PNG", "PDF", "SVG"])
        export_layout.addWidget(self.export_format)

        # QDoubleSpinBox: 浮点数输入（带单位后缀）
        self.dpi_spin = QDoubleSpinBox()
        self.dpi_spin.setRange(72, 600)  # DPI范围: 72-600
        self.dpi_spin.setValue(150)  # 默认150DPI
        self.dpi_spin.setSuffix(" DPI")  # 后缀显示
        export_layout.addWidget(QLabel("分辨率:"))
        export_layout.addWidget(self.dpi_spin)

        layout.addWidget(export_group)

        # 弹性空间
        layout.addStretch()


class Particle3DWidget(ChartWidget):
    """
    粒子位置3D图部件

    【功能】
    显示PSO优化过程中粒子的空间分布

    【图表特点】
    - 3D散点图显示粒子位置
    - 用颜色表示适应度值
    - 显示全局最优位置
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, positions: np.ndarray, fitness: np.ndarray = None,
             global_best: np.ndarray = None, title: str = "粒子位置3D图"):
        """绘制粒子3D位置图"""
        figure = ChartFactory().create_particle_3d(
            positions, fitness, global_best, title
        )
        self.set_figure(figure)

    def plot_trajectory(self, trajectory: list, title: str = "粒子轨迹3D图"):
        """绘制粒子群演化轨迹"""
        figure = ChartFactory().create_particle_trajectory_3d(trajectory, title)
        self.set_figure(figure)


class SensitivityHeatmapWidget(ChartWidget):
    """
    参数敏感性热图部件

    【功能】
    显示各参数对目标函数的影响程度

    【分析方法】
    - 展示参数之间相互作用
    - 颜色深浅表示敏感性程度
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, param_names: list, sensitivity_matrix: np.ndarray,
             title: str = "参数敏感性热图"):
        """绘制参数敏感性热图"""
        figure = ChartFactory().create_sensitivity_heatmap(
            param_names, sensitivity_matrix, title
        )
        self.set_figure(figure)


class ParticleScatterWidget(ChartWidget):
    """
    粒子分布散点图部件

    【功能】
    以2D散点图形式展示粒子分布情况

    【图表特点】
    - 双参数维度切片
    - 颜色/大小编码适应度
    - 支持多时间步对比
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 移除最小高度限制，让图表自动填充空间

    def plot(self, positions: np.ndarray, fitness: np.ndarray,
             x_param: int = 0, y_param: int = 1,
             title: str = "粒子分布散点图"):
        """绘制粒子散点图"""
        figure = ChartFactory().create_particle_scatter(
            positions, fitness, x_param, y_param, title
        )
        self.set_figure(figure)
