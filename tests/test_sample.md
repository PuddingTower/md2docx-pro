# 设备健康度评估与预警技术报告

本报告汇总设备集群在最近一个评估周期内的健康度指标，并给出评分模型与预警阈值的实现说明。

## 1. 评估指标与对比结果

评估覆盖响应时延、连接成功率、并发能力与误报率四类指标，评分采用加权归一化模型。

### 1.1 关键指标对比

本次版本迭代前后的关键指标对比如下表所示：

表 1 版本迭代前后关键指标对比

| 评估指标 | 基线版本 | 优化版本 | 变化幅度 (%) | 评价结论 |
| :--- | :---: | :---: | :---: | :--- |
| 综合健康度评分 $H$ | 82.4 | 91.6 | +11.2% | 显著提升 |
| 平均响应时延 $T_{avg}$ | 128 | 96 | -25.0% | 明显改善 |
| 连接成功率 $P_{conn}$ | 98.2% | 99.6% | +1.4% | 稳定可靠 |
| 单机并发上限 $N_{\max}$ | 1200 | 1500 | +25.0% | 满足扩容 |
| 故障误报率 $R_{fp}$ | 3.1% | 1.8% | -42.0% | 显著下降 |

> **核心结论：**
> 时延与误报率同步下降，说明缓存命中策略与阈值整定有效；并发上限提升未引入新的稳定性风险。

## 2. 评分模型

健康度评分由可用性、性能与稳定性三个分量加权得到：

$$
\begin{aligned}
H &= w_a \cdot A + w_p \cdot P + w_s \cdot S \\
A &= P_{conn},\quad P = 1 - \frac{T_{avg}}{T_{\max}},\quad S = 1 - R_{fp}
\end{aligned}
$$

式中，$w_a$、$w_p$、$w_s$ 为权重系数，$T_{\max}$ 为可接受的最大响应时延。

## 3. 评分实现片段

以下为健康度计算与预警判定的核心逻辑：

```python
def health_score(conn, avg_latency, false_positive, weights=(0.4, 0.35, 0.25)):
    """按可用性、性能、稳定性加权计算健康度。"""
    availability = max(0.0, min(1.0, conn))
    performance = max(0.0, 1.0 - avg_latency / 500.0)
    stability = max(0.0, 1.0 - false_positive)
    score = sum(w * v for w, v in zip(weights, (availability, performance, stability)))
    return round(score * 100, 1)


def alert_level(score, warn=85.0, critical=70.0):
    if score >= warn:
        return "normal"
    return "warning" if score >= critical else "critical"
```

- 权重系数需与业务 SLA 对齐，变更后应重新标定
- 预警阈值采用双阈值策略，避免抖动导致频繁告警
- 评分与告警结果每日归档，用于回归分析
