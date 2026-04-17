"""
数据导入模块
==============
支持多种格式的数据导入：
- Excel (.xlsx, .xls)
- CSV (.csv) - 支持智能解析
- JSON (.json)
- 文本 (.txt)
"""

import os
import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class DataInfo:
    """数据信息"""
    filename: str
    file_path: str
    data_type: str  # "nerve" or "generic"
    shape: Tuple[int, int]
    columns: List[str]
    dtypes: Dict[str, str]
    preview: pd.DataFrame = None
    raw_data: pd.DataFrame = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 胫神经电刺激专用字段
    frequencies: List[float] = field(default_factory=list)
    pulse_width: float = 200e-6
    current_unit: str = "mA"


class NerveDataParser:
    """胫神经电刺激数据专用解析器"""

    # 数据格式模板
    FORMAT_TEMPLATES = [
        # 标准格式: 电流, Freq_10Hz, Freq_20Hz
        {
            'pattern': r'.*I_peak.*Freq.*',
            'columns': ['电流_mA', 'Freq_10Hz', 'Freq_20Hz']
        },
        # 多频率格式
        {
            'pattern': r'.*Freq.*Hz.*',
            'extract_freq': True
        },
        # 通用格式
        {
            'pattern': r'.*',
            'generic': True
        }
    ]

    @classmethod
    def parse_emg_file(cls, lines: List[str]) -> Tuple[pd.DataFrame, Dict]:
        """
        解析EMG响应数据文件

        标准格式:
        I_peak(mA),Freq_10Hz,Freq_20Hz
        5.0000,0.049514,0.051621
        ...
        """
        data_lines = []
        header_found = False
        columns = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            parts = [p.strip() for p in stripped.split(',')]

            if not header_found:
                # 尝试识别表头
                if cls._is_header(parts):
                    columns = cls._normalize_columns(parts)
                    header_found = True
                continue

            # 解析数据行
            if len(parts) >= 2:
                try:
                    row = [float(p) for p in parts]
                    data_lines.append(row)
                except ValueError:
                    continue

        if not columns:
            columns = [f'Col_{i}' for i in range(len(data_lines[0]) if data_lines else 1)]

        df = pd.DataFrame(data_lines, columns=columns[:len(data_lines[0]) if data_lines else 1])

        # 提取频率信息
        frequencies = cls._extract_frequencies(columns)
        metadata = {'frequencies': frequencies}

        return df, metadata

    @classmethod
    def parse_stim_params_file(cls, lines: List[str]) -> Tuple[pd.DataFrame, Dict]:
        """
        解析刺激参数文件

        标准格式:
        Parameter,Value,Unit
        PW,200,us
        Freqs,"5, 10, 15, 20",Hz

        I_peak_Sequence(mA)
        5.0000
        6.1000
        ...
        """
        params = {}
        current_sequence = []
        in_sequence = False
        parse_errors = []  # 收集解析错误

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            parts = [p.strip() for p in stripped.split(',')]

            # 参数行
            if parts[0] in ['Parameter', 'PW', 'Freqs', 'Freq']:
                if len(parts) >= 2:
                    if parts[0] == 'PW':
                        try:
                            params['pulse_width_us'] = float(parts[1])
                        except ValueError:
                            parse_errors.append(f"无法解析脉宽值: '{parts[1]}'")
                    elif parts[0] == 'Freqs':
                        # 解析频率列表
                        freq_str = parts[1].replace(' ', '')
                        try:
                            params['frequencies'] = [float(f) for f in freq_str.split(',')]
                        except ValueError:
                            parse_errors.append(f"无法解析频率列表: '{parts[1]}'")
                continue

            # 序列数据开始标记
            if 'I_peak' in stripped or 'Sequence' in stripped or in_sequence:
                if 'Sequence' in stripped:
                    in_sequence = True
                    continue
                try:
                    val = float(parts[0])
                    current_sequence.append(val)
                except ValueError:
                    if in_sequence:
                        in_sequence = False
                continue

        metadata = {
            'pulse_width': params.get('pulse_width_us', 200) * 1e-6,  # 转为秒
            'frequencies': params.get('frequencies', [10, 20]),
            'parse_errors': parse_errors,  # 添加错误信息
        }

        if current_sequence:
            df = pd.DataFrame({'电流_mA': current_sequence})
        else:
            df = pd.DataFrame()

        return df, metadata

    @classmethod
    def _is_header(cls, parts: List[str]) -> bool:
        """判断是否为表头行"""
        if not parts:
            return False

        # 非数字开头的列名
        header_keywords = ['i_peak', 'current', 'freq', 'hz', '响应', 'response', '电流']
        first_col = parts[0].lower()

        for keyword in header_keywords:
            if keyword in first_col:
                return True

        # 检查是否包含字符串（非数字）
        try:
            float(parts[0])
            return False
        except ValueError:
            return True

    @classmethod
    def _normalize_columns(cls, parts: List[str]) -> List[str]:
        """标准化列名"""
        columns = []
        for p in parts:
            p_lower = p.lower()

            # 电流列
            if 'i_peak' in p_lower or 'current' in p_lower or '电流' in p:
                columns.append('电流_mA')
            # 频率列
            elif 'freq' in p_lower or 'hz' in p_lower:
                # 提取频率值
                freq_match = re.search(r'(\d+(?:\.\d+)?)\s*hz', p_lower)
                if freq_match:
                    freq = freq_match.group(1)
                    columns.append(f'Freq_{freq}Hz')
                else:
                    columns.append(p)
            else:
                columns.append(p)

        return columns

    @classmethod
    def _extract_frequencies(cls, columns: List[str]) -> List[float]:
        """从列名中提取频率"""
        frequencies = []
        for col in columns:
            freq_match = re.search(r'(\d+(?:\.\d+)?)\s*hz', col.lower())
            if freq_match:
                frequencies.append(float(freq_match.group(1)))
        return frequencies


class DataImporter:
    """数据导入器"""

    def __init__(self):
        self.supported_formats = {
            ".xlsx": self._import_excel,
            ".xls": self._import_excel,
            ".csv": self._import_csv,
            ".json": self._import_json,
            ".txt": self._import_txt,
        }
        self.current_data: Optional[DataInfo] = None

    def import_file(self, file_path: str) -> DataInfo:
        """
        导入数据文件

        Args:
            file_path: 文件路径

        Returns:
            DataInfo: 数据信息对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = path.suffix.lower()
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {ext}")

        # 执行导入
        df, metadata = self.supported_formats[ext](file_path)

        # 自动检测数据类型
        data_type = self._detect_data_type(df)

        # 提取频率信息
        frequencies = metadata.get('frequencies', [])
        pulse_width = metadata.get('pulse_width', 200e-6)

        # 创建DataInfo
        data_info = DataInfo(
            filename=path.name,
            file_path=str(path),
            data_type=data_type,
            shape=df.shape,
            columns=list(df.columns),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            preview=df.head(100),
            raw_data=df,
            metadata=metadata,
            frequencies=frequencies,
            pulse_width=pulse_width,
            current_unit='mA',
        )

        self.current_data = data_info
        return data_info

    def import_nerve_data(self, emg_file: str, stim_file: str = None) -> DataInfo:
        """
        导入胫神经电刺激数据

        Args:
            emg_file: EMG响应数据文件
            stim_file: 刺激参数文件（可选）

        Returns:
            DataInfo: 数据信息对象
        """
        # 读取EMG文件
        with open(emg_file, 'r', encoding='utf-8-sig') as f:
            emg_lines = f.readlines()

        df, metadata = NerveDataParser.parse_emg_file(emg_lines)

        # 读取刺激参数文件
        if stim_file and os.path.exists(stim_file):
            with open(stim_file, 'r', encoding='utf-8-sig') as f:
                stim_lines = f.readlines()

            stim_df, stim_metadata = NerveDataParser.parse_stim_params_file(stim_lines)
            metadata.update(stim_metadata)

        # 检测数据类型
        data_type = 'nerve'

        data_info = DataInfo(
            filename=Path(emg_file).name,
            file_path=str(emg_file),
            data_type=data_type,
            shape=df.shape,
            columns=list(df.columns),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            preview=df.head(100),
            raw_data=df,
            metadata=metadata,
            frequencies=metadata.get('frequencies', []),
            pulse_width=metadata.get('pulse_width', 200e-6),
        )

        self.current_data = data_info
        return data_info

    def _import_excel(self, file_path: str) -> Tuple[pd.DataFrame, Dict]:
        """导入Excel文件"""
        try:
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names

            if len(sheets) == 1:
                df = pd.read_excel(file_path)
                metadata = {"sheet_names": sheets}
            else:
                df = pd.read_excel(file_path, sheet_name=sheets[0])
                metadata = {"sheet_names": sheets, "selected_sheet": sheets[0]}

            return df, metadata

        except Exception as e:
            raise ValueError(f"Excel文件读取失败: {str(e)}")

    def _import_csv(self, file_path: str) -> Tuple[pd.DataFrame, Dict]:
        """导入CSV文件"""
        try:
            # 读取原始内容用于分析
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            lines = content.strip().split('\n')

            # 检测是否为EMG响应数据格式
            if self._is_emg_format(lines):
                df, metadata = NerveDataParser.parse_emg_file(lines)
                return df, metadata

            # 检测是否为刺激参数格式
            if self._is_stim_params_format(lines):
                df, metadata = NerveDataParser.parse_stim_params_file(lines)
                return df, metadata

            # 标准CSV导入
            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    return df, {"encoding": encoding}
                except UnicodeDecodeError:
                    continue

            raise ValueError("无法识别CSV文件的编码格式")

        except Exception as e:
            raise ValueError(f"CSV文件读取失败: {str(e)}")

    def _is_emg_format(self, lines: List[str]) -> bool:
        """检测是否为EMG响应数据格式"""
        for line in lines[:10]:
            stripped = line.strip()
            if not stripped:
                continue
            if 'I_peak' in stripped and ('Freq' in stripped or 'Hz' in stripped):
                return True
        return False

    def _is_stim_params_format(self, lines: List[str]) -> bool:
        """检测是否为刺激参数格式"""
        for line in lines[:10]:
            if 'PW' in line or 'Freqs' in line:
                return True
        return False

    def _import_json(self, file_path: str) -> Tuple[pd.DataFrame, Dict]:
        """导入JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if "data" in data:
                    df = pd.DataFrame(data["data"])
                elif "records" in data:
                    df = pd.DataFrame(data["records"])
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError("JSON格式不支持")

            metadata = {"original_keys": list(data.keys()) if isinstance(data, dict) else None}
            return df, metadata

        except Exception as e:
            raise ValueError(f"JSON文件读取失败: {str(e)}")

    def _import_txt(self, file_path: str) -> Tuple[pd.DataFrame, Dict]:
        """导入文本文件"""
        try:
            # 读取原始内容
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            lines = content.strip().split('\n')

            # 尝试EMG格式
            if self._is_emg_format(lines):
                df, metadata = NerveDataParser.parse_emg_file(lines)
                return df, metadata

            # 尝试刺激参数格式
            if self._is_stim_params_format(lines):
                df, metadata = NerveDataParser.parse_stim_params_file(lines)
                return df, metadata

            # 尝试多种分隔符
            for sep in [',', '\t', ';', ' ']:
                try:
                    df = pd.read_csv(file_path, sep=sep, encoding='utf-8-sig')
                    if df.shape[1] > 1:
                        return df, {"separator": sep}
                except:
                    pass

            raise ValueError("无法解析文本文件格式")

        except Exception as e:
            raise ValueError(f"文本文件读取失败: {str(e)}")

    def _detect_data_type(self, df: pd.DataFrame) -> str:
        """
        自动检测数据类型

        Args:
            df: DataFrame

        Returns:
            "nerve" 或 "generic"
        """
        columns_lower = [col.lower() for col in df.columns]

        # 胫神经电刺激数据的特征列名
        nerve_keywords = ['电流', 'freq', 'hz', '响应', 'response', 'p_', 'p-', 'emg', '刺激']

        for keyword in nerve_keywords:
            if any(keyword in col for col in columns_lower):
                return "nerve"

        # 检查是否有数值型列且适合做曲线分析
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            return "nerve"

        return "generic"

    def get_current_data(self) -> Optional[DataInfo]:
        """获取当前数据"""
        return self.current_data

    def get_frequencies(self) -> List[float]:
        """获取当前数据的频率列表"""
        if self.current_data:
            return self.current_data.frequencies
        return []

    def get_response_columns(self) -> List[str]:
        """获取响应列"""
        if not self.current_data:
            return []

        columns = self.current_data.columns
        response_cols = []

        for col in columns:
            col_lower = col.lower()
            if 'freq' in col_lower or 'hz' in col_lower or '响应' in col:
                response_cols.append(col)

        return response_cols


class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_nerve_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        验证胫神经电刺激数据格式

        Args:
            df: DataFrame

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        if df.shape[1] < 2:
            errors.append("数据列数不足，至少需要2列")

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            errors.append("数据中至少需要2列数值数据")

        # 检查响应概率范围
        for col in df.columns:
            if col.lower().startswith('freq') or '响应' in col.lower():
                values = df[col].dropna()
                if len(values) > 0:
                    if values.min() < 0 or values.max() > 1.5:  # 允许少量超出1
                        errors.append(f"列 '{col}' 的值可能超出正常响应概率范围[0,1]")

        return len(errors) == 0, errors

    @staticmethod
    def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取数据摘要

        Args:
            df: DataFrame

        Returns:
            摘要信息字典
        """
        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_rows": df.duplicated().sum(),
        }

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe()
            summary["numeric_stats"] = stats.to_dict()

        return summary
