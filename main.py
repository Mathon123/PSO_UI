"""
PSO数据分析工具 - 主程序入口
============================

【项目说明】
这是一个胫神经电刺激数据分析工具，集成了PSO（粒子群优化）算法
用于神经电刺激模型的参数辨识。

【支持功能】
- 双文件导入: stim_params.csv (刺激参数) + emg_processed.csv (EMG响应)
- 数据预处理和验证
- PSO参数辨识 (完整RLC电路模型)
- 模型评估 (RMSE/MAE/R²)
- 阈值电流计算
- SD曲线生成
- 数据导出 (Excel/CSV/JSON/图片)

【程序架构】
┌─────────────────────────────────────────────────────────────┐
│                      main.py (主入口)                        │
│  - 应用程序初始化                                            │
│  - 主窗口创建                                                │
│  - 信号槽绑定                                                │
├─────────────────────────────────────────────────────────────┤
│                      PSODataAnalysisApp                      │
│  - 继承自MainWindow                                         │
│  - 管理数据流                                                │
│  - 处理用户交互                                              │
├─────────────────────────────────────────────────────────────┤
│                    OptimizationThread                        │
│  - PSO优化在独立线程中运行                                   │
│  - 通过信号槽与主线程通信                                    │
│  - 避免UI冻结                                                │
└─────────────────────────────────────────────────────────────┘

【使用流程】
1. 导入EMG数据文件
2. 查看数据预览
3. 设置PSO参数
4. 运行优化
5. 查看优化结果
6. 导出数据/图表
"""

import sys
import os
import io
import time as time_module

# 设置UTF-8编码，解决Windows控制台GBK编码问题
# sys.stdout/sys.stderr: Python的标准输出/错误流
# io.TextIOWrapper: 包装器，将输出转换为UTF-8编码
# errors='replace': 遇到无法编码的字符时替换为?而不是抛出异常
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from typing import Optional, Dict, List
import numpy as np
import pandas as pd

# PyQt6核心组件
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QMessageBox, QWidget,
    QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QLabel, QPushButton, QFrame, QTextEdit, QProgressBar,
    QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
    QScrollArea, QSizePolicy, QComboBox, QLineEdit,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# 导入UI组件
from ui.main_window import MainWindow, StyleSheet
from modules.config import (
    APP_NAME, APP_VERSION, COLORS, FONTS,
    SUPPORTED_FILE_TYPES, CHART_TYPES
)
from modules.data_importer import DataImporter, DataInfo
from modules.data_processor import DataProcessor
from modules.visualization import ChartFactory
from modules.pso_optimizer import NerveParameterOptimizer, format_params
from ui.chart_widgets import (
    ResponseCurveWidget, ComparisonCurveWidget, ConvergenceCurveWidget,
    ResidualPlotWidget, ParameterBarWidget, SDCurveWidget,
    ComprehensiveAnalysisWidget, MultiChartWidget
)
from ui.analysis_workflow import NerveAnalysisWorkflow, NerveDataLoader


class OptimizationThread(QThread):
    """
    PSO优化线程
    
    【设计目的】
    PSO优化是计算密集型任务，可能耗时较长。
    为了避免UI冻结，将优化放在独立线程中执行。
    
    【线程通信机制】
    使用PyQt6的信号槽进行线程间通信:
    - progress 信号: 发射优化进度 (迭代次数, 当前RMSE)
    - finished 信号: 优化完成，携带结果数据
    - error 信号: 发生错误时发射
    
    【使用示例】
    thread = OptimizationThread(workflow, n_particles, n_iterations, ...)
    thread.progress.connect(self._on_optimization_progress)
    thread.finished.connect(self._on_optimization_finished)
    thread.start()  # 启动线程
    """

    # 信号定义 - 线程间通信
    # pyqtSignal(int, float): 发射 (迭代次数, RMSE值)
    progress = pyqtSignal(int, float)
    
    # pyqtSignal(object): 发射完整结果对象
    finished = pyqtSignal(object)
    
    # pyqtSignal(str): 发射错误信息
    error = pyqtSignal(str)

    def __init__(self, workflow, n_particles, n_iterations, target_rmse, frequency):
        """
        初始化优化线程
        
        Args:
            workflow: NerveAnalysisWorkflow 实例（注意：workflow.data应在主线程中设置）
            n_particles: 粒子群数量
            n_iterations: 最大迭代次数
            target_rmse: 目标RMSE值
            frequency: 分析频率 (Hz)
        """
        super().__init__()  # 调用父类构造函数
        
        self.workflow = workflow  # 分析工作流实例
        self.n_particles = n_particles  # 粒子数
        self.n_iterations = n_iterations  # 迭代次数
        self.target_rmse = target_rmse  # 目标RMSE
        self.frequency = frequency  # 频率

    def run(self):
        """
        线程主函数
        
        【执行流程】
        1. 检查数据是否有效
        2. 创建优化器并设置数据
        3. 执行优化（带进度回调）
        4. 发射完成/错误信号
        
        【注意】
        - 这是在线程中执行的函数
        - 不要在这里直接操作UI组件
        - 使用信号槽与主线程通信
        """
        try:
            print(f"[PSO Thread] 开始优化: particles={self.n_particles}, iterations={self.n_iterations}, target_rmse={self.target_rmse}", flush=True)
            
            # 记录开始时间
            start_time = time_module.time()
            
            # 直接从 workflow 获取数据（data已在主线程中设置好）
            data = self.workflow.data
            
            if data is None:
                raise ValueError("workflow.data 为 None，请先导入数据")
            
            # 获取频率对应的响应数据
            freq_key = f'Freq_{int(self.frequency)}Hz'
            responses = data.responses.get(freq_key)

            if responses is None:
                available_freqs = list(data.responses.keys())
                raise ValueError(f"频率 {self.frequency}Hz 不存在，可用频率: {available_freqs}")

            print(f"[PSO Thread] 频率={freq_key}, 数据点数={len(responses)}", flush=True)

            # 创建优化器并设置数据
            from modules.pso_optimizer import NerveParameterOptimizer
            optimizer = NerveParameterOptimizer()
            optimizer.set_data(
                currents=data.currents_A,  # 电流数组 (A)
                responses=responses,  # 响应概率数组
                pulse_width=data.pulse_width_s  # 脉宽 (s)
            )
            print(f"[PSO Thread] 优化器创建完成", flush=True)

            # 创建回调函数，直接发射进度信号
            # 进度回调在优化过程中被PSO算法调用
            def progress_callback(it, rmse):
                # self.progress.emit: 发射信号到主线程
                self.progress.emit(it, rmse)

            # 执行优化
            print(f"[PSO Thread] 开始执行优化...", flush=True)
            result = optimizer.optimize(
                n_particles=self.n_particles,
                n_iterations=self.n_iterations,
                target_rmse=self.target_rmse,
                verbose=False,
                progress_callback=progress_callback
            )
            
            # 计算耗时
            elapsed = time_module.time() - start_time
            print(f"[PSO Thread] 优化完成! RMSE={result.best_rmse:.6f}, 迭代={len(result.history.gbest_fitness_history)}, 耗时={elapsed:.2f}s", flush=True)

            # 更新 workflow 的优化器引用
            self.workflow.optimizer = optimizer
            self.workflow.optimization_result = result
            print(f"[PSO Thread] 结果已保存到 workflow", flush=True)

            # 发射完成信号，携带结果
            # self.finished.emit: 触发finished信号
            # 字典包含: result(优化结果), params(辨识的参数)
            self.finished.emit({
                'result': result,
                'params': optimizer.get_identified_params()
            })
            print(f"[PSO Thread] finished 信号已发射", flush=True)

        except Exception as e:
            # 捕获所有异常，发射错误信号
            import traceback
            print(f"[PSO Thread] 异常: {type(e).__name__}: {str(e)}", flush=True)
            print(f"[PSO Thread] 异常详情:\n{traceback.format_exc()}", flush=True)
            error_detail = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_detail)


class PSODataAnalysisApp(MainWindow):
    """PSO数据分析应用主类"""

    def __init__(self):
        # 初始化组件
        self.data_importer = DataImporter()
        self.data_processor = DataProcessor()
        self.chart_factory = ChartFactory()

        # 分析工作流
        self.workflow = NerveAnalysisWorkflow()
        self.optimizer = None
        self.optimization_thread = None

        # 数据
        self.current_data_info: Optional[DataInfo] = None
        self.experiment_data = None

        # 图表组件
        self.chart_widgets = {}

        # 优化结果
        self.optimization_result = None
        self.identified_params = {}
        self.result_tab = None

        super().__init__()

        # 绑定信号槽
        self.bind_signals()

        # 初始化图表区域
        QTimer.singleShot(0, self.init_chart_area)

        self.update_status("就绪 - 请导入EMG数据文件")

    def bind_signals(self):
        """绑定信号槽"""
        # 文件操作
        self.action_import.triggered.connect(self.import_data)
        self.btn_import.clicked.connect(self.import_data)

        self.action_export_excel.triggered.connect(self.export_excel)
        self.action_export_csv.triggered.connect(self.export_csv)
        self.action_export_json.triggered.connect(self.export_json)

        self.action_save_figure.triggered.connect(self.save_current_figure)
        self.action_exit.triggered.connect(self.close)

        # 数据操作
        self.action_refresh.triggered.connect(self.refresh_data)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.action_clear.triggered.connect(self.clear_data)
        self.btn_clear.clicked.connect(self.clear_data)

        # 分析操作
        self.btn_calc_stats.clicked.connect(self.calculate_statistics)
        self.action_statistics.triggered.connect(self.calculate_statistics)
        self.action_fit_quality.triggered.connect(self.show_fit_quality)

        # PSO优化
        self.btn_run_pso.clicked.connect(self.run_pso_optimization)
        self.action_pso_optimize.triggered.connect(self.run_pso_optimization)

        # 帮助
        self.action_about.triggered.connect(self.show_about)

    def init_chart_area(self):
        """初始化图表区域"""
        # 确保 chart_tabs 存在
        if not hasattr(self, 'chart_tabs'):
            return

        # 保存"优化结果"Tab的引用
        self.result_tab = self.main_tabs.widget(1) if hasattr(self, 'main_tabs') else None
        print(f"[UI] 获取 result_tab: {self.result_tab is not None}", flush=True)

        self.chart_tabs.clear()

        self.chart_widgets = {
            'response': ResponseCurveWidget(),
            'comparison': ComparisonCurveWidget(),
            'convergence': ConvergenceCurveWidget(),
            'residual': ResidualPlotWidget(),
            'parameter': ParameterBarWidget(),
            'sd_curve': SDCurveWidget(),
            'comprehensive': ComprehensiveAnalysisWidget(),
        }

        chart_names = {
            'response': '响应曲线',
            'comparison': '实验vs仿真',
            'convergence': '收敛曲线',
            'residual': '残差分析',
            'parameter': '参数分布',
            'sd_curve': 'SD曲线',
            'comprehensive': '综合分析',
        }

        for key, widget in self.chart_widgets.items():
            self.chart_tabs.addTab(widget, chart_names[key])

    @pyqtSlot()
    def import_data(self):
        """导入数据 - 支持双文件导入"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择EMG数据文件",
            self.get_file_dialog_path(),
            "EMG数据 (*.csv);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            self.update_status("正在导入数据...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)

            # 获取同目录下的刺激参数文件
            data_dir = Path(file_path).parent
            stim_file = data_dir / "stim_params.csv"

            # 尝试加载工作流
            try:
                self.experiment_data = NerveDataLoader.load_experiment_data(
                    file_path,
                    str(stim_file) if stim_file.exists() else None
                )

                # 保存文件路径
                self.current_file = file_path

                # 更新UI
                self._update_data_ui()

                self.update_status(
                    f"成功导入: {self.experiment_data.filename} "
                    f"({self.experiment_data.n_points}点, "
                    f"{', '.join(map(str, self.experiment_data.frequencies))}Hz)",
                    5000
                )

                # 自动生成响应曲线
                self._plot_response_curve()

            except Exception as e:
                # 降级到普通数据导入
                self.current_data_info = self.data_importer.import_file(file_path)
                self.load_data_to_table(self.current_data_info.raw_data)
                self.update_data_info({
                    'filename': self.current_data_info.filename,
                    'rows': self.current_data_info.shape[0],
                    'cols': self.current_data_info.shape[1],
                    'type': 'EMG数据'
                })
                self.update_status(f"成功导入: {self.current_data_info.filename}", 3000)

        except Exception as e:
            self.show_error("导入失败", str(e))
            self.update_status("导入失败")
        finally:
            self.progress_bar.setVisible(False)

    def _update_data_ui(self):
        """更新数据UI"""
        print(f"[UI] _update_data_ui 被调用", flush=True)

        # 记录导入前尺寸
        if hasattr(self, 'central_splitter'):
            sizes_before = self.central_splitter.sizes()
            print(f"[SIZE-DEBUG] _update_data_ui 开始前 splitter 尺寸: {sizes_before}", flush=True)
        print(f"[UI] experiment_data = {self.experiment_data}", flush=True)

        if self.experiment_data:
            print(f"[UI] 数据点数: {self.experiment_data.n_points}", flush=True)
            print(f"[UI] 频率列表: {self.experiment_data.frequencies}", flush=True)

            # 加载到表格
            df = pd.DataFrame({
                '电流_mA': self.experiment_data.currents_mA
            })
            for freq in self.experiment_data.frequencies:
                df[f'Freq_{int(freq)}Hz'] = self.experiment_data.responses.get(
                    f'Freq_{int(freq)}Hz', []
                )
            print(f"[UI] 表格DataFrame:\n{df}", flush=True)
            self.load_data_to_table(df)

            # 更新侧边栏
            freq_str = ', '.join([f"{f}Hz" for f in self.experiment_data.frequencies])
            self.update_data_info({
                'filename': self.experiment_data.filename,
                'rows': self.experiment_data.n_points,
                'cols': len(self.experiment_data.frequencies) + 1,
                'type': f'胫神经数据 (脉宽{self.experiment_data.pulse_width_us:.0f}us, {freq_str})'
            })

            # 检查尺寸变化
            if hasattr(self, 'central_splitter'):
                sizes_after = self.central_splitter.sizes()
                print(f"[SIZE-DEBUG] _update_data_ui 完成后 splitter 尺寸: {sizes_after}", flush=True)
        else:
            print("[UI] experiment_data 为 None，跳过UI更新", flush=True)

    def _plot_response_curve(self):
        """绘制响应曲线"""
        if not self.experiment_data:
            return

        responses = {}
        for freq in self.experiment_data.frequencies:
            freq_key = f'Freq_{int(freq)}Hz'
            if freq_key in self.experiment_data.responses:
                responses[freq_key] = self.experiment_data.responses[freq_key]

        if responses:
            self.chart_widgets['response'].plot(
                self.experiment_data.currents_mA,
                responses,
                title=f"响应曲线 - {self.experiment_data.filename}"
            )

    @pyqtSlot()
    def export_excel(self):
        """导出Excel"""
        if not self.experiment_data and not self.current_data_info:
            self.show_warning("导出失败", "请先导入数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出Excel",
            str(Path.home() / "pso_analysis_export.xlsx"),
            "Excel (*.xlsx)"
        )

        if file_path:
            try:
                if self.experiment_data:
                    df = pd.DataFrame({
                        '电流_mA': self.experiment_data.currents_mA
                    })
                    for freq in self.experiment_data.frequencies:
                        df[f'Freq_{int(freq)}Hz'] = self.experiment_data.responses.get(
                            f'Freq_{int(freq)}Hz', []
                        )
                    self.data_processor.to_excel(df, file_path)
                else:
                    self.data_processor.to_excel(self.current_data_info.raw_data, file_path)

                self.update_status(f"已导出: {file_path}", 3000)
            except Exception as e:
                self.show_error("导出失败", str(e))

    @pyqtSlot()
    def export_csv(self):
        """导出CSV"""
        if not self.experiment_data and not self.current_data_info:
            self.show_warning("导出失败", "请先导入数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV",
            str(Path.home() / "pso_analysis_export.csv"),
            "CSV (*.csv)"
        )

        if file_path:
            try:
                if self.experiment_data:
                    df = pd.DataFrame({
                        '电流_mA': self.experiment_data.currents_mA
                    })
                    for freq in self.experiment_data.frequencies:
                        df[f'Freq_{int(freq)}Hz'] = self.experiment_data.responses.get(
                            f'Freq_{int(freq)}Hz', []
                        )
                    self.data_processor.to_csv(df, file_path)
                else:
                    self.data_processor.to_csv(self.current_data_info.raw_data, file_path)

                self.update_status(f"已导出: {file_path}", 3000)
            except Exception as e:
                self.show_error("导出失败", str(e))

    @pyqtSlot()
    def export_json(self):
        """导出JSON"""
        if not self.experiment_data and not self.current_data_info:
            self.show_warning("导出失败", "请先导入数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出JSON",
            str(Path.home() / "pso_analysis_export.json"),
            "JSON (*.json)"
        )

        if file_path:
            try:
                if self.experiment_data:
                    data = {
                        'metadata': {
                            'filename': self.experiment_data.filename,
                            'n_points': self.experiment_data.n_points,
                            'frequencies': self.experiment_data.frequencies,
                            'pulse_width_us': self.experiment_data.pulse_width_us,
                        },
                        'data': {
                            'currents_mA': [float(x) for x in self.experiment_data.currents_mA],
                            'responses': {k: [float(x) for x in v] for k, v in self.experiment_data.responses.items()}
                        }
                    }
                    self.data_processor.to_json(data, file_path)
                else:
                    data = {
                        'metadata': {'filename': self.current_data_info.filename},
                        'data': self.current_data_info.raw_data.to_dict(orient='records')
                    }
                    self.data_processor.to_json(data, file_path)

                self.update_status(f"已导出: {file_path}", 3000)
            except Exception as e:
                self.show_error("导出失败", str(e))

    @pyqtSlot()
    def save_current_figure(self):
        """保存当前图表"""
        current_widget = self.chart_tabs.currentWidget()
        if hasattr(current_widget, 'save_chart'):
            current_widget.save_chart()

    @pyqtSlot()
    def refresh_data(self):
        """刷新数据"""
        if self.experiment_data:
            self._update_data_ui()
        self.update_status("数据已刷新")

    @pyqtSlot()
    def clear_data(self):
        """清空数据"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空当前数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 停止正在运行的优化线程
            if self.optimization_thread is not None:
                if self.optimization_thread.isRunning():
                    self.optimization_thread.requestInterruption()
                    if not self.optimization_thread.wait(1000):  # 等待最多1秒
                        self.optimization_thread.terminate()
                        self.optimization_thread.wait()
                self.optimization_thread = None
            
            self.experiment_data = None
            self.current_data_info = None
            self.optimization_result = None
            self.identified_params = {}
            self.workflow.data = None
            self.workflow.optimizer = None
            self.workflow.optimization_result = None
            self.optimizer = None
            self.table_widget.clear()
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            self.update_data_info({
                'filename': '未加载数据',
                'rows': 0, 'cols': 0, 'type': '-'
            })
            self.table_info_label.setText("未加载")
            # 重置优化结果表格
            if hasattr(self, 'metrics_table'):
                for row in range(self.metrics_table.rowCount()):
                    self.metrics_table.item(row, 1).setText("-")
            if hasattr(self, 'params_text'):
                self.params_text.setText("暂无参数结果")
            if hasattr(self, 'threshold_text'):
                self.threshold_text.setText("暂无阈值结果")
            if hasattr(self, 'result_status_label'):
                self.result_status_label.setText("等待优化")
                self.result_status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
            self.update_status("数据已清空")

    def load_data_to_table(self, data):
        """加载数据到表格"""
        if data is None:
            return

        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)

        self.table_widget.setRowCount(len(df))
        self.table_widget.setColumnCount(len(df.columns))
        self.table_widget.setHorizontalHeaderLabels(list(df.columns))

        for i, (_, row) in enumerate(df.iterrows()):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(i, j, item)

        self.table_widget.resizeColumnsToContents()
        self.table_widget.verticalHeader().setVisible(True)

        # 更新表格信息
        if hasattr(self, 'table_info_label'):
            self.table_info_label.setText(f"{len(df)} 行 x {len(df.columns)} 列")

    @pyqtSlot()
    def calculate_statistics(self):
        """计算统计指标"""
        if not self.experiment_data:
            self.show_warning("统计失败", "请先导入EMG数据")
            return

        stats_lines = []
        stats_lines.append("=" * 50)
        stats_lines.append("EMG数据统计摘要")
        stats_lines.append("=" * 50)
        stats_lines.append(f"数据点数: {self.experiment_data.n_points}")
        stats_lines.append(f"电流范围: {self.experiment_data.currents_mA.min():.2f} - {self.experiment_data.currents_mA.max():.2f} mA")
        stats_lines.append(f"脉宽: {self.experiment_data.pulse_width_us:.0f} us")
        stats_lines.append(f"频率: {', '.join(map(str, self.experiment_data.frequencies))} Hz")
        stats_lines.append("")

        for freq in self.experiment_data.frequencies:
            freq_key = f'Freq_{int(freq)}Hz'
            resp = self.experiment_data.responses.get(freq_key, [])

            stats_lines.append(f"【{freq_key}】")
            stats_lines.append(f"  均值:   {np.mean(resp):.4f}")
            stats_lines.append(f"  标准差: {np.std(resp):.4f}")
            stats_lines.append(f"  最小值: {np.min(resp):.4f}")
            stats_lines.append(f"  最大值: {np.max(resp):.4f}")
            stats_lines.append("")

        stats_text = "\n".join(stats_lines)

        # 更新数据信息卡片中的统计摘要
        if hasattr(self, 'table_info_label'):
            summary = f"{self.experiment_data.n_points}点 | {self.experiment_data.currents_mA.min():.1f}-{self.experiment_data.currents_mA.max():.1f}mA | {', '.join(map(str, self.experiment_data.frequencies))}Hz"
            self.table_info_label.setText(summary)

        # 在弹窗中显示统计结果
        self.show_info("统计结果", stats_text)
        self.update_status("统计计算完成")

    @pyqtSlot()
    def generate_chart(self):
        """生成图表"""
        if not self.experiment_data:
            self.show_warning("图表生成失败", "请先导入数据")
            return

        # 使用当前激活的图表tab
        # 如果有优化结果，刷新当前图表
        if self.optimization_result:
            self._refresh_current_chart()

    def _plot_comparison_curve(self):
        """绘制实验vs仿真对比曲线"""
        if not self.experiment_data or not self.optimizer:
            return

        try:
            currents, responses_sim = self.optimizer.compute_response_curve()

            # 构建包含所有频率的实验响应字典
            responses_exp_dict = {}
            for freq in self.experiment_data.frequencies:
                freq_key = f'Freq_{int(freq)}Hz'
                responses_exp_dict[freq_key] = self.experiment_data.responses.get(freq_key, [])

            # 获取当前选中的频率（默认第一个）
            freq = self.experiment_data.frequencies[0] if self.experiment_data.frequencies else 10
            freq_key = f'Freq_{int(freq)}Hz'

            # 获取对比曲线widget
            comparison_widget = self.chart_widgets['comparison']
            
            # 保存完整的响应数据字典供频率切换使用
            comparison_widget.responses_exp_dict = responses_exp_dict
            
            # 绘制对比曲线（传递字典）
            comparison_widget.plot(
                currents * 1000,  # 转为mA
                responses_exp_dict,
                responses_sim,
                freq_key
            )
        except Exception as e:
            import traceback
            print(f"[UI] [_plot_comparison_curve] 绘制失败: {e}", flush=True)
            print(f"[UI] 异常详情:\n{traceback.format_exc()}", flush=True)
            self.update_status(f"绘制失败: {str(e)}")

    @pyqtSlot()
    def show_fit_quality(self):
        """显示拟合质量"""
        if not self.optimization_result:
            self.show_warning("拟合评估失败", "请先运行PSO优化")
            return

        self.chart_tabs.setCurrentWidget(self.chart_widgets['comprehensive'])
        self._plot_comprehensive()

    def _plot_residual_analysis(self):
        """绘制残差分析图"""
        if not self.experiment_data or not self.optimizer:
            return

        try:
            # 获取仿真响应曲线
            currents, responses_sim = self.optimizer.compute_response_curve()

            # 获取当前选中频率的实验响应
            freq = self.experiment_data.frequencies[0] if self.experiment_data.frequencies else 10
            freq_key = f'Freq_{int(freq)}Hz'
            responses_exp = self.experiment_data.responses.get(freq_key, [])

            if len(responses_exp) > 0 and len(responses_sim) > 0:
                # 计算残差
                residuals = np.array(responses_exp) - responses_sim[:len(responses_exp)]

                # 绘制残差分析图
                self.chart_widgets['residual'].plot(
                    currents * 1000,  # 转为mA
                    None,  # residuals
                    responses_exp,
                    responses_sim[:len(responses_exp)],
                    title=f"残差分析 - {freq_key}"
                )
        except Exception as e:
            print(f"[UI] [_plot_residual_analysis] 绘制异常: {e}", flush=True)
            self.update_status(f"残差分析绘制失败: {str(e)}")

    def _plot_comprehensive(self):
        """绘制综合分析图"""
        if not self.experiment_data or not self.optimizer:
            return

        try:
            fit_quality = self.optimizer.evaluate_fit_quality()

            currents, responses_sim = self.optimizer.compute_response_curve()

            # 构建响应数据
            responses_exp = {}
            for freq in self.experiment_data.frequencies:
                freq_key = f'Freq_{int(freq)}Hz'
                responses_exp[freq_key] = self.experiment_data.responses.get(freq_key, [])

            # 计算残差
            residuals = {}
            for freq_key, resp_exp in responses_exp.items():
                resp_sim = responses_sim[:len(resp_exp)]
                residuals[freq_key] = np.array(resp_exp) - resp_sim

            self.chart_widgets['comprehensive'].plot(
                currents * 1000,
                responses_exp,
                responses_sim,
                residuals,
                fit_quality,
                title="胫神经电刺激综合分析"
            )
        except Exception as e:
            self.update_status(f"绘制失败: {str(e)}")

    @pyqtSlot()
    def run_pso_optimization(self):
        """运行PSO优化"""
        print(f"[DEBUG] run_pso_optimization 被调用", flush=True)
        print(f"[DEBUG] experiment_data = {self.experiment_data}", flush=True)
        
        if not self.experiment_data:
            print(f"[DEBUG] 没有数据，显示警告", flush=True)
            self.show_warning("优化失败", "请先导入EMG数据")
            return

        # 检查是否已有线程在运行
        if self.optimization_thread is not None and self.optimization_thread.isRunning():
            print(f"[DEBUG] 线程正在运行，显示警告", flush=True)
            self.show_warning("优化失败", "优化任务正在进行中，请等待完成")
            return

        # 保存 splitter 尺寸，防止布局变化
        if hasattr(self, 'central_splitter'):
            sizes = self.central_splitter.sizes()
            self._saved_splitter_sizes = sizes
            print(f"[DEBUG-SIZE] 运行优化前保存尺寸: {sizes}", flush=True)

        # 获取参数
        n_particles = self.spin_particles.value()
        n_iterations = self.spin_iterations.value()
        target_rmse = self.spin_target_rmse.value()

        # 选择频率
        freq = self.experiment_data.frequencies[0] if self.experiment_data.frequencies else 10

        self.update_status(f"正在运行PSO优化 (频率={freq}Hz)...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, n_iterations)
        self.progress_bar.setValue(0)
        self.btn_run_pso.setEnabled(False)

        # 【重要】在主线程中设置workflow数据，避免线程安全问题
        self.workflow.data = self.experiment_data
        
        # 创建优化线程
        self.optimization_thread = OptimizationThread(
            self.workflow,
            n_particles, n_iterations, target_rmse, freq
        )

        self.optimization_thread.progress.connect(self._on_optimization_progress)
        self.optimization_thread.finished.connect(self._on_optimization_finished)
        self.optimization_thread.error.connect(self._on_optimization_error)
        self.optimization_thread.start()

    def _on_optimization_progress(self, iteration: int, rmse: float):
        """优化进度更新"""
        self.progress_bar.setValue(iteration)
        self.update_status(f"PSO优化中... 迭代 {iteration}, RMSE: {rmse:.6f}")

    def _on_optimization_finished(self, result):
        """优化完成"""
        import traceback
        from PyQt6.QtWidgets import QApplication
        
        print(f"[UI] 收到优化完成信号", flush=True)
        
        # 保存结果数据
        self.optimization_result = result['result']
        self.identified_params = result['params']

        print(f"[UI] RMSE={self.optimization_result.best_rmse:.6f}", flush=True)
        print(f"[UI] 参数数量: {len(self.identified_params) if self.identified_params else 0}", flush=True)

        # 获取优化器
        self.optimizer = self.workflow.optimizer
        print(f"[UI] 获取优化器成功: {self.optimizer is not None}", flush=True)

        # 恢复 splitter 尺寸
        if hasattr(self, 'central_splitter') and hasattr(self, '_saved_splitter_sizes'):
            self.central_splitter.setSizes(self._saved_splitter_sizes)
            print(f"[DEBUG-SIZE] splitter尺寸已恢复", flush=True)

        self.progress_bar.setVisible(False)
        self.btn_run_pso.setEnabled(True)

        self.update_status(f"优化完成: {self.optimization_result.message}")
        print(f"[UI] UI状态已更新", flush=True)

        # 获取收敛历史
        history = self.workflow.get_convergence_history()
        print(f"[UI] 收敛历史长度: {len(history)}", flush=True)
        
        if len(history) == 0:
            print("[UI] 警告: 收敛历史为空!", flush=True)

        # 【修复1】首先显示优化结果（优先于图表更新）
        print("[UI] [Step 1] 开始显示优化结果...", flush=True)
        
        # 调试信息
        print(f"[UI] [Step 1] result_tab = {self.result_tab is not None}", flush=True)
        print(f"[UI] [Step 1] main_tabs = {hasattr(self, 'main_tabs') and self.main_tabs is not None}", flush=True)
        
        # 检查 result_tab 是否有效
        if self.result_tab is None:
            print("[UI] [Step 1] 警告: result_tab 为 None，尝试重新获取", flush=True)
            if hasattr(self, 'main_tabs') and self.main_tabs is not None:
                self.result_tab = self.main_tabs.widget(1)
                print(f"[UI] [Step 1] 重新获取 result_tab: {self.result_tab is not None}", flush=True)
        
        try:
            # 切换到"优化结果"Tab
            if self.result_tab:
                self.main_tabs.setCurrentWidget(self.result_tab)
                print("[UI] [Step 1] 已切换到优化结果 Tab", flush=True)
                QApplication.processEvents()
            else:
                print("[UI] [Step 1] 错误: result_tab 仍然为 None，无法切换 Tab", flush=True)
            
            # 显示结果
            print("[UI] [Step 1] 调用 _show_optimization_result()...", flush=True)
            self._show_optimization_result()
            print("[UI] [Step 1] 优化结果显示完成", flush=True)
        except Exception as e:
            print(f"[UI] [Step 1] 显示结果异常: {type(e).__name__}: {str(e)}", flush=True)
            print(f"[UI] 异常详情:\n{traceback.format_exc()}", flush=True)

        # 【修复2】然后延迟更新图表（分离关注点）
        QTimer.singleShot(200, lambda: self._update_charts_after_optimization(history))

    def _update_charts_after_optimization(self, history: list):
        """延迟更新图表（在结果Tab显示后执行）"""
        import traceback
        from PyQt6.QtWidgets import QApplication
        
        print("[UI] [Step 2] 开始更新图表...", flush=True)
        
        try:
            # 处理事件确保 Tab 切换完成
            QApplication.processEvents()
            
            # 绘制收敛曲线
            print("[UI] [Step 2] 绘制收敛曲线...", flush=True)
            convergence_widget = self.chart_widgets['convergence']
            self.chart_tabs.setCurrentWidget(convergence_widget)
            convergence_widget.plot(
                history,
                self.spin_target_rmse.value(),
                "PSO优化收敛曲线"
            )
            print("[UI] [Step 2] 收敛曲线绘制完成", flush=True)
            QApplication.processEvents()
            
            # 绘制参数柱状图
            print("[UI] [Step 2] 绘制参数柱状图...", flush=True)
            param_widget = self.chart_widgets['parameter']
            param_widget.plot(
                self.identified_params,
                NerveParameterOptimizer.PARAM_DISPLAY_NAMES,
                "辨识的参数分布"
            )
            print("[UI] [Step 2] 参数柱状图绘制完成", flush=True)
            QApplication.processEvents()
            
            # 绘制对比曲线
            print("[UI] [Step 2] 绘制对比曲线...", flush=True)
            self._plot_comparison_curve()
            print("[UI] [Step 2] 对比曲线绘制完成", flush=True)
            QApplication.processEvents()
            
            # 绘制SD曲线
            try:
                pw_us, curr_mA = self.optimizer.compute_sd_curve(target_p=0.8)
                self.chart_widgets['sd_curve'].plot(pw_us, curr_mA, target_p=0.8)
                print("[UI] [Step 2] SD曲线绘制完成", flush=True)
            except Exception as e:
                print(f"[UI] [Step 2] SD曲线绘制异常: {e}", flush=True)
            
            # 绘制残差分析图
            print("[UI] [Step 2] 绘制残差分析...", flush=True)
            self._plot_residual_analysis()
            print("[UI] [Step 2] 残差分析绘制完成", flush=True)
            QApplication.processEvents()
            
            # 绘制综合分析图
            print("[UI] [Step 2] 绘制综合分析...", flush=True)
            self._plot_comprehensive()
            print("[UI] [Step 2] 综合分析绘制完成", flush=True)
            QApplication.processEvents()
            
            print("[UI] [Step 2] 所有图表更新完成", flush=True)
            
        except Exception as e:
            print(f"[UI] [Step 2] 图表更新异常: {type(e).__name__}: {str(e)}", flush=True)
            print(f"[UI] 异常详情:\n{traceback.format_exc()}", flush=True)
            self.update_status("图表更新时出错")
            # 不显示错误弹窗，因为结果已正常显示

    def _on_optimization_error(self, error_msg: str):
        """优化错误"""
        print(f"[UI] 收到优化错误信号: {error_msg[:200]}...", flush=True)
        self.progress_bar.setVisible(False)
        self.btn_run_pso.setEnabled(True)
        self.update_status("优化失败")
        self.show_error("优化失败", error_msg)

    def _show_optimization_result(self):
        """显示优化结果"""
        print(f"[UI] [_show_optimization_result] 方法开始执行", flush=True)
        
        # 数据验证
        if not self.optimization_result:
            print("[UI] [_show_optimization_result] 错误: optimization_result 为 None", flush=True)
            return
        
        if self.optimization_result is None:
            print("[UI] [_show_optimization_result] 错误: optimization_result 为 None", flush=True)
            return
            
        print(f"[UI] [_show_optimization_result] optimizer: {self.optimizer is not None}", flush=True)
        print(f"[UI] [_show_optimization_result] experiment_data: {self.experiment_data is not None}", flush=True)
        
        # 打印当前标签状态
        print(f"[UI] [_show_optimization_result] 检查标签存在:", flush=True)
        print(f"  - self.rmse_value: {hasattr(self, 'rmse_value')}", flush=True)
        print(f"  - self.r2_value: {hasattr(self, 'r2_value')}", flush=True)
        print(f"  - self.iter_value: {hasattr(self, 'iter_value')}", flush=True)
        print(f"  - self.time_value: {hasattr(self, 'time_value')}", flush=True)
        
        # 计算基础指标
        n_iterations = len(self.optimization_result.history.gbest_fitness_history)
        elapsed = self.optimization_result.history.optimization_time
        print(f"[UI] [_show_optimization_result] 迭代次数={n_iterations}, 耗时={elapsed:.2f}s", flush=True)

        # 计算R²（带详细异常处理）
        r2_value = 0.0
        try:
            if self.experiment_data and self.optimizer:
                responses_sim = self.optimizer.compute_response_curve()[1]
                freq = self.experiment_data.frequencies[0] if self.experiment_data.frequencies else 10
                freq_key = f'Freq_{int(freq)}Hz'
                responses_exp = self.experiment_data.responses.get(freq_key, [])

                if len(responses_exp) > 0 and len(responses_sim) > 0:
                    ss_res = sum((a - b) ** 2 for a, b in zip(responses_exp, responses_sim[:len(responses_exp)]))
                    ss_tot = sum((a - sum(responses_exp) / len(responses_exp)) ** 2 for a in responses_exp)
                    r2_value = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        except Exception as e:
            print(f"[UI] R²计算异常: {e}", flush=True)

        # 计算阈值电流（每个单独处理，确保部分成功也能显示）
        threshold_data = {}
        try:
            threshold_50 = self.optimizer.compute_threshold_current(0.5)
            if threshold_50:
                threshold_data['P=50%'] = f"{threshold_50*1000:.2f} mA"
        except Exception as e:
            print(f"[UI] 阈值P=50%计算异常: {e}", flush=True)

        try:
            threshold_80 = self.optimizer.compute_threshold_current(0.8)
            if threshold_80:
                threshold_data['P=80%'] = f"{threshold_80*1000:.2f} mA"
        except Exception as e:
            print(f"[UI] 阈值P=80%计算异常: {e}", flush=True)

        try:
            threshold_90 = self.optimizer.compute_threshold_current(0.9)
            if threshold_90:
                threshold_data['P=90%'] = f"{threshold_90*1000:.2f} mA"
        except Exception as e:
            print(f"[UI] 阈值P=90%计算异常: {e}", flush=True)

        # 确保params不为空
        params = self.identified_params if self.identified_params else {}
        print(f"[UI] 显示数据: params={len(params)}, threshold={len(threshold_data)}", flush=True)

        # 总是调用更新（即使数据部分为空）
        self.update_optimization_result_display({
            'rmse': self.optimization_result.best_rmse,
            'iterations': n_iterations,
            'r2': r2_value,
            'elapsed': elapsed,
            'message': self.optimization_result.message,
            'params': params,
            'threshold': threshold_data
        })

        print(f"[UI] [_show_optimization_result] 调用 update_optimization_result_display 完成", flush=True)

    @pyqtSlot()
    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(
            self,
            f"关于 {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            f"<p>版本: {APP_VERSION}</p>"
            f"<p>胫神经电刺激数据分析与PSO参数优化工具。</p>"
            f"<hr>"
            f"<p><b>使用方法:</b></p>"
            f"<ol>"
            f"<li>导入EMG数据文件 (emg_processed.csv)</li>"
            f"<li>查看数据预览和统计信息</li>"
            f"<li>设置PSO参数并运行优化</li>"
            f"<li>查看辨识的参数和拟合质量</li>"
            f"<li>计算目标响应的阈值电流</li>"
            f"</ol>"
        )


def main():
    """主函数"""
    import os
    os.environ['QT_QPA_PLATFORM'] = 'windows'

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI, Microsoft YaHei", 10))

    # 添加异常处理
    def exception_hook(exc_type, exc_value, exc_traceback):
        import traceback
        print(f"[EXCEPTION] {exc_type.__name__}: {exc_value}", flush=True)
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_hook

    window = PSODataAnalysisApp()
    window.show()

    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
