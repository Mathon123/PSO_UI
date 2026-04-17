# PSO数据分析工具

胫神经电刺激数据分析与PSO（粒子群优化）参数辨识工具。

## 项目概述

本工具是一款专门用于胫神经电刺激实验数据分析的桌面应用程序。通过集成PSO优化算法，实现对神经电刺激模型的8个物理参数（R1, R2, R3, L, C, alpha, beta, V_th）进行自动辨识。

## 核心功能

- **数据导入**：支持CSV/Excel格式的EMG数据，支持双文件导入（stim_params.csv + emg_processed.csv）
- **PSO优化**：自适应粒子群优化算法，智能参数辨识
- **模型评估**：RMSE、MAE、R²等多维度指标评估
- **阈值计算**：计算达到目标响应概率所需的刺激电流
- **SD曲线生成**：刺激-剂量曲线可视化
- **多图表分析**：响应曲线、收敛曲线、对比曲线、残差分析等

## 技术架构

```
├── main.py              # 主程序入口
├── ui/                  # UI层
│   ├── main_window.py   # 主窗口
│   ├── chart_widgets.py # 图表组件
│   └── analysis_workflow.py # 分析工作流
├── modules/             # 业务逻辑层
│   ├── pso_optimizer.py    # PSO优化器
│   ├── nerve_model.py      # 神经电刺激模型
│   ├── data_importer.py    # 数据导入
│   ├── data_processor.py   # 数据处理
│   ├── visualization.py    # 图表工厂
│   └── config.py           # 配置
└── tests/               # 单元测试
```

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI框架 | PyQt6 >= 6.4.0 |
| 数值计算 | NumPy >= 1.24.0 |
| 科学计算 | SciPy >= 1.10.0 |
| 数据处理 | Pandas >= 2.0.0 |
| 可视化 | Matplotlib >= 3.7.0 |
| Excel支持 | openpyxl >= 3.1.0 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 使用流程

1. 点击"导入数据"按钮，选择EMG数据文件
2. 查看数据预览和统计信息
3. 设置PSO参数（粒子数、迭代次数、目标RMSE）
4. 点击"运行PSO优化"开始参数辨识
5. 查看优化结果和拟合质量
6. 导出数据或图表

## 数据格式要求

### EMG数据文件 (emg_processed.csv)

| 列名 | 说明 | 示例 |
|------|------|------|
| I_peak(mA) | 峰值电流 | 1.0, 2.0, 3.0... |
| Freq_10Hz | 10Hz频率响应 | 0.1, 0.2, 0.3... |
| Freq_20Hz | 20Hz频率响应 | 0.15, 0.25, 0.35... |

### 刺激参数文件 (stim_params.csv)

```
PW,200
Freqs,"10, 20"
```

## 文档

- [用户手册](docs/用户手册.md) - 详细使用说明
- [开发者文档](docs/开发者文档.md) - API接口文档
- [快速开始指南](docs/快速开始.md) - 快速入门
- [常见问题](docs/常见问题.md) - FAQ

## 项目结构

```
PSO_UI/
├── main.py                          # 主入口
├── requirements.txt                 # 依赖清单
├── PSO数据分析工具_技术设计文档.md  # 技术设计文档
│
├── ui/                              # UI层
│   ├── __init__.py
│   ├── main_window.py              # 主窗口类
│   ├── chart_widgets.py            # 图表组件
│   └── analysis_workflow.py        # 分析工作流
│
├── modules/                         # 业务逻辑层
│   ├── __init__.py
│   ├── config.py                    # 配置
│   ├── pso_optimizer.py            # PSO优化器
│   ├── nerve_model.py               # 神经模型
│   ├── data_importer.py             # 数据导入
│   ├── data_processor.py            # 数据处理
│   └── visualization.py            # 图表工厂
│
├── utils/                           # 工具层
│   └── __init__.py
│
├── tests/                           # 测试
│   ├── test_pso_optimizer.py
│   ├── test_nerve_model.py
│   ├── test_data_processor.py
│   └── test_integration.py
│
└── docs/                            # 文档目录
    ├── 用户手册.md
    ├── 开发者文档.md
    ├── 快速开始.md
    └── 常见问题.md
```

## 版本信息

- 当前版本：1.0.0
- 更新日期：2026-04-15

## 许可

本项目仅供科研使用。