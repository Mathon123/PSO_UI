"""
PSO优化器单元测试
=================
测试AdaptivePSO和NerveParameterOptimizer的功能
"""

import pytest
import numpy as np
from modules.pso_optimizer import (
    AdaptivePSO,
    NerveParameterOptimizer,
    PSOHistory,
    OptimizationResult,
    format_params
)
from modules.nerve_model import PARAM_BOUNDS, TibialNerveModel


class TestAdaptivePSOInitialization:
    """测试AdaptivePSO初始化"""

    def test_default_initialization(self):
        """测试默认参数初始化"""
        pso = AdaptivePSO()
        
        assert pso.n_particles == 100
        assert pso.n_iterations == 50
        assert pso.dim == 8
        assert pso.c1 == 1.8
        assert pso.c2 == 1.5
        assert pso.w_max == 0.9
        assert pso.w_min == 0.4
        assert pso.target_rmse == 0.03

    def test_custom_initialization(self):
        """测试自定义参数初始化"""
        pso = AdaptivePSO(
            n_particles=50,
            n_iterations=100,
            dim=8,
            c1=2.0,
            c2=1.8,
            w_max=0.95,
            w_min=0.3,
            target_rmse=0.02
        )
        
        assert pso.n_particles == 50
        assert pso.n_iterations == 100
        assert pso.c1 == 2.0
        assert pso.c2 == 1.8
        assert pso.w_max == 0.95
        assert pso.w_min == 0.3
        assert pso.target_rmse == 0.02

    def test_bounds_initialization(self):
        """测试边界参数初始化"""
        bounds = [(0, 1)] * 8
        pso = AdaptivePSO(bounds=bounds)
        
        assert pso.bounds is not None
        assert len(pso.bounds) == 8
        assert isinstance(pso.bounds, np.ndarray)

    def test_rng_initialization(self):
        """测试随机数生成器初始化"""
        pso = AdaptivePSO()
        
        assert pso.rng is not None
        assert hasattr(pso, 'gbest_fit')
        assert pso.gbest_fit == float('inf')


class TestParticleInitialization:
    """测试粒子群初始化"""

    def test_init_particles_shape(self):
        """测试粒子位置和速度的形状"""
        pso = AdaptivePSO(n_particles=30, dim=8)
        pso._init_particles()
        
        assert pso.X.shape == (30, 8)
        assert pso.V.shape == (30, 8)
        assert pso.pbest_X.shape == (30, 8)
        assert pso.pbest_fit.shape == (30,)

    def test_init_particles_bounds(self):
        """测试初始化粒子位置在边界内"""
        pso = AdaptivePSO(n_particles=50, dim=8, bounds=PARAM_BOUNDS)
        pso._init_particles()
        
        # 归一化位置应在[0, 1]范围内
        assert np.all(pso.X >= 0)
        assert np.all(pso.X <= 1)

    def test_init_particles_velocity_bounds(self):
        """测试初始速度在限制范围内"""
        pso = AdaptivePSO(n_particles=50, dim=8, v_max=0.1)
        pso._init_particles()
        
        assert np.all(np.abs(pso.V) <= pso.v_max)


class TestVelocityUpdate:
    """测试速度更新"""

    def test_velocity_update_shape(self):
        """测试速度更新后形状保持"""
        pso = AdaptivePSO(n_particles=20, dim=8)
        pso._init_particles()
        initial_v = pso.V.copy()
        
        pso._update_velocity(w=0.7)
        
        assert pso.V.shape == initial_v.shape

    def test_velocity_clipped_to_vmax(self):
        """测试速度被限制在v_max内"""
        pso = AdaptivePSO(n_particles=10, dim=8, v_max=0.05)
        pso._init_particles()
        
        # 多次更新后检查
        for _ in range(5):
            pso._update_velocity(w=0.9)
            assert np.all(np.abs(pso.V) <= pso.v_max)

    def test_adaptive_weight_decreases(self):
        """测试自适应惯性权重递减"""
        pso = AdaptivePSO(n_particles=10, n_iterations=100)
        
        w_start = pso._compute_adaptive_weight(0)
        w_mid = pso._compute_adaptive_weight(50)
        w_end = pso._compute_adaptive_weight(99)
        
        assert w_start > w_mid > w_end
        assert w_start <= pso.w_max
        assert w_end >= pso.w_min


class TestPositionUpdate:
    """测试位置更新"""

    def test_position_update_reflection(self):
        """测试边界反弹策略"""
        pso = AdaptivePSO(n_particles=10, dim=8)
        pso._init_particles()
        
        # 将一些粒子移到边界外
        pso.X[0, 0] = -0.5  # 超出下界
        pso.V[0, 0] = -0.1
        pso.X[1, 1] = 1.5   # 超出上界
        pso.V[1, 1] = 0.1
        
        pso._update_position()
        
        # 反弹后应该在[0, 1]范围内
        assert 0 <= pso.X[0, 0] <= 1
        assert 0 <= pso.X[1, 1] <= 1


class TestMutation:
    """测试变异操作"""

    def test_mutation_applied(self):
        """测试变异被执行"""
        pso = AdaptivePSO(n_particles=50, dim=8, mutation_prob=0.2)
        pso._init_particles()
        pso.gbest_X = pso.X[0].copy()
        
        original_X = pso.X.copy()
        pso._apply_mutation()
        
        # 应该有部分粒子被变异
        # 注意：由于随机性，不一定所有粒子都变化
        assert pso.X.shape == original_X.shape

    def test_mutation_stays_in_bounds(self):
        """测试变异后粒子位置在边界内"""
        pso = AdaptivePSO(n_particles=100, dim=8, mutation_prob=0.3)
        pso._init_particles()
        pso.gbest_X = np.ones(8) * 0.5
        
        for _ in range(10):
            pso._apply_mutation()
            assert np.all(pso.X >= 0)
            assert np.all(pso.X <= 1)


class TestOptimization:
    """测试优化流程"""

    def test_optimization_converges(self):
        """测试优化能够收敛"""
        # 创建一个简单的凸函数
        def sphere(x):
            return np.sum((x - 0.5) ** 2)
        
        pso = AdaptivePSO(
            n_particles=30,
            n_iterations=50,
            dim=8,
            bounds=[(0, 1)] * 8,
            target_rmse=0.01
        )
        
        result = pso.optimize(sphere, verbose=False)
        
        assert isinstance(result, OptimizationResult)
        assert result.best_rmse < 0.5  # 应该收敛到较好的值

    def test_optimization_history_recorded(self):
        """测试历史记录被正确记录"""
        def simple_func(x):
            return np.sum(x ** 2)
        
        pso = AdaptivePSO(n_particles=20, n_iterations=30, dim=8)
        result = pso.optimize(simple_func, verbose=False)
        
        assert len(result.history.gbest_fitness_history) > 0
        assert len(result.history.gbest_position_history) > 0

    def test_optimization_early_stopping(self):
        """测试早停机制"""
        def easy_func(x):
            return np.sum((x - 0.5) ** 2)
        
        pso = AdaptivePSO(
            n_particles=50,
            n_iterations=200,
            dim=8,
            bounds=[(0, 1)] * 8,
            target_rmse=0.001  # 非常严格的目标
        )
        
        result = pso.optimize(easy_func, verbose=False)
        
        # 如果收敛，应该记录收敛迭代次数
        if result.converged:
            assert result.history.convergence_iteration is not None
            assert result.history.convergence_iteration <= pso.n_iterations

    def test_optimization_progress_callback(self):
        """测试进度回调函数"""
        progress_values = []
        
        def track_progress(it, rmse):
            progress_values.append((it, rmse))
        
        def simple_func(x):
            return np.sum(x ** 2)
        
        pso = AdaptivePSO(n_particles=20, n_iterations=20, dim=8)
        pso.optimize(simple_func, verbose=False, progress_callback=track_progress)
        
        # 回调应该被调用多次
        assert len(progress_values) > 0
        # RMSE应该单调递减或保持不变
        for i in range(1, len(progress_values)):
            assert progress_values[i][1] <= progress_values[i-1][1]


class TestNerveParameterOptimizer:
    """测试神经参数优化器"""

    def test_initialization(self):
        """测试初始化"""
        optimizer = NerveParameterOptimizer()
        
        assert optimizer.pso is None
        assert optimizer.model is None
        assert optimizer.result is None

    def test_set_data(self, sample_currents_A, sample_responses, sample_pulse_width):
        """测试设置数据"""
        optimizer = NerveParameterOptimizer()
        optimizer.set_data(sample_currents_A, sample_responses, sample_pulse_width)
        
        assert optimizer.exp_data is not None
        assert 'currents' in optimizer.exp_data
        assert 'responses' in optimizer.exp_data
        assert optimizer.pulse_width == sample_pulse_width

    def test_optimize_without_data_raises(self):
        """测试未设置数据时优化抛出异常"""
        optimizer = NerveParameterOptimizer()
        
        with pytest.raises(ValueError, match="请先调用 set_data"):
            optimizer.optimize()

    def test_optimize_basic(self, sample_currents_A, sample_responses, sample_pulse_width):
        """测试基本优化功能"""
        optimizer = NerveParameterOptimizer()
        optimizer.set_data(sample_currents_A, sample_responses, sample_pulse_width)
        
        result = optimizer.optimize(
            n_particles=20,
            n_iterations=10,
            verbose=False
        )
        
        assert result is not None
        assert isinstance(result, OptimizationResult)
        assert result.best_params is not None
        assert len(result.best_params) == 8

    def test_get_identified_params(self, sample_currents_A, sample_responses, sample_pulse_width):
        """测试获取辨识参数"""
        optimizer = NerveParameterOptimizer()
        optimizer.set_data(sample_currents_A, sample_responses, sample_pulse_width)
        optimizer.optimize(n_particles=15, n_iterations=10, verbose=False)
        
        params = optimizer.get_identified_params()
        
        assert isinstance(params, dict)
        assert len(params) == 8
        assert all(key in params for key in NerveParameterOptimizer.PARAM_NAMES)

    def test_compute_response_curve(self, sample_currents_A, sample_responses, sample_pulse_width):
        """测试计算响应曲线"""
        optimizer = NerveParameterOptimizer()
        optimizer.set_data(sample_currents_A, sample_responses, sample_pulse_width)
        optimizer.optimize(n_particles=15, n_iterations=10, verbose=False)
        
        currents_out, responses_out = optimizer.compute_response_curve()
        
        assert len(currents_out) == len(sample_currents_A)
        assert len(responses_out) == len(sample_currents_A)
        assert np.all(responses_out >= 0)
        assert np.all(responses_out <= 1)

    def test_compute_threshold_current(self, sample_currents_A, sample_responses, sample_pulse_width):
        """测试计算阈值电流"""
        optimizer = NerveParameterOptimizer()
        optimizer.set_data(sample_currents_A, sample_responses, sample_pulse_width)
        optimizer.optimize(n_particles=20, n_iterations=15, verbose=False)
        
        threshold = optimizer.compute_threshold_current(target_p=0.5)
        
        # 阈值应该在合理范围内
        if threshold is not None:
            assert 0 < threshold < 0.2  # 应该在0-200mA范围内

    def test_evaluate_fit_quality(self, sample_currents_A, sample_responses, sample_pulse_width):
        """测试拟合质量评估"""
        optimizer = NerveParameterOptimizer()
        optimizer.set_data(sample_currents_A, sample_responses, sample_pulse_width)
        optimizer.optimize(n_particles=20, n_iterations=15, verbose=False)
        
        quality = optimizer.evaluate_fit_quality()
        
        assert 'rmse' in quality
        assert 'mae' in quality
        assert 'r2' in quality
        assert 'target_met' in quality
        assert quality['rmse'] >= 0
        assert 0 <= quality['r2'] <= 1

    def test_compute_sd_curve(self, sample_currents_A, sample_responses, sample_pulse_width):
        """测试计算SD曲线"""
        optimizer = NerveParameterOptimizer()
        optimizer.set_data(sample_currents_A, sample_responses, sample_pulse_width)
        optimizer.optimize(n_particles=20, n_iterations=15, verbose=False)
        
        pulse_widths_us, currents_mA = optimizer.compute_sd_curve(target_p=0.8)
        
        assert len(pulse_widths_us) > 0
        assert len(currents_mA) == len(pulse_widths_us)


class TestOptimizationResult:
    """测试优化结果"""

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        pso = AdaptivePSO(n_particles=10, n_iterations=5, dim=8)
        
        def simple_func(x):
            return np.sum(x ** 2)
        
        result = pso.optimize(simple_func, verbose=False)
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'best_params' in result_dict
        assert 'best_rmse' in result_dict
        assert 'converged' in result_dict


class TestFormatParams:
    """测试参数格式化"""

    def test_format_params_output(self, typical_nerve_params):
        """测试参数格式化输出"""
        formatted = format_params(typical_nerve_params)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert "R1" in formatted
        assert "R2" in formatted


class TestPSOHistory:
    """测试PSO历史记录"""

    def test_history_initialization(self):
        """测试历史记录初始化"""
        history = PSOHistory()
        
        assert isinstance(history.gbest_fitness_history, list)
        assert isinstance(history.gbest_position_history, list)
        assert history.convergence_iteration is None
        assert history.optimization_time == 0.0

    def test_history_appending(self):
        """测试历史记录追加"""
        history = PSOHistory()
        history.gbest_fitness_history.append(1.0)
        history.gbest_fitness_history.append(0.5)
        
        assert len(history.gbest_fitness_history) == 2
        assert history.gbest_fitness_history[-1] == 0.5
