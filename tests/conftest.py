"""
pytest配置文件和测试fixtures
============================
提供测试所需的公共fixture和配置
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root_path):
    """测试数据目录"""
    data_dir = project_root_path / "data"
    if not data_dir.exists():
        data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_currents():
    """示例电流数组 (mA)"""
    return np.linspace(5, 50, 20)


@pytest.fixture
def sample_currents_A(sample_currents):
    """示例电流数组 (A)"""
    return sample_currents / 1000


@pytest.fixture
def sample_responses():
    """示例响应概率数组 (模拟S型曲线)"""
    currents_mA = np.linspace(5, 50, 20)
    # 模拟神经响应S型曲线
    normalized = (currents_mA - 20) / 15
    responses = 1 / (1 + np.exp(-normalized * 3))
    # 添加一些噪声
    np.random.seed(42)
    responses += np.random.normal(0, 0.02, len(responses))
    responses = np.clip(responses, 0, 1)
    return responses


@pytest.fixture
def sample_pulse_width():
    """示例脉宽 (s)"""
    return 200e-6


@pytest.fixture
def typical_nerve_params():
    """典型的神经模型参数"""
    return {
        'R1': 50000,      # 50kΩ
        'R2': 2000,       # 2kΩ
        'R3': 10000,      # 10kΩ
        'L': 0.5,         # 0.5H
        'C': 20e-9,       # 20nF
        'alpha': 5000,
        'beta': 2.0,
        'V_th': -0.05,    # -50mV
    }


@pytest.fixture
def boundary_params():
    """参数边界"""
    from modules.nerve_model import PARAM_BOUNDS
    return PARAM_BOUNDS


@pytest.fixture
def sample_nerve_experiment_data(sample_currents, sample_responses):
    """示例神经电刺激实验数据"""
    from ui.analysis_workflow import NerveExperimentData

    return NerveExperimentData(
        filename="test_emg.csv",
        currents_mA=sample_currents,
        currents_A=sample_currents / 1000,
        frequencies=[10.0, 20.0],
        responses={
            'Freq_10Hz': sample_responses,
            'Freq_20Hz': sample_responses * 0.95,  # 略低响应
        },
        pulse_width_us=200.0,
        pulse_width_s=200e-6,
        n_points=len(sample_currents)
    )


@pytest.fixture
def simple_optimizer_data():
    """简化优化器测试数据 (小规模)"""
    # 用于快速测试的简化数据
    currents = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
    # 简化的响应曲线
    responses = np.array([0.1, 0.2, 0.4, 0.7, 0.9])
    return currents, responses


@pytest.fixture
def mock_nerve_model(typical_nerve_params):
    """创建模拟神经模型实例"""
    from modules.nerve_model import TibialNerveModel
    return TibialNerveModel(typical_nerve_params)


@pytest.fixture
def mock_pso_optimizer():
    """创建PSO优化器实例"""
    from modules.pso_optimizer import AdaptivePSO
    return AdaptivePSO


@pytest.fixture
def sample_dataframe():
    """示例DataFrame数据"""
    return pd.DataFrame({
        '电流_mA': np.linspace(5, 50, 10),
        'Freq_10Hz': np.random.rand(10),
        'Freq_20Hz': np.random.rand(10),
    })


@pytest.fixture
def temp_output_dir(tmp_path):
    """临时输出目录"""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


# Pytest配置
def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """自动为测试添加标记"""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_" in item.nodeid and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
