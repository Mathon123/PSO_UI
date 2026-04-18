"""
主窗口模块
=========

【模块说明】
本模块定义了PSO（粒子群优化）数据分析工具的主窗口界面，
负责构建完整的GUI交互界面，包括菜单栏、工具栏、侧边栏、数据表格和图表区域。

【依赖框架】
- PyQt6: Qt6的Python绑定，用于构建跨平台GUI应用程序
- QSettings: Qt设置存储系统，用于持久化用户偏好

【核心类】
- StyleSheet: 全局样式表类，定义Figma风格的QSS样式
- MainWindow: 主窗口类，继承自QMainWindow，实现所有UI组件和业务逻辑

【布局结构】
┌─────────────────────────────────────────────────────────────────────┐
│  菜单栏 (Menu Bar)                                                   │
│  ├─ 文件: 导入数据 / 导出(Excel/CSV/JSON) / 保存图表 / 退出         │
│  ├─ 数据: 刷新数据 / 清空数据 / 计算统计指标                         │
│  ├─ 分析: 运行PSO优化 / 拟合质量评估                                 │
│  └─ 帮助: 关于                                                       │
├─────────────────────────────────────────────────────────────────────┤
├────────────────┬──────────────────────────────────────────────────────┤
│                │                                                       │
│   左侧面板      │              右侧区域                               │
│   (260-320px)  │   (可伸缩，比例 1:3)                               │
│                │                                                       │
│  ┌──────────┐  │   ┌───────────────────────┬──────────────────────┐│
│  │数据信息   │  │   │  主Tab                 │  图表Tab             ││
│  │ 文件名    │  │   │  ├─ 数据预览           │  ├─ 时域响应图       ││
│  │ 类型      │  │   │  └─ 优化结果           │  ├─ 频域响应图       ││
│  │ 行数      │  │   │                       │  ├─ 残差分布图       ││
│  │ 列数      │  │   │  ┌─────────────────┐  │  ├─ 拟合对比图       ││
│  └──────────┘  │   │  │ 数据表格         │  │  ├─ 收敛曲线图       ││
│                │   │  │ (搜索框/右键菜单)│  │  ├─ 参数分布图       ││
│  ┌──────────┐  │   │  └─────────────────┘  │  └─ 综合分析图       ││
│  │PSO参数    │  │   │                       │                      ││
│  │ 粒子数[+]│  │   │  ┌─────────────────┐  │                      ││
│  │ 迭代次数 │  │   │  │ 状态标签         │  │                      ││
│  │ 目标RMSE │  │   │  │ 指标表格(RMSE/R²)│  │                      ││
│  │ 分析频率 │  │   │  │ 详细参数/阈值    │  │                      ││
│  └──────────┘  │   │  └─────────────────┘  │                      ││
│                │   └───────────────────────┴──────────────────────┘│
│  ┌──────────┐  │                                                       │
│  │操作       │  │                                                       │
│  │[导入数据] │  │                                                       │
│  │[运行优化] │  │                                                       │
│  │[计算统计] │  │                                                       │
│  │[刷新][清空]│  │                                                       │
│  └──────────┘  │                                                       │
├────────────────┴──────────────────────────────────────────────────────┤
│  状态栏: [状态消息标签]                            [进度条]          │
└─────────────────────────────────────────────────────────────────────┘

【布局说明】
- 左侧面板固定宽度260-320px，右侧区域自适应拉伸
- 右侧主Tab与图表Tab比例约为1:3（可通过拖拽调整）
- 数据预览Tab包含表格工具栏（信息标签+搜索框）和数据表格
- 优化结果Tab包含状态标签、4行指标表格、参数文本和阈值电流文本
- 状态栏左侧显示状态消息，右侧永久显示进度条

【窗口状态持久化】
使用QSettings保存以下信息：
- window_width: 窗口宽度
- window_height: 窗口高度
- central_splitter_sizes: 左右面板分割比例
- h_splitter_sizes: 主Tab与图表Tab分割比例

【PSO参数范围】
- 粒子数(Particles): 10-500，默认100
- 迭代次数(Iterations): 10-500，默认50
- 目标RMSE: 0.001-1.0，默认0.03

【信号连接】
- 粒子数: ±按钮点击信号 → 数值更新回调
- 迭代次数: ±按钮点击信号 → 数值更新回调
- 目标RMSE: ±按钮点击信号 → 数值更新回调
- 数据表格: 搜索文本变化信号 → 过滤显示回调
- 表格: 右键菜单请求信号 → 上下文菜单显示
"""

# ================================================================
# 标准库导入
# ================================================================

# PyQt6.widgets模块: 包含所有QtWidgets命名空间下的GUI组件
# - QWidget: 所有用户界面对象的基类
# - QVBoxLayout: 垂直布局管理器，按从上到下顺序排列子部件
# - QHBoxLayout: 水平布局管理器，按从左到右顺序排列子部件
# - QSplitter: 分裂器组件，允许用户通过拖拽调整子部件大小
# - QTabWidget: 标签页组件，支持多页面切换显示
# - QLabel: 标签组件，用于显示文本或图片
# - QPushButton: 按钮组件，用于触发点击事件
# - QFrame: 框架组件，提供视觉分隔和容器功能
# - QTextEdit: 多行文本编辑组件，支持富文本显示
# - QProgressBar: 进度条组件，显示任务进度
# - QSpinBox: 整数微调框组件，提供数值输入和上下箭头调节
# - QDoubleSpinBox: 浮点数微调框组件，用于小数数值输入
# - QGroupBox: 分组框组件，带标题的逻辑容器
# - QCheckBox: 复选框组件，多选状态控制
# - QScrollArea: 滚动区域组件，支持内容滚动浏览
# - QSizePolicy: 尺寸策略枚举，控制组件如何适应可用空间
# - QComboBox: 下拉组合框组件，选择列表中的单个选项
# - QLineEdit: 单行文本编辑组件，用户输入或显示文本
# - QMenuBar: 菜单栏组件，应用程序主菜单
# - QMenu: 菜单组件，下拉菜单项容器
# - QToolBar: 工具栏组件，快捷操作按钮条
# - QStatusBar: 状态栏组件，底部状态信息显示
# - QTableWidget: 表格组件，行列数据展示
# - QTableWidgetItem: 表格单元格组件，单个表格数据项
# - QHeaderView: 表头视图组件，表格列/行标题
# - QGridLayout: 网格布局管理器，表格形式排列组件
# - QMainWindow: 主窗口类，标准应用程序主窗口
# - QToolButton: 工具按钮组件，工具栏快捷按钮
# - QApplication: 应用程序实例类，管理全局应用状态
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

# PyQt6.QtCore模块: Qt核心功能和非GUI类
# - Qt: Qt命名空间，包含各种枚举和常量
# - QSize: 二维尺寸类，表示宽度和高度
# - pyqtSlot: 装饰器，将Python方法标记为Qt槽函数
# - QTimer: 定时器组件，用于单次或重复定时事件
# - QSettings: 应用程序配置存储，读写用户偏好设置
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QTimer, QSettings

# PyQt6.QtGui模块: Qt GUI相关类和图形功能
# - QAction: 动作组件，代表用户可触发的命令
# - QFont: 字体类，定义文本的字体属性
# - QIcon: 图标类，定义图形图标
# - QKeyEvent: 键盘事件类，封装键盘输入
# - QIntValidator: 整数验证器，限制输入为指定范围的整数
# - QDoubleValidator: 浮点数验证器，限制输入为指定范围的浮点数
from PyQt6.QtGui import QAction, QFont, QIcon, QKeyEvent, QIntValidator, QDoubleValidator

# ================================================================
# 内部模块导入
# ================================================================

# 从modules.config模块导入全局配置常量
# - COLORS: 颜色配置字典，包含UI各元素颜色值
# - FONTS: 字体配置字典，定义各层级字体大小和族名
# - SPACING: 间距配置字典，定义元素间距常量
# - BORDER_RADIUS: 圆角配置字典，定义各尺寸圆角值
# - WINDOW_MIN_WIDTH/WINDOW_MIN_HEIGHT: 窗口最小宽高尺寸
# - WINDOW_DEFAULT_WIDTH/WINDOW_DEFAULT_HEIGHT: 窗口默认宽高尺寸
from modules.config import (
    COLORS, FONTS, SPACING, BORDER_RADIUS,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
)


# ================================================================
# 样式表类
# ================================================================

class StyleSheet:
    """
    全局样式表类

    【功能说明】
    集中管理整个应用程序的QSS（Qt Style Sheets）样式定义，
    采用Figma设计风格的统一配色方案和简洁控件样式。

    【设计原则】
    - 使用CSS类选择器统一定义同类型组件样式
    - 使用伪选择器（:hover, :pressed, :selected等）定义交互状态
    - 样式变量从config模块的配置字典动态读取
    - 支持组件ID选择器用于特殊样式覆盖

    【样式分类】
    1. 全局样式: *选择器、QWidget基础样式
    2. 菜单栏样式: QMenuBar、QMenu、QMenuBar::item
    3. 工具栏样式: QToolBar、QToolButton
    4. 分组框样式: QGroupBox及其标题
    5. 按钮样式: QPushButton主按钮和#secondaryBtn次要按钮
    6. 输入控件样式: QSpinBox、QDoubleSpinBox、QLineEdit、QComboBox
    7. 复选框样式: QCheckBox及其指示器
    8. 表格样式: QTableWidget及行列样式
    9. Tab控件样式: QTabWidget及标签页样式
    10. 进度条样式: QProgressBar及其色块
    11. 标签样式: QLabel普通标签和ID选择器标签
    12. 文本框样式: QTextEdit
    13. 滚动区域样式: QScrollArea及滚动条
    14. 状态栏样式: QStatusBar
    15. 分隔器样式: QSplitter拖拽手柄
    """

    @staticmethod
    def get_stylesheet() -> str:
        """
        获取完整的QSS样式表字符串

        【功能】
        将所有样式定义组合成单个QSS字符串，供QApplication或QWidget.applyStyleSheet()调用。

        【返回值】
        str: 格式化的QSS样式表字符串，包含CSS语法和动态配置值插值

        【样式表结构】
        /* 注释分隔线 */
        选择器 {{
            属性: 值;
            属性: {配置变量};
        }}
        选择器:伪选择器 {{
            属性: 值;
        }}
        """
        # 使用f-string格式化字符串，将配置变量嵌入QSS
        return f"""
        /* ================================================================
           全局样式
           应用于所有Qt组件的基础样式定义
           ================================================================ */

        /* 通配符选择器，定义全局字体族
           FONTS['family']: 从config读取字体族名称（如"Segoe UI", "Microsoft YaHei"等） */
        * {{
            font-family: {FONTS['family']};
        }}

        /* QWidget基类样式，定义默认字体大小和主文本颜色
           FONTS['size_md']: 中号字体大小
           COLORS['text_primary']: 主文本颜色（通常为深色） */
        QWidget {{
            font-size: {FONTS['size_md']}px;
            color: {COLORS['text_primary']};
        }}

        /* QMainWindow主窗口背景色
           COLORS['bg_main']: 主背景颜色 */
        QMainWindow {{
            background-color: {COLORS['bg_main']};
        }}

        /* ================================================================
           菜单栏样式
           定义顶部菜单栏、菜单项和悬停效果
           ================================================================ */

        /* QMenuBar菜单栏容器样式
           - bg_card: 卡片背景色作为菜单栏背景
           - border-bottom: 底部边框分隔菜单栏和工具栏
           - padding: 上下左右内边距调整菜单项位置 */
        QMenuBar {{
            background-color: {COLORS['bg_card']};
            border-bottom: 1px solid {COLORS['border']};
            padding: 4px 8px;
            font-size: {FONTS['size_md']}px;
        }}

        /* QMenuBar::item: 菜单栏中的单个菜单项（如"文件"、"编辑"）
           - background-color: transparent透明背景，默认不显示背景
           - padding: 菜单项内部间距，上右下左分别为6px 12px 6px 12px
           - border-radius: 微圆角，与BORDER_RADIUS['sm']保持一致 */
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: {BORDER_RADIUS['sm']}px;
        }}

        /* QMenuBar::item:selected: 鼠标悬停时的菜单项样式
           - bg_hover: 悬停背景色，提供视觉反馈 */
        QMenuBar::item:selected {{
            background-color: {COLORS['bg_hover']};
        }}

        /* QMenu: 下拉菜单容器样式
           - border: 1px边框包裹菜单
           - padding: 菜单内边距4px
           - border-radius: 圆角与BORDER_RADIUS['sm']保持一致 */
        QMenu {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 4px;
        }}

        /* QMenu::item: 下拉菜单中的单个菜单项
           - padding: 上下8px，左右24px 12px（左移留出勾选图标空间）
           - border-radius: 圆角效果 */
        QMenu::item {{
            padding: 8px 24px 8px 12px;
            border-radius: {BORDER_RADIUS['sm']}px;
        }}

        /* QMenu::item:selected: 悬停时菜单项样式 */
        QMenu::item:selected {{
            background-color: {COLORS['bg_hover']};
        }}

        /* ================================================================
           工具栏样式
           定义工具栏和工具按钮的样式
           ================================================================ */

        /* QToolBar: 工具栏容器样式
           - spacing: 工具按钮之间的间距
           - padding: 工具栏内边距 */
        QToolBar {{
            background-color: {COLORS['bg_card']};
            border-bottom: 1px solid {COLORS['border']};
            spacing: 8px;
            padding: 6px 12px;
        }}

        /* QToolButton: 工具栏按钮样式
           - border: none无边框，更简洁的视觉效果
           - padding: 按钮内部间距
           - font-size: 使用小号字体(FONTS['size_sm']) */
        QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 8px 12px;
            font-size: {FONTS['size_sm']}px;
            color: {COLORS['text_primary']};
        }}

        /* QToolButton:hover: 工具按钮悬停状态 */
        QToolButton:hover {{
            background-color: {COLORS['bg_hover']};
        }}

        /* QToolButton:pressed: 工具按钮按下状态 */
        QToolButton:pressed {{
            background-color: {COLORS['border']};
        }}

        /* ================================================================
           分组框样式
           定义QGroupBox分组框的标题和边框样式
           ================================================================ */

        /* QGroupBox: 分组框容器样式
           - font-weight: bold标题加粗
           - margin-top: 16px为标题留出空间
           - padding-top: 12px标题与内容间距 */
        QGroupBox {{
            font-size: {FONTS['size_lg']}px;
            font-weight: bold;
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            margin-top: 16px;
            padding-top: 12px;
            background-color: {COLORS['bg_card']};
        }}

        /* QGroupBox::title: 分组框标题样式
           - subcontrol-origin: margin标题位置相对于margin计算
           - subcontrol-position: top left标题位于左上角
           - left: 12px左边距与边框保持距离
           - padding: 0 8px水平内边距 */
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 8px;
            color: {COLORS['text_primary']};
        }}

        /* ================================================================
           按钮样式
           定义主按钮和次要按钮的不同样式
           ================================================================ */

        /* QPushButton: 主按钮样式
           - background-color: primary主色调背景
           - color: white白色文字
           - border: none无边框
           - padding: 10px 20px水平内边距较大，更宽敞
           - font-weight: 500中等字重 */
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 10px 20px;
            font-size: {FONTS['size_md']}px;
            font-weight: 500;
        }}

        /* QPushButton:hover: 主按钮悬停状态，使用primary_hover颜色加深 */
        QPushButton:hover {{
            background-color: {COLORS['primary_hover']};
        }}

        /* QPushButton:pressed: 主按钮按下状态，使用primary_pressed颜色更深 */
        QPushButton:pressed {{
            background-color: {COLORS['primary_pressed']};
        }}

        /* QPushButton:disabled: 主按钮禁用状态
           - background-color: border灰色背景
           - color: text_muted灰色文字，表示不可点击 */
        QPushButton:disabled {{
            background-color: {COLORS['border']};
            color: {COLORS['text_muted']};
        }}

        /* QPushButton#secondaryBtn: ID选择器定义的次要按钮
           - background-color: bg_hover淡色背景
           - color: text_primary深色文字
           - border: 1px solid边框，更有层次感 */
        QPushButton#secondaryBtn {{
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
        }}

        /* QPushButton#secondaryBtn:hover: 次要按钮悬停状态 */
        QPushButton#secondaryBtn:hover {{
            background-color: {COLORS['border']};
        }}

        /* ================================================================
           输入控件样式
           定义SpinBox、DoubleSpinBox、LineEdit、ComboBox的统一样式
           ================================================================ */

        /* QSpinBox, QDoubleSpinBox, QLineEdit: 数值输入和文本输入控件
           - background-color: bg_card卡片背景
           - border: 1px solid边框
           - padding: 8px 40px 8px 12px右侧40px留出上下箭头空间
           - min-height: 32px最小高度保证可点击区域
           - padding-right: 40px为SpinBox的上下箭头按钮留空间 */
        QSpinBox, QDoubleSpinBox, QLineEdit {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 8px 40px 8px 12px;
            font-size: {FONTS['size_md']}px;
            min-height: 32px;
        }}

        /* QComboBox: 下拉组合框样式
           - padding: 4px 32px 4px 12px右侧32px为下拉箭头留空间
           - min-height: 25px比SpinBox略矮 */
        QComboBox {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            padding: 4px 32px 4px 12px;         
            font-size: {FONTS['size_md']}px;
            min-height: 25px;    
        }}

        /* QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus:
           获取焦点时的边框样式，2px solid primary加粗强调 */
        QSpinBox:focus, QDoubleSpinBox:focus,
        QLineEdit:focus {{
            border: 2px solid {COLORS['primary']};
        }}

        /* QComboBox:focus: 下拉框获取焦点样式 */
        QComboBox:focus {{
            border: 2px solid {COLORS['primary']};
        }}

        /* QSpinBox#paramSpinBox, QDoubleSpinBox#paramSpinBox:
           ID选择器，用于参数设置中的SpinBox特定样式
           padding-right: 32px与下拉框箭头宽度保持一致 */
        QSpinBox#paramSpinBox, QDoubleSpinBox#paramSpinBox {{
            padding: 8px 32px 8px 12px;
        }}

        /* QSpinBox::up-button, QDoubleSpinBox::up-button:
           SpinBox右上角的向上箭头按钮
           - width/height: 24px x 16px按钮尺寸
           - border: none无默认边框
           - border-left: 1px solid左边分割线
           - border-bottom: 1px solid底部分割线
           - subcontrol-position: top right定位到右上角 */
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            width: 24px;
            height: 16px;
            border: none;
            border-left: 1px solid {COLORS['border']};
            border-bottom: 1px solid {COLORS['border']};
            background-color: {COLORS['bg_card']};
            subcontrol-position: top right;
        }}

        /* QSpinBox::up-button:hover: 向上按钮悬停状态 */
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background-color: {COLORS['bg_hover']};
        }}

        /* QSpinBox::down-button, QDoubleSpinBox::down-button:
           SpinBox右下角的向下箭头按钮
           - border-left: 1px solid左边分割线（无底边）
           - subcontrol-position: bottom right定位到右下角 */
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: 24px;
            height: 16px;
            border: none;
            border-left: 1px solid {COLORS['border']};
            background-color: {COLORS['bg_card']};
            subcontrol-position: bottom right;
        }}

        /* QSpinBox::down-button:hover: 向下按钮悬停状态 */
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: {COLORS['bg_hover']};
        }}

        /* QSpinBox::up-arrow, QDoubleSpinBox::up-arrow:
           向上箭头图标，使用CSS边框绘制三角形
           - width/height: 0无尺寸
           - border-left/right: 5px solid transparent透明左右边框
           - border-bottom: 6px solid text_secondary实色底边，形成向上的三角形 */
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-bottom: 6px solid {COLORS['text_secondary']};
        }}

        /* QSpinBox::down-arrow, QDoubleSpinBox::down-arrow:
           向下箭头图标，border-top实色形成向下的三角形 */
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS['text_secondary']};
        }}

        /* ================================================================
           复选框样式
           定义QCheckBox的外观和选中状态
           ================================================================ */

        /* QCheckBox: 复选框整体样式
           - spacing: 8px图标与文字之间的间距 */
        QCheckBox {{
            spacing: 8px;
            font-size: {FONTS['size_md']}px;
        }}

        /* QCheckBox::indicator: 复选框指示器（小方框）
           - width/height: 18px x 18px方框尺寸
           - border: 2px solid边框
           - border-radius: 4px微圆角
           - background-color: bg_card未选中时的背景 */
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {COLORS['border']};
            border-radius: 4px;
            background-color: {COLORS['bg_card']};
        }}

        /* QCheckBox::indicator:checked: 选中状态
           - background-color: primary主色填充
           - border-color: primary边框同步变色
           注意：需要配合::indicator:after或QStyle绘制勾选标记 */
        QCheckBox::indicator:checked {{
            background-color: {COLORS['primary']};
            border-color: {COLORS['primary']};
        }}

        /* QCheckBox::indicator:hover: 悬停状态，边框变为主色 */
        QCheckBox::indicator:hover {{
            border-color: {COLORS['primary']};
        }}

        /* ================================================================
           表格样式
           定义QTableWidget表格的样式
           ================================================================ */

        /* QTableWidget: 表格容器样式
           - gridline-color: table_even_row交替行背景色用于网格线
           - font-size: size_sm小号字体适应紧凑布局 */
        QTableWidget {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            gridline-color: {COLORS['border_light']};
            font-size: {FONTS['size_sm']}px;
        }}

        /* QHeaderView::section: 表头单元格样式
           - background-color: table_header_bg表头背景色
           - font-weight: bold加粗
           - padding: 10px内边距
           - border: none无边框
           - border-bottom: 2px solid底部分割线加粗 */
        QHeaderView::section {{
            background-color: {COLORS['table_header_bg']};
            color: {COLORS['text_primary']};
            font-weight: bold;
            padding: 10px;
            border: none;
            border-bottom: 2px solid {COLORS['border']};
        }}

        /* QTableWidget::item: 表格单元格样式
           - padding: 8px单元格内边距
           - border-bottom: 1px solid底部分割线 */
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {COLORS['border_light']};
        }}

        /* QTableWidget::item:alternate: 偶数行背景色
           - background-color: table_even_row交替行背景色增强可读性 */
        QTableWidget::item:alternate {{
            background-color: {COLORS['table_even_row']};
        }}

        /* QTableWidget::item:selected: 选中单元格背景色
           - background-color: table_selected选中高亮色 */
        QTableWidget::item:selected {{
            background-color: {COLORS['table_selected']};
        }}

        /* ================================================================
           Tab控件样式
           定义QTabWidget标签页的样式
           ================================================================ */

        /* QTabWidget::pane: Tab页内容面板
           - border: 1px solid边框包围内容区
           - padding: 0无内边距（内容区域直接贴边）
           - background-color: bg_card内容区背景 */
        QTabWidget::pane {{
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 0px;
            background-color: {COLORS['bg_card']};
        }}

        /* QTabBar::tab: 单个标签页按钮样式
           - padding: 10px 20px水平内边距
           - margin-right: 4px标签之间间距
           - border-top-left/right-radius: 顶边圆角
           - background-color: bg_hover未选中标签背景
           - color: text_secondary未选中标签文字灰色 */
        QTabBar::tab {{
            padding: 10px 20px;
            margin-right: 4px;
            border-top-left-radius: {BORDER_RADIUS['md']}px;
            border-top-right-radius: {BORDER_RADIUS['md']}px;
            background-color: {COLORS['bg_hover']};
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_md']}px;
        }}

        /* QTabBar::tab:selected: 选中标签页样式
           - background-color: bg_card与内容区背景一致
           - border: 1px solid边框（无底边）
           - border-bottom: none移除底边，融入内容区
           - font-weight: bold加粗强调
           - color: primary主色文字 */
        QTabBar::tab:selected {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-bottom: none;
            font-weight: bold;
            color: {COLORS['primary']};
        }}

        /* QTabBar::tab:hover:!selected: 悬停但未选中的标签
           - background-color: border_light浅灰背景 */
        QTabBar::tab:hover:!selected {{
            background-color: {COLORS['border_light']};
        }}

        /* ================================================================
           进度条样式
           定义QProgressBar的样式
           ================================================================ */

        /* QProgressBar: 进度条容器
           - background-color: bg_hover轨道背景
           - border: none无边框，更简洁
           - height: 8px进度条高度
           - text-align: center文字居中（显示百分比） */
        QProgressBar {{
            background-color: {COLORS['bg_hover']};
            border: none;
            border-radius: {BORDER_RADIUS['sm']}px;
            height: 8px;
            text-align: center;
        }}

        /* QProgressBar::chunk: 进度条填充色块
           - background-color: primary主色填充
           - border-radius: 圆角与容器一致 */
        QProgressBar::chunk {{
            background-color: {COLORS['primary']};
            border-radius: {BORDER_RADIUS['sm']}px;
        }}

        /* ================================================================
           标签样式
           定义QLabel的样式，包括特殊ID标签
           ================================================================ */

        /* QLabel: 默认标签样式
           - font-size: size_md中号字体 */
        QLabel {{
            font-size: {FONTS['size_md']}px;
            color: {COLORS['text_primary']};
        }}

        /* QLabel#titleLabel: ID选择器，标题标签
           - font-size: size_xl特大号字体
           - font-weight: bold加粗
           用于重要标题文字 */
        QLabel#titleLabel {{
            font-size: {FONTS['size_xl']}px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        }}

        /* QLabel#subtitleLabel: 副标题标签
           - font-size: size_lg大号字体
           - color: text_secondary灰色文字
           用于次要说明文字 */
        QLabel#subtitleLabel {{
            font-size: {FONTS['size_lg']}px;
            color: {COLORS['text_secondary']};
        }}

        /* QLabel#valueLabel: 数值标签
           - font-size: size_xxl超大号字体
           - font-weight: bold加粗
           - color: primary主色数字
           用于突出显示关键数值 */
        QLabel#valueLabel {{
            font-size: {FONTS['size_xxl']}px;
            font-weight: bold;
            color: {COLORS['primary']};
        }}

        /* ================================================================
           文本框样式
           定义QTextEdit和QLineEdit的样式
           ================================================================ */

        /* QTextEdit, QLineEdit: 多行/单行文本编辑框
           - padding: 12px较大内边距，更舒适
           - border-radius: md中等圆角 */
        QTextEdit, QLineEdit {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['md']}px;
            padding: 12px;
            font-size: {FONTS['size_md']}px;
        }}

        /* ================================================================
           滚动区域样式
           定义QScrollArea和滚动条的样式
           ================================================================ */

        /* QScrollArea: 滚动区域容器
           - background-color: transparent透明背景，不遮挡底层
           - border: none无边框 */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}

        /* QScrollBar:vertical: 垂直滚动条
           - width: 10px滚动条宽度
           - margin: 0px无外边距，贴边显示 */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            margin: 0px;
        }}

        /* QScrollBar::handle:vertical: 垂直滚动条滑块
           - min-height: 30px滑块最小高度
           - border-radius: 5px圆角滑块 */
        QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: 5px;
            min-height: 30px;
        }}

        /* QScrollBar::handle:vertical:hover: 滑块悬停状态 */
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['text_muted']};
        }}

        /* QScrollBar::add-line/sub-line:vertical: 滚动条上下箭头区域
           - height: 0px隐藏，不显示箭头按钮 */
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* QScrollBar:horizontal: 水平滚动条
           - height: 10px滚动条高度
           - margin: 0px无外边距 */
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 10px;
            margin: 0px;
        }}

        /* QScrollBar::handle:horizontal: 水平滚动条滑块
           - min-width: 30px滑块最小宽度 */
        QScrollBar::handle:horizontal {{
            background-color: {COLORS['border']};
            border-radius: 5px;
            min-width: 30px;
        }}

        /* ================================================================
           状态栏样式
           定义QStatusBar的样式
           ================================================================ */

        /* QStatusBar: 状态栏容器
           - padding: 6px 12px内边距
           - font-size: size_sm小号字体
           - color: text_secondary灰色文字 */
        QStatusBar {{
            background-color: {COLORS['bg_card']};
            border-top: 1px solid {COLORS['border']};
            padding: 6px 12px;
            font-size: {FONTS['size_sm']}px;
            color: {COLORS['text_secondary']};
        }}

        /* QStatusBar::item: 状态栏内子部件
           - border: none无边框，更整洁 */
        QStatusBar::item {{
            border: none;
        }}

        /* ================================================================
           分隔器样式
           定义QSplitter拖拽手柄的样式
           ================================================================ */

        /* QSplitter::handle: 分裂器拖拽手柄基础样式
           - background-color: border灰色手柄 */
        QSplitter::handle {{
            background-color: {COLORS['border']};
        }}

        /* QSplitter::handle:horizontal: 水平分裂器手柄（左右分割）
           - width: 1px手柄宽度1像素 */
        QSplitter::handle:horizontal {{
            width: 1px;
        }}

        /* QSplitter::handle:vertical: 垂直分裂器手柄（上下分割）
           - height: 1px手柄高度1像素 */
        QSplitter::handle:vertical {{
            height: 1px;
        }}
        """


# ================================================================
# 主窗口类
# ================================================================

class MainWindow(QMainWindow):
    """
    PSO数据分析工具主窗口类

    【类功能】
    提供完整的主窗口界面，是应用程序的核心UI类。
    继承自QMainWindow，使用QMainWindow的标准布局结构：
    - 菜单栏（menuBar）
    - 工具栏（toolBar）
    - 中央部件（centralWidget）
    - 状态栏（statusBar）

    【UI组件构成】
    1. 菜单栏(_menu_bar):
       - 文件菜单: 导入数据、导出(Excel/CSV/JSON)、保存图表、退出
       - 数据菜单: 刷新数据、清空数据、计算统计指标
       - 分析菜单: 运行PSO优化、拟合质量评估
       - 帮助菜单: 关于

    2. 工具栏:
       (当前版本工具栏预留，暂未实现具体功能)

    3. 左侧面板:
       - 数据信息卡片: 显示当前加载数据的元信息
       - PSO参数设置组: 粒子数、迭代次数、目标RMSE、分析频率
       - 操作按钮组: 导入数据、运行PSO优化、计算统计、刷新、清空

    4. 右侧区域:
       - 主Tab区域: 数据预览Tab、优化结果Tab
       - 图表Tab区域: 7种可视化图表Tab

    5. 状态栏:
       - 状态消息标签
       - 进度条组件

    【布局结构】
    ┌──────────────────────────────────────────────────────────────┐
    │  菜单栏                                                       │
    ├──────────────────────────────────────────────────────────────┤
    │  工具栏                                                       │
    ├─────────────────┬─────────────────────────────────────────────┤
    │                 │                                              │
    │   左侧面板      │              右侧区域                        │
    │   260-320px     │   可伸缩区域                                │
    │                 │                                              │
    │  ┌───────────┐  │  ┌────────────────────────────────────┐    │
    │  │数据信息   │  │  │  主Tab: 数据预览 | 优化结果        │    │
    │  └───────────┘  │  ├────────────────────────────────────┤    │
    │                 │  │                                    │    │
    │  ┌───────────┐  │  │  数据表格/优化结果面板              │    │
    │  │PSO参数   │  │  │                                    │    │
    │  │  粒子数  │  │  └────────────────────────────────────┘    │
    │  │  迭代次数│  │                                              │
    │  │  目标RMSE│  │  ┌────────────────────────────────────┐    │
    │  │  分析频率│  │  │  图表Tab (7种图表)                │    │
    │  └───────────┘  │  │                                    │    │
    │                 │  │                                    │    │
    │  ┌───────────┐  │  └────────────────────────────────────┘    │
    │  │操作按钮   │  │                                              │
    │  │[导入数据] │  │                                              │
    │  │[运行优化] │  │                                              │
    │  └───────────┘  │                                              │
    ├─────────────────┴─────────────────────────────────────────────┤
    │  状态栏                                                       │
    └──────────────────────────────────────────────────────────────┘

    【窗口状态持久化】
    使用QSettings在关闭窗口时保存：
    - 窗口尺寸(window_width, window_height)
    - 分裂器尺寸(central_splitter_sizes, h_splitter_sizes)
    在窗口打开时恢复这些设置。

    【PSO参数说明】
    粒子群优化(PSO)算法的核心参数：
    - 粒子数(Particles): 搜索空间中的粒子数量，影响全局搜索能力
    - 迭代次数(Iterations): 最大迭代轮数，影响优化精度
    - 目标RMSE: 优化目标阈值，达到此精度即可停止

    【信号与槽】
    组件交互通过信号槽机制：
    - 粒子数±按钮 → _on_particles_inc/_on_particles_dec
    - 迭代次数±按钮 → _on_iterations_inc/_on_iterations_dec
    - 目标RMSE±按钮 → _on_rmse_inc/_on_rmse_dec
    - 表格搜索框 → _on_table_search
    - 表格右键菜单 → _show_table_context_menu

    【使用示例】
    ```python
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    ```
    """

    def __init__(self, parent=None):
        """
        主窗口构造函数

        【功能】
        初始化主窗口，设置窗口属性，创建所有UI组件。

        【参数】
        parent: 父窗口对象，None表示顶级窗口

        【初始化流程】
        1. 调用父类构造函数
        2. 应用全局样式表
        3. 设置窗口标题和尺寸约束
        4. 加载保存的窗口尺寸（如果有）
        5. 初始化内部状态变量
        6. 创建菜单栏、中心部件、状态栏
        """
        # 调用QMainWindow父类的构造函数
        # parent参数传递给父类，用于建立父子窗口关系
        super().__init__(parent)

        # 应用全局QSS样式表
        # StyleSheet.get_stylesheet()返回格式化后的QSS字符串
        # setStyleSheet()将样式应用到当前窗口及所有子组件
        self.setStyleSheet(StyleSheet.get_stylesheet())

        # 设置窗口标题，显示在窗口标题栏
        self.setWindowTitle("PSO数据分析工具")

        # 设置窗口最小尺寸约束
        # WINDOW_MIN_WIDTH/WINDOW_MIN_HEIGHT为config中定义的最小宽高
        # 防止窗口过小导致UI布局混乱
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # 创建QSettings实例用于持久化存储
        # 第一个参数"PSO_Tools": 组织名称/公司名，用于分类设置
        # 第二个参数"DataAnalyzer": 应用程序名称
        # QSettings会自动在系统注册表中(Windows)或配置文件中(Linux/Mac)存储
        settings = QSettings("PSO_Tools", "DataAnalyzer")

        # 从设置中读取保存的窗口宽度
        # value(key, defaultValue, type): 读取键值，提供默认值
        # 如果没有保存过设置，返回默认值WINDOW_DEFAULT_WIDTH
        saved_width = settings.value("window_width", WINDOW_DEFAULT_WIDTH, type=int)

        # 从设置中读取保存的窗口高度
        # 如果没有保存过设置，返回默认值WINDOW_DEFAULT_HEIGHT
        saved_height = settings.value("window_height", WINDOW_DEFAULT_HEIGHT, type=int)

        # 使用保存的尺寸调整窗口大小
        # 如果没有保存过，会使用上面读取的默认值
        self.resize(saved_width, saved_height)

        # 初始化数据信息显示组件字典
        # 键为组件标识名，值为QLabel组件引用
        # 用于update_data_info()方法批量更新数据信息
        self._info_widgets = {}

        # 初始化指标显示组件字典
        # 用于update_optimization_result_display()方法更新优化结果
        self._metric_widgets = {}

        # 初始化当前文件路径为None
        # 用于记录用户最近打开的数据文件路径
        self.current_file = None

        # 创建菜单栏
        # _create_menu_bar()构建文件、数据、分析、帮助四个菜单
        self._create_menu_bar()

        # 创建中央部件
        # _create_central_widget()构建左右分栏布局的主内容区
        self._create_central_widget()

        # 创建状态栏
        # _create_status_bar()构建底部状态显示区
        self._create_status_bar()

    def closeEvent(self, event):
        """
        窗口关闭事件处理

        【功能】
        当用户点击窗口关闭按钮时自动调用，用于保存用户偏好设置。

        【参数】
        event: QCloseEvent事件对象

        【保存的数据】
        1. window_width/window_height: 当前窗口尺寸
        2. central_splitter_sizes: 左右面板分割比例
        3. h_splitter_sizes: 主Tab与图表Tab分割比例

        【重要提示】
        调用super().closeEvent(event)会触发实际的窗口关闭操作，
        必须放在所有清理工作之后执行。
        """
        # 创建QSettings实例，与__init__中保持一致的组织名和应用名
        # 确保读取和写入使用相同的配置存储位置
        settings = QSettings("PSO_Tools", "DataAnalyzer")

        # 使用setValue()保存窗口当前宽度
        # self.width()返回窗口当前宽度（包含边框）
        settings.setValue("window_width", self.width())

        # 保存窗口当前高度
        settings.setValue("window_height", self.height())

        # 保存主分割器（左右面板）的尺寸比例
        # self.central_splitter.sizes()返回包含各子部件宽度的列表
        # 例如 [280, 920] 表示左侧280px，右侧920px
        settings.setValue("central_splitter_sizes", self.central_splitter.sizes())

        # 保存水平分割器（主Tab与图表Tab）的尺寸比例
        # self.h_splitter.sizes()返回包含各子部件宽度的列表
        # 例如 [400, 800] 表示左侧400px，右侧800px（1:2比例）
        settings.setValue("h_splitter_sizes", self.h_splitter.sizes())

        # 调用父类实现完成窗口关闭
        # 此行代码必须最后执行，以确保所有清理工作完成后再关闭窗口
        super().closeEvent(event)

    # ============================================================
    # PSO参数控制方法（粒子数）
    # ============================================================

    def _on_particles_inc(self):
        """
        粒子数增加按钮点击处理

        【功能】
        当用户点击粒子数"+"按钮时，增加粒子数10个。

        【业务逻辑】
        - 检查当前值是否小于最大值
        - 如果未超限，值增加10并更新显示
        - 使用增量方式修改，便于用户微调
        """
        # 判断条件：当前值小于允许的最大值
        # self._particles_max = 500，防止超出范围
        if self._particles_value < self._particles_max:
            # 增量增加10个粒子
            self._particles_value += 10
            # 更新UI显示的数值
            # setText()需要字符串参数，使用str()转换
            self.label_particles_value.setText(str(self._particles_value))

    def _on_particles_dec(self):
        """
        粒子数减少按钮点击处理

        【功能】
        当用户点击粒子数"-"按钮时，减少粒子数10个。

        【业务逻辑】
        - 检查当前值是否大于最小值
        - 如果未超限，值减少10并更新显示
        """
        # 判断条件：当前值大于允许的最小值
        # self._particles_min = 10，防止低于最小值
        if self._particles_value > self._particles_min:
            # 增量减少10个粒子
            self._particles_value -= 10
            # 更新UI显示
            self.label_particles_value.setText(str(self._particles_value))

    def _on_particles_edit_finished(self):
        """
        粒子数手动输入完成处理

        【功能】
        当用户在粒子数输入框输入完成后（按回车或点击其他地方），
        验证并更新粒子数值。

        【验证逻辑】
        1. 尝试将输入文本转换为整数
        2. 检查是否在有效范围内[10, 500]
        3. 如果有效则更新，否则恢复原值

        【触发时机】
        - 用户在QLineEdit中按回车键
        - QLineEdit失去焦点（editingFinished信号）
        """
        # 使用try-except捕获类型转换异常
        # 当用户输入非数字内容时，int()会抛出ValueError
        try:
            # 获取输入框的文本内容并转换为整数
            value = int(self.edit_particles.text())

            # 验证输入值是否在允许范围内
            # self._particles_min = 10, self._particles_max = 500
            if self._particles_min <= value <= self._particles_max:
                # 输入有效，更新内部状态变量
                self._particles_value = value
                # 同步更新显示标签（确保一致性）
                self.label_particles_value.setText(str(self._particles_value))
            else:
                # 输入值超出范围，恢复为之前的有效值
                self.edit_particles.setText(str(self._particles_value))
        except ValueError:
            # 用户输入了非数字内容，恢复为之前的有效值
            self.edit_particles.setText(str(self._particles_value))

    def get_particles_value(self) -> int:
        """
        获取当前粒子数值

        【功能】
        提供给外部模块访问当前粒子群大小的接口。

        【返回值】
        int: 当前粒子数值，范围[10, 500]

        【使用场景】
        - 外部模块获取PSO参数配置
        - PSO优化算法读取粒子数设置
        """
        return self._particles_value

    def set_particles_value(self, value: int):
        """
        设置粒子数值

        【功能】
        程序化设置粒子数，通常用于加载保存的配置或默认值。

        【参数】
        value: 要设置的粒子数值

        【验证逻辑】
        验证输入值是否在有效范围内，无效值会被忽略。

        【UI同步】
        设置成功后同步更新显示标签
        """
        # 先验证范围，超出范围的值不处理
        if self._particles_min <= value <= self._particles_max:
            # 更新内部状态
            self._particles_value = value
            # 同步更新UI显示
            self.label_particles_value.setText(str(self._particles_value))

    # ============================================================
    # PSO参数控制方法（迭代次数）
    # ============================================================

    def _on_iterations_inc(self):
        """
        迭代次数增加按钮点击处理

        【功能】
        当用户点击迭代次数"+"按钮时，增加迭代次数。

        【业务逻辑】
        - 每次增加self._iterations_step（步长10）
        - 检查是否超过最大值，超限则修正为最大值
        - 更新输入框显示

        【步长说明】
        迭代次数使用步长10而非1，便于用户快速调整到合理范围
        """
        # 检查增加后是否小于等于最大值
        if self._iterations_value < self._iterations_max:
            # 按步长增加
            self._iterations_value += self._iterations_step

            # 边界检查：确保不会超过最大值
            if self._iterations_value > self._iterations_max:
                # 超过最大值时修正为最大值
                self._iterations_value = self._iterations_max

            # 更新输入框显示
            self.edit_iterations.setText(str(self._iterations_value))

    def _on_iterations_dec(self):
        """
        迭代次数减少按钮点击处理

        【功能】
        当用户点击迭代次数"-"按钮时，减少迭代次数。

        【业务逻辑】
        - 每次减少self._iterations_step（步长10）
        - 检查是否低于最小值，超限则修正为最小值
        - 更新输入框显示
        """
        # 检查减少后是否大于等于最小值
        if self._iterations_value > self._iterations_min:
            # 按步长减少
            self._iterations_value -= self._iterations_step

            # 边界检查：确保不会低于最小值
            if self._iterations_value < self._iterations_min:
                # 低于最小值时修正为最小值
                self._iterations_value = self._iterations_min

            # 更新输入框显示
            self.edit_iterations.setText(str(self._iterations_value))

    def _on_iterations_edit_finished(self):
        """
        迭代次数手动输入完成处理

        【功能】
        验证用户输入的迭代次数是否有效。

        【验证逻辑】
        1. 尝试转换为整数
        2. 检查范围[10, 500]
        3. 有效则更新，无效则恢复原值
        """
        try:
            # 获取并转换输入值
            value = int(self.edit_iterations.text())

            # 范围验证
            if self._iterations_min <= value <= self._iterations_max:
                self._iterations_value = value
            else:
                # 超出范围，恢复原值
                self.edit_iterations.setText(str(self._iterations_value))
        except ValueError:
            # 非数字输入，恢复原值
            self.edit_iterations.setText(str(self._iterations_value))

    def get_iterations_value(self) -> int:
        """
        获取当前迭代次数值

        【返回值】
        int: 当前迭代次数，范围[10, 500]
        """
        return self._iterations_value

    def set_iterations_value(self, value: int):
        """
        设置迭代次数值

        【参数】
        value: 要设置的迭代次数值
        """
        # 范围验证后更新
        if self._iterations_min <= value <= self._iterations_max:
            self._iterations_value = value
            # 同步更新UI
            self.edit_iterations.setText(str(self._iterations_value))

    # ============================================================
    # PSO参数控制方法（目标RMSE）
    # ============================================================

    def _on_rmse_inc(self):
        """
        目标RMSE增加按钮点击处理

        【功能】
        当用户点击目标RMSE"+"按钮时，增加目标RMSE值。

        【业务逻辑】
        - 每次增加self._target_rmse_step（步长0.01）
        - 使用小数格式化显示，精度3位小数
        - 边界检查防止超限
        """
        # 检查增加后是否小于最大值
        if self._target_rmse_value < self._target_rmse_max:
            # 按步长增加
            self._target_rmse_value += self._target_rmse_step

            # 边界修正
            if self._target_rmse_value > self._target_rmse_max:
                self._target_rmse_value = self._target_rmse_max

            # 更新显示，使用3位小数格式化
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    def _on_rmse_dec(self):
        """
        目标RMSE减少按钮点击处理

        【功能】
        当用户点击目标RMSE"-"按钮时，减少目标RMSE值。

        【业务逻辑】
        - 每次减少self._target_rmse_step（步长0.01）
        - 使用小数格式化显示，精度3位小数
        """
        # 检查减少后是否大于最小值
        if self._target_rmse_value > self._target_rmse_min:
            # 按步长减少
            self._target_rmse_value -= self._target_rmse_step

            # 边界修正
            if self._target_rmse_value < self._target_rmse_min:
                self._target_rmse_value = self._target_rmse_min

            # 更新显示，3位小数精度
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    def _on_rmse_edit_finished(self):
        """
        目标RMSE手动输入完成处理

        【功能】
        验证用户输入的RMSE值是否有效。

        【验证逻辑】
        1. 尝试将输入转换为浮点数
        2. 检查范围[0.001, 1.0]
        3. 有效则更新并格式化显示，无效则恢复原值
        """
        try:
            # 获取并转换为浮点数
            value = float(self.edit_target_rmse.text())

            # 范围验证
            if self._target_rmse_min <= value <= self._target_rmse_max:
                self._target_rmse_value = value
                # 重新格式化显示（修正用户输入精度）
                self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")
            else:
                # 超出范围，恢复原值
                self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")
        except ValueError:
            # 非数字输入，恢复原值
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    def get_target_rmse_value(self) -> float:
        """
        获取当前目标RMSE值

        【返回值】
        float: 当前目标RMSE值，范围[0.001, 1.0]
        """
        return self._target_rmse_value

    def set_target_rmse_value(self, value: float):
        """
        设置目标RMSE值

        【参数】
        value: 要设置的RMSE目标值
        """
        # 范围验证后更新
        if self._target_rmse_min <= value <= self._target_rmse_max:
            self._target_rmse_value = value
            # 同步更新UI，3位小数精度
            self.edit_target_rmse.setText(f"{self._target_rmse_value:.3f}")

    # ============================================================
    # 菜单栏创建方法
    # ============================================================

    def _create_menu_bar(self):
        """
        创建菜单栏

        【功能】
        构建应用程序主菜单栏，包含文件、数据、分析、帮助四个顶级菜单。

        【菜单结构】
        文件(F)
        ├─ 导入数据... (Ctrl+O)
        ├─ ──────────
        ├─ 导出 →
        │   ├─ 导出为 Excel...
        │   ├─ 导出为 CSV...
        │   └─ 导出为 JSON...
        ├─ 保存当前图表... (Ctrl+S)
        ├─ ──────────
        └─ 退出 (Ctrl+Q)

        数据(D)
        ├─ 刷新数据 (F5)
        ├─ 清空数据
        ├─ ──────────
        └─ 计算统计指标

        分析(A)
        ├─ 运行PSO优化 (F9)
        └─ 拟合质量评估

        帮助(H)
        └─ 关于

        【信号连接】
        菜单动作通过action属性暴露，由Controller层连接具体业务逻辑
        """
        # 获取窗口的菜单栏实例
        # QMainWindow.menuBar()返回单例菜单栏
        # 如果不存在则自动创建一个
        menubar = self.menuBar()

        # ==========================================
        # 文件菜单
        # ==========================================

        # 添加"文件"顶级菜单
        # addMenu()返回QMenu对象，可继续添加子项
        file_menu = menubar.addMenu("文件")

        # 创建"导入数据"动作
        # QAction参数：动作文本、父组件
        self.action_import = QAction("导入数据...", self)
        # 设置快捷键：Ctrl+O
        # setShortcut()接受QKeySequence或字符串
        self.action_import.setShortcut("Ctrl+O")
        # 添加到文件菜单
        file_menu.addAction(self.action_import)

        # 添加分隔线，分隔导入和导出功能
        file_menu.addSeparator()

        # 创建"导出"子菜单（嵌套菜单）
        # QMenu参数：菜单标题、父组件
        export_menu = QMenu("导出", self)

        # 创建导出子菜单的各个动作
        # 导出为Excel
        self.action_export_excel = QAction("导出为 Excel...", self)
        # 导出为CSV
        self.action_export_csv = QAction("导出为 CSV...", self)
        # 导出为JSON
        self.action_export_json = QAction("导出为 JSON...", self)

        # 添加动作到导出子菜单
        export_menu.addAction(self.action_export_excel)
        export_menu.addAction(self.action_export_csv)
        export_menu.addAction(self.action_export_json)

        # 将导出子菜单添加到文件菜单
        file_menu.addMenu(export_menu)

        # 创建"保存当前图表"动作
        self.action_save_figure = QAction("保存当前图表...", self)
        # Ctrl+S快捷键
        self.action_save_figure.setShortcut("Ctrl+S")
        file_menu.addAction(self.action_save_figure)

        # 添加分隔线
        file_menu.addSeparator()

        # 创建"退出"动作
        self.action_exit = QAction("退出", self)
        # Ctrl+Q快捷键，通常用于关闭应用
        self.action_exit.setShortcut("Ctrl+Q")
        file_menu.addAction(self.action_exit)

        # ==========================================
        # 数据菜单
        # ==========================================

        # 添加"数据"顶级菜单
        data_menu = menubar.addMenu("数据")

        # "刷新数据"动作，F5快捷键
        self.action_refresh = QAction("刷新数据", self)
        self.action_refresh.setShortcut("F5")
        data_menu.addAction(self.action_refresh)

        # "清空数据"动作
        self.action_clear = QAction("清空数据", self)
        data_menu.addAction(self.action_clear)

        # 分隔线
        data_menu.addSeparator()

        # "计算统计指标"动作
        self.action_statistics = QAction("计算统计指标", self)
        data_menu.addAction(self.action_statistics)

        # ==========================================
        # 分析菜单
        # ==========================================

        # 添加"分析"顶级菜单
        analysis_menu = menubar.addMenu("分析")

        # "运行PSO优化"动作，F9快捷键
        self.action_pso_optimize = QAction("运行PSO优化", self)
        self.action_pso_optimize.setShortcut("F9")
        analysis_menu.addAction(self.action_pso_optimize)

        # "拟合质量评估"动作
        self.action_fit_quality = QAction("拟合质量评估", self)
        analysis_menu.addAction(self.action_fit_quality)

        # ==========================================
        # 帮助菜单
        # ==========================================

        # 添加"帮助"顶级菜单
        help_menu = menubar.addMenu("帮助")

        # "关于"动作
        self.action_about = QAction("关于", self)
        help_menu.addAction(self.action_about)

    # ============================================================
    # 中央部件创建方法
    # ============================================================

    def _create_central_widget(self):
        """
        创建中央部件

        【功能】
        构建主窗口的中央内容区域，采用左右分栏布局。

        【布局结构】
        ┌────────────────────────────────────────────────────┐
        │  左侧面板 (固定宽度260-320px)                       │
        │  - 数据信息卡片                                    │
        │  - PSO参数设置                                     │
        │  - 操作按钮                                        │
        ├────────────────────────────────────────────────────┤
        │  右侧区域 (可伸缩)                                 │
        │  - 主Tab + 图表Tab (QSplitter分隔)                 │
        └────────────────────────────────────────────────────┘

        【分割器管理】
        - central_splitter: 水平分割器，管理左右布局
        - h_splitter: 水平分割器，管理主Tab与图表Tab比例

        【状态恢复】
        从QSettings加载保存的分割器尺寸比例
        """
        # 创建中央部件容器
        central_widget = QWidget()
        # 设置为窗口中央部件
        # QMainWindow会自动将centralWidget放入合适位置
        self.setCentralWidget(central_widget)

        # 创建主水平布局
        main_layout = QHBoxLayout(central_widget)
        # 设置布局边距：上右下左，8像素
        main_layout.setContentsMargins(8, 8, 8, 8)
        # 设置布局内元素间距，4像素
        main_layout.setSpacing(4)

        # 创建左侧参数控制面板
        # 返回值是包含所有左侧组件的QWidget
        left_panel = self._create_left_panel()

        # 创建右侧数据展示区域
        # 返回值是包含Tab组件的QWidget
        right_area = self._create_right_area()

        # 创建水平分割器管理左右布局
        # Qt.Orientation.Horizontal: 水平方向分割（左右）
        self.central_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 添加左侧面板到分割器
        self.central_splitter.addWidget(left_panel)

        # 添加右侧区域到分割器
        self.central_splitter.addWidget(right_area)

        # 设置左侧拉伸因子为0，固定宽度
        # setStretchFactor(index, stretch): 设置指定索引子部件的拉伸权重
        # 0表示不拉伸，保持原始/最小尺寸
        self.central_splitter.setStretchFactor(0, 0)

        # 设置右侧拉伸因子为1，可伸缩
        # 拉伸因子表示分配剩余空间的比例
        self.central_splitter.setStretchFactor(1, 1)

        # 从QSettings加载保存的分割器尺寸
        settings = QSettings("PSO_Tools", "DataAnalyzer")

        # 读取主分割器（左右）的保存尺寸
        central_sizes = settings.value("central_splitter_sizes")
        if central_sizes:
            # QSettings返回的可能是字符串列表
            # 使用列表推导式将每个元素转换为整数
            self.central_splitter.setSizes([int(x) for x in central_sizes])

        # 读取水平分割器（主Tab与图表Tab）的保存尺寸
        h_sizes = settings.value("h_splitter_sizes")
        if h_sizes:
            # 同样转换为整数列表
            self.h_splitter.setSizes([int(x) for x in h_sizes])

        # 将分割器添加到主布局
        # stretch参数为0，不参与拉伸分配
        main_layout.addWidget(self.central_splitter)

    # ============================================================
    # 左侧面板创建方法
    # ============================================================

    def _create_left_panel(self) -> QWidget:
        """
        创建左侧面板

        【功能】
        构建左侧参数控制区域，包含数据信息、PSO参数设置和操作按钮。

        【组件构成】
        1. 数据信息卡片 (QGroupBox)
           - 文件名、数据类型、行数、列数

        2. PSO优化算法参数设置 (QGroupBox)
           - 粒子数：LineEdit + +/- 按钮
           - 迭代次数：LineEdit + +/- 按钮
           - 目标RMSE：LineEdit + +/- 按钮
           - 分析频率：ComboBox下拉选择

        3. 操作按钮组 (QGroupBox)
           - 主按钮：导入数据、运行PSO优化
           - 次要按钮：计算统计
           - 辅助按钮：刷新、清空

        【返回值的类型注解】
        QWidget: 包含完整左侧面板的QWidget实例

        【尺寸约束】
        - 最小宽度：260px
        - 最大宽度：320px
        """
        # 创建左侧面板容器
        left_widget = QWidget()

        # 设置宽度约束，防止面板过窄或过宽
        # 最小宽度260px确保所有内容可见
        left_widget.setMinimumWidth(260)
        # 最大宽度320px防止占据过多空间
        left_widget.setMaximumWidth(320)

        # 创建垂直布局管理器
        # QVBoxLayout: 从上到下排列子部件
        layout = QVBoxLayout(left_widget)

        # 设置布局参数
        # setContentsMargins(左, 上, 右, 下)：外边距，0表示无额外边距
        layout.setContentsMargins(0, 0, 0, 0)
        # setSpacing()：子部件之间的垂直间距，8像素
        layout.setSpacing(8)

        # ==========================================
        # 数据信息卡片
        # ==========================================

        # 创建"数据信息"分组框
        # QGroupBox自带标题和边框，可折叠
        info_group = QGroupBox("数据信息")

        # 为分组框设置网格布局
        # QGridLayout: 网格形式排列，支持行列定位
        info_layout = QGridLayout(info_group)

        # 设置网格间距：8像素
        # 影响同行或同列元素之间的间隔
        info_layout.setSpacing(8)

        # -------- 文件名 --------
        # 在第0行第0列添加"文件名:"标签
        info_layout.addWidget(QLabel("文件名:"), 0, 0)

        # 创建文件名显示标签，初始值"-"表示未加载
        self._info_widgets['filename'] = QLabel("-")
        # 添加到第0行第1列
        info_layout.addWidget(self._info_widgets['filename'], 0, 1)

        # -------- 数据类型 --------
        info_layout.addWidget(QLabel("类型:"), 1, 0)
        self._info_widgets['type'] = QLabel("-")
        info_layout.addWidget(self._info_widgets['type'], 1, 1)

        # -------- 数据行数 --------
        info_layout.addWidget(QLabel("行数:"), 2, 0)
        self._info_widgets['rows'] = QLabel("0")
        info_layout.addWidget(self._info_widgets['rows'], 2, 1)

        # -------- 数据列数 --------
        info_layout.addWidget(QLabel("列数:"), 3, 0)
        self._info_widgets['cols'] = QLabel("0")
        info_layout.addWidget(self._info_widgets['cols'], 3, 1)

        # 将数据信息卡片添加到主布局
        layout.addWidget(info_group)

        # ==========================================
        # PSO参数设置卡片
        # ==========================================

        # 创建"PSO优化算法参数设置"分组框
        pso_group = QGroupBox("PSO优化算法参数设置")

        # 创建网格布局
        pso_layout = QGridLayout(pso_group)
        pso_layout.setSpacing(8)

        # -------- 粒子数设置 --------
        # 第0行第0列：标签
        pso_layout.addWidget(QLabel("粒子数:"), 0, 0)

        # 创建粒子数输入组件容器
        # 使用容器Widget + 水平布局包含输入框和按钮
        particles_widget = QWidget()

        # 水平布局：输入框在左，按钮在右
        particles_layout = QHBoxLayout(particles_widget)
        # 布局边距设为0，让内部布局占满容器
        particles_layout.setContentsMargins(0, 0, 0, 0)
        # 元素间距4像素
        particles_layout.setSpacing(4)

        # 创建粒子数文本输入框
        # QLineEdit: 单行文本编辑组件
        self.edit_particles = QLineEdit("100")
        # 设置文本水平居中对齐
        self.edit_particles.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # setFixedSize(): 设置固定宽高，不随布局拉伸
        self.edit_particles.setFixedSize(80, 35)
        # setMaxLength(): 限制最大输入字符数
        # 限制3位数字，防止输入过长
        self.edit_particles.setMaxLength(3)
        # 创建整数验证器，限制范围10-500
        self.edit_particles.setValidator(QIntValidator(10, 500, self))
        # setToolTip(): 鼠标悬停时显示的提示文本
        self.edit_particles.setToolTip("PSO粒子群中的粒子数量 (10-500)")

        # 自定义输入框样式，与全局样式保持一致
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

        # 创建"+"增加按钮
        self.btn_particles_inc = QPushButton("+")
        # setFixedWidth(): 设置固定宽度
        self.btn_particles_inc.setFixedWidth(28)
        self.btn_particles_inc.setToolTip("增加粒子数")

        # "+"按钮样式（无边框透明背景）
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

        # 创建"-"减少按钮
        self.btn_particles_dec = QPushButton("-")
        self.btn_particles_dec.setFixedWidth(28)
        self.btn_particles_dec.setToolTip("减少粒子数")

        # "-"按钮样式
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

        # 将输入框和按钮添加到水平布局
        particles_layout.addWidget(self.edit_particles)
        particles_layout.addWidget(self.btn_particles_inc)
        particles_layout.addWidget(self.btn_particles_dec)

        # -------- 粒子数参数存储 --------
        # 当前值，初始默认值100
        self._particles_value = 100
        # 最小值：10个粒子
        self._particles_min = 10
        # 最大值：500个粒子
        self._particles_max = 500

        # -------- 连接信号槽 --------
        # clicked信号：按钮被点击时触发
        # connect()：连接到对应的处理方法
        self.btn_particles_inc.clicked.connect(self._on_particles_inc)
        self.btn_particles_dec.clicked.connect(self._on_particles_dec)
        # editingFinished信号：编辑完成（回车或失焦）时触发
        self.edit_particles.editingFinished.connect(self._on_particles_edit_finished)

        # 将粒子数组件添加到网格布局
        # 参数：组件, 行号, 列号
        pso_layout.addWidget(particles_widget, 0, 1)

        # -------- 迭代次数设置 --------
        # 标签
        pso_layout.addWidget(QLabel("迭代次数:"), 1, 0)

        # 创建迭代次数输入容器
        iterations_widget = QWidget()
        iterations_layout = QHBoxLayout(iterations_widget)
        iterations_layout.setContentsMargins(0, 0, 0, 0)
        iterations_layout.setSpacing(4)

        # 迭代次数输入框
        self.edit_iterations = QLineEdit("50")
        self.edit_iterations.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_iterations.setFixedSize(80, 35)
        self.edit_iterations.setMaxLength(3)
        # 整数验证器，范围10-500
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

        # "+"按钮
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

        # "-"按钮
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

        # -------- 迭代次数参数存储 --------
        self._iterations_value = 50      # 当前值，默认50
        self._iterations_min = 10        # 最小值
        self._iterations_max = 500      # 最大值
        self._iterations_step = 10       # 每次增减的步长

        # 连接信号槽
        self.btn_iterations_inc.clicked.connect(self._on_iterations_inc)
        self.btn_iterations_dec.clicked.connect(self._on_iterations_dec)
        self.edit_iterations.editingFinished.connect(self._on_iterations_edit_finished)

        pso_layout.addWidget(iterations_widget, 1, 1)

        # -------- 目标RMSE设置 --------
        pso_layout.addWidget(QLabel("目标RMSE:"), 2, 0)

        # 创建RMSE输入容器
        rmse_widget = QWidget()
        rmse_layout = QHBoxLayout(rmse_widget)
        rmse_layout.setContentsMargins(0, 0, 0, 0)
        rmse_layout.setSpacing(4)

        # RMSE输入框
        self.edit_target_rmse = QLineEdit("0.03")
        self.edit_target_rmse.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_target_rmse.setFixedSize(80, 35)
        # QDoubleValidator: 浮点数验证器
        # 参数：最小值, 最大值, 小数位数, 父组件
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

        # "+"按钮
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

        # "-"按钮
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

        # -------- RMSE参数存储 --------
        self._target_rmse_value = 0.03    # 当前值，默认0.03
        self._target_rmse_min = 0.001     # 最小值
        self._target_rmse_max = 1.0       # 最大值
        self._target_rmse_step = 0.01     # 步长

        # 连接信号槽
        self.btn_rmse_inc.clicked.connect(self._on_rmse_inc)
        self.btn_rmse_dec.clicked.connect(self._on_rmse_dec)
        self.edit_target_rmse.editingFinished.connect(self._on_rmse_edit_finished)

        pso_layout.addWidget(rmse_widget, 2, 1)

        # -------- 分析频率选择 --------
        # 标签
        pso_layout.addWidget(QLabel("分析频率:"), 3, 0)

        # 创建下拉组合框
        # QComboBox: 下拉选择组件
        self.combo_frequency = QComboBox()
        # setFixedHeight(): 固定高度，28像素
        self.combo_frequency.setFixedHeight(28)
        # 宽度计算：输入框80 + 间距4 + 两个按钮28+28 = 140
        self.combo_frequency.setFixedWidth(140)

        # addItems(): 批量添加选项列表
        self.combo_frequency.addItems(["10Hz", "20Hz", "All"])

        # setCurrentIndex(): 设置当前选中项索引（0开始）
        # 索引2即"All"，作为默认值
        self.combo_frequency.setCurrentIndex(2)

        pso_layout.addWidget(self.combo_frequency, 3, 1)

        # 将PSO参数卡片添加到主布局
        layout.addWidget(pso_group)

        # ==========================================
        # 操作按钮卡片
        # ==========================================

        # 创建"操作"分组框
        btn_group = QGroupBox("操作")
        btn_layout = QVBoxLayout(btn_group)
        # 按钮垂直间距10像素
        btn_layout.setSpacing(10)

        # -------- 主操作按钮 --------
        # 导入数据按钮
        self.btn_import = QPushButton("导入数据")
        self.btn_import.setFixedSize(260, 40)  # 固定尺寸260x40
        btn_layout.addWidget(self.btn_import)

        # 运行PSO优化按钮
        self.btn_run_pso = QPushButton("运行PSO优化")
        self.btn_run_pso.setFixedSize(260, 40)
        btn_layout.addWidget(self.btn_run_pso)

        # -------- 次要操作按钮 --------
        # 计算统计按钮
        self.btn_calc_stats = QPushButton("计算统计")
        self.btn_calc_stats.setFixedSize(260, 40)
        # setObjectName(): 设置对象名称，用于QSS ID选择器
        # 配合样式表中的#secondaryBtn使用
        self.btn_calc_stats.setObjectName("secondaryBtn")
        btn_layout.addWidget(self.btn_calc_stats)

        # -------- 分隔线 --------
        # QFrame: 框架组件，可用作分隔线
        separator = QFrame()
        # setFrameShape(): 设置框架形状
        # HLine: 水平线
        separator.setFrameShape(QFrame.Shape.HLine)
        # 使用样式表设置分隔线颜色
        separator.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        btn_layout.addWidget(separator)

        # -------- 辅助操作按钮 --------
        # 创建水平布局容器
        h_layout = QHBoxLayout()
        h_layout.setSpacing(8)  # 按钮间距8像素

        # 刷新按钮
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setObjectName("secondaryBtn")
        self.btn_refresh.setMinimumHeight(32)  # 最小高度32像素
        h_layout.addWidget(self.btn_refresh)

        # 清空按钮
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setObjectName("secondaryBtn")
        self.btn_clear.setMinimumHeight(32)
        h_layout.addWidget(self.btn_clear)

        btn_layout.addLayout(h_layout)  # 添加水平布局

        layout.addWidget(btn_group)

        # -------- 弹性空间 --------
        # addStretch(): 添加弹性空间，填充剩余垂直空间
        # 将按钮组推送到顶部，保持紧凑布局
        layout.addStretch()

        return left_widget

    # ============================================================
    # 右侧区域创建方法
    # ============================================================

    def _create_right_area(self) -> QWidget:
        """
        创建右侧区域

        【功能】
        构建右侧数据展示区域，包含主Tab和图表Tab两部分。

        【布局结构】
        ┌─────────────────┬────────────────────────────┐
        │                 │                             │
        │   主Tab区域     │       图表Tab区域            │
        │                 │                             │
        │  ┌────────────┐ │  ┌────────────────────────┐ │
        │  │ 数据预览  │ │  │                        │ │
        │  ├────────────┤ │  │   7种可视化图表        │ │
        │  │ 优化结果  │ │  │                        │ │
        │  └────────────┘ │  └────────────────────────┘ │
        │                 │                             │
        └─────────────────┴────────────────────────────┘

        【分割比例】
        - 左侧主Tab：stretchFactor = 1
        - 右侧图表Tab：stretchFactor = 3
        - 实际比例约为1:3（左侧1份，右侧3份）
        """
        # 创建右侧容器
        right_widget = QWidget()

        # 垂直布局
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        layout.setSpacing(12)  # 间距12像素

        # 创建水平分割器管理主Tab和图表Tab
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ==========================================
        # 左侧：主Tab区域
        # ==========================================

        # 创建Tab组件
        self.main_tabs = QTabWidget()

        # 创建数据预览Tab
        data_preview = self._create_data_preview_tab()
        # addTab(): 添加标签页
        # 参数：组件, 标签文本
        self.main_tabs.addTab(data_preview, "数据预览")

        # 创建优化结果Tab
        result_tab = self._create_result_tab()
        self.main_tabs.addTab(result_tab, "优化结果")

        # 保存结果Tab引用，供外部更新使用
        self.result_tab = result_tab

        # 添加到分割器
        self.h_splitter.addWidget(self.main_tabs)
        # 设置左侧拉伸因子为1
        self.h_splitter.setStretchFactor(0, 1)

        # ==========================================
        # 右侧：图表Tab区域
        # ==========================================

        # 创建图表Tab组件
        self.chart_tabs = QTabWidget()

        # 自定义图表Tab样式
        # 与主Tab保持一致的Figma风格
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

        # 添加图表Tab到分割器
        self.h_splitter.addWidget(self.chart_tabs)
        # 设置右侧拉伸因子为3
        self.h_splitter.setStretchFactor(1, 3)

        # 将分割器添加到布局
        # stretch参数为1使分割器占据所有可用空间
        layout.addWidget(self.h_splitter, 1)

        return right_widget

    # ============================================================
    # 数据预览Tab创建方法
    # ============================================================

    def _create_data_preview_tab(self) -> QWidget:
        """
        创建数据预览Tab

        【功能】
        构建数据表格展示界面，支持数据搜索、右键菜单和快捷键操作。

        【组件结构】
        ┌──────────────────────────────────────────┐
        │  工具栏区域                               │
        │  [表格信息标签]        [搜索框...]       │
        ├──────────────────────────────────────────┤
        │                                          │
        │           QTableWidget                   │
        │           数据表格                       │
        │                                          │
        │                                          │
        └──────────────────────────────────────────┘

        【表格特性】
        - 交替行颜色：奇偶行不同背景，增强可读性
        - 行选择模式：整行选中
        - 禁用编辑：防止意外修改
        - 启用排序：点击表头排序
        - 显示网格：可视化单元格边界
        - 显示行号：左侧垂直表头
        - 右键菜单：复制、全选等功能
        - 键盘复制：Ctrl+C复制选中单元格
        """
        # 创建Tab内容容器
        widget = QWidget()

        # 垂直布局
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)  # 边距
        layout.setSpacing(4)  # 间距

        # ==========================================
        # 工具栏区域
        # ==========================================

        toolbar_layout = QHBoxLayout()

        # 表格信息标签
        # 显示当前数据状态，如"未加载数据"或"共100行"
        self.table_info_label = QLabel("未加载数据")
        self.table_info_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_sm']}px;
            padding: 4px;
        """)
        toolbar_layout.addWidget(self.table_info_label)

        # 添加弹性空间，将搜索框推到右侧
        toolbar_layout.addStretch()

        # 搜索框
        self.table_search = QLineEdit()
        # setPlaceholderText(): 设置占位提示文本
        # 灰色显示"搜索..."，输入时自动消失
        self.table_search.setPlaceholderText("搜索...")
        # setMaximumWidth(): 最大宽度限制
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
        # textChanged信号：文本变化时触发
        # 连接搜索过滤方法
        self.table_search.textChanged.connect(self._on_table_search)
        toolbar_layout.addWidget(self.table_search)

        layout.addLayout(toolbar_layout)

        # ==========================================
        # 数据表格容器
        # ==========================================

        # 创建表格容器部件
        # 用于添加背景色和圆角边框
        table_container = QWidget()
        table_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
            }}
        """)

        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)  # 无边距

        # ==========================================
        # 数据表格
        # ==========================================

        # 创建表格组件
        self.table_widget = QTableWidget()

        # setAlternatingRowColors(): 启用交替行颜色
        # 奇偶行显示不同背景色，增强可读性
        self.table_widget.setAlternatingRowColors(True)

        # setSelectionBehavior(): 设置选择行为
        # SelectRows: 选择整行
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # setEditTriggers(): 设置编辑触发方式
        # NoEditTriggers: 禁止编辑，防止意外修改数据
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # setSortingEnabled(): 启用点击表头排序
        self.table_widget.setSortingEnabled(True)

        # setShowGrid(): 显示网格线
        self.table_widget.setShowGrid(True)

        # verticalHeader(): 获取垂直表头（行号）
        # setVisible(): 显示行号列
        self.table_widget.verticalHeader().setVisible(True)
        # 自定义行号表头样式
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

        # horizontalHeader(): 获取水平表头（列标题）
        # setStretchLastSection(): 最后列拉伸占满剩余空间
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        # setSectionsClickable(): 列标题可点击（配合排序）
        self.table_widget.horizontalHeader().setSectionsClickable(True)

        # setContextMenuPolicy(): 设置右键菜单策略
        # CustomContextMenu: 自定义右键菜单
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # customContextMenuRequested: 右键请求信号
        self.table_widget.customContextMenuRequested.connect(self._show_table_context_menu)

        # 启用Ctrl+C复制功能
        # 通过重写keyPressEvent实现
        # _create_table_key_handler()返回一个包装的处理函数
        self.table_widget.keyPressEvent = self._create_table_key_handler(
            self.table_widget.keyPressEvent, self.table_widget
        )

        table_layout.addWidget(self.table_widget)
        layout.addWidget(table_container)

        return widget

    def _on_table_search(self, text: str):
        """
        表格搜索过滤处理

        【功能】
        根据搜索文本过滤显示表格行，只显示包含搜索词的行。

        【参数】
        text: 搜索文本字符串

        【搜索逻辑】
        1. 如果搜索框为空，显示所有行
        2. 否则，遍历所有行
        3. 对每行的每个单元格检查是否包含搜索文本
        4. 不区分大小写匹配
        5. 任意单元格匹配则显示该行

        【性能优化】
        使用setRowHidden()显示/隐藏行，而非删除数据
        """
        # 遍历所有行
        for row in range(self.table_widget.rowCount()):
            # 标记该行是否匹配
            match = False

            # 空搜索框时，全部匹配
            if not text:
                match = True
            else:
                # 遍历该行的所有列
                for col in range(self.table_widget.columnCount()):
                    # 获取单元格项
                    item = self.table_widget.item(row, col)
                    # 检查单元格是否存在且包含搜索文本
                    # lower()转换为小写实现不区分大小写
                    if item and text.lower() in item.text().lower():
                        match = True
                        # 找到匹配后跳出列循环
                        break

            # 设置行是否隐藏
            # True: 隐藏, False: 显示
            self.table_widget.setRowHidden(row, not match)

    def _show_table_context_menu(self, pos):
        """
        显示表格右键菜单

        【功能】
        在用户右键点击表格时，在鼠标位置弹出上下文菜单。

        【参数】
        pos: QPoint对象，鼠标右键点击的表格内坐标

        【菜单项】
        1. 复制：复制选中的单元格
        2. 复制整行：复制当前行的所有单元格
        3. 分隔线
        4. 全选：选中所有单元格

        【exec()返回值】
        返回用户选择的动作对象，用于判断执行哪个操作
        """
        # 动态导入QMenu（在方法内部导入避免循环引用）
        from PyQt6.QtWidgets import QMenu

        # 创建菜单对象
        menu = QMenu(self)

        # 添加菜单动作
        copy_action = menu.addAction("复制")
        copy_row_action = menu.addAction("复制整行")
        menu.addSeparator()  # 添加分隔线
        select_all_action = menu.addAction("全选")

        # exec(): 显示菜单并等待用户选择
        # mapToGlobal(): 将表格局部坐标转换为全局屏幕坐标
        action = menu.exec(self.table_widget.mapToGlobal(pos))

        # 判断用户选择的动作并执行
        if action == copy_action:
            self._copy_selected_cells()
        elif action == copy_row_action:
            self._copy_current_row()
        elif action == select_all_action:
            self.table_widget.selectAll()

    def _copy_selected_cells(self):
        """
        复制选中的单元格

        【功能】
        将用户选中的单元格内容复制到系统剪贴板。

        【复制格式】
        - 列之间用Tab分隔
        - 行之间用换行符分隔
        - 可直接粘贴到Excel或文本编辑器

        【实现逻辑】
        1. 获取所有选中的单元格索引
        2. 提取所有涉及的行列号
        3. 按行分组，按列排序
        4. 拼接为制表符分隔的文本
        """
        # 获取选中的单元格索引列表
        selection = self.table_widget.selectedIndexes()

        # 如果有选中项
        if selection:
            # 提取所有涉及的行号和列号
            # set去重，sorted排序
            rows = sorted(set(index.row() for index in selection))
            columns = sorted(set(index.column() for index in selection))

            # 初始化结果文本
            text = ""

            # 遍历每一行
            for row in rows:
                # 存储该行的单元格文本
                row_data = []
                for col in columns:
                    # 获取单元格内容
                    item = self.table_widget.item(row, col)
                    # 如果单元格存在，取其文本；否则为空字符串
                    row_data.append(item.text() if item else "")
                # 用Tab连接同一行的单元格
                text += "\t".join(row_data) + "\n"

            # 复制到系统剪贴板
            from PyQt6.QtGui import QClipboard
            clipboard = QApplication.clipboard()
            # setText()设置剪贴板文本
            # strip()去除末尾多余换行符
            clipboard.setText(text.strip())

    def _copy_current_row(self):
        """
        复制当前行

        【功能】
        复制光标所在行的所有单元格内容到剪贴板。

        【适用场景】
        快速复制一整行数据，无需先选中
        """
        # 获取当前选中行索引
        row = self.table_widget.currentRow()

        # 如果存在有效行（索引 >= 0）
        if row >= 0:
            text = ""
            # 遍历该行所有列
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                # 单元格文本 + Tab分隔符
                text += (item.text() if item else "") + "\t"

            # 复制到剪贴板
            from PyQt6.QtGui import QClipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(text.strip())

    def _create_table_key_handler(self, original_method, table):
        """
        创建表格按键处理包装函数

        【功能】
        为表格添加Ctrl+C复制功能，同时保留原有按键处理。

        【参数】
        original_method: 原始的keyPressEvent方法引用
        table: 表格组件引用

        【返回值】
        包装后的key_handler函数

        【实现原理】
        返回一个新函数替代table的keyPressEvent：
        1. 检测Ctrl+C组合键
        2. 如果是，调用复制方法
        3. 否则，调用原始按键处理方法
        """
        # 定义按键处理包装函数
        def key_handler(event):
            # event.matches(): 检测按键是否匹配指定快捷键
            # QKeyEvent.Copy 对应 Ctrl+C
            if event.matches(QKeyEvent.Copy):
                # 执行单元格复制
                self._copy_selected_cells()
            else:
                # 其他按键交给原始方法处理
                original_method(event)

        # 返回包装函数
        return key_handler

    # ============================================================
    # 优化结果Tab创建方法
    # ============================================================

    def _create_result_tab(self) -> QWidget:
        """
        创建优化结果Tab

        【功能】
        构建PSO优化结果展示界面，包含状态、指标、详细参数等区域。

        【组件结构】
        ┌──────────────────────────────────────────────────────┐
        │  结果状态标签                                          │
        │  [等待优化] / [优化成功] / [未达标]                   │
        ├──────────────────────────────────────────────────────┤
        │  核心指标卡片                                          │
        │  ┌─────────────────┬─────────────────────────────┐   │
        │  │ 指标名          │ 指标值                       │   │
        │  ├─────────────────┼─────────────────────────────┤   │
        │  │ RMSE            │ 0.025631                     │   │
        │  │ R²             │ 0.9845                       │   │
        │  │ 迭代次数        │ 150                          │   │
        │  │ 耗时            │ 2.35s                        │   │
        │  └─────────────────┴─────────────────────────────┘   │
        ├──────────────────────────────────────────────────────┤
        │  详细结果区域（左右布局）                             │
        │  ┌────────────────────┬─────────────────────────┐    │
        │  │ 神经响应辨识参数    │ 推荐刺激电流            │    │
        │  │ (QScrollArea)      │ (QTextEdit)             │    │
        │  │                    │                         │    │
        │  └────────────────────┴─────────────────────────┘    │
        └──────────────────────────────────────────────────────┘

        【状态标签样式】
        - 等待优化: 灰色背景（默认）
        - 优化成功: 绿色背景（COLORS['success']）
        - 未达标: 橙色背景（COLORS['warning']）
        """
        # 创建Tab内容容器
        widget = QWidget()
        # setMinimumSize(): 设置最小尺寸
        # 确保Tab内容区域不会过小
        widget.setMinimumSize(350, 180)

        # 垂直布局
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)  # 较大边距
        layout.setSpacing(16)  # 间距16像素

        # ==========================================
        # 结果状态标签
        # ==========================================

        status_layout = QHBoxLayout()

        # 创建状态标签
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

        # 添加弹性空间，将状态标签靠左
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # ==========================================
        # 核心指标表格
        # ==========================================

        # 创建指标卡片容器
        self.metrics_card = QWidget()
        self.metrics_card.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: {BORDER_RADIUS['md']}px;
                padding: 35px;
            }}
        """)
        # 设置最小高度
        self.metrics_card.setMinimumHeight(10)

        # 卡片内垂直布局
        metrics_layout = QVBoxLayout(self.metrics_card)
        metrics_layout.setContentsMargins(8, 8, 8, 8)
        metrics_layout.setSpacing(0)

        # 创建指标表格：4行2列
        # QTableWidget(rows, columns)
        self.metrics_table = QTableWidget(4, 2)

        # setHorizontalHeaderLabels(): 设置水平表头标签
        self.metrics_table.setHorizontalHeaderLabels(["指标名", "指标值"])

        # 表头拉伸最后一列占满空间
        self.metrics_table.horizontalHeader().setStretchLastSection(True)

        # 隐藏垂直表头（行号）
        self.metrics_table.verticalHeader().setVisible(False)

        # 不显示网格线
        self.metrics_table.setShowGrid(False)

        # 禁用焦点（点击时无虚线框）
        self.metrics_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # 禁用选择模式
        self.metrics_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        # 禁用编辑
        self.metrics_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 水平滚动条策略：始终关闭
        self.metrics_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # -------- 表头样式 --------
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

        # -------- 指标名称单元格样式 --------
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

        # -------- 指标值单元格样式 --------
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

        # 应用组合样式
        self.metrics_table.setStyleSheet(header_style + cell_style)

        # 启用交替行颜色
        self.metrics_table.setAlternatingRowColors(True)

        # -------- 初始化指标数据 --------
        # 定义4个指标的初始值
        metric_data = [
            ("RMSE", "-"),      # 均方根误差
            ("R²", "-"),        # 决定系数
            ("迭代次数", "-"),   # 实际迭代次数
            ("耗时", "-"),      # 优化耗时（秒）
        ]

        # 遍历数据创建表格项
        for row, (name, value) in enumerate(metric_data):
            # 创建指标名称单元格
            name_item = QTableWidgetItem(name)
            # setTextAlignment(): 设置文本对齐方式
            # AlignLeft: 左对齐, AlignVCenter: 垂直居中
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            # setItem(row, col, item): 设置单元格内容
            self.metrics_table.setItem(row, 0, name_item)

            # 创建指标值单元格
            value_item = QTableWidgetItem(value)
            # AlignCenter: 水平居中
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.metrics_table.setItem(row, 1, value_item)

        # 设置列宽度
        self.metrics_table.setColumnWidth(0, 100)  # 指标名列宽100
        self.metrics_table.setColumnWidth(1, 150)  # 指标值列宽150

        # 将表格添加到卡片布局
        metrics_layout.addWidget(self.metrics_table)

        # 将指标卡片添加到主布局
        layout.addWidget(self.metrics_card)

        # ==========================================
        # 详细结果区域
        # ==========================================

        # 水平布局容器
        detail_layout = QHBoxLayout()
        detail_layout.setSpacing(16)

        # -------- 参数显示区域 --------
        params_group = QGroupBox("神经响应辨识参数")
        params_layout = QVBoxLayout(params_group)

        # 创建滚动区域
        # QScrollArea: 当内容超出可视区域时显示滚动条
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)  # 内容可调整大小
        scroll.setFrameShape(QFrame.Shape.NoFrame)  # 无边框

        # 创建参数文本显示
        self.params_text = QTextEdit()
        self.params_text.setReadOnly(True)  # 只读
        self.params_text.setMaximumHeight(200)  # 最大高度200px
        self.params_text.setText("暂无参数结果")
        self.params_text.setStyleSheet(f"""
            background-color: {COLORS['bg_hover']};
            border: 1px solid {COLORS['border']};
            border-radius: {BORDER_RADIUS['sm']}px;
            font-family: {FONTS['monospace']};
            font-size: {FONTS['size_sm']}px;
            padding: 8px;
        """)

        # 将文本编辑框设置为滚动区域的内容部件
        scroll.setWidget(self.params_text)
        params_layout.addWidget(scroll)

        # -------- 推荐刺激电流区域 --------
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

        # -------- 添加到详细结果布局 --------
        # stretch参数为1，两区域等宽分配空间
        detail_layout.addWidget(params_group, 1)
        detail_layout.addWidget(threshold_group, 1)

        layout.addLayout(detail_layout)

        # 添加弹性空间
        layout.addStretch()

        return widget

    def _create_metric_card(self, title: str, value: str, subtitle: str, unit: str = "") -> QWidget:
        """
        创建指标卡片组件

        【功能】
        生成一个可复用的指标展示卡片，包含标题、数值和说明。

        【参数说明】
        - title: 卡片标题，如"RMSE"、"R²"等
        - value: 要显示的数值，如"0.025631"
        - subtitle: 副标题/说明，如"均方根误差"
        - unit: 单位（可选），如"ms"、"%"等

        【返回值】
        QWidget: 包含样式化卡片的组件

        【卡片结构】
        ┌─────────────────────────────────┐
        │ [图标] 标题              │
        │                                 │
        │      数值        单位         │
        │                                 │
        │      副标题/说明              │
        └─────────────────────────────────┘

        【图标映射】
        - RMSE: 📐（三角板，暗示误差测量）
        - R²: 📊（柱状图，暗示相关性）
        - 迭代次数: 🔄（循环箭头，暗示迭代）
        - 耗时: ⏱（秒表，暗示时间）
        """
        # 创建卡片容器
        card = QWidget()

        # 卡片样式
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
        card.setMinimumWidth(150)  # 最小宽度150px
        # setCursor(): 鼠标悬停时显示手型光标
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        # 垂直布局
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # -------- 标题行 --------
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        # 图标映射字典
        icon_map = {
            'RMSE': '📐',
            'R²': '📊',
            '迭代次数': '🔄',
            '耗时': '⏱'
        }

        # 创建图标标签
        icon_label = QLabel(icon_map.get(title, '📈'))  # 默认📈图标
        icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(icon_label)

        # 创建标题标签
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_sm']}px;
            font-weight: 500;
        """)
        # addWidget(widget, stretch): 添加部件，拉伸因子为1
        header_layout.addWidget(title_label, 1)
        layout.addLayout(header_layout)

        # -------- 数值显示行 --------
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)

        # 创建数值标签
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: {FONTS['size_xxl']}px;
            font-weight: bold;
            font-family: {FONTS['monospace']};
        """)
        value_layout.addWidget(value_label)

        # 如果有单位，添加单位标签
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                font-size: {FONTS['size_sm']}px;
                margin-left: 4px;
            """)
            value_layout.addWidget(unit_label)

        # 弹性空间，将数值和单位靠左
        value_layout.addStretch()
        layout.addLayout(value_layout)

        # 保存数值标签引用到字典
        # 用于外部快速更新数值
        metric_keys = {'RMSE': 'rmse', 'R²': 'r2', '迭代次数': 'iterations', '耗时': 'elapsed'}
        if title in metric_keys:
            self._metric_widgets[metric_keys[title]] = value_label

        # -------- 副标题/说明 --------
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: {FONTS['size_xs']}px;
        """)
        layout.addWidget(sub_label)

        return card

    # ============================================================
    # 状态栏创建方法
    # ============================================================

    def _create_status_bar(self) -> QStatusBar:
        """
        创建状态栏

        【功能】
        构建底部状态栏，包含状态消息和进度条。

        【组件构成】
        ┌──────────────────────────────────────────────────────────┐
        │  [状态消息标签]                    [进度条]            │
        │   就绪                               ████░░░░░ 40%      │
        └──────────────────────────────────────────────────────────┘

        【组件说明】
        - status_label: 显示当前操作状态，如"就绪"、"正在导入..."
        - progress_bar: 显示任务进度，默认隐藏，完成后自动隐藏

        【返回值】
        QStatusBar: 创建的状态栏实例
        """
        # 创建状态栏
        statusbar = QStatusBar()

        # 设置为窗口状态栏
        # QMainWindow会自动布局状态栏到底部
        self.setStatusBar(statusbar)

        # -------- 状态消息标签 --------
        self.status_label = QLabel("就绪")
        # addWidget(widget, stretch): 添加标签，拉伸因子1
        # stretch=1使标签占据多余空间，消息靠左显示
        statusbar.addWidget(self.status_label, 1)

        # -------- 进度条 --------
        self.progress_bar = QProgressBar()
        # 最大宽度200px，避免占用过多空间
        self.progress_bar.setMaximumWidth(200)
        # 默认不可见，有进度任务时显示
        self.progress_bar.setVisible(False)
        # addPermanentWidget(): 添加永久部件（靠右显示）
        statusbar.addPermanentWidget(self.progress_bar)

        return statusbar

    # ============================================================
    # 公共方法（供外部调用）
    # ============================================================

    def update_status(self, message: str, timeout: int = 0):
        """
        更新状态栏消息

        【功能】
        更改状态栏显示的文本消息。

        【参数说明】
        - message: 要显示的状态消息，如"正在加载数据..."
        - timeout: 自动恢复时间（毫秒）
          - 0（默认值）: 消息永久显示
          - >0: 显示指定毫秒后自动恢复为"就绪"

        【使用示例】
        # 永久显示
        self.update_status("正在导入数据...")
        # 3秒后自动恢复
        self.update_status("导入成功！", timeout=3000)
        """
        # 设置状态标签文本
        self.status_label.setText(message)

        # 如果设置了超时时间
        if timeout > 0:
            # QTimer.singleShot(): 单次定时器
            # 参数：超时时间（毫秒）, 超时后执行的函数
            QTimer.singleShot(timeout, lambda: self.status_label.setText("就绪"))

    def update_data_info(self, info: dict):
        """
        更新数据信息卡片

        【功能】
        批量更新左侧面板"数据信息"分组框中的显示内容。

        【参数说明】
        info: 包含数据信息的字典，键值对：
          - filename (str): 数据文件名，如"data.xlsx"
          - rows (int): 数据总行数
          - cols (int): 数据总列数
          - type (str): 数据类型描述，如"Excel"、"CSV"等

        【使用示例】
        self.update_data_info({
            'filename': 'experiment_data.csv',
            'rows': 1000,
            'cols': 5,
            'type': 'CSV'
        })
        """
        # 从字典获取值，不存在时使用默认值
        # info.get(key, default): 安全获取，键不存在返回默认值
        filename = info.get('filename', '未知')
        rows = info.get('rows', 0)
        cols = info.get('cols', 0)
        data_type = info.get('type', '-')

        # 逐项更新标签显示
        self._info_widgets['filename'].setText(filename)
        self._info_widgets['type'].setText(data_type)
        self._info_widgets['rows'].setText(str(rows))
        self._info_widgets['cols'].setText(str(cols))

    def update_optimization_result_display(self, result: dict):
        """
        更新优化结果显示

        【功能】
        在优化完成后，更新"优化结果"Tab中的所有显示内容。

        【参数说明】
        result: 包含优化结果的字典，键值对：
          - rmse (float): 均方根误差值，越小越好
          - r2 (float): 决定系数，范围0-1，越接近1越好
          - iterations (int): 实际迭代次数
          - elapsed (float): 优化耗时（秒）
          - params (dict): 神经响应辨识参数，{参数名: 参数值}
          - threshold (dict): 推荐刺激电流，{电流类型: 电流值}

        【状态判断逻辑】
        - rmse < 0.03: "优化成功"（绿色背景）
        - rmse >= 0.03: "未达标"（橙色背景）

        【使用示例】
        self.update_optimization_result_display({
            'rmse': 0.025631,
            'r2': 0.9845,
            'iterations': 150,
            'elapsed': 2.35,
            'params': {'tau': 0.0123, 'R': 1.456},
            'threshold': {'rh': 2.5, 'rl': 0.8}
        })
        """
        # 调试日志输出
        print(f"[UI] [update_optimization_result_display] 方法开始执行", flush=True)

        # 从字典安全获取各项结果值
        # 使用get()并提供默认值，防止键不存在导致异常
        rmse = result.get('rmse', 0)
        iterations = result.get('iterations', 0)
        r2 = result.get('r2', 0)
        elapsed = result.get('elapsed', 0)
        params = result.get('params', {})
        threshold = result.get('threshold', {})

        # 输出接收到的数据日志
        print(f"[UI] [update_optimization_result_display] 输入数据: rmse={rmse}, iter={iterations}, r2={r2}, elapsed={elapsed}", flush=True)

        # -------- 更新核心指标表格 --------
        # 检查metrics_table属性是否存在（可能Tab未创建）
        if hasattr(self, 'metrics_table'):
            # item(row, col): 获取指定单元格
            # setText(): 更新单元格文本
            # f"{value:.6f}": 格式化为6位小数

            # 第0行第1列：RMSE
            self.metrics_table.item(0, 1).setText(f"{rmse:.6f}")

            # 第1行第1列：R²
            self.metrics_table.item(1, 1).setText(f"{r2:.4f}")

            # 第2行第1列：迭代次数（整数）
            self.metrics_table.item(2, 1).setText(str(iterations))

            # 第3行第1列：耗时（2位小数+单位）
            self.metrics_table.item(3, 1).setText(f"{elapsed:.2f}s")

        # -------- 更新状态标签 --------
        # 根据RMSE值判断优化是否达标
        if rmse < 0.03:
            # 达标：绿色成功样式
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
            # 未达标：橙色警告样式
            self.result_status_label.setText("未达标")
            self.result_status_label.setStyleSheet(f"""
                font-size: {FONTS['size_lg']}px;
                font-weight: bold;
                color: white;
                padding: 8px 16px;
                background-color: {COLORS['warning']};
                border-radius: {BORDER_RADIUS['sm']}px;
            """)

        # -------- 更新参数文本 --------
        if params:
            # 将参数字典转换为格式化文本
            params_lines = []
            for name, value in params.items():
                # 格式：参数名: 0.000000（6位小数）
                params_lines.append(f"{name}: {value:.6f}")
            # 用换行符连接各行
            self.params_text.setText("\n".join(params_lines))
        else:
            # 无参数时显示提示文本
            self.params_text.setText("暂无参数结果")

        # -------- 更新阈值电流文本 --------
        if threshold:
            # 将阈值字典转换为格式化文本
            threshold_lines = []
            for key, value in threshold.items():
                # 格式：电流类型: 电流值
                threshold_lines.append(f"{key}: {value}")
            self.threshold_text.setText("\n".join(threshold_lines))
        else:
            self.threshold_text.setText("暂无阈值结果")

    def show_error(self, title: str, message: str):
        """
        显示错误对话框

        【功能】
        弹出错误信息提示框，用于显示操作失败等错误情况。

        【参数说明】
        - title: 对话框标题，如"导入错误"
        - message: 错误详情文本

        【对话框类型】
        QMessageBox.Icon.Critical: 红色错误图标

        【阻塞行为】
        show()不阻塞，exec()模态显示等待用户确认
        """
        # 动态导入避免顶部循环引用
        from PyQt6.QtWidgets import QMessageBox

        # 创建消息框
        msg = QMessageBox(self)

        # setIcon(): 设置图标类型
        # Icon.Critical显示红色X图标
        msg.setIcon(QMessageBox.Icon.Critical)

        # setWindowTitle(): 设置窗口标题
        msg.setWindowTitle(title)

        # setText(): 设置主要文本内容
        msg.setText(message)

        # exec(): 显示对话框并等待用户关闭
        # 模态对话框，用户必须先关闭此对话框才能操作其他窗口
        msg.exec()

    def show_warning(self, title: str, message: str):
        """
        显示警告对话框

        【功能】
        弹出警告信息提示框，用于提醒用户注意潜在问题。

        【参数说明】
        - title: 对话框标题
        - message: 警告详情文本

        【对话框类型】
        QMessageBox.Icon.Warning: 黄色警告图标
        """
        from PyQt6.QtWidgets import QMessageBox

        msg = QMessageBox(self)
        # Icon.Warning显示黄色三角感叹号图标
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    def show_info(self, title: str, message: str):
        """
        显示信息对话框

        【功能】
        弹出信息提示框，用于显示操作成功或一般信息。

        【参数说明】
        - title: 对话框标题
        - message: 信息详情文本

        【对话框类型】
        QMessageBox.Icon.Information: 蓝色信息图标
        """
        from PyQt6.QtWidgets import QMessageBox

        msg = QMessageBox(self)
        # Icon.Information显示蓝色圆形i图标
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

    def get_file_dialog_path(self) -> str:
        """
        获取文件对话框的默认路径

        【功能】
        返回文件打开/保存对话框的默认起始目录。

        【返回值】
        str: 默认路径字符串，通常为用户主目录

        【实现说明】
        使用pathlib.Path.home()获取当前用户的主目录路径：
        - Windows: C:/Users/用户名
        - Linux: /home/用户名
        - macOS: /Users/用户名

        【使用场景】
        导入/导出文件时设置QFileDialog的起始目录
        """
        from pathlib import Path
        # Path.home(): 返回用户主目录的Path对象
        # str(): 转换为字符串供QFileDialog使用
        return str(Path.home())
