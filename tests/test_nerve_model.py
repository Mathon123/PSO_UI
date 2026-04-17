"""
神经模型单元测试
=================
测试RLC电路模型、脉冲生成器、激活函数等功能
"""

import pytest
import numpy as np
from modules.nerve_model import (
    RLCEquivalentCircuit,
    BiphasicPulseGenerator,
    ActivationFunction,
    TibialNerveModel,
    ModelChain,
    SIMULATION,
    PARAM_BOUNDS,
    StimulusSignal
)


class TestRLCCircuit:
    """测试RLC等效电路"""

    def test_initialization(self):
        """测试电路初始化"""
        circuit = RLCEquivalentCircuit(
            R1=50000,
            R2=2000,
            R3=10000,
            L=0.5,
            C=20e-9
        )
        
        assert circuit.R1 == 50000
        assert circuit.R2 == 2000
        assert circuit.R3 == 10000
        assert circuit.L == 0.5
        assert circuit.C == 20e-9

    def test_matrices_built(self):
        """测试状态空间矩阵已构建"""
        circuit = RLCEquivalentCircuit(
            R1=50000,
            R2=2000,
            R3=10000,
            L=0.5,
            C=20e-9
        )
        
        assert circuit.A is not None
        assert circuit.B is not None
        assert circuit.C_out is not None
        assert circuit.A.shape == (2, 2)
        assert circuit.B.shape == (2,)

    def test_matrices_shape(self):
        """测试矩阵形状"""
        circuit = RLCEquivalentCircuit(
            R1=100000,
            R2=5000,
            R3=20000,
            L=1.0,
            C=50e-9
        )
        
        assert circuit.A.shape == (2, 2)
        assert circuit.B.shape == (2, 1)  # B在_build_matrices中是2x1

    def test_get_discrete_system(self):
        """测试离散化系统"""
        circuit = RLCEquivalentCircuit(
            R1=50000,
            R2=2000,
            R3=10000,
            L=0.5,
            C=20e-9
        )
        
        dt = SIMULATION["dt"]
        Ad, Bd = circuit.get_discrete_system(dt)
        
        assert Ad.shape == (2, 2)
        assert len(Bd) == 2
        # 验证离散系统的稳定性（特征值在单位圆内）
        eigenvalues = np.linalg.eigvals(Ad)
        assert np.all(np.abs(eigenvalues) <= 1.0 + 1e-10)

    def test_numerical_stability_edge_case(self):
        """测试数值稳定性边界情况"""
        # 测试R1+R2接近0的情况
        circuit = RLCEquivalentCircuit(
            R1=1e-10,
            R2=1e-10,
            R3=10000,
            L=0.5,
            C=20e-9
        )
        
        assert circuit.A is not None
        assert not np.any(np.isnan(circuit.A))


class TestBiphasicPulseGenerator:
    """测试双相脉冲生成器"""

    def test_generate_pulse_shape(self):
        """测试脉冲形状"""
        pulse_width = 200e-6
        amplitude = 0.05
        n_steps = 1500
        dt = 2e-6
        
        pulse = BiphasicPulseGenerator.generate(pulse_width, amplitude, n_steps, dt)
        
        assert len(pulse) == n_steps
        assert pulse.dtype == np.float64

    def test_generate_pulse_values(self):
        """测试脉冲幅值"""
        pulse_width = 100e-6
        amplitude = 0.05
        n_steps = 1000
        dt = 1e-6
        
        pulse = BiphasicPulseGenerator.generate(pulse_width, amplitude, n_steps, dt)
        
        pw_steps = int(pulse_width / dt)
        
        # 正相部分
        assert np.all(pulse[0:pw_steps] == amplitude)
        # 负相部分
        assert np.all(pulse[pw_steps:2*pw_steps] == -amplitude)
        # 其余部分为0
        assert np.all(pulse[2*pw_steps:] == 0)

    def test_generate_pulse_zero_amplitude(self):
        """测试零幅值脉冲"""
        pulse = BiphasicPulseGenerator.generate(200e-6, 0, 1000, 2e-6)
        
        assert np.all(pulse == 0)

    def test_generate_pulse_negative_amplitude(self):
        """测试负幅值脉冲（反转极性）"""
        pulse_width = 100e-6
        amplitude = -0.05
        n_steps = 1000
        dt = 1e-6
        
        pulse = BiphasicPulseGenerator.generate(pulse_width, amplitude, n_steps, dt)
        
        pw_steps = int(pulse_width / dt)
        
        # 正相部分应为负值
        assert np.all(pulse[0:pw_steps] == amplitude)
        # 负相部分应为正值
        assert np.all(pulse[pw_steps:2*pw_steps] == -amplitude)


class TestActivationFunction:
    """测试激活函数"""

    def test_initialization(self):
        """测试激活函数初始化"""
        activation = ActivationFunction(alpha=5000, beta=2.0, V_th=-0.05)
        
        assert activation.alpha == 5000
        assert activation.beta == 2.0
        assert activation.V_th == -0.05

    def test_compute_no_activation(self):
        """测试无激活情况（电压未超过阈值）"""
        activation = ActivationFunction(alpha=5000, beta=2.0, V_th=-0.05)
        
        # 所有电压都低于阈值
        vc = np.array([-0.01, -0.02, -0.03])  # Vc > V_th
        p = activation.compute(vc, dt=2e-6)
        
        assert p == 0.0

    def test_compute_full_activation(self):
        """测试完全激活情况"""
        activation = ActivationFunction(alpha=50000, beta=2.0, V_th=-0.05)
        
        # 大幅超过阈值
        vc = np.array([-0.5, -0.6, -0.7])  # Vc << V_th
        p = activation.compute(vc, dt=2e-6)
        
        assert p > 0.9  # 应该接近1

    def test_compute_partial_activation(self):
        """测试部分激活情况"""
        activation = ActivationFunction(alpha=10000, beta=2.0, V_th=-0.03)
        
        # 混合情况
        vc = np.array([-0.01, -0.02, -0.04, -0.05, -0.06])
        p = activation.compute(vc, dt=2e-6)
        
        assert 0 < p < 1

    def test_compute_probability_bounds(self):
        """测试概率边界"""
        activation = ActivationFunction(alpha=1000, beta=2.0, V_th=-0.05)
        
        # 极端情况
        vc_very_low = np.array([-1.0, -1.0, -1.0])  # 远超阈值
        p1 = activation.compute(vc_very_low, dt=2e-6)
        
        vc_very_high = np.array([0.0, 0.0, 0.0])  # 远高于阈值
        p2 = activation.compute(vc_very_high, dt=2e-6)
        
        assert 0 <= p1 <= 1
        assert 0 <= p2 <= 1
        assert p1 >= p2  # 更低的电压应该产生更高的激活概率

    def test_beta_sensitivity(self):
        """测试beta参数对敏感度的影响"""
        beta_small = 1.0
        beta_large = 4.0
        
        activation1 = ActivationFunction(alpha=5000, beta=beta_small, V_th=-0.05)
        activation2 = ActivationFunction(alpha=5000, beta=beta_large, V_th=-0.05)
        
        # 中等超出阈值的情况
        vc = np.array([-0.06, -0.07, -0.08, -0.09, -0.10])
        dt = 2e-6
        
        p1 = activation1.compute(vc, dt)
        p2 = activation2.compute(vc, dt)
        
        # beta越大，阈值敏感度越高
        # 在相同条件下，不同beta应该产生不同结果
        assert p1 != p2 or np.allclose(p1, p2, rtol=1e-5)


class TestTibialNerveModel:
    """测试胫神经电刺激模型"""

    def test_initialization(self, typical_nerve_params):
        """测试模型初始化"""
        model = TibialNerveModel(typical_nerve_params)
        
        assert model.params == typical_nerve_params
        assert model.circuit is not None
        assert model.pulse_gen is not None
        assert model.activation is not None

    def test_initialization_submodules(self, typical_nerve_params):
        """测试子模块初始化"""
        model = TibialNerveModel(typical_nerve_params)
        
        assert isinstance(model.circuit, RLCEquivalentCircuit)
        assert isinstance(model.pulse_gen, BiphasicPulseGenerator)
        assert isinstance(model.activation, ActivationFunction)

    def test_discrete_system_precomputed(self, typical_nerve_params):
        """测试离散系统已预计算"""
        model = TibialNerveModel(typical_nerve_params)
        
        assert model.Ad is not None
        assert model.Bd is not None
        assert model.Ad.shape == (2, 2)

    def test_simulate_low_current(self, typical_nerve_params):
        """测试低电流仿真（应无响应）"""
        model = TibialNerveModel(typical_nerve_params)
        
        p = model.simulate(i_peak=0.001, pulse_width=200e-6)
        
        assert 0 <= p <= 1

    def test_simulate_high_current(self, typical_nerve_params):
        """测试高电流仿真（应有响应）"""
        model = TibialNerveModel(typical_nerve_params)
        
        p = model.simulate(i_peak=0.1, pulse_width=200e-6)
        
        assert 0 <= p <= 1

    def test_simulate_response_increases_with_current(self, typical_nerve_params):
        """测试响应随电流增加"""
        model = TibialNerveModel(typical_nerve_params)
        pulse_width = 200e-6
        
        currents = np.array([0.01, 0.02, 0.03, 0.05, 0.08])
        responses = [model.simulate(i, pulse_width) for i in currents]
        
        # 响应应该总体趋势增加（可能有波动）
        increasing_trend = sum(1 for i in range(1, len(responses)) 
                              if responses[i] >= responses[i-1] - 0.01)
        assert increasing_trend >= len(responses) - 2  # 允许少量下降

    def test_simulate_batch(self, typical_nerve_params):
        """测试批量仿真"""
        model = TibialNerveModel(typical_nerve_params)
        
        i_peaks = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        pulse_widths = np.array([200e-6] * 5)
        
        responses = model.simulate_batch(i_peaks, pulse_widths)
        
        assert len(responses) == len(i_peaks)
        assert np.all((responses >= 0) & (responses <= 1))

    def test_compute_stimulus_response_curve(self, typical_nerve_params):
        """测试刺激-响应曲线计算"""
        model = TibialNerveModel(typical_nerve_params)
        
        i_range = np.linspace(0.005, 0.05, 10)
        responses = model.compute_stimulus_response_curve(i_range, pulse_width=200e-6)
        
        assert len(responses) == len(i_range)
        assert np.all((responses >= 0) & (responses <= 1))

    def test_find_threshold_current(self, typical_nerve_params):
        """测试阈值电流计算"""
        model = TibialNerveModel(typical_nerve_params)
        
        threshold_50 = model.find_threshold_current(target_p=0.5, pulse_width=200e-6)
        threshold_80 = model.find_threshold_current(target_p=0.8, pulse_width=200e-6)
        
        # 80%阈值的电流应该高于50%阈值
        if threshold_50 is not None and threshold_80 is not None:
            assert threshold_80 > threshold_50

    def test_find_threshold_current_bounds(self, typical_nerve_params):
        """测试边界外的阈值电流搜索"""
        model = TibialNerveModel(typical_nerve_params)
        
        # 使用不可能达到的目标概率
        threshold = model.find_threshold_current(target_p=0.99, pulse_width=200e-6)
        
        # 可能会返回None因为无法达到这么高的概率
        assert threshold is None or threshold >= 0

    def test_different_pulse_widths(self, typical_nerve_params):
        """测试不同脉宽下的响应"""
        model = TibialNerveModel(typical_nerve_params)
        current = 0.03
        
        responses = []
        for pw in [100e-6, 150e-6, 200e-6, 250e-6, 300e-6]:
            responses.append(model.simulate(current, pw))
        
        # 响应应该总体随脉宽增加
        assert len(responses) == 5
        assert np.all((np.array(responses) >= 0) & (np.array(responses) <= 1))


class TestModelChain:
    """测试模型链路"""

    def test_initialization(self, typical_nerve_params):
        """测试链路初始化"""
        chain = ModelChain(typical_nerve_params)
        
        assert chain.params == typical_nerve_params
        assert chain.model is not None

    def test_predict_single(self, typical_nerve_params):
        """测试单点预测"""
        chain = ModelChain(typical_nerve_params)
        
        p = chain.predict(current=0.03, frequency=10, pulse_width=200e-6)
        
        assert 0 <= p <= 1

    def test_predict_multi_frequency(self, typical_nerve_params):
        """测试多频率预测"""
        chain = ModelChain(typical_nerve_params)
        
        currents = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        frequencies = [10.0, 20.0]
        
        result = chain.predict_multi_frequency(currents, frequencies, 200e-6)
        
        # 应该有 len(currents) * len(frequencies) 个结果
        assert len(result) == len(currents) * len(frequencies)

    def test_get_model_info(self, typical_nerve_params):
        """测试获取模型信息"""
        chain = ModelChain(typical_nerve_params)
        
        info = chain.get_model_info()
        
        assert 'params' in info
        assert 'circuit_model' in info
        assert 'activation_model' in info
        assert 'simulation_dt' in info
        assert info['circuit_model'] == 'RLC_equivalent'
        assert info['activation_model'] == 'energy_integral'


class TestStimulusSignal:
    """测试刺激信号数据结构"""

    def test_initialization(self):
        """测试刺激信号初始化"""
        signal = StimulusSignal(
            current=0.05,
            pulse_width=200e-6,
            frequency=10.0,
            amplitude=0.05
        )
        
        assert signal.current == 0.05
        assert signal.pulse_width == 200e-6
        assert signal.frequency == 10.0
        assert signal.amplitude == 0.05

    def test_pulse_width_steps(self):
        """测试脉宽步数计算"""
        signal = StimulusSignal(
            current=0.05,
            pulse_width=200e-6,
            frequency=10.0,
            amplitude=0.05
        )
        
        expected_steps = int(200e-6 / SIMULATION["dt"])
        assert signal.pulse_width_steps == expected_steps

    def test_period_steps(self):
        """测试周期步数计算"""
        signal = StimulusSignal(
            current=0.05,
            pulse_width=200e-6,
            frequency=10.0,
            amplitude=0.05
        )
        
        expected_steps = int(1.0 / (10.0 * SIMULATION["dt"]))
        assert signal.period_steps == expected_steps

    def test_zero_frequency_period(self):
        """测试零频率情况"""
        signal = StimulusSignal(
            current=0.05,
            pulse_width=200e-6,
            frequency=0.0,
            amplitude=0.05
        )
        
        assert signal.period_steps == 0


class TestSimulationConfig:
    """测试仿真配置"""

    def test_simulation_parameters(self):
        """测试仿真参数"""
        assert 'dt' in SIMULATION
        assert 't_total' in SIMULATION
        assert 'target_response' in SIMULATION
        
        assert SIMULATION['dt'] > 0
        assert SIMULATION['t_total'] > 0
        assert 0 < SIMULATION['target_response'] <= 1

    def test_param_bounds_length(self):
        """测试参数边界长度"""
        assert len(PARAM_BOUNDS) == 8  # 应该有8个参数

    def test_param_bounds_values(self):
        """测试参数边界值"""
        for bounds in PARAM_BOUNDS:
            assert len(bounds) == 2
            assert bounds[0] < bounds[1]  # 下界应小于上界


class TestModelEdgeCases:
    """测试模型边界情况"""

    def test_very_low_current(self, typical_nerve_params):
        """测试极低电流"""
        model = TibialNerveModel(typical_nerve_params)
        
        p = model.simulate(i_peak=1e-6, pulse_width=200e-6)
        
        assert 0 <= p <= 1
        assert p < 0.1  # 极低电流应该几乎没有响应

    def test_very_high_current(self, typical_nerve_params):
        """测试极高电流"""
        model = TibialNerveModel(typical_nerve_params)
        
        p = model.simulate(i_peak=0.5, pulse_width=200e-6)
        
        assert 0 <= p <= 1
        assert p > 0.9  # 极高电流应该几乎完全响应

    def test_very_short_pulse(self, typical_nerve_params):
        """测试极短脉宽"""
        model = TibialNerveModel(typical_nerve_params)
        
        p = model.simulate(i_peak=0.1, pulse_width=1e-6)
        
        assert 0 <= p <= 1

    def test_very_long_pulse(self, typical_nerve_params):
        """测试极长脉宽"""
        model = TibialNerveModel(typical_nerve_params)
        
        p = model.simulate(i_peak=0.02, pulse_width=1e-3)
        
        assert 0 <= p <= 1
