"""
主窗口模块
=========

【模块说明】
本模块定义了PSO数据分析工具的主窗口界面，
包括菜单栏、工具栏、侧边栏、数据表格和图表区域。

【布局结构】
┌─────────────────────────────────────────────────────────────────┐
│  菜单栏 (Menu Bar)                                               │
├─────────────────────────────────────────────────────────────────┤
│  工具栏 (Tool Bar)                                              │
├────────────────┬────────────────────────────────────────────────┤
│                │                                                 │
│   左侧面板      │              右侧区域                           │
│   (参数控制)    │   ┌─────────────────────────────┐              │
│                │   │  主Tab区域                  │              │
│   - PSO参数    │   │  ├─ 数据预览                 │              │
│   - 频率选择   │   │  └─ 优化结果                 │              │
│   - 目标RMSE   │   └─────────────────────────────┘              │
│                │                                                 │
│   操作按钮      │   ┌─────────────────────────────┐              │
│                │   │  图表Tab区域                 │              │
│                │   │  (7种图表)                  │              │
│                │   └─────────────────────────────┘              │
│                │                                                 │
├────────────────┴────────────────────────────────────────────────┤
│  状态栏 (Status Bar)                                           │
└─────────────────────────────────────────────────────────────────┘
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QLabel, QPushButton, QFrame, QTextEdit, QProgressBar,
    QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
    QScrollArea, QSizePolicy, QComboBox, QLineEdit,
    QMenuBar, QMenu, QToolBar, QStatusBar, QTableWidget,
    QTableWidgetItem, QHeaderView,
    QGridLayout, QSizePolicy, QMainWindow, QToolButton,
    QApplication
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QTimer, QSettings
from PyQt6.QtGui import QAction, QFont, QIcon, QKeyEvent, QIntValidator, QDoubleValidator

from modules.config import (
    COLORS, FONTS, SPACING, BORDER_RADIUS,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
)


class StyleSheet:
    """
    全局样式表

    【样式规范】
    - 使用Figma风格设计
    - 统一的配色方案
    - 简洁的控件样式
    """

    @staticmethod
    def get_stylesheet() -> str:
        """
        获取完整的QSS样式表

        Returns:
            QSS样式表字符串
        """
        return f"""
        /* ================================================================
           全局样式
           ================================================================ */

        * {{
            font-family: {FONTS['family']};
        }}

        QWidget {{
            font-size: {FONTS['size_md']}px;
            color: {COLORS['text_primary']};
        }}

        QMainWindow {{
            background-color: {COLORS['bg_main']};
        }}

        /* ================================================================
           菜单栏
           ================================================================ */

        QMenuBar {{
            background-color: {COLORS['bg_card']};
            border-bottom: 1px solid {COLORS['border']};
            padding: 4px 8px;
            font-size: {FONTS['size_md']}px;
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: {BORDER_RADIUS['sm']}px;
        }}

        QMenuBar::item:selected {{
            background-color: {COLORS['bg_hover']};
        }}

        QMenu {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 8px 24px 8px 12px;
            border-radius: {BORDER_RADIUS['sm']}px;
        }}

        QMenu::item:selected {{
            background-color: {COLORS['bg_hover']};
        }}

        /* ================================================================
           工具栏
           ================================================================ */

        QToolBar {{
            background-color: {COLORS['bg_card']};
            border-bottom: 1px solid {COLORS['border']};
            spacing: 8px;
            padding: 6px 12px;
        }}

        QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 8px 12px;
            font-size: {FONTS['size_sm']}px;
            color: {COLORS['text_primary']};
        }}

        QToolButton:hover {{
            background-color: {COLORS['bg_hover']};
        }}

        QToolButton:pressed {{
            background-color: {COLORS['border']};
        }}

        /* ================================================================
           分组框
           ================================================================ */

        QGroupBox {{
            font-size: {FONTS['size_lg']}px;
            font-weight: bold;
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            margin-top: 16px;
            padding-top: 12px;
            background-color: {COLORS['bg_card']};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 8px;
            color: {COLORS['text_primary']};
        }}

        /* ================================================================
           按钮
           ================================================================ */

        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 10px 20px;
            font-size: {FONTS['size_md']}px;
            font-weight: 500;
        }}

        QPushButton:hover {{
            background-color: {COLORS['primary_hover']};
        }}

        QPushButton:pressed {{
            background-color: {COLORS['primary_pressed']};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['border']};
            color: {COLORS['text_muted']};
        }}

        QPushButton#secondaryBtn {{
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
        }}

        QPushButton#secondaryBtn:hover {{
            background-color: {COLORS['border']};
        }}

        /* ================================================================
           输入控件
           ================================================================ */

        QSpinBox, QDoubleSpinBox, QLineEdit {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 8px 40px 8px 12px;
            font-size: {FONTS['size_md']}px;
            min-height: 32px;
        }}

        QComboBox {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 4px 32px 4px 12px;         
            font-size: {FONTS['size_md']}px;
            min-height: 25px;    
        }}

        QSpinBox:focus, QDoubleSpinBox:focus,
        QLineEdit:focus {{
            border: 2px solid {COLORS['primary']};
        }}

        QComboBox:focus {{
            border: 2px solid {COLORS['primary']};
        }}

        /* 参数设置中的SpinBox样式 - 与分析频率下拉菜单保持一致 */
        QSpinBox#paramSpinBox, QDoubleSpinBox#paramSpinBox {{
            padding: 8px 32px 8px 12px;
        }}

        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            width: 24px;
            height: 16px;
            border: none;
            border-left: 1px solid {COLORS['border']};
            border-bottom: 1px solid {COLORS['border']};
            background-color: {COLORS['bg_card']};
            subcontrol-position: top right;
        }}

        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background-color: {COLORS['bg_hover']};
        }}

        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: 24px;
            height: 16px;
            border: none;
            border-left: 1px solid {COLORS['border']};
            background-color: {COLORS['bg_card']};
            subcontrol-position: bottom right;
        }}

        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: {COLORS['bg_hover']};
        }}

        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-bottom: 6px solid {COLORS['text_secondary']};
        }}

        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS['text_secondary']};
        }}

        /* ================================================================
           复选框
           ================================================================ */

        QCheckBox {{
            spacing: 8px;
            font-size: {FONTS['size_md']}px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {COLORS['border']};
            border-radius: 4px;
            background-color: {COLORS['bg_card']};
        }}

        QCheckBox::indicator:checked {{
            background-color: {COLORS['primary']};
            border-color: {COLORS['primary']};
        }}

        QCheckBox::indicator:hover {{
            border-color: {COLORS['primary']};
        }}

        /* ================================================================
           表格
           ================================================================ */

        QTableWidget {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            gridline-color: {COLORS['border_light']};
            font-size: {FONTS['size_sm']}px;
        }}

        QHeaderView::section {{
            background-color: {COLORS['table_header_bg']};
            color: {COLORS['text_primary']};
            font-weight: bold;
            padding: 10px;
            border: none;
            border-bottom: 2px solid {COLORS['border']};
        }}

        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {COLORS['border_light']};
        }}

        QTableWidget::item:alternate {{
            background-color: {COLORS['table_even_row']};
        }}

        QTableWidget::item:selected {{
            background-color: {COLORS['table_selected']};
        }}

        /* ================================================================
           Tab控件
           ================================================================ */

        QTabWidget::pane {{
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 0px;
            background-color: {COLORS['bg_card']};
        }}

        QTabBar::tab {{
            padding: 10px 20px;
            margin-right: 4px;
            border-top-left-radius: {BORDER_RADIUS['md']}px;
            border-top-right-radius: {BORDER_RADIUS['md']}px;
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_md']}px;
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

        /* ================================================================
           进度条
           ================================================================ */

        QProgressBar {{
            background-color: {COLORS['bg_hover']};
            border: none;
            border-radius: {BORDER_RADIUS['sm']}px;
            height: 8px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {COLORS['primary']};
            border-radius: {BORDER_RADIUS['sm']}px;
        }}

        /* ================================================================
           标签
           ================================================================ */

        QLabel {{
            font-size: {FONTS['size_md']}px;
            color: {COLORS['text_primary']};
        }}

        QLabel#titleLabel {{
            font-size: {FONTS['size_xl']}px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        }}

        QLabel#subtitleLabel {{
            font-size: {FONTS['size_lg']}px;
            color: {COLORS['text_secondary']};
        }}

        QLabel#valueLabel {{
            font-size: {FONTS['size_xxl']}px;
            font-weight: bold;
            color: {COLORS['primary']};
        }}

        /* ================================================================
           文本框
           ================================================================ */

        QTextEdit, QLineEdit {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 12px;
            font-size: {FONTS['size_md']}px;
        }}

        /* ================================================================
           滚动区域
           ================================================================ */

        QScrollArea {{
            background-color: transparent;
            border: none;
        }}

        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: 5px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['text_muted']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 10px;
            margin: 0px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {COLORS['border']};
            border-radius: 5px;
            min-width: 30px;
        }}

        /* ================================================================
           状态栏
           ================================================================ */

        QStatusBar {{
            background-color: {COLORS['bg_card']};
            border-top: 1px solid {COLORS['border']};
            padding: 6px 12px;
            font-size: {FONTS['size_sm']}px;
            color: {COLORS['text_secondary']};
        }}

        QStatusBar::item {{
            border: none;
        }}

        /* ================================================================
           分隔器
           ================================================================ */

        QSplitter::handle {{
            background-color: {COLORS['border']};
        }}

        QSplitter::handle:horizontal {{
            width: 1px;
        }}

        QSplitter::handle:vertical {{
            height: 1px;
        }}
        """


class MainWindow(QMainWindow):
    """
    主窗口类

    【功能】
    提供完整的主窗口界面，包括：
    - 菜单栏：文件、编辑、视图、帮助
    - 工具栏：常用操作快捷按钮
    - 左侧面板：PSO参数设置、数据操作
    - 右侧区域：主Tab（数据预览/优化结果）和图表Tab
    - 状态栏：状态信息和进度条

    【布局结构】
    ┌──────────────────────────────────────────────────────────────┐
    │  菜单栏                                                       │
    ├──────────────────────────────────────────────────────────────┤
    │  工具栏                                                       │
    ├─────────────────┬─────────────────────────────────────────────┤
    │                 │                                              │
    │   左侧面板      │              右侧区域                        │
    │   280px固定     │   可伸缩区域                                │
    │                 │                                              │
    │  ┌───────────┐  │  ┌────────────────────────────────────┐    │
    │  │PSO参数    │  │  │  主Tab: 数据预览 | 优化结果        │    │
    │  │  -粒子数  │  │  ├────────────────────────────────────┤    │
    │  │  -迭代次数│  │  │                                    │    │
    │  │  -目标RMSE│  │  │  数据表格/优化结果面板              │    │
    │  └───────────┘  │  │                                    │    │
    │                 │  └────────────────────────────────────┘    │
    │  ┌───────────┐  │                                              │
    │  │操作按钮   │  │  ┌────────────────────────────────────┐    │
    │  │[导入数据] │  │  │  图表Tab (7种图表)                │    │
    │  │[运行优化] │  │  │                                    │    │
    │  └───────────┘  │  │                                    │    │
    │                 │  └────────────────────────────────────┘    │
    ├─────────────────┴─────────────────────────────────────────────┤
    │  状态栏                                                       │
    └──────────────────────────────────────────────────────────────┘
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 应用样式
        self.setStyleSheet(StyleSheet.get_stylesheet())

        # 设置窗口属性
        self.setWindowTitle("PSO数据分析工具")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # 加载保存的窗口尺寸，如果没有则使用默认尺寸
        settings = QSettings("PSO_Tools", "DataAnalyzer")
        saved_width = settings.value("window_width", WINDOW_DEFAULT_WIDTH, type=int)
        saved_height = settings.value("window_height", WINDOW_DEFAULT_HEIGHT, type=int)
        self.resize(saved_width, saved_height)

        # 信息显示字典
        self._info_widgets = {}
        self._metric_widgets = {}

        # 当前文件路径
        self.current_file = None

        # 创建UI
        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()

    def closeEvent(self, event):
        """窗口关闭时保存当前尺寸和splitter状态"""
        settings = QSettings("PSO_Tools", "DataAnalyzer")
        # 保存窗口尺寸
        settings.setValue("window_width", self.width())
        settings.setValue("window_height", self.height())
        # 保存 splitter 尺寸状态
        settings.setValue("central_splitter_sizes", self.central_splitter.sizes())
        settings.setValue("h_splitter_sizes", self.h_splitter.sizes())
        super().closeEvent(event)

    def _on_particles_inc(self):
        """粒子数增加"""
        if self._particles_value < self._particles_max:
            self._particles_value += 10
            self.label_particles_value.setText(str(self._particles_value))

    def _on_particles_dec(self):
        """粒子数减少"""
        if self._particles_value > self._particles_min:
            self._particles_value -= 10
            self.label_particles_value.setText(str(self._particles_value))

    def _on_particles_edit_finished(self):
        """粒子数输入完成"""
        try:
            value = int(self.edit_particles.text())
            if self._particles_min <= value <= self._particles_max:
                self._particles_value = value
                self.label_particles_value.setText(str(self._particles_value))
            else:
                self.edit_particles.setText(str(self._particles_value))
        except ValueError:
            self.edit_particles.setText(str(self._particles_value))

    def get_particles_value(self) -> int:
        """获取当前粒子数值"""
        return self._particles_value

    def set_particles_value(self, value: int):
        """设置粒子数值"""
        if self._particles_min <= value <= self._particles_max:
            self._particles_value = value
            self.label_particles_value.setText(str(self._particles_value))

    def _on_iterations_inc(self):
        """迭代次数增加"""
        if self._iterations_value < self._iterations_max:
            self._iterations_value += self._iterations_step
            if self._iterations_value > self._iterations_max:
                self._iterations_value = self._iterations_max
            self.edit_iterations.setText(str(self._iterations_value))

    def _on_iterations_dec(self):
        """迭代次数减少"""
        if self._iterations_value > self._iterations_min:
            self._iterations_value -= self._iterations_step
            if self._iterations_value < self._iterations_min:
                self._iterations_value = self._iterations_min
            self.edit_iterations.setText(str(self._iterations_value))

    def _on_iterations_edit_finished(self):
        """迭代次数输入完成"""
        try:
            value = int(self.edit_iterations.text())
            if self._iterations_min <= value <= self._iterations_max:
                self._iterations_value = value
            else:
                self.edit_iterations.setText(str(self._iterations_value))
        except ValueError:
            self.edit_iterations.setText(str(self._iterations_value))

    def get_iterations_value(self) -> int:
        """获取当前迭代次数值"""
        return self._iterations_value

    def set_iterations_value(self, value: int):
        """设置迭代次数值"""
        if self._iterations_min <= value <= self._iterations_max:
            self._iterations_value = value
            self.edit_iterations.setText(str(self._iterations_value))

    def _on_rmse_inc(self):
        """目标RMSE增加"""
        if self._target_rmse_value < self._target_rmse_max:
            self._target_rmse_value += self._target_rmse_step
            if self._target_rmse_value > self._target_rmse_max:
                self._target_rmse_value = self._target_rmse_max
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    def _on_rmse_dec(self):
        """目标RMSE减少"""
        if self._target_rmse_value > self._target_rmse_min:
            self._target_rmse_value -= self._target_rmse_step
            if self._target_rmse_value < self._target_rmse_min:
                self._target_rmse_value = self._target_rmse_min
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    def _on_rmse_edit_finished(self):
        """目标RMSE输入完成"""
        try:
            value = float(self.edit_target_rmse.text())
            if self._target_rmse_min <= value <= self._target_rmse_max:
                self._target_rmse_value = value
                self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")
            else:
                self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")
        except ValueError:
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    def get_target_rmse_value(self) -> float:
        """获取当前目标RMSE值"""
        return self._target_rmse_value

    def set_target_rmse_value(self, value: float):
        """设置目标RMSE值"""
        if self._target_rmse_min <= value <= self._target_rmse_max:
            self._target_rmse_value = value
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        self.action_import = QAction("导入数据...", self)
        self.action_import.setShortcut("Ctrl+O")
        file_menu.addAction(self.action_import)

        file_menu.addSeparator()

        export_menu = QMenu("导出", self)
        self.action_export_excel = QAction("导出为 Excel...", self)
        self.action_export_csv = QAction("导出为 CSV...", self)
        self.action_export_json = QAction("导出为 JSON...", self)
        export_menu.addAction(self.action_export_excel)
        export_menu.addAction(self.action_export_csv)
        export_menu.addAction(self.action_export_json)
        file_menu.addMenu(export_menu)

        self.action_save_figure = QAction("保存当前图表...", self)
        self.action_save_figure.setShortcut("Ctrl+S")
        file_menu.addAction(self.action_save_figure)

        file_menu.addSeparator()

        self.action_exit = QAction("退出", self)
        self.action_exit.setShortcut("Ctrl+Q")
        file_menu.addAction(self.action_exit)

        # 数据菜单
        data_menu = menubar.addMenu("数据")

        self.action_refresh = QAction("刷新数据", self)
        self.action_refresh.setShortcut("F5")
        data_menu.addAction(self.action_refresh)

        self.action_clear = QAction("清空数据", self)
        data_menu.addAction(self.action_clear)

        data_menu.addSeparator()

        self.action_statistics = QAction("计算统计指标", self)
        data_menu.addAction(self.action_statistics)

        # 分析菜单
        analysis_menu = menubar.addMenu("分析")

        self.action_pso_optimize = QAction("运行PSO优化", self)
        self.action_pso_optimize.setShortcut("F9")
        analysis_menu.addAction(self.action_pso_optimize)

        self.action_fit_quality = QAction("拟合质量评估", self)
        analysis_menu.addAction(self.action_fit_quality)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        self.action_about = QAction("关于", self)
        help_menu.addAction(self.action_about)

    def _create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        # 创建左侧面板
        left_panel = self._create_left_panel()

        # 创建右侧区域
        right_area = self._create_right_area()

        # 使用Splitter分隔左右区域
        self.central_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.central_splitter.addWidget(left_panel)
        self.central_splitter.addWidget(right_area)
        self.central_splitter.setStretchFactor(0, 0)  # 左侧固定
        self.central_splitter.setStretchFactor(1, 1)   # 右侧可伸缩

        # 加载保存的 splitter 尺寸
        settings = QSettings("PSO_Tools", "DataAnalyzer")
        central_sizes = settings.value("central_splitter_sizes")
        if central_sizes:
            # QSettings返回字符串列表，需要转换为整数
            self.central_splitter.setSizes([int(x) for x in central_sizes])

        h_sizes = settings.value("h_splitter_sizes")
        if h_sizes:
            self.h_splitter.setSizes([int(x) for x in h_sizes])

        main_layout.addWidget(self.central_splitter)

    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        left_widget = QWidget()
        left_widget.setMinimumWidth(260)
        left_widget.setMaximumWidth(320)

        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ========== 数据信息卡片 ==========
        info_group = QGroupBox("数据信息")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(8)  # 网格元素间距

        # 文件名
        info_layout.addWidget(QLabel("文件名:"), 0, 0)
        self._info_widgets['filename'] = QLabel("-")
        info_layout.addWidget(self._info_widgets['filename'], 0, 1)

        # 数据类型
        info_layout.addWidget(QLabel("类型:"), 1, 0)
        self._info_widgets['type'] = QLabel("-")
        info_layout.addWidget(self._info_widgets['type'], 1, 1)

        # 数据点数
        info_layout.addWidget(QLabel("行数:"), 2, 0)
        self._info_widgets['rows'] = QLabel("0")
        info_layout.addWidget(self._info_widgets['rows'], 2, 1)

        # 列数
        info_layout.addWidget(QLabel("列数:"), 3, 0)
        self._info_widgets['cols'] = QLabel("0")
        info_layout.addWidget(self._info_widgets['cols'], 3, 1)

        layout.addWidget(info_group)

        # ========== PSO参数设置 ==========
        pso_group = QGroupBox("PSO优化算法参数设置")
        pso_layout = QGridLayout(pso_group)
        pso_layout.setSpacing(8)  # 网格元素间距

        # 粒子数 - 使用自定义 +/- 按钮布局，支持直接输入
        pso_layout.addWidget(QLabel("粒子数:"), 0, 0)

        # 数值显示和按钮容器
        particles_widget = QWidget()
        particles_layout = QHBoxLayout(particles_widget)
        particles_layout.setContentsMargins(0, 0, 0, 0)
        particles_layout.setSpacing(4)

        # 数值输入框（可编辑）
        self.edit_particles = QLineEdit("100")
        self.edit_particles.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_particles.setFixedSize(80, 35)
        self.edit_particles.setMaxLength(3)
        self.edit_particles.setValidator(QIntValidator(10, 500, self))
        self.edit_particles.setToolTip("PSO粒子群中的粒子数量 (10-500)")
        self.edit_particles.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['sm']}px;
                padding: 0px 4px;
                font-size: {FONTS['size_md']}px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)

        # + 按钮
        self.btn_particles_inc = QPushButton("+")
        self.btn_particles_inc.setFixedWidth(28)
        self.btn_particles_inc.setToolTip("增加粒子数")
        self.btn_particles_inc.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)

        # - 按钮
        self.btn_particles_dec = QPushButton("-")
        self.btn_particles_dec.setFixedWidth(28)
        self.btn_particles_dec.setToolTip("减少粒子数")
        self.btn_particles_dec.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)

        particles_layout.addWidget(self.edit_particles)
        particles_layout.addWidget(self.btn_particles_inc)
        particles_layout.addWidget(self.btn_particles_dec)

        # 粒子数参数存储
        self._particles_value = 100
        self._particles_min = 10
        self._particles_max = 500

        # 连接信号
        self.btn_particles_inc.clicked.connect(self._on_particles_inc)
        self.btn_particles_dec.clicked.connect(self._on_particles_dec)
        self.edit_particles.editingFinished.connect(self._on_particles_edit_finished)

        pso_layout.addWidget(particles_widget, 0, 1)

        # 迭代次数 - 使用自定义 +/- 按钮布局，支持直接输入
        pso_layout.addWidget(QLabel("迭代次数:"), 1, 0)

        # 数值显示和按钮容器
        iterations_widget = QWidget()
        iterations_layout = QHBoxLayout(iterations_widget)
        iterations_layout.setContentsMargins(0, 0, 0, 0)
        iterations_layout.setSpacing(4)

        # 数值输入框（可编辑）
        self.edit_iterations = QLineEdit("50")
        self.edit_iterations.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_iterations.setFixedSize(80, 35)
        self.edit_iterations.setMaxLength(3)
        self.edit_iterations.setValidator(QIntValidator(10, 500, self))
        self.edit_iterations.setToolTip("PSO最大迭代次数 (10-500)")
        self.edit_iterations.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['sm']}px;
                padding: 0px 4px;
                font-size: {FONTS['size_md']}px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)

        # + 按钮
        self.btn_iterations_inc = QPushButton("+")
        self.btn_iterations_inc.setFixedWidth(28)
        self.btn_iterations_inc.setToolTip("增加迭代次数")
        self.btn_iterations_inc.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)

        # - 按钮
        self.btn_iterations_dec = QPushButton("-")
        self.btn_iterations_dec.setFixedWidth(28)
        self.btn_iterations_dec.setToolTip("减少迭代次数")
        self.btn_iterations_dec.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)

        iterations_layout.addWidget(self.edit_iterations)
        iterations_layout.addWidget(self.btn_iterations_inc)
        iterations_layout.addWidget(self.btn_iterations_dec)

        # 迭代次数参数存储
        self._iterations_value = 50
        self._iterations_min = 10
        self._iterations_max = 500
        self._iterations_step = 10

        # 连接信号
        self.btn_iterations_inc.clicked.connect(self._on_iterations_inc)
        self.btn_iterations_dec.clicked.connect(self._on_iterations_dec)
        self.edit_iterations.editingFinished.connect(self._on_iterations_edit_finished)

        pso_layout.addWidget(iterations_widget, 1, 1)

        # 目标RMSE - 使用自定义 +/- 按钮布局，支持直接输入
        pso_layout.addWidget(QLabel("目标RMSE:"), 2, 0)

        # 数值显示和按钮容器
        rmse_widget = QWidget()
        rmse_layout = QHBoxLayout(rmse_widget)
        rmse_layout.setContentsMargins(0, 0, 0, 0)
        rmse_layout.setSpacing(4)

        # 数值输入框（可编辑）
        self.edit_target_rmse = QLineEdit("0.03")
        self.edit_target_rmse.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_target_rmse.setFixedSize(80, 35)
        self.edit_target_rmse.setValidator(QDoubleValidator(0.001, 1.0, 4, self))
        self.edit_target_rmse.setToolTip("优化目标RMSE阈值 (0.001-1.0)")
        self.edit_target_rmse.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['sm']}px;
                padding: 0px 4px;
                font-size: {FONTS['size_md']}px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)

        # + 按钮
        self.btn_rmse_inc = QPushButton("+")
        self.btn_rmse_inc.setFixedWidth(28)
        self.btn_rmse_inc.setToolTip("增加目标RMSE")
        self.btn_rmse_inc.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)

        # - 按钮
        self.btn_rmse_dec = QPushButton("-")
        self.btn_rmse_dec.setFixedWidth(28)
        self.btn_rmse_dec.setToolTip("减少目标RMSE")
        self.btn_rmse_dec.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background-color: {COLORS['border']};
            }}
        """)

        rmse_layout.addWidget(self.edit_target_rmse)
        rmse_layout.addWidget(self.btn_rmse_inc)
        rmse_layout.addWidget(self.btn_rmse_dec)

        # 目标RMSE参数存储
        self._target_rmse_value = 0.03
        self._target_rmse_min = 0.001
        self._target_rmse_max = 1.0
        self._target_rmse_step = 0.01

        # 连接信号
        self.btn_rmse_inc.clicked.connect(self._on_rmse_inc)
        self.btn_rmse_dec.clicked.connect(self._on_rmse_dec)
        self.edit_target_rmse.editingFinished.connect(self._on_rmse_edit_finished)

        pso_layout.addWidget(rmse_widget, 2, 1)

        # 频率选择 - 宽度与目标RMSE行对齐（输入框80 + 间距4 + 两个按钮各28 = 140）
        pso_layout.addWidget(QLabel("分析频率:"), 3, 0)
        self.combo_frequency = QComboBox()
        self.combo_frequency.setFixedHeight(28)
        self.combo_frequency.setFixedWidth(180)  # 与目标RMSE行（输入框80+间距4+两个按钮28+28）对齐
        self.combo_frequency.addItems(["10Hz", "20Hz", "All"])
        self.combo_frequency.setCurrentIndex(2)   #设置默认选中第 2 项（All）
        pso_layout.addWidget(self.combo_frequency, 3, 1)

        layout.addWidget(pso_group)

        # ========== 操作按钮 ==========
        btn_group = QGroupBox("操作")
        btn_layout = QVBoxLayout(btn_group)
        btn_layout.setSpacing(10)  # 按钮间距

        # 主操作按钮
        self.btn_import = QPushButton("导入数据")
        self.btn_import.setFixedSize(260, 40)
        btn_layout.addWidget(self.btn_import)

        self.btn_run_pso = QPushButton("运行PSO优化")
        self.btn_run_pso.setFixedSize(260, 40)
        btn_layout.addWidget(self.btn_run_pso)

        # 次要操作按钮
        self.btn_calc_stats = QPushButton("计算统计")
        self.btn_calc_stats.setFixedSize(260, 40)
        self.btn_calc_stats.setObjectName("secondaryBtn")
        btn_layout.addWidget(self.btn_calc_stats)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        btn_layout.addWidget(separator)

        # 辅助操作按钮
        h_layout = QHBoxLayout()
        h_layout.setSpacing(8)
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setObjectName("secondaryBtn")
        self.btn_refresh.setMinimumHeight(32)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setObjectName("secondaryBtn")
        self.btn_clear.setMinimumHeight(32)
        h_layout.addWidget(self.btn_refresh)
        h_layout.addWidget(self.btn_clear)
        btn_layout.addLayout(h_layout)

        layout.addWidget(btn_group)

        # 弹性空间
        layout.addStretch()

        return left_widget

    def _create_right_area(self) -> QWidget:
        """创建右侧区域"""
        right_widget = QWidget()

        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 创建水平 Splitter（左侧主Tab + 右侧图表Tab）
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ========== 左侧：主Tab区域 ==========
        self.main_tabs = QTabWidget()

        # 数据预览Tab
        data_preview = self._create_data_preview_tab()
        self.main_tabs.addTab(data_preview, "数据预览")

        # 优化结果Tab
        result_tab = self._create_result_tab()
        self.main_tabs.addTab(result_tab, "优化结果")
        self.result_tab = result_tab

        self.h_splitter.addWidget(self.main_tabs)
        self.h_splitter.setStretchFactor(0, 1)  # 左侧比例 1

        # ========== 右侧：图表Tab区域 ==========
        self.chart_tabs = QTabWidget()

        # 图表Tab样式 - 与主Tab保持一致的Figma风格
        self.chart_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
                padding: 8px;
                background-color: {COLORS['bg_card']};
            }}
            QTabBar::tab {{
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: {BORDER_RADIUS['md']}px;
                border-top-right-radius: {BORDER_RADIUS['md']}px;
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-size: {FONTS['size_md']}px;
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

        self.h_splitter.addWidget(self.chart_tabs)
        self.h_splitter.setStretchFactor(1, 3)  # 右侧比例 3 (左右1:3)

        layout.addWidget(self.h_splitter, 1)

        return right_widget

    def _create_data_preview_tab(self) -> QWidget:
        """创建数据预览Tab"""
        widget = QWidget()

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 表格工具栏
        toolbar_layout = QHBoxLayout()

        # 表格信息标签
        self.table_info_label = QLabel("未加载数据")
        self.table_info_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_sm']}px;
            padding: 4px;
        """)
        toolbar_layout.addWidget(self.table_info_label)
        toolbar_layout.addStretch()

        # 搜索框
        self.table_search = QLineEdit()
        self.table_search.setPlaceholderText("搜索...")
        self.table_search.setMaximumWidth(200)
        self.table_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['sm']}px;
                padding: 6px 12px;
                font-size: {FONTS['size_sm']}px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.table_search.textChanged.connect(self._on_table_search)
        toolbar_layout.addWidget(self.table_search)

        layout.addLayout(toolbar_layout)

        # 数据表格容器
        table_container = QWidget()
        table_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
            }}
        """)

        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # 数据表格
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSortingEnabled(True)  # 启用排序
        self.table_widget.setShowGrid(True)  # 显示网格
        self.table_widget.verticalHeader().setVisible(True)  # 显示行号
        self.table_widget.verticalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {COLORS['table_header_bg']};
                color: {COLORS['text_secondary']};
                font-size: {FONTS['size_xs']}px;
                padding: 4px;
                border: none;
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionsClickable(True)  # 列可点击排序
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self._show_table_context_menu)

        # 启用复制快捷键
        self.table_widget.keyPressEvent = self._create_table_key_handler(
            self.table_widget.keyPressEvent, self.table_widget
        )

        table_layout.addWidget(self.table_widget)
        layout.addWidget(table_container)

        return widget

    def _on_table_search(self, text: str):
        """表格搜索过滤"""
        for row in range(self.table_widget.rowCount()):
            match = False
            if not text:
                match = True
            else:
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item and text.lower() in item.text().lower():
                        match = True
                        break
            self.table_widget.setRowHidden(row, not match)

    def _show_table_context_menu(self, pos):
        """显示表格右键菜单"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        copy_action = menu.addAction("复制")
        copy_row_action = menu.addAction("复制整行")
        menu.addSeparator()
        select_all_action = menu.addAction("全选")
        action = menu.exec(self.table_widget.mapToGlobal(pos))
        if action == copy_action:
            self._copy_selected_cells()
        elif action == copy_row_action:
            self._copy_current_row()
        elif action == select_all_action:
            self.table_widget.selectAll()

    def _copy_selected_cells(self):
        """复制选中的单元格"""
        selection = self.table_widget.selectedIndexes()
        if selection:
            rows = sorted(set(index.row() for index in selection))
            columns = sorted(set(index.column() for index in selection))
            text = ""
            for row in rows:
                row_data = []
                for col in columns:
                    item = self.table_widget.item(row, col)
                    row_data.append(item.text() if item else "")
                text += "\t".join(row_data) + "\n"
            from PyQt6.QtGui import QClipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(text.strip())

    def _copy_current_row(self):
        """复制当前行"""
        row = self.table_widget.currentRow()
        if row >= 0:
            text = ""
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                text += (item.text() if item else "") + "\t"
            from PyQt6.QtGui import QClipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(text.strip())

    def _create_table_key_handler(self, original_method, table):
        """创建表格按键处理"""
        def key_handler(event):
            if event.matches(QKeyEvent.Copy):
                self._copy_selected_cells()
            else:
                original_method(event)
        return key_handler

    def _create_result_tab(self) -> QWidget:
        """创建优化结果Tab"""
        widget = QWidget()
        widget.setMinimumSize(350, 180)  # 设置最小宽高确保显示完整

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # ========== 结果状态 ==========
        status_layout = QHBoxLayout()

        self.result_status_label = QLabel("等待优化")
        self.result_status_label.setStyleSheet(f"""
            font-size: {FONTS['size_lg']}px;
            font-weight: bold;
            color: {COLORS['text_muted']};
            padding: 8px 16px;
            background-color: {COLORS['bg_hover']};
            border-radius: {BORDER_RADIUS['sm']}px;
        """)
        status_layout.addWidget(self.result_status_label)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # ========== 核心指标表格 ==========  #35px指标卡片外框尺寸
        self.metrics_card = QWidget()
        self.metrics_card.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
                padding: 35px;
            }}
        """)
        self.metrics_card.setMinimumHeight(10)

        metrics_layout = QVBoxLayout(self.metrics_card)
        metrics_layout.setContentsMargins(8, 8, 8, 8)
        metrics_layout.setSpacing(0)

        self.metrics_table = QTableWidget(4, 2)    #指标卡片表格 4行2列
        self.metrics_table.setHorizontalHeaderLabels(["指标名", "指标值"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.verticalHeader().setVisible(False)
        self.metrics_table.setShowGrid(False)
        self.metrics_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.metrics_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.metrics_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.metrics_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 样式
        header_style = f"""
            QHeaderView::section {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-size: {FONTS['size_sm']}px;
                font-weight: bold;
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """
        cell_style = f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                font-size: {FONTS['size_md']}px;
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item {{
                padding: 10px 12px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QTableWidget::item:alternate {{
                background-color: {COLORS['bg_hover']};
            }}
        """
        value_style = f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                font-size: {FONTS['size_lg']}px;
                font-weight: bold;
                font-family: {FONTS['monospace']};
                color: {COLORS['primary']};
            }}
            QTableWidget::item {{
                padding: 10px 12px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """
        self.metrics_table.setStyleSheet(header_style + cell_style)
        self.metrics_table.setAlternatingRowColors(True)

        # 初始化数据
        metric_data = [
            ("RMSE", "-"),
            ("R²", "-"),
            ("迭代次数", "-"),
            ("耗时", "-"),
        ]
        for row, (name, value) in enumerate(metric_data):
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.metrics_table.setItem(row, 0, name_item)

            value_item = QTableWidgetItem(value)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.metrics_table.setItem(row, 1, value_item)

        # 设置列宽
        self.metrics_table.setColumnWidth(0, 100)
        self.metrics_table.setColumnWidth(1, 150)

        metrics_layout.addWidget(self.metrics_table)

        layout.addWidget(self.metrics_card)

        # ========== 详细结果区域 ==========
        detail_layout = QHBoxLayout()
        detail_layout.setSpacing(16)

        # 参数显示
        params_group = QGroupBox("神经响应辨识参数")
        params_layout = QVBoxLayout(params_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.params_text = QTextEdit()
        self.params_text.setReadOnly(True)
        self.params_text.setMaximumHeight(200)
        self.params_text.setText("暂无参数结果")
        self.params_text.setStyleSheet(f"""
            background-color: {COLORS['bg_hover']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            font-family: {FONTS['monospace']};
            font-size: {FONTS['size_sm']}px;
            padding: 8px;
        """)
        scroll.setWidget(self.params_text)
        params_layout.addWidget(scroll)

        detail_layout.addWidget(params_group, 1)

        # 推荐刺激电流显示
        threshold_group = QGroupBox("推荐刺激电流")
        threshold_layout = QVBoxLayout(threshold_group)

        self.threshold_text = QTextEdit()
        self.threshold_text.setReadOnly(True)
        self.threshold_text.setMaximumHeight(200)
        self.threshold_text.setText("暂无推荐电流结果")
        self.threshold_text.setStyleSheet(f"""
            background-color: {COLORS['bg_hover']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            font-family: {FONTS['monospace']};
            font-size: {FONTS['size_sm']}px;
            padding: 8px;
        """)
        threshold_layout.addWidget(self.threshold_text)

        detail_layout.addWidget(threshold_group, 1)

        layout.addLayout(detail_layout)

        # 添加弹性空间
        layout.addStretch()

        return widget

    def _create_metric_card(self, title: str, value: str, subtitle: str, unit: str = "") -> QWidget:
        """
        创建指标卡片

        Args:
            title: 卡片标题
            value: 卡片值
            subtitle: 副标题
            unit: 单位（可选）

        Returns:
            QWidget卡片
        """
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
                padding: 16px;
            }}
            QWidget:hover {{
                border-color: {COLORS['primary']};
            }}
        """)
        card.setMinimumWidth(150)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # 图标和标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        # 根据标题添加对应图标
        icon_map = {
            'RMSE': '📐',
            'R²': '📊',
            '迭代次数': '🔄',
            '耗时': '⏱'
        }
        icon_label = QLabel(icon_map.get(title, '📈'))
        icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_sm']}px;
            font-weight: 500;
        """)
        header_layout.addWidget(title_label, 1)
        layout.addLayout(header_layout)

        # 值显示
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: {FONTS['size_xxl']}px;
            font-weight: bold;
            font-family: {FONTS['monospace']};
        """)
        value_layout.addWidget(value_label)

        # 单位显示
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                font-size: {FONTS['size_sm']}px;
                margin-left: 4px;
            """)
            value_layout.addWidget(unit_label)

        value_layout.addStretch()
        layout.addLayout(value_layout)

        # 保存值标签的引用
        metric_keys = {'RMSE': 'rmse', 'R²': 'r2', '迭代次数': 'iterations', '耗时': 'elapsed'}
        if title in metric_keys:
            self._metric_widgets[metric_keys[title]] = value_label

        # 副标题
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: {FONTS['size_xs']}px;
        """)
        layout.addWidget(sub_label)

        return card

    def _create_status_bar(self) -> QStatusBar:
        """创建状态栏"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)

        # 状态标签
        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label, 1)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        statusbar.addPermanentWidget(self.progress_bar)

        return statusbar

    # ============================================================
    # 公共方法
    # ============================================================

    def update_status(self, message: str, timeout: int = 0):
        """
        更新状态栏消息

        Args:
            message: 状态消息
            timeout: 显示时长（毫秒），0表示永久显示
        """
        self.status_label.setText(message)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.status_label.setText("就绪"))

    def update_data_info(self, info: dict):
        """
        更新数据信息卡片

        Args:
            info: 包含以下键的字典:
                  - filename: 文件名
                  - rows: 数据行数
                  - cols: 数据列数
                  - type: 数据类型
        """
        filename = info.get('filename', '未知')
        rows = info.get('rows', 0)
        cols = info.get('cols', 0)
        data_type = info.get('type', '-')

        # 更新标签
        self._info_widgets['filename'].setText(filename)
        self._info_widgets['type'].setText(data_type)
        self._info_widgets['rows'].setText(str(rows))
        self._info_widgets['cols'].setText(str(cols))

    def update_optimization_result_display(self, result: dict):
        """
        更新优化结果显示

        Args:
            result: 包含以下键的字典:
                  - rmse: RMSE值
                  - iterations: 迭代次数
                  - r2: R²值
                  - elapsed: 耗时
                  - message: 状态消息
                  - params: 辨识参数
                  - threshold: 阈值电流
        """
        print(f"[UI] [update_optimization_result_display] 方法开始执行", flush=True)
        
        rmse = result.get('rmse', 0)
        iterations = result.get('iterations', 0)
        r2 = result.get('r2', 0)
        elapsed = result.get('elapsed', 0)
        params = result.get('params', {})
        threshold = result.get('threshold', {})
        
        print(f"[UI] [update_optimization_result_display] 输入数据: rmse={rmse}, iter={iterations}, r2={r2}, elapsed={elapsed}", flush=True)

        # 更新表格中的指标值
        if hasattr(self, 'metrics_table'):
            self.metrics_table.item(0, 1).setText(f"{rmse:.6f}")
            self.metrics_table.item(1, 1).setText(f"{r2:.4f}")
            self.metrics_table.item(2, 1).setText(str(iterations))
            self.metrics_table.item(3, 1).setText(f"{elapsed:.2f}s")

        # 更新状态标签
        if rmse < 0.03:
            self.result_status_label.setText("优化成功")
            self.result_status_label.setStyleSheet(f"""
                font-size: {FONTS['size_lg']}px;
                font-weight: bold;
                color: white;
                padding: 8px 16px;
                background-color: {COLORS['success']};
                border-radius: {BORDER_RADIUS['sm']}px;
            """)
        else:
            self.result_status_label.setText("未达标")
            self.result_status_label.setStyleSheet(f"""
                font-size: {FONTS['size_lg']}px;
                font-weight: bold;
                color: white;
                padding: 8px 16px;
                background-color: {COLORS['warning']};
                border-radius: {BORDER_RADIUS['sm']}px;
            """)

        # 更新参数文本
        if params:
            params_lines = []
            for name, value in params.items():
                params_lines.append(f"{name}: {value:.6f}")
            self.params_text.setText("\n".join(params_lines))
        else:
            self.params_text.setText("暂无参数结果")

        # 更新阈值文本
        if threshold:
            threshold_lines = []
            for key, value in threshold.items():
                threshold_lines.append(f"{key}: {value}")
            self.threshold_text.setText("\n".join(threshold_lines))
        else:
            self.threshold_text.setText("暂无阈值结果")

    def show_error(self, title: str, message: str):
        """
        显示错误对话框

        Args:
            title: 对话框标题
            message: 错误消息
        """
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    def show_warning(self, title: str, message: str):
        """
        显示警告对话框

        Args:
            title: 对话框标题
            message: 警告消息
        """
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    def show_info(self, title: str, message: str):
        """
        显示信息对话框

        Args:
            title: 对话框标题
            message: 信息消息
        """
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    def get_file_dialog_path(self) -> str:
        """
        获取文件对话框的默认路径

        Returns:
            默认路径字符串
        """
        from pathlib import Path
        return str(Path.home())
