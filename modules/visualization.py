"""
可视化模块
==========

【模块说明】
本模块负责所有图表的绘制，基于Matplotlib库。

【图表类型】
1. 响应曲线 - 电流与响应概率的关系
2. 多频率响应 - 多个频率的响应对比
3. 对比曲线 - 实验vs仿真的直接对比
4. 收敛曲线 - PSO优化过程
5. 残差分析 - 拟合误差分析
6. 参数柱状图 - 辨识参数展示
7. SD曲线 - 刺激剂量关系
8. 综合分析 - 多指标仪表板

【字体配置】
- 中文优先使用 Microsoft YaHei (微软雅黑)
- 英文使用 Arial
- 备选 DejaVu Sans

【导出格式】
支持 PNG/PDF/SVG，PNG为默认格式
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.font_manager import FontProperties, fontManager
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import os

# =============================================================
# Matplotlib 字体配置
# =============================================================

# 设置中文字体支持
# plt.rcParams: 全局Matplotlib配置
# font.sans-serif: 无衬线字体列表
# axes.unicode_minus: 解决负号显示问题（False使用Unicode负号）
plt.rcParams['font.sans-serif'] = [
    'Microsoft YaHei',      # 微软雅黑（中文）
    'Microsoft JhengHei',    # 微软正黑（繁体）
    'SimHei',               # 黑体
    'SimSun',               # 宋体
    'WenQuanYi Micro Hei',  # 文泉驿
    'Arial Unicode MS',     # Mac字体
    'DejaVu Sans'           # 备选
]
plt.rcParams['axes.unicode_minus'] = False  # 使用Unicode负号，避免显示问题

# =============================================================
# Windows 中文字体文件加载
# =============================================================

# Windows系统字体路径
font_paths = [
    r'C:\Windows\Fonts\msyh.ttc',   # 微软雅黑常规
    r'C:\Windows\Fonts\msyhbd.ttc',  # 微软雅黑粗体
    r'C:\Windows\Fonts\simhei.ttf',   # 黑体
    r'C:\Windows\Fonts\simsun.ttc',   # 宋体
]

# 添加字体到Matplotlib字体管理器
# 静默加载字体，不输出日志

# 设置默认字体族为 sans-serif
plt.rcParams['font.family'] = 'sans-serif'


# =============================================================
# Figma风格配置类
# =============================================================

class FigmaStyle:
    """
    Figma风格图表配置
    
    【设计原则】
    - 简洁的配色方案
    - 清晰的网格线
    - 适度的透明度
    - 去掉多余的边框
    """

    # 颜色定义
    COLORS = {
        # 主题色
        'primary': '#4A90D9',      # 主蓝色
        'secondary': '#7F8C8D',   # 次灰色
        
        # 状态色
        'success': '#27AE60',      # 绿色-成功
        'warning': '#F39C12',      # 橙色-警告
        'danger': '#E74C3C',       # 红色-错误
        
        # 图表配色 - 用于多条数据线
        # 彩虹色谱，区分度高
        'chart': [
            '#E74C3C',  # 红色
            '#3498DB',  # 蓝色
            '#2ECC71',  # 绿色
            '#9B59B6',  # 紫色
            '#F39C12',  # 橙色
            '#1ABC9C',  # 青色
            '#E91E63',  # 粉色
            '#00BCD4',  # 浅蓝
        ],
        
        # 实验/仿真数据颜色
        'exp_color': '#E74C3C',    # 实验数据 - 红色
        'sim_color': '#3498DB',   # 仿真数据 - 蓝色
        
        # 背景与文字
        'grid': '#E1E8ED',        # 网格线颜色
        'background': '#FFFFFF',   # 图表背景
        'text': '#2C3E50',        # 文字颜色
    }

    # 样式配置
    STYLE = {
        # 背景
        'figure.facecolor': '#FFFFFF',   # 图形背景白色
        'axes.facecolor': '#FFFFFF',    # 坐标轴背景白色
        
        # 边框
        'axes.edgecolor': '#E1E8ED',    # 坐标轴边框颜色
        'axes.linewidth': 1,            # 边框宽度
        
        # 网格
        'grid.color': '#E1E8ED',         # 网格颜色
        'grid.linestyle': '--',          # 网格线型：虚线
        'grid.linewidth': 0.5,          # 网格线宽
        
        # 字体大小
        'axes.labelsize': 11,            # 坐标轴标签
        'axes.titlesize': 13,           # 标题
        'font.size': 10,                # 默认字体
        'legend.fontsize': 9,           # 图例
        'xtick.labelsize': 9,          # X轴刻度
        'ytick.labelsize': 9,          # Y轴刻度
    }

    @classmethod
    def apply(cls):
        """
        应用样式配置
        
        【调用时机】
        - ChartFactory初始化时
        - 创建新图表前
        """
        # 使用默认样式
        plt.style.use('default')
        
        # 逐项应用样式
        for key, value in cls.STYLE.items():
            plt.rcParams[key] = value


class ChartFactory:
    """
    图表工厂类
    
    【职责】
    创建各种类型的图表，返回matplotlib Figure对象
    
    【使用流程】
    1. factory = ChartFactory()  # 初始化
    2. fig = factory.create_xxx(...)  # 创建图表
    3. canvas = FigureCanvas(fig)  # 转为PyQt6兼容格式
    """

    # 类级别中文字体配置
    # 用于图表中的中文文字渲染
    CHINESE_FONT = {'family': 'Microsoft YaHei'}

    def __init__(self):
        """
        初始化图表工厂
        
        【初始化操作】
        1. 应用Figma风格
        2. 设置中文字体
        """
        FigmaStyle.apply()  # 应用样式
        
        # 设置中文字体栈
        plt.rcParams['font.sans-serif'] = [
            'Microsoft YaHei', 'SimHei', 'Microsoft JhengHei', 'DejaVu Sans'
        ]
        plt.rcParams['font.family'] = 'sans-serif'
        
        # 创建默认字体属性
        from matplotlib.font_manager import FontProperties
        
        # 检查微软雅黑字体是否存在
        font_path = r'C:\Windows\Fonts\msyh.ttc'
        if os.path.exists(font_path):
            # FontProperties: 用于设置单个文本的字体
            self._default_font = FontProperties(fname=font_path)
        else:
            self._default_font = None
        
        self.figures: Dict[str, Figure] = {}  # 保存已创建的图表
    
    def _set_chinese_font(self, ax):
        """
        为坐标轴设置中文字体
        
        【设置内容】
        - xlabel: X轴标签
        - ylabel: Y轴标签
        - title: 标题
        - legend: 图例
        - tick labels: 刻度标签
        
        Args:
            ax: matplotlib Axes对象
        """
        if self._default_font is None:
            return  # 没有配置中文字体，跳过
        
        # 设置坐标轴标签
        for label in [ax.get_xlabel(), ax.get_ylabel()]:
            if label:
                # get_xlabelfontsize: 获取当前字体大小
                ax.set_xlabel(
                    label, 
                    fontproperties=self._default_font, 
                    fontsize=ax.get_xlabelfontsize() if ax.get_xlabelfontsize() else 11
                )
                ax.set_ylabel(
                    label, 
                    fontproperties=self._default_font, 
                    fontsize=ax.get_ylabelfontsize() if ax.get_ylabelfontsize() else 11
                )
        
        # 设置标题
        if ax.get_title():
            ax.set_title(
                ax.get_title(), 
                fontproperties=self._default_font, 
                fontsize=ax.get_titlefontsize() if ax.get_titlefontsize() else 12
            )
        
        # 设置图例
        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                text.set_fontproperties(self._default_font)
        
        # 设置刻度标签
        ax.set_xticklabels(
            [t.get_text() for t in ax.get_xticklabels()], 
            fontproperties=self._default_font
        )
        ax.set_yticklabels(
            [t.get_text() for t in ax.get_yticklabels()], 
            fontproperties=self._default_font
        )

    def create_response_curve(self,
                              currents: np.ndarray,
                              responses_exp: Dict[str, np.ndarray] = None,
                              responses_sim: np.ndarray = None,
                              title: str = "响应曲线",
                              xlabel: str = "电流 (mA)",
                              ylabel: str = "响应概率") -> Figure:
        """
        创建响应曲线图
        
        【功能】
        显示神经电刺激的电流-响应概率关系曲线
        
        【图表元素】
        - 散点: 实验数据点 (marker='o', alpha=0.6)
        - 虚线: 实验数据连线 (alpha=0.4)
        - 实线: 仿真拟合曲线 (linewidth=2.5)
        
        【布局设置】
        - 图表尺寸: 10x6 英寸
        - Y轴范围: [0, 1.05] (留出5%空间)
        - X轴范围: [min-1, max+1]
        
        Args:
            currents: 电流数组 (mA)
            responses_exp: 实验响应数据 {频率: 数据}
            responses_sim: 仿真响应数据（单一曲线）
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签

        Returns:
            matplotlib Figure对象
        """
        # 创建图表和坐标轴
        # figsize: 图表尺寸(宽,高)英寸
        fig, ax = plt.subplots(figsize=(10, 6))

        # 绘制实验数据
        if responses_exp:
            for i, (freq, data) in enumerate(responses_exp.items()):
                # 循环使用颜色
                color = FigmaStyle.COLORS['chart'][i % len(FigmaStyle.COLORS['chart'])]
                
                # 散点图
                # s=50: 点大小
                # alpha=0.6: 透明度
                # edgecolors='white': 白色边缘
                # linewidth=0.5: 边缘宽度
                ax.scatter(currents, data, c=color, alpha=0.6, s=50,
                           label=f'{freq} 实验值', marker='o', edgecolors='white', linewidth=0.5)
                
                # 虚线连接
                ax.plot(currents, data, color=color, linewidth=1.5, alpha=0.4, linestyle='--')

        # 绘制仿真曲线
        if responses_sim is not None:
            ax.plot(currents, responses_sim, color=FigmaStyle.COLORS['sim_color'],
                   linewidth=2.5, label='仿真拟合', alpha=0.9)

        # 设置坐标轴标签
        ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        
        # 设置标题
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='#2C3E50')
        
        # 图例
        ax.legend(loc='lower right', framealpha=0.95, fontsize=10,
                 edgecolor='gray', fancybox=True, shadow=True)
        
        # 网格
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Y轴范围: [0, 1.05] 留出5%空间
        ax.set_ylim([0, 1.05])
        
        # X轴范围: 数据范围±1
        ax.set_xlim([currents.min() - 1, currents.max() + 1])

        # 隐藏顶部和右侧边框（美观设计）
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(1)
        ax.spines['bottom'].set_linewidth(1)

        plt.tight_layout()
        return fig

    def create_multi_frequency_response(self,
                                        currents: np.ndarray,
                                        responses_all: Dict[str, np.ndarray],
                                        responses_sim: np.ndarray = None,
                                        title: str = "多频率响应曲线") -> Figure:
        """
        创建多频率响应曲线
        
        【功能】
        在子图中显示多个频率的响应曲线
        
        【布局规则】
        - n_cols: 最多2列
        - n_rows: 根据频率数量计算
        - 图表尺寸: 10宽, 4*行高 英寸
        
        Args:
            currents: 电流数组
            responses_all: 所有频率响应数据
            responses_sim: 仿真曲线（可选）
            title: 标题

        Returns:
            matplotlib Figure对象
        """
        n_freqs = len(responses_all)
        n_cols = min(2, n_freqs)  # 最多2列
        n_rows = (n_freqs + n_cols - 1) // n_cols  # 计算行数

        # 创建子图
        # n_rows x n_cols布局
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 4 * n_rows))
        
        # 处理单行或单列的情况
        if n_freqs == 1:
            axes = [axes]  # 确保axes是列表
        else:
            axes = axes.flatten() if n_rows > 1 else axes

        for idx, (freq, data) in enumerate(responses_all.items()):
            ax = axes[idx]
            color = FigmaStyle.COLORS['chart'][idx % len(FigmaStyle.COLORS['chart'])]

            # 实验散点
            ax.scatter(currents, data, c=color, alpha=0.6, s=40,
                       marker='o', edgecolors='white', linewidth=0.5,
                       label=f'实验数据')

            # 实验连线
            ax.plot(currents, data, color=color, linewidth=1.5, alpha=0.5, linestyle='--')

            # 仿真曲线
            if responses_sim is not None:
                ax.plot(currents, responses_sim, color=FigmaStyle.COLORS['sim_color'],
                       linewidth=2, label='仿真曲线', alpha=0.9)

            # 设置坐标轴
            ax.set_xlabel('电流 (mA)', fontsize=10)
            ax.set_ylabel('响应概率', fontsize=10)
            ax.set_title(f'{freq} 响应曲线', fontsize=11, fontweight='bold')
            ax.legend(loc='lower right', fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1.05])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        # 隐藏多余的子图
        for idx in range(n_freqs, len(axes)):
            axes[idx].set_visible(False)

        # 总标题
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        return fig

    def create_comparison_curve(self,
                                 currents: np.ndarray,
                                 responses_exp: np.ndarray,
                                 responses_sim: np.ndarray,
                                 freq_label: str = "10Hz",
                                 title: str = None) -> Figure:
        """
        创建实验vs仿真对比曲线
        
        【功能】
        直接对比实验数据与仿真拟合结果
        
        【图表特点】
        - 填充区域显示误差
        - 标注RMSE/MAE指标
        - 包含图例
        
        【参数说明】
        Args:
            currents: 电流数组 (mA)
            responses_exp: 实验响应数组
            responses_sim: 仿真响应数组
            freq_label: 频率标签
            title: 自定义标题（可选）

        Returns:
            matplotlib Figure对象
        """
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 设置中文字体
        if self._default_font:
            for text in fig.findobj(plt.Text):
                text.set_fontproperties(self._default_font)
            for text in ax.findobj(plt.Text):
                text.set_fontproperties(self._default_font)

        # 实验数据散点
        # zorder=3: 绘制顺序，在最上层
        ax.scatter(currents, responses_exp, c=FigmaStyle.COLORS['exp_color'],
                  alpha=0.7, s=60, marker='o', label='实验数据',
                  edgecolors='white', linewidth=1, zorder=3)

        # 仿真曲线
        ax.plot(currents, responses_sim, color=FigmaStyle.COLORS['sim_color'],
               linewidth=2.5, label='仿真曲线', alpha=0.9, zorder=2)

        # 填充区域显示误差
        # alpha=0.2: 半透明
        ax.fill_between(currents, responses_exp, responses_sim,
                       alpha=0.2, color='gray', label='误差区域')

        # 计算指标
        rmse = np.sqrt(np.mean((responses_exp - responses_sim) ** 2))
        mae = np.mean(np.abs(responses_exp - responses_sim))

        # 设置坐标轴
        ax.set_xlabel('电流 (mA)', fontsize=12, fontweight='bold', fontproperties=self._default_font)
        ax.set_ylabel('响应概率', fontsize=12, fontweight='bold', fontproperties=self._default_font)
        
        # 标题（显示RMSE）
        ax.set_title(title or f'{freq_label} 响应曲线对比 (RMSE={rmse:.4f})',
                    fontsize=14, fontweight='bold', pad=15, fontproperties=self._default_font)
        
        ax.legend(loc='lower right', framealpha=0.95, fontsize=10, prop=self._default_font)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1.05])

        # 添加指标文本框
        # bbox: 文本框样式
        textstr = f'RMSE: {rmse:.4f}\nMAE: {mae:.4f}'
        props = dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray')
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=props, fontproperties=self._default_font)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        return fig

    def create_convergence_curve(self,
                                  fitness_history: List[float],
                                  target_rmse: float = None,
                                  title: str = "PSO优化收敛曲线") -> Figure:
        """
        创建收敛曲线
        
        【功能】
        显示PSO优化过程中RMSE的收敛过程
        
        【图表组成】
        ┌──────────────────┬──────────────────┐
        │   线性坐标        │   对数坐标        │
        │                  │                  │
        │  标注最优点       │   显示收敛细节     │
        └──────────────────┴──────────────────┘
        
        Args:
            fitness_history: 适应度(RMSE)历史列表
            target_rmse: 目标RMSE值（水平线）
            title: 标题

        Returns:
            matplotlib Figure对象
        """
        # 左右两栏布局
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 设置中文字体
        if self._default_font:
            for text in fig.findobj(plt.Text):
                text.set_fontproperties(self._default_font)
            for ax in axes:
                for text in ax.findobj(plt.Text):
                    text.set_fontproperties(self._default_font)

        iterations = range(len(fitness_history))

        # ========== 左图: 线性坐标 ==========
        ax1 = axes[0]
        ax1.plot(iterations, fitness_history, color=FigmaStyle.COLORS['primary'],
                linewidth=2, alpha=0.8)

        # 目标RMSE水平线
        if target_rmse:
            ax1.axhline(y=target_rmse, color=FigmaStyle.COLORS['danger'],
                       linestyle='--', linewidth=2, label=f'目标 RMSE={target_rmse}')

        # 标注最优点
        min_idx = np.argmin(fitness_history)
        min_val = fitness_history[min_idx]
        
        # 红色星形标记
        ax1.scatter([min_idx], [min_val], c=FigmaStyle.COLORS['success'],
                   s=100, zorder=5, marker='*', label=f'最优: {min_val:.6f}')
        
        # 添加文字标注
        # xytext: 文字位置偏移
        ax1.annotate(f'最优: {min_val:.6f}', xy=(min_idx, min_val),
                     xytext=(min_idx + len(fitness_history)*0.08, min_val * 1.1),
                     fontsize=10, arrowprops=dict(arrowstyle='->', color='gray'),
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # 坐标轴设置
        ax1.set_xlabel('迭代次数', fontsize=11, fontproperties=self._default_font)
        ax1.set_ylabel('RMSE', fontsize=11, fontproperties=self._default_font)
        ax1.set_title('收敛曲线 (线性坐标)', fontsize=12, fontweight='bold', fontproperties=self._default_font)
        ax1.legend(loc='upper right', fontsize=9, prop=self._default_font)
        ax1.grid(True, alpha=0.3)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # ========== 右图: 对数坐标 ==========
        ax2 = axes[1]
        
        # semilogy: Y轴对数刻度
        ax2.semilogy(iterations, fitness_history, color=FigmaStyle.COLORS['primary'],
                    linewidth=2, alpha=0.8)
        
        # 目标RMSE线
        if target_rmse:
            ax2.axhline(y=target_rmse, color=FigmaStyle.COLORS['danger'],
                       linestyle='--', linewidth=2)

        ax2.set_xlabel('迭代次数', fontsize=11, fontproperties=self._default_font)
        ax2.set_ylabel('RMSE (log)', fontsize=11, fontproperties=self._default_font)
        ax2.set_title('收敛曲线 (对数坐标)', fontsize=12, fontweight='bold', fontproperties=self._default_font)
        ax2.grid(True, alpha=0.3, which='both')  # which='both': 主次网格都显示
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # 总标题
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02, fontproperties=self._default_font)
        plt.tight_layout()
        return fig

    def create_residual_plot(self,
                             currents: np.ndarray,
                             residuals: Dict[str, np.ndarray],
                             title: str = "残差分析") -> Figure:
        """
        创建残差分析图

        Args:
            currents: 电流数组
            residuals: 残差数据 {频率: 残差}
            title: 标题

        Returns:
            matplotlib Figure
        """
        n_freqs = len(residuals)
        n_cols = min(2, n_freqs)
        n_rows = (n_freqs + n_cols - 1) // n_cols

        # 增大图表高度，为顶部标题留出足够空间
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 5 * n_rows + 1.5))
        if n_freqs == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_rows > 1 else axes

        for idx, (freq, res) in enumerate(residuals.items()):
            ax = axes[idx]
            color = FigmaStyle.COLORS['chart'][idx % len(FigmaStyle.COLORS['chart'])]

            ax.scatter(currents, res, c=color, alpha=0.6, s=40, marker='o')
            ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5)

            # 添加误差带
            mean_res = np.mean(res)
            std_res = np.std(res)
            ax.axhline(y=mean_res, color=FigmaStyle.COLORS['warning'],
                      linestyle='-', linewidth=1, alpha=0.5)
            ax.axhline(y=mean_res + 2*std_res, color='gray',
                      linestyle=':', linewidth=1, alpha=0.7)
            ax.axhline(y=mean_res - 2*std_res, color='gray',
                      linestyle=':', linewidth=1, alpha=0.7)

            ax.set_xlabel('电流 (mA)', fontsize=10)
            ax.set_ylabel('残差 (实验-仿真)', fontsize=10)
            ax.set_title(f'{freq} 残差分析 (std={std_res:.4f})', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        for idx in range(n_freqs, len(axes)):
            axes[idx].set_visible(False)

        # 调整 suptitle 位置和 tight_layout，为顶部标题留出空间
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        return fig

    def create_residual_histogram(self,
                                   residuals: np.ndarray,
                                   title: str = "残差分布") -> Figure:
        """
        创建残差直方图

        Args:
            residuals: 残差数组
            title: 标题

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(8, 5))

        n, bins, patches = ax.hist(residuals, bins=20,
                                     color=FigmaStyle.COLORS['primary'], alpha=0.7)
        ax.axvline(x=0, color=FigmaStyle.COLORS['danger'],
                  linestyle='--', linewidth=2, label='零线')
        ax.axvline(x=np.mean(residuals), color=FigmaStyle.COLORS['warning'],
                  linestyle='-', linewidth=2,
                  label=f'均值: {np.mean(residuals):.4f}')

        ax.set_xlabel('残差值', fontsize=11)
        ax.set_ylabel('频数', fontsize=11)
        ax.set_title(f'{title} (标准差: {np.std(residuals):.4f})',
                    fontsize=12, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        return fig

    def create_parameter_bar(self,
                              params: Dict[str, float],
                              param_units: Dict[str, str] = None,
                              title: str = "参数分布") -> Figure:
        """
        创建参数柱状图

        Args:
            params: 参数字典 {名称: 值}
            param_units: 参数单位 {名称: 单位}
            title: 标题

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 设置全局字体
        if self._default_font:
            for text in fig.findobj(plt.Text):
                text.set_fontproperties(self._default_font)
            for text in ax.findobj(plt.Text):
                text.set_fontproperties(self._default_font)

        names = list(params.keys())
        values = list(params.values())

        labels = []
        for name in names:
            unit = param_units.get(name, '') if param_units else ''
            if unit:
                labels.append(f'{name}\n({unit})')
            else:
                labels.append(name)

        colors = [FigmaStyle.COLORS['chart'][i % len(FigmaStyle.COLORS['chart'])]
                  for i in range(len(values))]

        bars = ax.bar(range(len(values)), values, color=colors, alpha=0.85,
                     edgecolor='white', linewidth=1)

        for bar, val in zip(bars, values):
            height = bar.get_height()
            label_text = f'{val:.2e}' if abs(val) < 0.001 or abs(val) > 1000 else f'{val:.4f}'
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   label_text, ha='center', va='bottom', fontsize=9,
                   fontweight='bold', fontproperties=self._default_font)

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9, fontproperties=self._default_font)
        ax.set_ylabel('参数值', fontsize=11, fontweight='bold', fontproperties=self._default_font)
        ax.set_title(title, fontsize=14, fontweight='bold', fontproperties=self._default_font)
        ax.grid(True, alpha=0.3, axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        return fig

    def create_sd_curve(self,
                         pulse_widths: np.ndarray,
                         currents: np.ndarray,
                         target_p: float = 0.5,
                         title: str = "刺激-剂量曲线") -> Figure:
        """
        创建刺激-剂量曲线

        Args:
            pulse_widths: 脉宽数组 (us)
            currents: 对应电流 (mA)
            target_p: 目标响应概率
            title: 标题

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(pulse_widths, currents, color=FigmaStyle.COLORS['success'],
               linewidth=2.5, marker='o', markersize=8,
               label=f'目标 P={target_p}', alpha=0.9)

        # 标注关键点
        for i in range(0, len(pulse_widths), max(1, len(pulse_widths)//4)):
            ax.annotate(f'{currents[i]:.1f}mA',
                       xy=(pulse_widths[i], currents[i]),
                       xytext=(5, 10), textcoords='offset points',
                       fontsize=9, color=FigmaStyle.COLORS['text'])

        ax.set_xlabel('脉宽 (us)', fontsize=12, fontweight='bold')
        ax.set_ylabel('推荐电流强度 (mA)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        return fig

    def create_comprehensive_analysis(self,
                                       currents: np.ndarray,
                                       responses_exp: Dict[str, np.ndarray],
                                       responses_sim: np.ndarray,
                                       residuals: Dict[str, np.ndarray],
                                       metrics: Dict[str, float],
                                       title: str = "综合分析") -> Figure:
        """
        创建综合分析图

        Args:
            currents: 电流数组
            responses_exp: 实验响应数据
            responses_sim: 仿真响应数据
            residuals: 残差数据
            metrics: 评估指标
            title: 标题

        Returns:
            matplotlib Figure
        """
        n_freqs = len(responses_exp)
        
        # 增大图表尺寸以容纳更多内容
        fig = plt.figure(figsize=(18, 14))
        
        # 使用 GridSpec 更好地控制布局
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(3, 3, figure=fig, hspace=0.4, wspace=0.35,
                     left=0.06, right=0.96, top=0.93, bottom=0.06)

        # 1. 响应曲线对比 (第一行左)
        ax1 = fig.add_subplot(gs[0, 0])
        for idx, (freq, data) in enumerate(responses_exp.items()):
            color = FigmaStyle.COLORS['chart'][idx % len(FigmaStyle.COLORS['chart'])]
            ax1.scatter(currents, data, c=color, alpha=0.6, s=35, marker='o', label=freq)
        ax1.plot(currents, responses_sim, color=FigmaStyle.COLORS['sim_color'],
                linewidth=2, label='仿真拟合')
        ax1.set_xlabel('电流 (mA)', fontsize=9)
        ax1.set_ylabel('响应概率', fontsize=9)
        ax1.set_title(f'响应曲线 (RMSE={metrics.get("rmse", 0):.4f})', fontsize=10, fontweight='bold')
        ax1.legend(loc='lower right', fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, 1.05])

        # 2. 残差图 (第一行中)
        ax2 = fig.add_subplot(gs[0, 1])
        for idx, (freq, res) in enumerate(residuals.items()):
            color = FigmaStyle.COLORS['chart'][idx % len(FigmaStyle.COLORS['chart'])]
            ax2.scatter(currents, res, c=color, alpha=0.6, s=35, label=freq)
        ax2.axhline(y=0, color='black', linestyle='--', linewidth=1.5)
        ax2.set_xlabel('电流 (mA)', fontsize=9)
        ax2.set_ylabel('残差', fontsize=9)
        ax2.set_title('残差散点图', fontsize=10, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=8)
        ax2.grid(True, alpha=0.3)

        # 3. 残差直方图 (第一行右)
        ax3 = fig.add_subplot(gs[0, 2])
        all_res = np.concatenate(list(residuals.values()))
        ax3.hist(all_res, bins=15, color=FigmaStyle.COLORS['primary'], alpha=0.7, edgecolor='white')
        ax3.axvline(x=0, color=FigmaStyle.COLORS['danger'],
                   linestyle='--', linewidth=2)
        ax3.set_xlabel('残差值', fontsize=9)
        ax3.set_ylabel('频数', fontsize=9)
        ax3.set_title(f'残差分布 (std={np.std(all_res):.4f})', fontsize=10, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')

        # 4. 统计信息表 (第二行左)
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.axis('off')
        table_data = [
            ['RMSE', f'{metrics.get("rmse", 0):.6f}'],
            ['MAE', f'{metrics.get("mae", 0):.6f}'],
            ['R²', f'{metrics.get("r2", 0):.4f}'],
            ['MAPE', f'{metrics.get("mape", 0):.2f}%'],
        ]
        table = ax4.table(cellText=table_data, colLabels=['指标', '数值'],
                         loc='center', cellLoc='center',
                         bbox=[0.1, 0.2, 0.8, 0.6])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.0, 1.6)
        # 设置表头样式
        for i in range(2):
            table[(0, i)].set_facecolor('#E8F4FD')
            table[(0, i)].set_text_props(weight='bold')
        ax4.set_title('拟合质量评估', fontsize=10, fontweight='bold', pad=10)

        # 5. 频率RMSE对比 (第二行中)
        ax5 = fig.add_subplot(gs[1, 1])
        freqs = list(responses_exp.keys())
        freq_colors = [FigmaStyle.COLORS['chart'][i % len(FigmaStyle.COLORS['chart'])]
                      for i in range(len(freqs))]
        freq_rmse = metrics.get('freq_rmse', {f: 0 for f in freqs})
        bars = ax5.bar(range(len(freqs)), [freq_rmse.get(f, 0) for f in freqs],
                      color=freq_colors, alpha=0.85, edgecolor='white')
        ax5.set_xticks(range(len(freqs)))
        ax5.set_xticklabels([f.replace('Freq_', '') for f in freqs], fontsize=9)
        ax5.set_xlabel('频率', fontsize=9)
        ax5.set_ylabel('RMSE', fontsize=9)
        ax5.set_title('各频率RMSE对比', fontsize=10, fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='y')
        # 添加数值标签
        for bar, val in zip(bars, [freq_rmse.get(f, 0) for f in freqs]):
            ax5.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.002,
                    f'{val:.4f}', ha='center', va='bottom', fontsize=8)

        # 6. 响应曲线(对数Y轴) (第二行右)
        ax6 = fig.add_subplot(gs[1, 2])
        for idx, (freq, data) in enumerate(responses_exp.items()):
            color = FigmaStyle.COLORS['chart'][idx % len(FigmaStyle.COLORS['chart'])]
            ax6.semilogy(currents, np.maximum(data, 0.001), 'o-', c=color, 
                        alpha=0.6, markersize=5, label=freq, linewidth=1.5)
        ax6.semilogy(currents, np.maximum(responses_sim, 0.001), '--', 
                    color=FigmaStyle.COLORS['sim_color'], linewidth=2, label='仿真')
        ax6.set_xlabel('电流 (mA)', fontsize=9)
        ax6.set_ylabel('响应概率 (log)', fontsize=9)
        ax6.set_title('响应曲线(对数坐标)', fontsize=10, fontweight='bold')
        ax6.legend(loc='lower right', fontsize=8)
        ax6.grid(True, alpha=0.3, which='both')
        ax6.set_ylim([0.001, 1.1])

        # 7. 摘要信息 (第三行，跨两列)
        ax7 = fig.add_subplot(gs[2, :2])
        ax7.axis('off')
        target_met = metrics.get("rmse", 1) < 0.03
        summary_lines = [
            f"电流范围: {currents.min():.1f} - {currents.max():.1f} mA",
            f"数据点数: {len(currents)}",
            f"频率数: {n_freqs}",
            f"目标RMSE: 0.03",
            f"实际RMSE: {metrics.get('rmse', 0):.6f}",
            f"R²: {metrics.get('r2', 0):.4f}",
            f"拟合状态: {'通过 ✓' if target_met else '未通过 ✗'}",
        ]
        
        # 创建简洁的摘要表格
        col_count = 3
        row_count = (len(summary_lines) + col_count - 1) // col_count
        summary_data = []
        for i in range(row_count):
            row = []
            for j in range(col_count):
                idx = i * col_count + j
                if idx < len(summary_lines):
                    row.append(summary_lines[idx])
                else:
                    row.append('')
            summary_data.append(row)
        
        summary_table = ax7.table(
            cellText=summary_data,
            loc='center',
            cellLoc='left',
            bbox=[0.05, 0.1, 0.9, 0.8]
        )
        summary_table.auto_set_font_size(False)
        summary_table.set_fontsize(10)
        summary_table.scale(1.2, 1.8)
        for i in range(row_count):
            for j in range(col_count):
                summary_table[(i, j)].set_edgecolor('white')
        
        ax7.set_title('数据摘要', fontsize=10, fontweight='bold', pad=10)

        # 8. 参数拟合详情 (第三行最后一列)
        ax8 = fig.add_subplot(gs[2, 2])
        ax8.axis('off')
        
        # 显示每个频率的详细指标
        detail_text = "各频率详细指标\n" + "─" * 20 + "\n"
        for freq, data in responses_exp.items():
            freq_rmse_val = freq_rmse.get(freq, 0)
            detail_text += f"{freq}:\n"
            detail_text += f"  RMSE: {freq_rmse_val:.6f}\n"
        
        ax8.text(0.1, 0.9, detail_text, transform=ax8.transAxes,
                fontsize=10, verticalalignment='top',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA',
                         edgecolor='#E0E0E0', alpha=0.9))
        ax8.set_title('详细指标', fontsize=10, fontweight='bold', pad=10)

        # 总标题
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        return fig

    def save_figure(self, fig: Figure, file_path: str, formats: List[str] = None,
                    dpi: int = 150):
        """保存图表"""
        formats = formats or ['png']
        path = Path(file_path)

        for fmt in formats:
            save_path = path.with_suffix(f'.{fmt}')
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight',
                       facecolor='white', edgecolor='none')

    def close_figure(self, fig: Figure):
        """关闭图表释放内存"""
        plt.close(fig)

    def create_particle_3d(self,
                            positions: np.ndarray,
                            fitness: np.ndarray = None,
                            global_best: np.ndarray = None,
                            title: str = "粒子位置3D图") -> Figure:
        """
        创建粒子3D位置图

        Args:
            positions: 粒子位置 (n_particles, n_dims)
            fitness: 适应度值
            global_best: 全局最优位置
            title: 标题

        Returns:
            matplotlib Figure
        """
        from mpl_toolkits.mplot3d import Axes3D

        n_particles, n_dims = positions.shape

        if n_dims < 3:
            # 如果维度不足3维，使用前两个维度 + 随机第三维
            z_data = np.random.randn(n_particles) * 0.1
        else:
            z_data = positions[:, 2]

        fig = plt.figure(figsize=(10, 8))

        # 设置中文字体
        if self._default_font:
            for text in fig.findobj(plt.Text):
                text.set_fontproperties(self._default_font)

        ax = fig.add_subplot(111, projection='3d')

        # 根据适应度选择颜色
        if fitness is not None:
            colors = plt.cm.RdYlGn_r((fitness - fitness.min()) / (fitness.max() - fitness.min() + 1e-10))
        else:
            colors = FigmaStyle.COLORS['primary']

        # 绘制粒子散点
        scatter = ax.scatter(positions[:, 0], positions[:, 1], z_data,
                            c=colors, s=50, alpha=0.7, edgecolors='white', linewidth=0.5)

        # 标记全局最优
        if global_best is not None:
            if len(global_best) >= 3:
                ax.scatter([global_best[0]], [global_best[1]], [global_best[2]],
                          c='gold', s=200, marker='*', label='全局最优', edgecolors='black', linewidth=1)
            else:
                ax.scatter([global_best[0]], [global_best[1]], [np.random.randn() * 0.1],
                          c='gold', s=200, marker='*', label='全局最优', edgecolors='black', linewidth=1)

        ax.set_xlabel('参数1', fontweight='bold', fontproperties=self._default_font)
        ax.set_ylabel('参数2', fontweight='bold', fontproperties=self._default_font)
        ax.set_zlabel('参数3', fontweight='bold', fontproperties=self._default_font)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, fontproperties=self._default_font)

        if global_best is not None:
            ax.legend(loc='upper right', fontsize=10)

        # 设置背景和视角
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor('white')
        ax.yaxis.pane.set_edgecolor('white')
        ax.zaxis.pane.set_edgecolor('white')

        plt.tight_layout()
        return fig

    def create_particle_trajectory_3d(self, trajectory: list, title: str = "粒子轨迹3D图") -> Figure:
        """
        创建粒子群演化轨迹3D图

        Args:
            trajectory: 每个迭代的粒子位置列表
            title: 标题

        Returns:
            matplotlib Figure
        """
        from mpl_toolkits.mplot3d import Axes3D

        fig = plt.figure(figsize=(12, 9))

        if self._default_font:
            for text in fig.findobj(plt.Text):
                text.set_fontproperties(self._default_font)

        ax = fig.add_subplot(111, projection='3d')

        n_steps = len(trajectory)
        colors = plt.cm.viridis(np.linspace(0, 1, n_steps))

        for i, positions in enumerate(trajectory):
            if positions.shape[1] >= 3:
                ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                          c=[colors[i]], s=20, alpha=0.5)
                # 绘制到中心点的连线
                mean_pos = positions.mean(axis=0)
                ax.plot([mean_pos[0]], [mean_pos[1]], [mean_pos[2]],
                       'o', color=colors[i], markersize=5, alpha=0.7)

        ax.set_xlabel('参数1', fontweight='bold')
        ax.set_ylabel('参数2', fontweight='bold')
        ax.set_zlabel('参数3', fontweight='bold')
        ax.set_title(f'{title}\n(颜色从蓝到黄表示迭代进度)', fontsize=13, fontweight='bold', pad=15)

        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False

        plt.tight_layout()
        return fig

    def create_sensitivity_heatmap(self, param_names: list, sensitivity_matrix: np.ndarray,
                                   title: str = "参数敏感性热图") -> Figure:
        """
        创建参数敏感性热图

        Args:
            param_names: 参数名称列表
            sensitivity_matrix: 敏感性矩阵 (n_params, n_params)
            title: 标题

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        if self._default_font:
            for text in fig.findobj(plt.Text):
                text.set_fontproperties(self._default_font)
            for text in ax.findobj(plt.Text):
                text.set_fontproperties(self._default_font)

        # 使用seaborn样式的热图
        im = ax.imshow(sensitivity_matrix, cmap='YlOrRd', aspect='auto')

        # 设置刻度
        ax.set_xticks(np.arange(len(param_names)))
        ax.set_yticks(np.arange(len(param_names)))
        ax.set_xticklabels(param_names, rotation=45, ha='right', fontsize=10)
        ax.set_yticklabels(param_names, fontsize=10)

        # 添加数值标注
        for i in range(len(param_names)):
            for j in range(len(param_names)):
                value = sensitivity_matrix[i, j]
                color = 'white' if abs(value) > sensitivity_matrix.max() * 0.5 else 'black'
                ax.text(j, i, f'{value:.2f}', ha='center', va='center', color=color, fontsize=9)

        # 颜色条
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('敏感性指数', fontsize=11, fontproperties=self._default_font)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, fontproperties=self._default_font)

        plt.tight_layout()
        return fig

    def create_particle_scatter(self, positions: np.ndarray, fitness: np.ndarray,
                                x_param: int = 0, y_param: int = 1,
                                title: str = "粒子分布散点图") -> Figure:
        """
        创建粒子分布散点图

        Args:
            positions: 粒子位置数组
            fitness: 适应度值
            x_param: X轴参数索引
            y_param: Y轴参数索引
            title: 标题

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(10, 7))

        if self._default_font:
            for text in fig.findobj(plt.Text):
                text.set_fontproperties(self._default_font)
            for text in ax.findobj(plt.Text):
                text.set_fontproperties(self._default_font)

        # 根据适应度设置颜色和大小
        if fitness is not None:
            # 反转颜色：适应度越好颜色越绿
            norm_fitness = (fitness - fitness.min()) / (fitness.max() - fitness.min() + 1e-10)
            colors = plt.cm.RdYlGn(1 - norm_fitness)  # 反转
            sizes = 30 + 70 * (1 - norm_fitness)  # 越好的粒子越大
        else:
            colors = FigmaStyle.COLORS['primary']
            sizes = 50

        scatter = ax.scatter(positions[:, x_param], positions[:, y_param],
                            c=colors, s=sizes, alpha=0.7, edgecolors='white', linewidth=0.8)

        # 标记最优粒子
        if fitness is not None:
            best_idx = np.argmin(fitness)
            ax.scatter([positions[best_idx, x_param]], [positions[best_idx, y_param]],
                      c='gold', s=250, marker='*', edgecolors='black', linewidth=1.5,
                      label=f'最优粒子 (RMSE={fitness[best_idx]:.4f})', zorder=5)

        ax.set_xlabel(f'参数{x_param + 1}', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'参数{y_param + 1}', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        if fitness is not None:
            ax.legend(loc='upper right', fontsize=10)

        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # 添加颜色条
        if fitness is not None:
            cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
            cbar.set_label('RMSE (越低越好)', fontsize=10)

        plt.tight_layout()
        return fig
