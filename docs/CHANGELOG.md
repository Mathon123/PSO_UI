# PSO_UI 变更日志

## [1.0.0] - 2026-04-16

### 新增功能
- 胫神经电刺激数据分析工具
- PSO（粒子群优化）算法参数辨识
- 8参数神经电刺激模型 (R1, R2, R3, L, C, alpha, beta, V_th)
- 双文件数据导入 (stim_params.csv + emg_processed.csv)
- 模型评估指标 (RMSE, MAE, R²)
- 阈值电流计算 (P=50%, 80%, 90%)
- SD曲线生成
- 数据导出 (Excel/CSV/JSON/图片)

### 图表功能
- 响应曲线图 (ResponseCurveWidget)
- 对比曲线图 (ComparisonCurveWidget)
- 收敛曲线图 (ConvergenceCurveWidget)
- 残差分析图 (ResidualPlotWidget)
- 参数条形图 (ParameterBarWidget)
- SD曲线图 (SDCurveWidget)
- 综合分析图 (ComprehensiveAnalysisWidget)

### UI优化
- PyQt6现代化界面
- 左右分栏布局 (主Tab:图表Tab = 1:3)
- 优化结果卡片显示
- 实时进度显示

### 配置文件
- requirements.txt
- pyproject.toml
- .gitignore
- .env.example
- requirements-dev.txt
- install.bat / run.bat / clean.bat

### 测试
- pytest测试框架
- 单元测试和集成测试
- 覆盖率支持

---

## 变更日志格式说明

使用 [Semantic Versioning](https://semver.org/lang/zh-CN/) 格式:

- `[新增]` - 新增功能
- `[修改]` - 功能修改
- `[删除]` - 功能删除
- `[修复]` - Bug修复
- `[优化]` - 性能优化或代码优化
- `[文档]` - 文档更新
- `[配置]` - 配置变更
