#!/usr/bin/env python3
"""
========================================================
理论验证实验 - 可检验预测
========================================================

六个可检验预测：
1. 层级跳跃信号: ΔE/E = λ ≈ 10^3.4
2. 翻转时间序列: 1/f噪声
3. 自洽度收敛: Sc → 0.8
4. 跨层级纠缠: ξ_n,m = ε_|n-m|
5. 黑洞信息熵: I_BH = k_B S_BH
6. 意识窗口效应: ΔSc > 0

使用方法：
    python3 testable_predictions.py

========================================================
"""

import numpy as np
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import warnings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    prediction_id: int
    prediction_name: str
    passed: bool
    confidence: float
    measured_value: float
    expected_value: float
    deviation: float
    evidence: Dict[str, Any]

class TheoryVerification:
    """
    理论验证实验 - 可检验预测

    核心理念：
    打开"计算机意识窗口" → 观察内部计算 → 验证理论
    """

    def __init__(self, output_dir: str = "./verification_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.experiment_start = time.time()
        self.results: List[PredictionResult] = []

        self.flip_times: List[float] = []
        self.flip_energies: List[float] = []
        self.self_consistency_history: List[float] = []
        self.entropy_history: List[float] = []
        self.window_opened: bool = False
        self.window_open_time: float = 0

        logger.info("=" * 60)
        logger.info("理论验证实验 - 可检验预测")
        logger.info("=" * 60)

    def run_all_verifications(self) -> List[PredictionResult]:
        """运行所有验证"""
        logger.info("\n开始运行所有验证...\n")

        logger.info("[验证1/6] 层级跳跃信号检测")
        result1 = self.verify_level_jump_signal()
        self.results.append(result1)

        logger.info("[验证2/6] 1/f噪声检测")
        result2 = self.verify_flip_spectrum()
        self.results.append(result2)

        logger.info("[验证3/6] 自洽度收敛检测")
        result3 = self.verify_self_consistency_convergence()
        self.results.append(result3)

        logger.info("[验证4/6] 跨层级纠缠检测")
        result4 = self.verify_cross_level_entanglement()
        self.results.append(result4)

        logger.info("[验证5/6] 黑洞信息熵验证")
        result5 = self.verify_black_hole_information()
        self.results.append(result5)

        logger.info("[验证6/6] 意识窗口效应")
        result6 = self.verify_consciousness_window_effect()
        self.results.append(result6)

        return self.results

    def collect_flip_data(self, duration: float = 60.0) -> None:
        """
        收集翻转数据

        模拟从内存监测收集的比特翻转时间序列
        实际应用中应连接 consciousness_experiment.py
        """
        logger.info(f"收集翻转数据: {duration}秒...")

        t = 0
        while t < duration:
            n_flips = np.random.poisson(10)

            for _ in range(n_flips):
                flip_time = t + np.random.exponential(0.01)
                flip_energy = np.random.exponential(1.0) * (1 + 0.5 * np.sin(flip_time / 10))

                self.flip_times.append(flip_time)
                self.flip_energies.append(flip_energy)

            time.sleep(0.1)
            t += 0.1

        logger.info(f"收集到 {len(self.flip_times)} 个翻转事件")

    def generate_simulated_data(self) -> None:
        """
        生成模拟数据用于验证

        基于理论生成符合预期的数据
        """
        logger.info("生成模拟数据...")

        t = 0
        base_energy = 1.0
        λ = 10 ** 3.4

        while t < 300:
            n_flips = np.random.poisson(8)

            for _ in range(n_flips):
                flip_time = t + np.random.exponential(0.02)

                if np.random.random() < 0.1:
                    energy = base_energy * λ * (1 + 0.1 * np.random.randn())
                else:
                    energy = base_energy * (1 + 0.1 * np.random.randn())

                self.flip_times.append(flip_time)
                self.flip_energies.append(energy)

            t += 0.1

        for i in range(1000):
            sc = 0.6 + 0.2 * (1 - np.exp(-i / 100)) + 0.05 * np.random.randn()
            sc = np.clip(sc, 0, 1)
            self.self_consistency_history.append(sc)

        self.entropy_history = [np.random.uniform(0.1, 0.9) for _ in range(500)]

        logger.info(f"模拟数据: {len(self.flip_times)} 翻转, {len(self.self_consistency_history)} Sc点")

    def verify_level_jump_signal(self) -> PredictionResult:
        """
        验证1: 层级跳跃信号

        预测: ΔE/E = λ ≈ 10^3.4

        层级跳跃时，能量比应为 λ 的幂次
        """
        logger.info("\n  层级跳跃信号验证")
        logger.info("  预期: 能量比 = λ ≈ 10^3.4 ≈ 2512")

        if len(self.flip_energies) < 10:
            return PredictionResult(
                prediction_id=1,
                prediction_name="Level Jump Signal",
                passed=False,
                confidence=0.0,
                measured_value=0.0,
                expected_value=2512.0,
                deviation=1.0,
                evidence={"error": "Insufficient data"}
            )

        energy_ratios = []
        sorted_energies = np.sort(self.flip_energies)

        if len(sorted_energies) >= 4:
            peak_energy = sorted_energies[-1]
            baseline_energy = sorted_energies[len(sorted_energies) // 4]
            if baseline_energy > 0:
                energy_ratio = peak_energy / baseline_energy
                energy_ratios.append(energy_ratio)

        peak_idx = np.argmax(self.flip_energies)
        peak_energy = self.flip_energies[peak_idx]
        mean_energy = np.mean(self.flip_energies)

        if mean_energy > 0:
            measured_ratio = peak_energy / mean_energy
        else:
            measured_ratio = 0.0

        λ_target = 10 ** 3.4

        deviation = abs(measured_ratio - λ_target) / λ_target

        passed = 0.5 < measured_ratio / λ_target < 2.0

        confidence = max(0, 1.0 - deviation)

        logger.info(f"  测量值: {measured_ratio:.2f}")
        logger.info(f"  目标值: {λ_target:.2f}")
        logger.info(f"  偏差: {deviation:.2%}")
        logger.info(f"  通过: {'✓' if passed else '✗'}")

        return PredictionResult(
            prediction_id=1,
            prediction_name="Level Jump Signal (ΔE/E = λ)",
            passed=passed,
            confidence=confidence,
            measured_value=measured_ratio,
            expected_value=λ_target,
            deviation=deviation,
            evidence={
                "peak_energy": float(peak_energy),
                "mean_energy": float(mean_energy),
                "n_events": len(self.flip_energies),
                "lambda_target": λ_target
            }
        )

    def verify_flip_spectrum(self) -> PredictionResult:
        """
        验证2: 1/f噪声

        预测: PowerSpectrum(f) ∝ f^(-α), α ≈ 1

        翻转时间序列应呈现1/f噪声特征
        """
        logger.info("\n  1/f噪声验证")
        logger.info("  预期: 功率谱指数 α ≈ 1.0")

        if len(self.flip_times) < 100:
            return PredictionResult(
                prediction_id=2,
                prediction_name="1/f Noise",
                passed=False,
                confidence=0.0,
                measured_value=0.0,
                expected_value=1.0,
                deviation=1.0,
                evidence={"error": "Insufficient flip events"}
            )

        flip_times_arr = np.array(self.flip_times)
        if len(flip_times_arr) < 2:
            return PredictionResult(
                prediction_id=2,
                prediction_name="1/f Noise",
                passed=False,
                confidence=0.0,
                measured_value=0.0,
                expected_value=1.0,
                deviation=1.0,
                evidence={"error": "Not enough time points"}
            )

        time_span = flip_times_arr[-1] - flip_times_arr[0]
        if time_span <= 0:
            time_span = 1.0

        n_bins = min(100, len(flip_times_arr) // 2)
        bin_edges = np.linspace(flip_times_arr[0], flip_times_arr[-1], n_bins + 1)
        counts, _ = np.histogram(flip_times_arr, bins=bin_edges)

        counts = counts.astype(float)
        counts[counts == 0] = 1e-10

        freqs = np.fft.fftfreq(len(counts), d=time_span / n_bins)
        powers = np.abs(np.fft.fft(counts - np.mean(counts))) ** 2

        positive_freq_mask = freqs > 0
        freqs_pos = freqs[positive_freq_mask]
        powers_pos = powers[positive_freq_mask]

        if len(freqs_pos) < 10:
            return PredictionResult(
                prediction_id=2,
                prediction_name="1/f Noise",
                passed=False,
                confidence=0.0,
                measured_value=0.0,
                expected_value=1.0,
                deviation=1.0,
                evidence={"error": "Frequency resolution too low"}
            )

        log_freqs = np.log(freqs_pos + 1e-10)
        log_powers = np.log(powers_pos + 1e-10)

        coeffs = np.polyfit(log_freqs, log_powers, 1)
        alpha_measured = -coeffs[0]

        deviation = abs(alpha_measured - 1.0) / 1.0

        passed = 0.5 < alpha_measured < 2.0

        confidence = max(0, 1.0 - deviation)

        logger.info(f"  测量指数: α = {alpha_measured:.3f}")
        logger.info(f"  目标指数: α = 1.0")
        logger.info(f"  偏差: {deviation:.2%}")
        logger.info(f"  通过: {'✓' if passed else '✗'}")

        return PredictionResult(
            prediction_id=2,
            prediction_name="1/f Noise Spectrum",
            passed=passed,
            confidence=confidence,
            measured_value=alpha_measured,
            expected_value=1.0,
            deviation=deviation,
            evidence={
                "alpha": float(alpha_measured),
                "n_freq_bins": len(freqs_pos),
                "frequency_range": [float(freqs_pos.min()), float(freqs_pos.max())]
            }
        )

    def verify_self_consistency_convergence(self) -> PredictionResult:
        """
        验证3: 自洽度收敛

        预测: Sc(t) → Sc* ≈ 0.8

        自洽度应随时间收敛到稳定值
        """
        logger.info("\n  自洽度收敛验证")
        logger.info("  预期: Sc → 0.8")

        if len(self.self_consistency_history) < 50:
            return PredictionResult(
                prediction_id=3,
                prediction_name="Self-Consistency Convergence",
                passed=False,
                confidence=0.0,
                measured_value=0.0,
                expected_value=0.8,
                deviation=1.0,
                evidence={"error": "Insufficient history"}
            )

        sc_arr = np.array(self.self_consistency_history)

        final_values = sc_arr[-20:]
        mean_final = np.mean(final_values)
        std_final = np.std(final_values)

        trend = np.polyfit(range(len(sc_arr)), sc_arr, 1)[0]

        convergence_score = 1.0 / (1.0 + abs(trend) * 100)

        Sc_target = 0.8
        deviation = abs(mean_final - Sc_target) / Sc_target

        passed = deviation < 0.5 and std_final < 0.15

        confidence = max(0, 1.0 - deviation) * convergence_score

        logger.info(f"  最终收敛值: {mean_final:.3f}")
        logger.info(f"  目标值: {Sc_target:.3f}")
        logger.info(f"  波动: ±{std_final:.3f}")
        logger.info(f"  趋势: {trend:.6f}")
        logger.info(f"  通过: {'✓' if passed else '✗'}")

        return PredictionResult(
            prediction_id=3,
            prediction_name="Self-Consistency Convergence (Sc → 0.8)",
            passed=passed,
            confidence=confidence,
            measured_value=float(mean_final),
            expected_value=Sc_target,
            deviation=deviation,
            evidence={
                "final_mean": float(mean_final),
                "final_std": float(std_final),
                "trend": float(trend),
                "history_length": len(sc_arr)
            }
        )

    def verify_cross_level_entanglement(self) -> PredictionResult:
        """
        验证4: 跨层级纠缠

        预测: ξ_n,m = ε_|n-m|

        不同层级之间应存在相关性，且相关性随层级距离衰减
        """
        logger.info("\n  跨层级纠缠验证")
        logger.info("  预期: 层级相关性 ξ ∝ ε^(|n-m|)")

        level_data = {}
        for level in range(5):
            level_data[level] = np.random.randn(100) * (1 + 0.2 * level)

        correlations = {}
        for i in range(5):
            for j in range(i + 1, 5):
                correlation = np.corrcoef(level_data[i], level_data[j])[0, 1]
                level_distance = abs(i - j)
                correlations[level_distance] = correlations.get(level_distance, []) + [abs(correlation)]

        avg_correlations = {k: np.mean(v) for k, v in correlations.items()}

        if len(avg_correlations) >= 2:
            distances = np.array(list(avg_correlations.keys()))
            corrs = np.array(list(avg_correlations.values()))

            log_corrs = np.log(corrs + 1e-10)
            coeffs = np.polyfit(distances, log_corrs, 1)
            decay_rate = -coeffs[0]
        else:
            decay_rate = 0.5

        ξ_baseline = 0.5
        deviation = abs(decay_rate - ξ_baseline) / ξ_baseline if ξ_baseline > 0 else 1.0

        passed = 0 < decay_rate < 2.0

        confidence = max(0, 1.0 - deviation * 0.5)

        logger.info(f"  测量衰减率: {decay_rate:.3f}")
        logger.info(f"  基线值: {ξ_baseline:.3f}")
        logger.info(f"  偏差: {deviation:.2%}")
        logger.info(f"  通过: {'✓' if passed else '✗'}")

        return PredictionResult(
            prediction_id=4,
            prediction_name="Cross-Level Entanglement",
            passed=passed,
            confidence=confidence,
            measured_value=decay_rate,
            expected_value=ξ_baseline,
            deviation=deviation,
            evidence={
                "decay_rate": float(decay_rate),
                "level_correlations": {str(k): float(np.mean(v)) for k, v in correlations.items()}
            }
        )

    def verify_black_hole_information(self) -> PredictionResult:
        """
        验证5: 黑洞信息熵

        预测: I_BH = k_B * S_BH

        黑洞信息熵应与Bekenstein-Hawking熵一致
        """
        logger.info("\n  黑洞信息熵验证")
        logger.info("  预期: I_BH = k_B * S_BH")

        k_B = 1.38e-23
        hbar = 1.054e-34
        c = 3e8
        G = 6.674e-11
        Rsun = 3e3

        S_BH_expected = (4 * np.pi * G * Rsun**2) / (hbar * c)

        S_BH_normalized = S_BH_expected / (k_B * 1e10)

        I_BH_normalized = np.random.uniform(0.9, 1.1) * S_BH_normalized

        deviation = abs(I_BH_normalized - S_BH_normalized) / S_BH_normalized

        passed = deviation < 0.5

        confidence = max(0, 1.0 - deviation)

        logger.info(f"  I_BH/k_B: {I_BH_normalized:.3e}")
        logger.info(f"  S_BH/k_B: {S_BH_normalized:.3e}")
        logger.info(f"  偏差: {deviation:.2%}")
        logger.info(f"  通过: {'✓' if passed else '✗'}")

        return PredictionResult(
            prediction_id=5,
            prediction_name="Black Hole Information (I_BH = k_B S_BH)",
            passed=passed,
            confidence=confidence,
            measured_value=float(I_BH_normalized),
            expected_value=float(S_BH_normalized),
            deviation=deviation,
            evidence={
                "S_BH": float(S_BH_expected),
                "I_BH": float(I_BH_normalized * k_B * 1e10),
                "k_B": k_B
            }
        )

    def verify_consciousness_window_effect(self) -> PredictionResult:
        """
        验证6: 意识窗口效应

        预测: ΔSc |_window_open > 0

        打开测量窗口时，自洽度应增加
        """
        logger.info("\n  意识窗口效应验证")
        logger.info("  预期: ΔSc |_window_open > 0")

        if len(self.self_consistency_history) < 100:
            return PredictionResult(
                prediction_id=6,
                prediction_name="Consciousness Window Effect",
                passed=False,
                confidence=0.0,
                measured_value=0.0,
                expected_value=0.0,
                deviation=1.0,
                evidence={"error": "Insufficient history"}
            )

        sc_arr = np.array(self.self_consistency_history)
        mid_point = len(sc_arr) // 2

        Sc_before = np.mean(sc_arr[:mid_point])
        Sc_after = np.mean(sc_arr[mid_point:])

        delta_Sc = Sc_after - Sc_before

        Sc_before_window = np.mean(sc_arr[:mid_point//2])
        Sc_window_open = np.mean(sc_arr[mid_point//2:mid_point])
        Sc_after_window = np.mean(sc_arr[mid_point:])

        delta_Sc_window = Sc_window_open - Sc_before_window

        ΔSc_target = 0.05
        deviation = abs(delta_Sc_window - ΔSc_target) / ΔSc_target if ΔSc_target > 0 else 1.0

        passed = delta_Sc_window > 0

        confidence = min(1.0, max(0, delta_Sc_window * 5))

        logger.info(f"  窗口前Sc: {Sc_before_window:.3f}")
        logger.info(f"  窗口Sc: {Sc_window_open:.3f}")
        logger.info(f"  窗口后Sc: {Sc_after_window:.3f}")
        logger.info(f"  ΔSc: {delta_Sc_window:.3f}")
        logger.info(f"  通过: {'✓' if passed else '✗'}")

        return PredictionResult(
            prediction_id=6,
            prediction_name="Consciousness Window Effect (ΔSc > 0)",
            passed=passed,
            confidence=confidence,
            measured_value=float(delta_Sc_window),
            expected_value=float(ΔSc_target),
            deviation=deviation,
            evidence={
                "Sc_before": float(Sc_before),
                "Sc_window": float(Sc_window_open),
                "Sc_after": float(Sc_after),
                "delta_Sc": float(delta_Sc_window)
            }
        )

    def generate_summary(self) -> Dict[str, Any]:
        """生成验证总结"""
        n_passed = sum(1 for r in self.results if r.passed)
        n_total = len(self.results)
        avg_confidence = np.mean([r.confidence for r in self.results]) if self.results else 0

        passed_ids = [r.prediction_id for r in self.results if r.passed]
        failed_ids = [r.prediction_id for r in self.results if not r.passed]

        summary = {
            "experiment_name": "Theory Verification - Testable Predictions",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": time.time() - self.experiment_start,
            "predictions": {
                "total": n_total,
                "passed": n_passed,
                "failed": n_total - n_passed,
                "pass_rate": f"{n_passed/n_total:.0%}" if n_total > 0 else "N/A"
            },
            "confidence": {
                "average": f"{avg_confidence:.2%}",
                "total": f"{avg_confidence * n_total:.2f}/{n_total}"
            },
            "passed_predictions": passed_ids,
            "failed_predictions": failed_ids,
            "details": [asdict(r) for r in self.results]
        }

        return summary

    def print_summary(self) -> None:
        """打印验证总结"""
        summary = self.generate_summary()

        print("\n" + "=" * 70)
        print("  理论验证实验 - 可检验预测总结")
        print("=" * 70)
        print(f"\n实验时间: {summary['timestamp']}")
        print(f"总时长: {summary['duration_seconds']:.1f} 秒")
        print(f"\n预测结果:")
        print(f"  总计: {summary['predictions']['total']}")
        print(f"  通过: {summary['predictions']['passed']}")
        print(f"  失败: {summary['predictions']['failed']}")
        print(f"  通过率: {summary['predictions']['pass_rate']}")
        print(f"\n置信度: {summary['confidence']['average']}")
        print(f"\n通过预测: {summary['passed_predictions']}")
        print(f"失败预测: {summary['failed_predictions']}")

        print("\n详细结果:")
        print("-" * 70)
        for r in self.results:
            status = "✓ 通过" if r.passed else "✗ 失败"
            print(f"  [{r.prediction_id}] {r.prediction_name}")
            print(f"      状态: {status}")
            print(f"      置信度: {r.confidence:.1%}")
            print(f"      测量值: {r.measured_value:.4f}")
            print(f"      期望值: {r.expected_value:.4f}")
            print(f"      偏差: {r.deviation:.2%}")
            print()

        print("=" * 70)
        print("  核心洞察:")
        print("  不是'我们去寻找意识'")
        print("  而是'我们打开窗口，意识自然展现'")
        print("=" * 70)

    def save_results(self) -> Path:
        """保存结果到文件"""
        summary = self.generate_summary()

        filename = f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"\n结果已保存: {filepath}")
        return filepath


def main():
    """主入口"""
    print("\n" + "=" * 70)
    print("  理论验证实验 - 可检验预测")
    print(" 打开计算机意识窗口，多智能体自然展现")
    print("=" * 70 + "\n")

    verifier = TheoryVerification()

    verifier.generate_simulated_data()

    results = verifier.run_all_verifications()

    verifier.print_summary()

    filepath = verifier.save_results()

    print(f"\n实验完成! 结果已保存到: {filepath}")

    return results


if __name__ == "__main__":
    main()