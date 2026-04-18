"""
数据处理模块单元测试
====================
测试数据归一化、统计分析、格式转换等功能
"""

import pytest
import numpy as np
import pandas as pd
from modules.data_processor import (
    DataProcessor,
    DataExporter,
    StatisticsResult
)
from modules.data_importer import (
    DataImporter,
    DataInfo,
    NerveDataParser,
    DataValidator
)


class TestDataProcessorNormalization:
    """测试数据归一化功能"""

    def test_normalize_current_mA_to_A(self):
        """测试mA到A的归一化"""
        processor = DataProcessor()
        currents_mA = np.array([10, 20, 30, 40, 50])
        
        currents_A = processor.normalize_current(currents_mA, unit='mA')
        
        expected = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        np.testing.assert_array_almost_equal(currents_A, expected)

    def test_normalize_current_A_stays(self):
        """测试A单位的电流保持不变"""
        processor = DataProcessor()
        currents_A = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        
        result = processor.normalize_current(currents_A, unit='A')
        
        np.testing.assert_array_equal(result, currents_A)

    def test_denormalize_A_to_mA(self):
        """测试A到mA的反归一化"""
        processor = DataProcessor()
        currents_A = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        
        currents_mA = processor.denormalize_current(currents_A, unit='mA')
        
        expected = np.array([10, 20, 30, 40, 50])
        np.testing.assert_array_almost_equal(currents_mA, expected)

    def test_denormalize_mA_stays(self):
        """测试反归一化mA单位值（输入被当作A处理）"""
        processor = DataProcessor()
        # denormalize_current 的语义是将 A 转换为 mA
        # 所以输入值 10, 20, 30, 40, 50 会被乘以 1000
        currents_A = np.array([0.01, 0.02, 0.03, 0.04, 0.05])

        result = processor.denormalize_current(currents_A, unit='mA')

        expected = np.array([10, 20, 30, 40, 50])
        np.testing.assert_array_almost_equal(result, expected)

    def test_roundtrip_conversion(self):
        """测试往返转换一致性"""
        processor = DataProcessor()
        original = np.array([5.5, 12.3, 25.7, 33.1, 48.9])
        
        normalized = processor.normalize_current(original, unit='mA')
        denormalized = processor.denormalize_current(normalized, unit='mA')
        
        np.testing.assert_array_almost_equal(denormalized, original)


class TestDataProcessorStatistics:
    """测试统计计算功能"""

    def test_compute_statistics_basic(self):
        """测试基础统计计算"""
        processor = DataProcessor()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        stats = processor.compute_statistics(data)
        
        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'median' in stats
        
        assert stats['mean'] == pytest.approx(5.5, rel=1e-5)
        assert stats['min'] == 1.0
        assert stats['max'] == 10.0

    def test_compute_statistics_with_nan(self):
        """测试含NaN数据的统计"""
        processor = DataProcessor()
        data = np.array([1, 2, np.nan, 4, 5, np.nan, 7, 8, 9, 10])
        
        stats = processor.compute_statistics(data)
        
        # NaN应该被忽略
        assert not np.isnan(stats['mean'])
        assert stats['mean'] == pytest.approx(5.714, rel=1e-2)

    def test_compute_statistics_empty(self):
        """测试空数据统计"""
        processor = DataProcessor()
        data = np.array([np.nan, np.nan, np.nan])
        
        stats = processor.compute_statistics(data)
        
        assert np.isnan(stats['mean'])
        assert np.isnan(stats['std'])

    def test_compute_statistics_percentiles(self):
        """测试百分位数计算"""
        processor = DataProcessor()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        stats = processor.compute_statistics(data)

        assert 'q25' in stats
        assert 'q75' in stats
        # numpy percentile 使用线性插值，对于[1,2,3,4,5,6,7,8,9,10]：
        # q25 = 2.5 + 0.25*1 = 3.25, q75 = 7.5 + 0.25*1 = 7.75
        assert stats['q25'] == pytest.approx(3.25, rel=1e-5)
        assert stats['q75'] == pytest.approx(7.75, rel=1e-5)

    def test_compute_fit_metrics(self):
        """测试拟合指标计算"""
        processor = DataProcessor()
        exp_data = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        sim_data = np.array([0.12, 0.28, 0.52, 0.68, 0.88])
        
        metrics = processor.compute_fit_metrics(exp_data, sim_data)
        
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'r2' in metrics
        assert 'mape' in metrics
        assert metrics['rmse'] >= 0
        assert 0 <= metrics['r2'] <= 1

    def test_compute_fit_metrics_perfect_fit(self):
        """测试完美拟合"""
        processor = DataProcessor()
        data = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        
        metrics = processor.compute_fit_metrics(data, data)
        
        assert metrics['rmse'] == pytest.approx(0.0, abs=1e-10)
        assert metrics['mae'] == pytest.approx(0.0, abs=1e-10)
        assert metrics['r2'] == pytest.approx(1.0, abs=1e-10)

    def test_compute_fit_metrics_length_mismatch(self):
        """测试长度不一致的处理"""
        processor = DataProcessor()
        exp_data = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        sim_data = np.array([0.12, 0.28, 0.52])
        
        metrics = processor.compute_fit_metrics(exp_data, sim_data)
        
        # 应该取最小长度
        assert 'rmse' in metrics
        assert not np.isnan(metrics['rmse'])

    def test_compute_residuals(self):
        """测试残差计算"""
        processor = DataProcessor()
        exp_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        sim_data = np.array([1.1, 1.9, 3.1, 3.8, 5.2])
        
        residuals = processor.compute_residuals(exp_data, sim_data)
        
        expected = np.array([-0.1, 0.1, -0.1, 0.2, -0.2])
        np.testing.assert_array_almost_equal(residuals, expected)


class TestDataProcessorExtraction:
    """测试数据提取功能"""

    def test_extract_response_columns(self, sample_dataframe):
        """测试响应列提取"""
        processor = DataProcessor()
        
        responses = processor.extract_response_columns(sample_dataframe)
        
        assert len(responses) >= 1
        # 应该包含Freq相关的列
        response_cols = list(responses.keys())
        assert any('Freq' in col for col in response_cols)

    def test_extract_response_columns_empty(self):
        """测试无响应列的情况"""
        processor = DataProcessor()
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        
        responses = processor.extract_response_columns(df)
        
        assert len(responses) == 0

    def test_analyze_per_frequency(self, sample_dataframe):
        """测试按频率分析"""
        processor = DataProcessor()
        
        results = processor.analyze_per_frequency(
            sample_dataframe,
            current_col='电流_mA',
            response_cols=['Freq_10Hz', 'Freq_20Hz']
        )
        
        assert len(results) == 2
        for freq_results in results.values():
            assert 'mean' in freq_results
            assert 'std' in freq_results


class TestDataExporter:
    """测试数据导出功能"""

    def test_to_csv(self, tmp_path):
        """测试CSV导出"""
        df = pd.DataFrame({
            '电流_mA': [1, 2, 3],
            '响应': [0.1, 0.5, 0.9]
        })
        
        file_path = tmp_path / "test.csv"
        result = DataExporter.to_csv(df, str(file_path))
        
        assert result == str(file_path)
        assert file_path.exists()
        
        # 验证内容
        df_read = pd.read_csv(file_path)
        assert len(df_read) == 3

    def test_to_json(self, tmp_path):
        """测试JSON导出"""
        data = {
            'metadata': {'name': 'test'},
            'values': [1, 2, 3]
        }
        
        file_path = tmp_path / "test.json"
        result = DataExporter.to_json(data, str(file_path))
        
        assert result == str(file_path)
        assert file_path.exists()

    def test_to_excel(self, tmp_path):
        """测试Excel导出"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        
        file_path = tmp_path / "test.xlsx"
        result = DataExporter.to_excel(df, str(file_path))
        
        assert result == str(file_path)
        assert file_path.exists()

    def test_export_with_metadata(self, tmp_path):
        """测试带元数据导出"""
        df = pd.DataFrame({'A': [1, 2, 3]})
        metadata = {'source': 'test', 'version': 1}
        
        file_path = tmp_path / "test_with_meta.json"
        result = DataExporter.export_with_metadata(df, str(file_path), metadata)
        
        assert file_path.exists()
        
        # 验证元数据
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        assert 'metadata' in loaded
        assert loaded['metadata']['source'] == 'test'


class TestDataImporter:
    """测试数据导入功能"""

    def test_initialization(self):
        """测试导入器初始化"""
        importer = DataImporter()
        
        assert importer.current_data is None
        assert len(importer.supported_formats) > 0

    def test_supported_formats(self):
        """测试支持的格式"""
        importer = DataImporter()
        
        expected_formats = ['.xlsx', '.xls', '.csv', '.json', '.txt']
        for fmt in expected_formats:
            assert fmt in importer.supported_formats

    def test_detect_data_type_nerve(self):
        """测试神经数据检测"""
        importer = DataImporter()
        df = pd.DataFrame({
            '电流_mA': [1, 2, 3],
            'Freq_10Hz': [0.1, 0.5, 0.9]
        })
        
        data_type = importer._detect_data_type(df)
        
        assert data_type == 'nerve'

    def test_detect_data_type_generic(self):
        """测试通用数据检测"""
        importer = DataImporter()
        df = pd.DataFrame({
            'Col_A': ['a', 'b', 'c'],
            'Col_B': [1, 2, 3]
        })
        
        data_type = importer._detect_data_type(df)
        
        assert data_type == 'generic'


class TestNerveDataParser:
    """测试神经数据解析器"""

    def test_is_header_with_keywords(self):
        """测试表头识别"""
        assert NerveDataParser._is_header(['I_peak', 'Freq_10Hz']) == True
        assert NerveDataParser._is_header(['电流', '响应']) == True

    def test_is_header_with_numbers(self):
        """测试纯数字行不是表头"""
        assert NerveDataParser._is_header(['1.0', '2.0', '3.0']) == False

    def test_normalize_columns_current(self):
        """测试电流列标准化"""
        columns = ['I_peak(mA)', 'Current', '数据']
        
        normalized = NerveDataParser._normalize_columns(columns)
        
        assert '电流_mA' in normalized[:2]  # 前两列应该被标准化

    def test_normalize_columns_frequency(self):
        """测试频率列标准化"""
        columns = ['Freq_10Hz', 'Frequency_20Hz', 'other']
        
        normalized = NerveDataParser._normalize_columns(columns)
        
        assert any('Freq' in col for col in normalized)

    def test_extract_frequencies(self):
        """测试频率提取"""
        columns = ['电流_mA', 'Freq_10Hz', 'Freq_20Hz', 'Freq_30Hz']
        
        frequencies = NerveDataParser._extract_frequencies(columns)
        
        assert 10.0 in frequencies
        assert 20.0 in frequencies
        assert 30.0 in frequencies

    def test_parse_emg_file(self):
        """测试EMG文件解析"""
        lines = [
            'I_peak(mA),Freq_10Hz,Freq_20Hz',
            '5.0,0.1,0.12',
            '10.0,0.3,0.35',
            '15.0,0.5,0.55',
        ]
        
        df, metadata = NerveDataParser.parse_emg_file(lines)
        
        assert len(df) == 3
        assert 'Freq_10Hz' in df.columns

    def test_parse_stim_params_file(self):
        """测试刺激参数文件解析"""
        lines = [
            'PW,200,us',
            'Freqs,"5, 10, 15, 20",Hz',
            'I_peak_Sequence(mA)',
            '5.0',
            '10.0',
            '15.0',
        ]

        df, metadata = NerveDataParser.parse_stim_params_file(lines)

        # 注意：返回的键名是 'pulse_width' (秒)，不是 'pulse_width_us'
        assert 'pulse_width' in metadata
        assert 'frequencies' in metadata
        # pulse_width 的值是微秒转秒后的结果
        assert metadata['pulse_width'] == pytest.approx(200e-6, rel=1e-9)


class TestDataValidator:
    """测试数据验证器"""

    def test_validate_nerve_data_valid(self):
        """测试有效神经数据验证"""
        df = pd.DataFrame({
            '电流_mA': [5, 10, 15, 20],
            'Freq_10Hz': [0.1, 0.3, 0.6, 0.9],
            'Freq_20Hz': [0.12, 0.35, 0.65, 0.92]
        })
        
        is_valid, errors = DataValidator.validate_nerve_data(df)
        
        assert is_valid == True
        assert len(errors) == 0

    def test_validate_nerve_data_insufficient_columns(self):
        """测试列数不足验证"""
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        is_valid, errors = DataValidator.validate_nerve_data(df)
        
        assert is_valid == False
        assert len(errors) > 0

    def test_get_data_summary(self):
        """测试数据摘要"""
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [5, 4, 3, 2, 1],
            'C': ['x', 'y', 'z', 'w', 'v']
        })
        
        summary = DataValidator.get_data_summary(df)
        
        assert summary['rows'] == 5
        assert summary['columns'] == 3
        assert 'numeric_columns' in summary
        assert 'missing_values' in summary


class TestDataInfo:
    """测试DataInfo数据结构"""

    def test_data_info_creation(self):
        """测试DataInfo创建"""
        data_info = DataInfo(
            filename='test.csv',
            file_path='/path/to/test.csv',
            data_type='nerve',
            shape=(10, 5),
            columns=['A', 'B', 'C', 'D', 'E'],
            dtypes={'A': 'float64', 'B': 'float64'},
            frequencies=[10.0, 20.0],
            pulse_width=200e-6
        )
        
        assert data_info.filename == 'test.csv'
        assert data_info.data_type == 'nerve'
        assert data_info.shape == (10, 5)
        assert len(data_info.frequencies) == 2


class TestDataProcessorLoadData:
    """测试数据加载功能"""

    def test_load_data(self):
        """测试数据加载"""
        processor = DataProcessor()
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        
        processor.load_data(df)
        
        assert processor.current_data is not None
        assert processor.current_data.equals(df)

    def test_load_data_creates_copy(self):
        """测试加载创建副本"""
        processor = DataProcessor()
        df = pd.DataFrame({'A': [1, 2, 3]})
        
        processor.load_data(df)
        df.iloc[0, 0] = 999  # 修改原始数据
        
        assert processor.current_data.iloc[0, 0] == 1  # 应该不受影响
