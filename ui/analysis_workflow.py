"""
数据分析工作流模块
==================
胫神经电刺激数据分析的完整工作流

功能:
1. 双文件导入 (stim_params.csv + emg_processed.csv)
2. 数据预处理和验证
3. PSO参数辨识
4. 模型评估
5. 阈值电流计算
6. SD曲线生成
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NerveExperimentData:
    """神经电刺激实验数据"""
    filename: str
    currents_mA: np.ndarray      # 电流 (mA)
    currents_A: np.ndarray       # 电流 (A)
    frequencies: List[float]    # 频率列表 (Hz)
    responses: Dict[str, np.ndarray]  # {频率: 响应概率}
    pulse_width_us: float       # 脉宽 (us)
    pulse_width_s: float        # 脉宽 (s)
    n_points: int               # 数据点数

    @property
    def all_currents(self) -> np.ndarray:
        """所有电流值"""
        return self.currents_A

    @property
    def all_responses(self) -> np.ndarray:
        """所有响应值（展平）"""
        all_resp = []
        for freq in self.frequencies:
            all_resp.extend(self.responses[freq])
        return np.array(all_resp)


class NerveDataLoader:
    """神经电刺激数据加载器"""

    @staticmethod
    def load_emg_data(emg_file: str) -> Tuple[pd.DataFrame, Dict]:
        """
        加载EMG响应数据

        Args:
            emg_file: EMG数据文件路径

        Returns:
            (DataFrame, 元数据字典)
        """
        df = pd.read_csv(emg_file, encoding='utf-8-sig')
        metadata = {}

        # 检测列名
        columns = list(df.columns)
        metadata['columns'] = columns

        return df, metadata

    @staticmethod
    def load_stim_params(stim_file: str) -> Dict:
        """
        加载刺激参数

        Args:
            stim_file: 刺激参数文件路径

        Returns:
            参数字典
        """
        params = {
            'pulse_width_us': 200,
            'frequencies': [10, 20],
        }

        if not os.path.exists(stim_file):
            return params

        with open(stim_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith('PW,'):
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        params['pulse_width_us'] = float(parts[1])
                    except ValueError:
                        pass
            elif line.startswith('Freqs,'):
                parts = line.split(',')
                if len(parts) >= 2:
                    freq_str = parts[1].replace(' ', '').strip('"')
                    try:
                        params['frequencies'] = [float(f) for f in freq_str.split(',')]
                    except ValueError:
                        pass

        return params

    @classmethod
    def load_experiment_data(cls, emg_file: str, stim_file: str = None) -> NerveExperimentData:
        """
        加载完整的实验数据

        Args:
            emg_file: EMG数据文件路径
            stim_file: 刺激参数文件路径（可选）

        Returns:
            NerveExperimentData
        """
        # 加载EMG数据
        df, metadata = cls.load_emg_data(emg_file)

        # 加载刺激参数
        if stim_file and os.path.exists(stim_file):
            stim_params = cls.load_stim_params(stim_file)
        else:
            stim_params = {'pulse_width_us': 200, 'frequencies': [10, 20]}

        # 提取电流
        # 查找电流列
        current_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'i_peak' in col_lower or '电流' in col:
                current_col = col
                break

        if current_col is None:
            current_col = df.columns[0]

        currents_mA = df[current_col].values
        currents_A = currents_mA * 1e-3  # mA -> A

        # 提取响应数据
        responses = {}
        freq_col_map = {}

        for col in df.columns:
            col_lower = col.lower()
            if 'freq' in col_lower or 'hz' in col_lower:
                # 提取频率
                import re
                freq_match = re.search(r'(\d+(?:\.\d+)?)\s*hz', col_lower)
                if freq_match:
                    freq = float(freq_match.group(1))
                    responses[f'Freq_{int(freq)}Hz'] = df[col].values
                    freq_col_map[freq] = f'Freq_{int(freq)}Hz'

        # 按频率排序
        frequencies = sorted(freq_col_map.keys())

        return NerveExperimentData(
            filename=Path(emg_file).name,
            currents_mA=currents_mA,
            currents_A=currents_A,
            frequencies=frequencies,
            responses={freq_col_map[f]: responses[freq_col_map[f]] for f in frequencies},
            pulse_width_us=stim_params['pulse_width_us'],
            pulse_width_s=stim_params['pulse_width_us'] * 1e-6,
            n_points=len(currents_mA)
        )


class NerveAnalysisWorkflow:
    """
    胫神经电刺激分析工作流

    完整流程:
    1. load_data() - 加载实验数据
    2. run_optimization() - 执行PSO参数辨识
    3. evaluate_model() - 评估模型质量
    4. compute_threshold() - 计算阈值电流
    5. generate_sd_curve() - 生成SD曲线
    6. export_results() - 导出结果
    """

    def __init__(self):
        self.data: Optional[NerveExperimentData] = None
        self.optimizer = None
        self.optimization_result = None
        self.fit_quality = None
        self.selected_freq = None
        self._status_callback = None

    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self._status_callback = callback

    def _update_status(self, message: str):
        """更新状态"""
        if self._status_callback:
            self._status_callback(message)

    def load_data(self, emg_file: str, stim_file: str = None) -> NerveExperimentData:
        """
        加载实验数据

        Args:
            emg_file: EMG响应数据文件
            stim_file: 刺激参数文件（可选）

        Returns:
            NerveExperimentData
        """
        self._update_status(f"正在加载数据: {Path(emg_file).name}")

        self.data = NerveDataLoader.load_experiment_data(emg_file, stim_file)

        self._update_status(f"数据加载完成: {self.data.n_points}个数据点, "
                           f"{len(self.data.frequencies)}个频率")

        return self.data

    def set_selected_frequency(self, freq: float):
        """设置选中的频率"""
        self.selected_freq = freq

    def run_optimization(self,
                        n_particles: int = 100,
                        n_iterations: int = 50,
                        target_rmse: float = 0.03,
                        frequency: float = None) -> Dict:
        """
        执行PSO参数辨识

        Args:
            n_particles: 粒子数
            n_iterations: 迭代次数
            target_rmse: 目标RMSE
            frequency: 指定频率（None则使用第一个频率）

        Returns:
            优化结果字典
        """
        if self.data is None:
            raise ValueError("请先加载数据")

        from modules.pso_optimizer import NerveParameterOptimizer

        # 选择频率
        if frequency is None:
            frequency = self.data.frequencies[0] if self.data.frequencies else 10

        freq_key = f'Freq_{int(frequency)}Hz'

        if freq_key not in self.data.responses:
            raise ValueError(f"频率 {frequency}Hz 的数据不存在")

        self.selected_freq = frequency
        responses = self.data.responses[freq_key]

        self._update_status(f"正在执行PSO优化 (频率={frequency}Hz)...")

        # 创建优化器
        self.optimizer = NerveParameterOptimizer()

        # 设置数据
        self.optimizer.set_data(
            currents=self.data.currents_A,
            responses=responses,
            pulse_width=self.data.pulse_width_s
        )

        # 执行优化
        def progress_callback(it, rmse):
            self._update_status(f"PSO优化中... 迭代 {it}, RMSE: {rmse:.6f}")

        self.optimization_result = self.optimizer.optimize(
            n_particles=n_particles,
            n_iterations=n_iterations,
            target_rmse=target_rmse,
            verbose=False,
            progress_callback=progress_callback
        )

        identified_params = self.optimizer.get_identified_params()
        self._update_status(f"优化完成: {self.optimization_result.message}")

        return {
            'result': self.optimization_result,
            'params': identified_params,
        }

    def evaluate_model(self) -> Dict:
        """
        评估模型拟合质量

        Returns:
            拟合质量指标
        """
        if self.optimizer is None:
            raise ValueError("请先执行优化")

        self.fit_quality = self.optimizer.evaluate_fit_quality()

        return self.fit_quality

    def compute_response_curve(self, currents_range: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算响应曲线

        Args:
            currents_range: 电流范围

        Returns:
            (电流数组, 响应数组)
        """
        if self.optimizer is None:
            raise ValueError("请先执行优化")

        return self.optimizer.compute_response_curve(currents_range)

    def compute_threshold_current(self, target_p: float = 0.8) -> float:
        """
        计算达到目标响应概率的阈值电流

        Args:
            target_p: 目标响应概率

        Returns:
            阈值电流 (A)
        """
        if self.optimizer is None:
            raise ValueError("请先执行优化")

        return self.optimizer.compute_threshold_current(target_p)

    def generate_sd_curve(self,
                         target_p: float = 0.8,
                         pulse_widths: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成刺激-剂量曲线

        Args:
            target_p: 目标响应概率
            pulse_widths: 脉宽数组 (us)

        Returns:
            (脉宽数组, 电流数组) 单位: us, mA
        """
        if self.optimizer is None:
            raise ValueError("请先执行优化")

        if pulse_widths is not None:
            pulse_widths_s = pulse_widths * 1e-6
        else:
            pulse_widths_s = None

        return self.optimizer.compute_sd_curve(pulse_widths_s, target_p)

    def get_convergence_history(self) -> List[float]:
        """获取收敛历史"""
        if self.optimization_result is None:
            return []

        return self.optimization_result.history.gbest_fitness_history

    def get_summary(self) -> str:
        """获取分析摘要"""
        if self.data is None:
            return "未加载数据"

        lines = []
        lines.append("=" * 60)
        lines.append("胫神经电刺激数据分析摘要")
        lines.append("=" * 60)
        lines.append(f"数据文件: {self.data.filename}")
        lines.append(f"数据点数: {self.data.n_points}")
        lines.append(f"电流范围: {self.data.currents_mA.min():.1f} - {self.data.currents_mA.max():.1f} mA")
        lines.append(f"脉宽: {self.data.pulse_width_us:.0f} us")
        lines.append(f"频率: {', '.join(map(str, self.data.frequencies))} Hz")
        lines.append("-" * 60)

        if self.optimization_result:
            lines.append(f"PSO优化结果: {self.optimization_result.message}")
            lines.append(f"RMSE: {self.optimization_result.best_rmse:.6f}")
            lines.append(f"迭代次数: {len(self.optimization_result.history.gbest_fitness_history)}")
            lines.append("-" * 60)

        if self.fit_quality:
            lines.append(f"拟合质量:")
            lines.append(f"  RMSE: {self.fit_quality['rmse']:.6f}")
            lines.append(f"  MAE:  {self.fit_quality['mae']:.6f}")
            lines.append(f"  R²:   {self.fit_quality['r2']:.4f}")
            lines.append(f"  目标达成: {'通过' if self.fit_quality['target_met'] else '未通过'}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def export_results(self, output_dir: str) -> Dict[str, str]:
        """
        导出结果

        Args:
            output_dir: 输出目录

        Returns:
            导出的文件路径字典
        """
        if self.data is None or self.optimizer is None:
            raise ValueError("请先执行完整分析流程")

        from modules.pso_optimizer import format_params
        import json
        from datetime import datetime

        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        paths = {}

        # 导出辨识的参数
        params = self.optimizer.get_identified_params()
        params_file = os.path.join(output_dir, f"params_{timestamp}.json")
        with open(params_file, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
        paths['params'] = params_file

        # 导出SD曲线
        if self.selected_freq:
            pw_us, curr_mA = self.generate_sd_curve(target_p=0.8)
            sd_df = pd.DataFrame({
                '脉宽_us': pw_us,
                '阈值电流_mA': curr_mA
            })
            sd_file = os.path.join(output_dir, f"sd_curve_{timestamp}.csv")
            sd_df.to_csv(sd_file, index=False, encoding='utf-8-sig')
            paths['sd_curve'] = sd_file

        # 导出响应曲线
        currents, responses = self.compute_response_curve()
        resp_df = pd.DataFrame({
            '电流_mA': currents * 1000,
            '仿真响应': responses
        })
        if self.selected_freq:
            freq_key = f'Freq_{int(self.selected_freq)}Hz'
            resp_df['实验响应'] = self.data.responses.get(freq_key, [np.nan] * len(currents))
        resp_file = os.path.join(output_dir, f"response_curve_{timestamp}.csv")
        resp_df.to_csv(resp_file, index=False, encoding='utf-8-sig')
        paths['response_curve'] = resp_file

        # 导出报告
        report_file = os.path.join(output_dir, f"report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self.get_summary())
            if params:
                f.write("\n\n")
                f.write(format_params(params))
        paths['report'] = report_file

        self._update_status(f"结果已导出到: {output_dir}")

        return paths
