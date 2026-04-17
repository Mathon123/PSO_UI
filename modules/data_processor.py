"""
数据处理模块
=============
提供数据预处理、格式转换、统计分析等功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class StatisticsResult:
    """统计分析结果"""
    metrics: Dict[str, float]
    column_stats: Dict[str, Dict[str, float]]
    quality_indicators: Dict[str, float]


class DataProcessor:
    """数据处理器"""

    def __init__(self):
        self.current_data: Optional[pd.DataFrame] = None

    def load_data(self, df: pd.DataFrame):
        """加载数据"""
        self.current_data = df.copy()

    def normalize_current(self, currents: np.ndarray, unit: str = 'mA') -> np.ndarray:
        """
        归一化电流值

        Args:
            currents: 电流数组
            unit: 原始单位 ('mA' 或 'A')

        Returns:
            归一化后的数组
        """
        if unit == 'mA':
            return currents / 1000  # mA -> A
        return currents

    def denormalize_current(self, currents: np.ndarray, unit: str = 'mA') -> np.ndarray:
        """
        反归一化电流值

        Args:
            currents: 电流数组 (A)
            unit: 目标单位 ('mA' 或 'A')

        Returns:
            转换后的电流数组
        """
        if unit == 'mA':
            return currents * 1000  # A -> mA
        return currents

    def extract_response_columns(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        提取响应列

        Args:
            df: DataFrame

        Returns:
            {列名: 数据数组} 的字典
        """
        responses = {}
        for col in df.columns:
            col_lower = col.lower()
            # 识别响应相关的列
            if any(keyword in col_lower for keyword in ['响应', 'response', 'p_', 'p-', 'freq']):
                if df[col].dtype in [np.float64, np.int64]:
                    responses[col] = df[col].values
        return responses

    def compute_statistics(self, data: np.ndarray, column_name: str = None) -> Dict[str, float]:
        """
        计算基础统计指标

        Args:
            data: 数据数组
            column_name: 列名（用于日志）

        Returns:
            统计指标字典
        """
        clean_data = data[~np.isnan(data)]
        if len(clean_data) == 0:
            return {"mean": np.nan, "std": np.nan, "min": np.nan,
                    "max": np.nan, "median": np.nan}

        return {
            "mean": float(np.mean(clean_data)),
            "std": float(np.std(clean_data)),
            "min": float(np.min(clean_data)),
            "max": float(np.max(clean_data)),
            "median": float(np.median(clean_data)),
            "q25": float(np.percentile(clean_data, 25)),
            "q75": float(np.percentile(clean_data, 75)),
        }

    def compute_fit_metrics(self, exp_data: np.ndarray, sim_data: np.ndarray) -> Dict[str, float]:
        """
        计算拟合质量指标

        Args:
            exp_data: 实验数据
            sim_data: 仿真数据

        Returns:
            拟合指标字典
        """
        # 确保长度一致
        min_len = min(len(exp_data), len(sim_data))
        exp = np.array(exp_data[:min_len])
        sim = np.array(sim_data[:min_len])

        # 移除NaN
        valid_mask = ~(np.isnan(exp) | np.isnan(sim))
        exp = exp[valid_mask]
        sim = sim[valid_mask]

        if len(exp) == 0:
            return {"rmse": np.nan, "mae": np.nan, "r2": np.nan}

        # RMSE
        rmse = float(np.sqrt(np.mean((exp - sim) ** 2)))

        # MAE
        mae = float(np.mean(np.abs(exp - sim)))

        # R²
        ss_res = np.sum((exp - sim) ** 2)
        ss_tot = np.sum((exp - np.mean(exp)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        return {
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "mape": float(np.mean(np.abs((exp - sim) / (exp + 1e-10))) * 100),
        }

    def compute_residuals(self, exp_data: np.ndarray, sim_data: np.ndarray) -> np.ndarray:
        """
        计算残差

        Args:
            exp_data: 实验数据
            sim_data: 仿真数据

        Returns:
            残差数组
        """
        min_len = min(len(exp_data), len(sim_data))
        return np.array(exp_data[:min_len]) - np.array(sim_data[:min_len])

    def analyze_per_frequency(self, df: pd.DataFrame, current_col: str,
                               response_cols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        按频率分析数据

        Args:
            df: DataFrame
            current_col: 电流列名
            response_cols: 响应列名列表

        Returns:
            {频率: {指标: 值}} 的字典
        """
        results = {}
        currents = df[current_col].values

        for col in response_cols:
            responses = df[col].values

            # 找到有效范围
            valid_mask = ~(np.isnan(currents) | np.isnan(responses))
            curr_valid = currents[valid_mask]
            resp_valid = responses[valid_mask]

            if len(curr_valid) == 0:
                continue

            # 计算统计
            stats = self.compute_statistics(resp_valid)

            # 提取频率信息
            freq = col
            for keyword in ['Hz', 'hz', 'freq', 'Freq']:
                if keyword in col:
                    parts = col.split(keyword)
                    if len(parts) > 1:
                        freq = parts[1].strip() if parts[1].strip() else parts[0].strip()
                        break

            results[freq] = stats

        return results


class DataExporter:
    """数据导出器"""

    @staticmethod
    def to_excel(df: pd.DataFrame, file_path: str, sheet_name: str = '数据',
                  include_index: bool = False) -> str:
        """
        导出为Excel

        Args:
            df: DataFrame
            file_path: 输出路径
            sheet_name: 工作表名
            include_index: 是否包含索引

        Returns:
            保存的文件路径
        """
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=include_index)

        return file_path

    @staticmethod
    def to_csv(df: pd.DataFrame, file_path: str, include_index: bool = False,
                encoding: str = 'utf-8-sig') -> str:
        """
        导出为CSV

        Args:
            df: DataFrame
            file_path: 输出路径
            include_index: 是否包含索引
            encoding: 编码格式

        Returns:
            保存的文件路径
        """
        df.to_csv(file_path, index=include_index, encoding=encoding)
        return file_path

    @staticmethod
    def to_json(data: Dict, file_path: str, indent: int = 2) -> str:
        """
        导出为JSON

        Args:
            data: 数据字典
            file_path: 输出路径
            indent: 缩进空格数

        Returns:
            保存的文件路径
        """
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return file_path

    @staticmethod
    def export_with_metadata(df: pd.DataFrame, file_path: str,
                              metadata: Dict[str, Any] = None) -> str:
        """
        导出带元数据的数据

        Args:
            df: DataFrame
            file_path: 输出路径
            metadata: 元数据

        Returns:
            保存的文件路径
        """
        export_data = {
            "metadata": metadata or {},
            "data": df.to_dict(orient='records'),
            "columns": list(df.columns),
        }

        ext = file_path.split('.')[-1].lower()
        if ext == 'json':
            return DataExporter.to_json(export_data, file_path)
        elif ext in ['xlsx', 'xls']:
            # Excel格式只导出数据
            return DataExporter.to_excel(df, file_path)
        else:
            return DataExporter.to_csv(df, file_path)
