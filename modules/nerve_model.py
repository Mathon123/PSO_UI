"""
胫神经电刺激模型模块
=========================================
电刺激参数 → 细胞膜电压 → 神经响应概率 的链路实现

数学模型说明:
1. 神经纤维等效为RLC电路模型
2. 细胞膜电压由微分方程描述
3. 响应概率由激活能量积分计算

从原项目移植:
- tibial_nerve_pso/models/nerve_model.py
- tibial_nerve_pso/config/settings.py
"""

import numpy as np
from scipy.signal import cont2discrete
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass


# =============================================================
# 仿真基础参数配置
# =============================================================
SIMULATION = {
    "dt": 2e-6,              # 仿真时间步长 (秒)
    "t_total": 3e-3,         # 单次模拟时长 (秒)
    "target_response": 0.8,  # 目标响应概率
}

# 8个待辨识物理参数搜索边界
IDENTIFICATION_PARAMS = {
    "R1": {"name": "等效电阻R1", "unit": "Ohm", "bounds": (1e4, 1.5e5)},
    "R2": {"name": "等效电阻R2", "unit": "Ohm", "bounds": (100, 1e4)},
    "R3": {"name": "等效电阻R3", "unit": "Ohm", "bounds": (1e3, 1e5)},
    "L":  {"name": "等效电感L",   "unit": "H",   "bounds": (0.001, 10.0)},
    "C":  {"name": "等效电容C",   "unit": "F",   "bounds": (1e-10, 80e-9)},
    "alpha": {"name": "激活系数α", "unit": "-",  "bounds": (10, 30000)},
    "beta":  {"name": "激活系数β", "unit": "-",  "bounds": (0.1, 12.0)},
    "V_th":  {"name": "阈值电压",  "unit": "V",  "bounds": (-0.15, -0.01)},
}

# 简化为数组形式的边界
PARAM_BOUNDS = [p["bounds"] for p in IDENTIFICATION_PARAMS.values()]


@dataclass
class StimulusSignal:
    """电刺激信号数据结构"""
    current: float      # 电流强度 (A)
    pulse_width: float  # 脉宽 (s)
    frequency: float    # 频率 (Hz)
    amplitude: float    # 峰值电流 (A)

    @property
    def pulse_width_steps(self) -> int:
        return int(self.pulse_width / SIMULATION["dt"])

    @property
    def period_steps(self) -> int:
        if self.frequency > 0:
            return int(1.0 / (self.frequency * SIMULATION["dt"]))
        return 0


class RLCEquivalentCircuit:
    """
    神经纤维等效RLC电路模型

    状态变量:
        x[0] = Vc (电容电压/细胞膜电压)
        x[1] = IL (电感电流)

    微分方程:
        dVc/dt = (-Vc/R3 - IL) / C
        dIL/dt = (-R1*R2*IL - R3*IL - R2*Vc) / (L*(R1+R2))
    """

    def __init__(self, R1: float, R2: float, R3: float, L: float, C: float):
        """
        初始化RLC电路参数

        Args:
            R1: 等效串联电阻 (Ohm)
            R2: 等效并联电阻 (Ohm)
            R3: 膜电阻 (Ohm)
            L: 等效电感 (H)
            C: 膜电容 (F)
        """
        self.R1 = R1
        self.R2 = R2
        self.R3 = R3
        self.L = L
        self.C = C
        self._build_matrices()

    def _build_matrices(self):
        """构建状态空间连续矩阵"""
        den = self.R1 + self.R2

        # 数值稳定性检查 - 多重检查防止数值不稳定
        if abs(den) < 1e-10:
            den = 1e-10
        if abs(self.C) < 1e-12:
            raise ValueError(f"电容值 {self.C} 过小，可能导致数值不稳定")
        if abs(self.L) < 1e-6:
            raise ValueError(f"电感值 {self.L} 过小，可能导致数值不稳定")

        # 状态矩阵 A: dX/dt = A*X + B*I
        self.A = np.array([
            [-1/(self.C * den), -self.R1/(self.C * den)],
            [self.R1/(self.L * den), -(self.R1*self.R2/den + self.R3)/self.L]
        ], dtype=np.float64)

        # 输入矩阵 B
        self.B = np.array([
            [self.R1/(self.C * den)],
            [self.R1*self.R2/(self.L * den)]
        ], dtype=np.float64)

        # 输出矩阵 C (观测电容电压)
        self.C_out = np.array([[1, 0]], dtype=np.float64)

    def get_discrete_system(self, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取离散化后的状态空间系统 (ZOH方法)

        Args:
            dt: 采样时间步长 (s)

        Returns:
            (Ad, Bd): 离散状态矩阵和输入矩阵
        """
        sys_d = cont2discrete(
            (self.A, self.B, self.C_out, 0),
            dt,
            method='zoh'
        )
        return sys_d[0], sys_d[1].flatten()


class BiphasicPulseGenerator:
    """
    双相刺激脉冲序列生成器

    双相脉冲波形:
        I
        ^
      Imax |-----|     |-----|
           |     |     |     |
           |     |-----|     |----->
           |           |           t
      -Imax|           |-----|
           |

    正相脉冲激活神经，然后负相脉冲去激活/保护组织
    """

    @staticmethod
    def generate(pulse_width: float, amplitude: float,
                 n_steps: int, dt: float) -> np.ndarray:
        """
        生成双相刺激脉冲序列

        Args:
            pulse_width: 单相脉宽 (s)
            amplitude: 脉冲幅度 (A)
            n_steps: 总步数
            dt: 时间步长 (s)

        Returns:
            脉冲序列数组
        """
        pw_steps = int(pulse_width / dt)
        u = np.zeros(n_steps)

        # 正相
        u[0:pw_steps] = amplitude
        # 负相 (去极化)
        u[pw_steps:2*pw_steps] = -amplitude

        return u


class ActivationFunction:
    """
    非线性激活概率函数

    基于能量积分的激活模型:
    P = 1 - exp(-α * E)

    其中 E = ∫(V_th - Vc)^β dt (超过阈值的能量积分)
    """
    
    # 能量积分上限，防止数值溢出
    ENERGY_LIMIT = 100

    def __init__(self, alpha: float, beta: float, V_th: float):
        """
        初始化激活函数参数

        Args:
            alpha: 激活系数，控制激活速率
            beta: 能量指数，控制阈值敏感度
            V_th: 阈值电压 (V)
        """
        self.alpha = alpha
        self.beta = beta
        self.V_th = V_th

    def compute(self, vc: np.ndarray, dt: float) -> float:
        """
        计算神经响应概率

        Args:
            vc: 细胞膜电压时间序列 (V)
            dt: 时间步长 (s)

        Returns:
            响应概率 P ∈ [0, 1]
        """
        # 计算超过阈值的电压差
        diff = self.V_th - vc  # 当Vc < V_th时diff > 0

        # 找到激活区域
        active_mask = diff > 0

        if not np.any(active_mask):
            return 0.0

        # 能量积分: E = Σ(V_th - Vc)^β * dt
        energy = np.sum(diff[active_mask] ** self.beta) * dt

        # 计算激活概率（使用类常量防止溢出）
        p = 1.0 - np.exp(-min(self.alpha * energy, self.ENERGY_LIMIT))

        return np.clip(p, 0.0, 1.0)


class TibialNerveModel:
    """
    胫神经电刺激响应模型

    模型链路:
    电刺激参数 → RLC电路响应 → 细胞膜电压 → 激活概率

    Attributes:
        circuit: RLC等效电路
        pulse_gen: 双相脉冲生成器
        activation: 激活函数
    """

    def __init__(self, params: dict):
        """
        初始化模型

        Args:
            params: 8维物理参数字典
                   {'R1', 'R2', 'R3', 'L', 'C', 'alpha', 'beta', 'V_th'}
        """
        self.params = params

        # 初始化子模块
        self.circuit = RLCEquivalentCircuit(
            R1=params['R1'],
            R2=params['R2'],
            R3=params['R3'],
            L=params['L'],
            C=params['C']
        )

        self.pulse_gen = BiphasicPulseGenerator()

        self.activation = ActivationFunction(
            alpha=params['alpha'],
            beta=params['beta'],
            V_th=params['V_th']
        )

        # 预计算离散系统
        dt = SIMULATION["dt"]
        self.Ad, self.Bd = self.circuit.get_discrete_system(dt)

        # 预热: 确保负相脉冲有足够的初始化
        self._init_state = np.zeros(2)

    def simulate(self, i_peak: float, pulse_width: float) -> float:
        """
        执行单次电刺激仿真

        Args:
            i_peak: 峰值电流 (A)
            pulse_width: 脉宽 (s)

        Returns:
            神经响应概率 P ∈ [0, 1]
        """
        dt = SIMULATION["dt"]
        t_total = SIMULATION["t_total"]
        n_steps = int(t_total / dt)

        # 生成双相脉冲
        u = self.pulse_gen.generate(pulse_width, i_peak, n_steps, dt)

        # 状态演化
        y = np.zeros((2, n_steps))
        y[:, 0] = self._init_state

        # 离散状态更新: x[k+1] = Ad*x[k] + Bd*u[k]
        for k in range(n_steps - 1):
            y[:, k+1] = self.Ad @ y[:, k] + self.Bd * u[k]

        # 提取细胞膜电压
        vc = y[0, :]

        # 计算激活概率
        p = self.activation.compute(vc, dt)

        return p

    def simulate_batch(self, i_peaks: np.ndarray,
                       pulse_widths: np.ndarray) -> np.ndarray:
        """
        批量仿真

        Args:
            i_peaks: 峰值电流数组 (A)
            pulse_widths: 脉宽数组 (s)

        Returns:
            响应概率数组
        """
        return np.array([
            self.simulate(i, pw)
            for i, pw in zip(i_peaks, pulse_widths)
        ])

    def compute_stimulus_response_curve(self,
                                        i_range: np.ndarray,
                                        pulse_width: float) -> np.ndarray:
        """
        计算刺激-响应曲线

        Args:
            i_range: 电流范围 (A)
            pulse_width: 固定脉宽 (s)

        Returns:
            响应概率数组
        """
        return self.simulate_batch(i_range, np.full_like(i_range, pulse_width))

    def find_threshold_current(self, target_p: float,
                               pulse_width: float,
                               i_bounds: Tuple[float, float] = (1e-4, 0.15)
                               ) -> Optional[float]:
        """
        寻找达到目标响应概率所需的阈值电流

        Args:
            target_p: 目标响应概率
            pulse_width: 脉宽 (s)
            i_bounds: 电流搜索边界 (A)

        Returns:
            阈值电流 (A), 如果无法达到返回None
        """
        from scipy.optimize import brentq

        def objective(i):
            return self.simulate(i, pulse_width) - target_p

        try:
            i_threshold = brentq(objective, i_bounds[0], i_bounds[1], xtol=1e-5)
            return i_threshold
        except ValueError:
            return None


class ModelChain:
    """
    模型链路管理器

    完整链路:
    [电流强度, 频率, 脉宽] → [细胞膜电压] → [响应概率]

    支持:
    - 单点预测
    - 批量预测
    - 参数敏感性分析
    - 阈值计算
    """

    def __init__(self, params: dict):
        """
        初始化模型链路

        Args:
            params: 8维物理参数
        """
        self.model = TibialNerveModel(params)
        self.params = params

    def predict(self,
                current: float,
                frequency: float,
                pulse_width: float) -> float:
        """
        单点预测

        Args:
            current: 电流强度 (A)
            frequency: 刺激频率 (Hz)
            pulse_width: 脉宽 (s)

        Returns:
            响应概率
        """
        # 对于频率响应，当前模型取时间平均
        # 后续可扩展为累加模型
        return self.model.simulate(current, pulse_width)

    def predict_multi_frequency(self,
                               currents: np.ndarray,
                               frequencies: List[float],
                               pulse_width: float) -> np.ndarray:
        """
        多频率预测

        Args:
            currents: 电流数组 (A)
            frequencies: 频率列表 (Hz)
            pulse_width: 脉宽 (s)

        Returns:
            所有频率下的响应概率 (flattened)
        """
        results = []
        for freq in frequencies:
            p = self.model.simulate_batch(
                currents,
                np.full_like(currents, pulse_width)
            )
            results.append(p)
        return np.concatenate(results)

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "params": self.params,
            "circuit_model": "RLC_equivalent",
            "activation_model": "energy_integral",
            "simulation_dt": SIMULATION["dt"],
            "simulation_duration": SIMULATION["t_total"],
        }
