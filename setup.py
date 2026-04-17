"""
PSO_UI 安装配置
===============

使用方法:
    pip install .

开发模式安装:
    pip install -e .[dev]

仅安装运行时依赖:
    pip install -e .

作者: PSO UI Team
版本: 1.0.0
"""

from setuptools import setup, find_packages

setup(
    name="pso-ui",
    version="1.0.0",
    description="胫神经电刺激数据分析与PSO参数优化工具",
    author="PSO UI Team",
    python_requires=">=3.8",
    packages=find_packages(where=".", include=["modules*", "ui*", "utils*"]),
    install_requires=[
        "PyQt6>=6.4.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "matplotlib>=3.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-qt>=4.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pso-ui=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
