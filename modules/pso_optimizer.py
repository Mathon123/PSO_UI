"""
PSO优化模块
============
粒子群优化算法实现，用于胫神经电刺激模型参数辨识
"""

import numpy as np
import time
from typing import Tuple, List, Callable, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class PSOHistory:
    """PSO优化历史记录"""
    gbest_fitness_history: List[float] = field(default_factory=list)
    gbest_position_history: List[np.ndarray] = field(default_factory=list)
    convergence_iteration: Optional[int] = None
    final_rmse: Optional[float] = None
    optimization_time: float = 0.0


@dataclass
class OptimizationResult:
    """优化结果"""
    best_params: np.ndarray
    best_rmse: float
    converged: bool
    history: PSOHistory
    n_evaluations: int
    message: str

    def to_dict(self) -> dict:
        return {
            "best_params": self.best_params.tolist(),
            "best_rmse": self.best_rmse,
            "converged": self.converged,
            "n_evaluations": self.n_evaluations,
            "message": self.message,
        }


class AdaptivePSO:
    """
    自适应粒子群优化器

    特性:
    1. 自适应惯性权重 - 根据迭代进度动态调整
    2. 速度限制 - 防止爆炸
    3. 边界处理 - 反弹策略
    4. 停滞检测 - 触发变异
    5. 早停机制 - 达到目标RMSE时停止
    """

    def __init__(self,
                 n_particles: int = 100,
                 n_iterations: int = 50,
                 dim: int = 8,
                 bounds: List[Tuple[float, float]] = None,
                 c1: float = 1.8,
                 c2: float = 1.5,
                 w_max: float = 0.9,
                 w_min: float = 0.4,
                 v_max: float = 0.1,
                 mutation_prob: float = 0.15,
                 stall_threshold: int = 10,
                 target_rmse: float = 0.03):
        """
        初始化PSO优化器
        """
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.dim = dim
        self.bounds = np.array(bounds)

        self.c1 = c1
        self.c2 = c2
        self.w_max = w_max
        self.w_min = w_min
        self.v_max = v_max
        self.mutation_prob = mutation_prob
        self.stall_threshold = stall_threshold
        self.target_rmse = target_rmse

        # 初始化粒子状态
        self.X = None
        self.V = None
        self.pbest_X = None
        self.pbest_fit = None
        self.gbest_X = None
        self.gbest_fit = float('inf')

        self.history = PSOHistory()
        self.n_evaluations = 0
        self.rng = np.random.default_rng()

    def _init_particles(self):
        """初始化粒子群"""
        self.X = self.rng.uniform(0, 1, (self.n_particles, self.dim))
        self.V = self.rng.uniform(-self.v_max, self.v_max, (self.n_particles, self.dim))
        self.pbest_X = np.copy(self.X)
        self.pbest_fit = np.full(self.n_particles, float('inf'))
        self.gbest_X = np.zeros(self.dim)
        self.gbest_fit = float('inf')

    def _to_physical(self, normalized_X: np.ndarray) -> np.ndarray:
        """归一化空间 -> 物理参数空间"""
        low = self.bounds[:, 0]
        high = self.bounds[:, 1]
        return low + normalized_X * (high - low)

    def _compute_adaptive_weight(self, iteration: int) -> float:
        """计算自适应惯性权重 - 平方递减策略"""
        progress = iteration / self.n_iterations
        return self.w_max - (self.w_max - self.w_min) * (progress ** 2)

    def _update_velocity(self, w: float):
        """更新粒子速度"""
        r1 = self.rng.uniform(0, 1, (self.n_particles, self.dim))
        r2 = self.rng.uniform(0, 1, (self.n_particles, self.dim))

        cognitive = self.c1 * r1 * (self.pbest_X - self.X)
        social = self.c2 * r2 * (self.gbest_X - self.X)

        self.V = w * self.V + cognitive + social
        self.V = np.clip(self.V, -self.v_max, self.v_max)

    def _update_position(self):
        """更新粒子位置"""
        self.X = self.X + self.V

        # 边界反弹处理 - 使用反射策略
        # 注意: 此实现可能导致边界附近震荡，后续可优化为clamp方式
        for j in range(self.n_particles):
            for d in range(self.dim):
                if self.X[j, d] < 0:
                    self.X[j, d] = -self.X[j, d]
                    self.V[j, d] *= -0.5  # 速度反向并衰减
                elif self.X[j, d] > 1:
                    self.X[j, d] = 2 - self.X[j, d]
                    self.V[j, d] *= -0.5  # 速度反向并衰减

    def _apply_mutation(self):
        """柯西变异 - 跳出局部最优"""
        n_mutate = int(self.n_particles * self.mutation_prob)

        for _ in range(n_mutate):
            idx = self.rng.integers(0, self.n_particles)
            perturbation = self.rng.standard_cauchy(self.dim) * 0.05
            self.X[idx] = np.clip(self.gbest_X + perturbation, 0, 1)

    def optimize(self,
                 fitness_func: Callable[[np.ndarray], float],
                 verbose: bool = True,
                 progress_callback: Callable[[int, float], None] = None) -> OptimizationResult:
        """
        执行PSO优化
        
        Args:
            fitness_func: 适应度函数
            verbose: 是否输出信息
            progress_callback: 进度回调函数（建议每10次迭代调用一次以提高性能）
        
        Returns:
            OptimizationResult
        """
        start_time = time.time()

        self._init_particles()
        self.n_evaluations = 0
        self.history = PSOHistory()

        # 初始评估
        for j in range(self.n_particles):
            fit = fitness_func(self.X[j])
            self.n_evaluations += 1
            self.pbest_fit[j] = fit

            if fit < self.gbest_fit:
                self.gbest_fit = fit
                self.gbest_X = np.copy(self.X[j])

        self.history.gbest_fitness_history.append(self.gbest_fit)
        self.history.gbest_position_history.append(np.copy(self.gbest_X))

        stall_counter = 0
        last_gbest = self.gbest_fit  # 用于停滞检测
        last_callback_iter = -10  # 初始化为-10，确保初期迭代也能发射

        # 发射初始进度（确保进度条从一开始就显示）
        if progress_callback:
            progress_callback(0, self.gbest_fit)
            last_callback_iter = 0

        for it in range(self.n_iterations):
            w = self._compute_adaptive_weight(it)
            self._update_velocity(w)
            self._update_position()

            for j in range(self.n_particles):
                fit = fitness_func(self.X[j])
                self.n_evaluations += 1

                if fit < self.pbest_fit[j]:
                    self.pbest_fit[j] = fit
                    self.pbest_X[j] = np.copy(self.X[j])

                    if fit < self.gbest_fit:
                        self.gbest_fit = fit
                        self.gbest_X = np.copy(self.X[j])

            self.history.gbest_fitness_history.append(self.gbest_fit)
            self.history.gbest_position_history.append(np.copy(self.gbest_X))

            if self.gbest_fit >= last_gbest:
                stall_counter += 1
            else:
                stall_counter = 0
                last_gbest = self.gbest_fit

            if stall_counter > self.stall_threshold:
                self._apply_mutation()
                stall_counter = 0

            # 【性能优化】仅在关键节点发射进度信号，避免UI过载
            if self.gbest_fit <= self.target_rmse:
                self.history.convergence_iteration = it + 1
                self.history.final_rmse = self.gbest_fit
                if progress_callback and it - last_callback_iter >= 5:
                    progress_callback(it + 1, self.gbest_fit)
                    last_callback_iter = it
                break

            # 每5次迭代发射一次进度信号，或当改善超过5%时立即发射
            improvement = last_gbest - self.gbest_fit
            # 使用相对改善比例，避免RMSE尺度依赖
            if progress_callback:
                should_emit = it - last_callback_iter >= 5
                if not should_emit and last_gbest > 0:
                    relative_improvement = improvement / last_gbest
                    should_emit = relative_improvement > 0.05  # 相对改善超过5%
                if should_emit:
                    progress_callback(it + 1, self.gbest_fit)
                    last_callback_iter = it

        self.history.optimization_time = time.time() - start_time
        converged = self.gbest_fit <= self.target_rmse

        if converged:
            message = f"优化成功! RMSE={self.gbest_fit:.6f} <= 目标值{self.target_rmse}"
        else:
            message = f"优化完成但未达到目标RMSE. 当前RMSE={self.gbest_fit:.6f}"

        best_params_physical = self._to_physical(self.gbest_X)

        return OptimizationResult(
            best_params=best_params_physical,
            best_rmse=self.gbest_fit,
            converged=converged,
            history=self.history,
            n_evaluations=self.n_evaluations,
            message=message
        )


class NerveParameterOptimizer:
    """胫神经电刺激参数优化器（对接真实神经模型）"""

    # 参数名称
    PARAM_NAMES = ['R1', 'R2', 'R3', 'L', 'C', 'alpha', 'beta', 'V_th']
    PARAM_DISPLAY_NAMES = {
        'R1': ('等效串联电阻', 'Ω'),
        'R2': ('等效并联电阻', 'Ω'),
        'R3': ('膜电阻', 'Ω'),
        'L': ('等效电感', 'H'),
        'C': ('膜电容', 'F'),
        'alpha': ('激活系数', ''),
        'beta': ('能量指数', ''),
        'V_th': ('阈值电压', 'V'),
    }

    def __init__(self):
        self.pso = None
        self.model = None
        self.result = None
        self.exp_data = None
        self.pulse_width = 200e-6  # 默认脉宽

    def set_data(self, currents: np.ndarray, responses: np.ndarray, pulse_width: float = 200e-6):
        """
        设置实验数据

        Args:
            currents: 电流数组 (A)
            responses: 响应概率数组
            pulse_width: 脉宽 (s)
        """
        self.exp_data = {
            'currents': currents,
            'responses': responses,
        }
        self.pulse_width = pulse_width

    def optimize(self,
                 n_particles: int = 100,
                 n_iterations: int = 50,
                 target_rmse: float = 0.03,
                 verbose: bool = True,
                 progress_callback: Callable[[int, float], None] = None) -> OptimizationResult:
        """
        执行参数优化

        Args:
            n_particles: 粒子数
            n_iterations: 迭代次数
            target_rmse: 目标RMSE
            verbose: 是否输出信息
            progress_callback: 进度回调函数

        Returns:
            OptimizationResult
        """
        if self.exp_data is None:
            raise ValueError("请先调用 set_data() 设置实验数据")

        from modules.nerve_model import TibialNerveModel, PARAM_BOUNDS

        currents = self.exp_data['currents']
        responses = self.exp_data['responses']
        pulse_width = self.pulse_width

        # 创建PSO优化器
        self.pso = AdaptivePSO(
            n_particles=n_particles,
            n_iterations=n_iterations,
            dim=8,
            bounds=PARAM_BOUNDS,
            target_rmse=target_rmse
        )

        # 构建适应度函数
        # 注意: 每次迭代都创建新的模型实例，效率较低但代码简洁
        # 优化方向: 可考虑复用模型实例或使用缓存
        def fitness_func(norm_params):
            phys_params = self.pso._to_physical(norm_params)

            # 构建参数字典
            params_dict = dict(zip(self.PARAM_NAMES, phys_params))

            # 创建模型并计算响应
            model = TibialNerveModel(params_dict)
            responses_sim = np.array([
                model.simulate(i, pulse_width) for i in currents
            ])

            # 计算RMSE
            rmse = np.sqrt(np.mean((responses - responses_sim) ** 2))
            return rmse

        self.result = self.pso.optimize(
            fitness_func,
            verbose=verbose,
            progress_callback=progress_callback
        )

        return self.result

    def get_identified_params(self) -> Dict[str, float]:
        """获取辨识的参数"""
        if self.result is None:
            return {}

        return dict(zip(self.PARAM_NAMES, self.result.best_params))

    def compute_response_curve(self, currents_range: np.ndarray = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        使用辨识的参数计算响应曲线

        Args:
            currents_range: 电流范围，默认使用实验数据范围

        Returns:
            (电流数组, 响应数组)
        """
        if self.result is None:
            raise ValueError("请先执行优化")

        from modules.nerve_model import TibialNerveModel

        params_dict = dict(zip(self.PARAM_NAMES, self.result.best_params))
        model = TibialNerveModel(params_dict)

        if currents_range is None:
            currents_range = self.exp_data['currents']

        responses = np.array([
            model.simulate(i, self.pulse_width) for i in currents_range
        ])

        return currents_range, responses

    def compute_threshold_current(self, target_p: float = 0.8) -> Optional[float]:
        """
        计算达到目标响应概率所需的阈值电流

        Args:
            target_p: 目标响应概率

        Returns:
            阈值电流 (A)
        """
        if self.result is None:
            raise ValueError("请先执行优化")

        from modules.nerve_model import TibialNerveModel

        params_dict = dict(zip(self.PARAM_NAMES, self.result.best_params))
        model = TibialNerveModel(params_dict)

        return model.find_threshold_current(target_p, self.pulse_width)

    def compute_sd_curve(self, pulse_widths: np.ndarray = None,
                        target_p: float = 0.8) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算刺激-剂量曲线

        Args:
            pulse_widths: 脉宽数组
            target_p: 目标响应概率

        Returns:
            (脉宽数组, 电流数组) 单位: us, mA
        """
        if self.result is None:
            raise ValueError("请先执行优化")

        from modules.nerve_model import TibialNerveModel

        if pulse_widths is None:
            pulse_widths = np.linspace(150e-6, 300e-6, 16)

        params_dict = dict(zip(self.PARAM_NAMES, self.result.best_params))
        model = TibialNerveModel(params_dict)

        currents = []
        for pw in pulse_widths:
            i_threshold = model.find_threshold_current(target_p, pw)
            if i_threshold is not None:
                currents.append(i_threshold * 1000)  # 转为mA
            else:
                currents.append(np.nan)

        return pulse_widths * 1e6, np.array(currents)

    def evaluate_fit_quality(self) -> Dict:
        """
        评估拟合质量

        Returns:
            包含RMSE, MAE, R²等指标的字典
        """
        if self.exp_data is None or self.result is None:
            raise ValueError("请先执行优化")

        from modules.nerve_model import TibialNerveModel

        currents = self.exp_data['currents']
        responses_exp = self.exp_data['responses']

        params_dict = dict(zip(self.PARAM_NAMES, self.result.best_params))
        model = TibialNerveModel(params_dict)

        responses_sim = np.array([
            model.simulate(i, self.pulse_width) for i in currents
        ])

        # 计算指标
        rmse = np.sqrt(np.mean((responses_exp - responses_sim) ** 2))
        mae = np.mean(np.abs(responses_exp - responses_sim))

        ss_res = np.sum((responses_exp - responses_sim) ** 2)
        ss_tot = np.sum((responses_exp - np.mean(responses_exp)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        return {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'target_met': rmse <= 0.03,
        }


def format_params(params: Dict[str, float]) -> str:
    """格式化参数输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("辨识的8个物理参数:")
    lines.append("=" * 60)

    for key, value in params.items():
        display_info = NerveParameterOptimizer.PARAM_DISPLAY_NAMES.get(key, (key, ''))
        name_cn, unit = display_info
        fmt_value = f"{value:.4e}" if (abs(value) < 0.001 or abs(value) > 10000) else f"{value:.4f}"
        lines.append(f"  {key:<6} ({name_cn:<10}): {fmt_value:>15} {unit}")

    lines.append("=" * 60)
    return "\n".join(lines)
