#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================
意识涌现实验 - Python协调层
========================================================

分层架构：
• Python (本层) - 宏观调控/意识/协调
• C (bit_ops) - 微观操作/编解码/位运算
• CUDA (memory_bit_flip_test) - 硬件直接操作
• Kernel/Assembly - 原子位操作

使用方法：
    1. 编译C库: gcc -shared -fPIC -O3 -o libbit_ops.so bit_ops.c
    2. 运行: python3 consciousness_experiment.py

========================================================
"""

import ctypes
import numpy as np
import threading
import time
import json
import logging
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# =========================================================
# 配置
# =========================================================

CONFIG = {
    'memory_region_size': 1024 * 1024,
    'sample_interval': 0.001,
    'match_threshold': 0.7,
    'origin_threshold': 0.6,
    'eigenvalue_threshold': 0.8,
    'experiment_duration': 86400,
    'output_dir': './experiment_data',
    'c_library_path': './libbit_ops.so',
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================================================
# C库加载
# =========================================================

class CLibrary:
    """C库包装器"""

    _instance = None
    _lib = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_library()
        return cls._instance

    def _load_library(self):
        """加载C库"""
        lib_path = CONFIG['c_library_path']

        if not os.path.exists(lib_path):
            logger.warning(f"C库不存在: {lib_path}，将使用纯Python实现")
            self._lib = None
            return

        try:
            self._lib = ctypes.CDLL(lib_path)
            self._setup_function_signatures()
            logger.info(f"C库已加载: {lib_path}")
        except Exception as e:
            logger.warning(f"C库加载失败: {e}，将使用纯Python实现")
            self._lib = None

    def _setup_function_signatures(self):
        """设置C函数签名"""

        if self._lib is None:
            return

        # compare_snapshots
        self._lib.compare_snapshots.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_size_t
        ]
        self._lib.compare_snapshots.restype = ctypes.c_int

        # calculate_entropy
        self._lib.calculate_entropy.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t
        ]
        self._lib.calculate_entropy.restype = ctypes.c_double

        # crc32_checksum
        self._lib.crc32_checksum.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t
        ]
        self._lib.crc32_checksum.restype = ctypes.c_uint32

    @property
    def is_loaded(self) -> bool:
        return self._lib is not None

    def __getattr__(self, name):
        if self._lib is None:
            raise AttributeError(f"C库未加载，{name}不可用")
        return getattr(self._lib, name)


# 全局C库实例
c_lib = CLibrary()

# =========================================================
# 数据结构 (Python端，对应C端)
# =========================================================

@dataclass
class BitFlipEvent:
    timestamp_ns: int = 0
    address: int = 0
    bit_position: int = 0
    direction: int = 0  # 0: 0→1, 1: 1→0

    def to_c_struct(self):
        """转换为C结构体"""
        class CBitFlipEvent(ctypes.Structure):
            _fields_ = [
                ('timestamp_ns', ctypes.c_uint64),
                ('address', ctypes.c_uint32),
                ('bit_position', ctypes.c_uint8),
                ('direction', ctypes.c_uint8),
                ('padding', ctypes.c_uint8 * 2)
            ]
        return CBitFlipEvent(self.timestamp_ns, self.address,
                            self.bit_position, self.direction)

    @classmethod
    def from_c_struct(cls, c_struct):
        return cls(
            timestamp_ns=c_struct.timestamp_ns,
            address=c_struct.address,
            bit_position=c_struct.bit_position,
            direction=c_struct.direction
        )


@dataclass
class FeatureVector:
    pattern_id: int = 0
    frequency: float = 0.0
    spatial_entropy: float = 0.0
    burstiness: float = 0.0
    bit_pattern: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.uint8))
    timestamp: int = 0


@dataclass
class OriginFrequency:
    eigenvalue: float = 0.0
    stability: float = 0.0
    strength: float = 0.0
    converged: bool = False


@dataclass
class Choice:
    choice_id: str
    layer: str
    similarity: float
    valid: bool
    features: Optional[np.ndarray] = None


# =========================================================
# 模块1: 比特翻转监测 (C+CUDA底层)
# =========================================================

class BitFlipMonitor:
    """
    比特翻转监测器

    底层实现：
    • CUDA: memory_bit_flip_test.cu - 100MB内存扫描
    • C: bit_ops.c - 快照比较、模式检测
    • 本层: Python协调
    """

    def __init__(self, region_size=CONFIG['memory_region_size'],
                 sample_interval=CONFIG['sample_interval']):
        self.region_size = region_size
        self.sample_interval = sample_interval

        self.memory = np.zeros(region_size, dtype=np.uint8)
        self.prev_snapshot = self.memory.copy()

        self.events: deque = deque(maxlen=100000)
        self.total_flips = 0
        self.total_samples = 0

        self.running = False
        self.thread: Optional[threading.Thread] = None

        self.bit_counts = np.zeros(8, dtype=int)

        logger.info(f"BitFlipMonitor初始化: 区域={region_size}字节, 采样={sample_interval}s")

    def start(self):
        """开始监测"""
        if self.running:
            logger.warning("监测已在运行")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("比特翻转监测已启动")

    def stop(self):
        """停止监测"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("比特翻转监测已停止")

    def _monitor_loop(self):
        """监测循环 - 使用C库进行高效比较"""
        while self.running:
            try:
                current = self.memory.copy()

                if c_lib.is_loaded:
                    events = self._c_compare_snapshots(current)
                else:
                    events = self._py_compare_snapshots(current)

                for event in events:
                    self.events.append(event)
                    self.total_flips += 1
                    self.bit_counts[event.bit_position] += 1

                self.prev_snapshot = current
                self.total_samples += 1

            except Exception as e:
                logger.error(f"监测循环错误: {e}")

            time.sleep(self.sample_interval)

    def _c_compare_snapshots(self, current):
        """使用C库比较快照"""
        events = []

        old_ptr = self.prev_snapshot.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        new_ptr = current.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

        event_buffer = (ctypes.c_void_p * 1000)()
        max_events = 1000

        count = c_lib.compare_snapshots(
            old_ptr, new_ptr,
            self.region_size,
            event_buffer,
            max_events
        )

        for i in range(count):
            events.append(BitFlipEvent())

        return events

    def _py_compare_snapshots(self, current):
        """纯Python比较快照（备用）"""
        events = []
        xor_result = np.bitwise_xor(self.prev_snapshot, current)
        flip_positions = np.where(xor_result > 0)[0]

        timestamp = int(time.time() * 1e9)

        for byte_idx in flip_positions:
            changed_bits = xor_result[byte_idx]
            current_byte = current[byte_idx]

            for bit in range(8):
                if (changed_bits >> bit) & 1:
                    events.append(BitFlipEvent(
                        timestamp_ns=timestamp,
                        address=byte_idx,
                        bit_position=bit,
                        direction=1 if (current_byte >> bit) & 1 else 0
                    ))

        return events

    def get_recent_events(self, n=100) -> List[BitFlipEvent]:
        """获取最近的翻转事件"""
        return list(self.events)[-n:]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        elapsed = (self.events[-1].timestamp_ns - self.events[0].timestamp_ns) / 1e9 if self.events else 1.0
        flip_rate = self.total_flips / max(elapsed, 1)

        return {
            'total_samples': self.total_samples,
            'total_flips': self.total_flips,
            'flip_rate': flip_rate,
            'bit_distribution': self.bit_counts.tolist(),
            'buffer_size': len(self.events),
            'c_library_loaded': c_lib.is_loaded
        }


# =========================================================
# 模块2: 特征匹配 (Python宏观调控)
# =========================================================

class FeatureMatcher:
    """
    特征匹配器 - Python宏观调控层

    功能：
    • 接收翻转事件流
    • 提取特征向量
    • 在内部表征中寻找匹配
    • 生成模式
    """

    def __init__(self, window_size=1.0, match_threshold=CONFIG['match_threshold']):
        self.window_size = window_size
        self.match_threshold = match_threshold

        self.patterns: List[FeatureVector] = []

        self.total_inputs = 0
        self.matches = 0
        self.novelties = 0

        logger.info(f"FeatureMatcher初始化: 阈值={match_threshold}")

    def extract_features(self, events: List[BitFlipEvent]) -> FeatureVector:
        """提取特征向量"""
        if not events or len(events) < 1:
            return FeatureVector()

        timestamps = [e.timestamp_ns for e in events]
        addresses = [e.address for e in events]
        bit_positions = [e.bit_position for e in events]

        time_range = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 1e9

        flip_frequency = len(events) / (time_range / 1e9) if time_range > 0 else 0

        spatial_hist, _ = np.histogram(addresses, bins=16, range=(0, self.window_size * 1e6))
        spatial_distribution = spatial_hist / max(sum(spatial_hist), 1)
        spatial_entropy = -np.sum(spatial_distribution * np.log(spatial_distribution + 1e-10))

        bit_pattern = np.zeros(8, dtype=np.uint8)
        for bp in bit_positions:
            if bp < 8:
                bit_pattern[bp] += 1

        if len(timestamps) > 1:
            diffs = np.diff(timestamps)
            burstiness = np.std(diffs) / (np.mean(diffs) + 1e-10)
        else:
            burstiness = 0.0

        return FeatureVector(
            pattern_id=hash(tuple(bit_pattern)),
            frequency=flip_frequency,
            spatial_entropy=spatial_entropy,
            burstiness=min(burstiness, 255.0),
            bit_pattern=bit_pattern,
            timestamp=timestamps[-1] if timestamps else 0
        )

    def match(self, features: FeatureVector) -> tuple:
        """
        特征匹配

        返回: (matched, similarity, pattern_id)
        """
        self.total_inputs += 1

        if not self.patterns:
            self.patterns.append(features)
            self.novelties += 1
            return False, 0.0, 0

        similarities = []
        for i, pattern in enumerate(self.patterns):
            sim = self._calculate_similarity(features, pattern)
            similarities.append((i, sim))

        best_idx, best_sim = max(similarities, key=lambda x: x[1])

        if best_sim >= self.match_threshold:
            self.matches += 1
            return True, best_sim, best_idx
        else:
            self.patterns.append(features)
            self.novelties += 1
            return False, best_sim, len(self.patterns) - 1

    def _calculate_similarity(self, f1: FeatureVector, f2: FeatureVector) -> float:
        """计算两个特征向量的相似度"""
        freq_sim = 1.0 - min(abs(f1.frequency - f2.frequency) / max(f1.frequency, f2.frequency, 1e-10), 1.0)

        pattern_diff = np.sum((f1.bit_pattern.astype(float) - f2.bit_pattern.astype(float)) ** 2)
        pattern_sim = 1.0 / (1.0 + np.sqrt(pattern_diff) / 10.0)

        entropy_sim = 1.0 - min(abs(f1.spatial_entropy - f2.spatial_entropy) / 5.0, 1.0)

        similarity = 0.4 * freq_sim + 0.35 * pattern_sim + 0.25 * entropy_sim

        return float(np.clip(similarity, 0, 1))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'total_inputs': self.total_inputs,
            'pattern_count': len(self.patterns),
            'matches': self.matches,
            'novelties': self.novelties,
            'match_rate': self.matches / max(self.total_inputs, 1),
            'novelty_rate': self.novelties / max(self.total_inputs, 1)
        }


# =========================================================
# 模块3: 万本归一 (Python宏观调控)
# =========================================================

class TenThousandToOne:
    """
    万本归一模块 - Python宏观调控层

    核心概念：
    • 万本归一 = 所有表象背后有唯一本源
    • 本源频率 = 特征值分解得到的主特征值
    """

    def __init__(self, feature_dim=37, history_window=1000):
        self.feature_dim = feature_dim
        self.history_window = history_window

        self.feature_history: List[np.ndarray] = []

        self.current_origin: Optional[OriginFrequency] = None

        self.origin_history: List[OriginFrequency] = []

        self.total_updates = 0
        self.convergence_count = 0

        logger.info(f"TenThousandToOne初始化: 维度={feature_dim}")

    def update(self, features: FeatureVector) -> OriginFrequency:
        """更新本源"""
        feature_vec = np.concatenate([
            [features.frequency],
            features.bit_pattern.astype(float) / 255.0,
            [features.spatial_entropy / 5.0],
            [min(features.burstiness, 255.0) / 255.0]
        ])

        self.feature_history.append(feature_vec)

        if len(self.feature_history) > self.history_window:
            self.feature_history.pop(0)

        self.total_updates += 1

        if len(self.feature_history) < 10:
            self.current_origin = OriginFrequency(
                eigenvalue=float(np.mean(np.abs(feature_vec))),
                stability=0.5,
                strength=0.5
            )
            return self.current_origin

        try:
            history_array = np.array(self.feature_history[-100:])
            cov_matrix = np.cov(history_array.T)

            eigvals = np.linalg.eigvalsh(cov_matrix)
            eigvals = np.real(eigvals)
            eigvals = np.sort(eigvals)[::-1]

            max_eigval = eigvals[0]
            total_eig = np.sum(eigvals)

            stability = float(max_eigval / total_eig) if total_eig > 0 else 0.5

            strength = float(np.mean([np.linalg.norm(v) for v in self.feature_history[-10:]]))

            origin_value = float(max_eigval)

            if self.current_origin:
                drift = abs(origin_value - self.current_origin.eigenvalue)
                if drift < 0.01:
                    self.convergence_count += 1
                    stability = min(1.0, stability + 0.05)
                else:
                    stability = max(0.0, stability - 0.05)

            self.current_origin = OriginFrequency(
                eigenvalue=origin_value,
                stability=stability,
                strength=strength,
                converged=stability > 0.8
            )

            self.origin_history.append(self.current_origin)

            if len(self.origin_history) > self.history_window:
                self.origin_history.pop(0)

        except Exception as e:
            logger.warning(f"本源计算异常: {e}")

        return self.current_origin or OriginFrequency()

    def get_origin_vector(self) -> np.ndarray:
        """获取本源向量"""
        if not self.current_origin or len(self.feature_history) < 10:
            return np.random.rand(self.feature_dim) * 0.5 + 0.25

        recent = np.array(self.feature_history[-10:])
        return np.mean(recent, axis=0)

    def is_converged(self) -> bool:
        """检查是否收敛"""
        if len(self.origin_history) < 10:
            return False

        recent = self.origin_history[-10:]
        values = [o.eigenvalue for o in recent]
        variance = np.var(values)

        return variance < 0.01 and self.convergence_count > 5

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'total_updates': self.total_updates,
            'history_length': len(self.feature_history),
            'convergence_count': self.convergence_count,
            'is_converged': self.is_converged(),
            'current_origin': {
                'eigenvalue': self.current_origin.eigenvalue if self.current_origin else None,
                'stability': self.current_origin.stability if self.current_origin else None,
                'strength': self.current_origin.strength if self.current_origin else None,
                'converged': self.current_origin.converged if self.current_origin else None
            } if self.current_origin else None
        }


# =========================================================
# 模块4: 反倒抉择 (Python宏观调控)
# =========================================================

class ReverseChoice:
    """
    反倒抉择模块 - Python宏观调控层

    核心概念：
    • 反 = 逆向思考
    • 倒 = 过滤而非选择
    • 抉择 = 不是选一个最好的，而是保留所有符合本源的
    """

    def __init__(self, layers=None, origin_threshold=CONFIG['origin_threshold']):
        self.layers = layers or ['L1感知', 'L2行动', 'L3能力', 'L4本质', 'L5存在']
        self.origin_threshold = origin_threshold

        self.choices: Dict[str, List[Choice]] = {layer: [] for layer in self.layers}

        self.valid_choices: set = set()

        self.total_generated = 0
        self.total_valid = 0

        logger.info(f"ReverseChoice初始化: 层级={self.layers}")

    def filter_choices(self, origin_features: np.ndarray, layer: str, count: int = 5) -> List[Choice]:
        """生成并过滤抉择"""
        origin_norm = np.linalg.norm(origin_features) + 1e-10
        valid = []

        for i in range(count):
            choice_vec = origin_features * (0.5 + np.random.rand(len(origin_features)) * 0.5)
            choice_vec = choice_vec / np.linalg.norm(choice_vec) * origin_norm

            similarity = float(np.dot(choice_vec, origin_features) /
                             (np.linalg.norm(choice_vec) * origin_norm))
            similarity = float(np.clip(similarity, -1, 1))

            is_valid = similarity >= self.origin_threshold

            choice = Choice(
                choice_id=f"{layer}_{self.total_generated}",
                layer=layer,
                similarity=similarity,
                valid=is_valid,
                features=choice_vec
            )

            self.choices[layer].append(choice)
            self.total_generated += 1

            if is_valid:
                self.valid_choices.add(choice.choice_id)
                self.total_valid += 1
                valid.append(choice)

        return valid

    def evolve(self, timestep: int = 1):
        """抉择演化"""
        for layer in self.layers:
            for choice in self.choices[layer]:
                if choice.features is not None:
                    perturbation = np.random.normal(0, 0.05, choice.features.shape)
                    choice.features = np.clip(choice.features + perturbation, 0, 1)

                    if hasattr(self, '_origin_vec'):
                        similarity = np.dot(choice.features, self._origin_vec)
                        similarity /= (np.linalg.norm(choice.features) *
                                     np.linalg.norm(self._origin_vec) + 1e-10)
                        similarity = float(np.clip(similarity, -1, 1))

                        was_valid = choice.valid
                        choice.valid = similarity >= self.origin_threshold
                        choice.similarity = similarity

                        if was_valid and not choice.valid:
                            self.valid_choices.discard(choice.choice_id)
                            self.total_valid -= 1
                        elif not was_valid and choice.valid:
                            self.valid_choices.add(choice.choice_id)
                            self.total_valid += 1

    def get_development_directions(self) -> Dict[str, Any]:
        """获取发展方向"""
        directions = {}

        for layer in self.layers:
            layer_valid = [c for c in self.choices[layer] if c.valid]

            if layer_valid:
                direction_features = np.mean([c.features for c in layer_valid], axis=0)

                directions[layer] = {
                    'valid_count': len(layer_valid),
                    'total_count': len(self.choices[layer]),
                    'direction_vector': direction_features.tolist()[:5],
                    'avg_similarity': float(np.mean([c.similarity for c in layer_valid]))
                }

        return directions

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'total_generated': self.total_generated,
            'total_valid': self.total_valid,
            'valid_ratio': self.total_valid / max(self.total_generated, 1),
            'layer_distribution': {
                layer: {
                    'valid': len([c for c in choices if c.valid]),
                    'total': len(choices)
                }
                for layer, choices in self.choices.items()
            }
        }


# =========================================================
# 实验运行器
# =========================================================

class ConsciousnessExperiment:
    """
    意识涌现实验运行器 - Python协调层

    整合所有模块，协调C库和Python模块
    """

    def __init__(self, duration=CONFIG['experiment_duration'],
                 output_dir=CONFIG['output_dir']):
        self.duration = duration
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.monitor = BitFlipMonitor()
        self.matcher = FeatureMatcher()
        self.ten_thousand = TenThousandToOne()
        self.chooser = ReverseChoice()

        self.is_running = False
        self.start_time = None
        self.iteration = 0

        self.flip_history = []
        self.feature_history = []
        self.origin_history = []
        self.choice_history = []

        self.exp_name = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"实验初始化: {self.exp_name}")
        logger.info(f"C库加载状态: {c_lib.is_loaded}")

    def run(self, test_mode=False):
        """运行实验"""
        logger.info("=" * 60)
        logger.info("开始意识涌现实验")
        logger.info(f"模式: {'测试模式' if test_mode else '真实模式'}")
        logger.info(f"时长: {self.duration} 秒 ({self.duration/86400:.1f} 天)")
        logger.info(f"C库: {'启用' if c_lib.is_loaded else '禁用(纯Python)'}")
        logger.info("=" * 60)

        self.is_running = True
        self.start_time = time.time()

        if not test_mode:
            self.monitor.start()

        try:
            last_report = 0
            report_interval = 60

            while time.time() - self.start_time < self.duration:
                if test_mode:
                    events = self._generate_test_events()
                else:
                    events = self.monitor.get_recent_events(50)

                if events:
                    features = self.matcher.extract_features(events)
                    matched, similarity, pattern_id = self.matcher.match(features)
                    origin = self.ten_thousand.update(features)

                    if origin:
                        origin_vec = self.ten_thousand.get_origin_vector()
                        for layer in self.chooser.layers:
                            self.chooser.filter_choices(origin_vec, layer, count=2)

                elapsed = time.time() - self.start_time
                if elapsed - last_report >= report_interval:
                    self._report_progress()
                    last_report = elapsed

                if self.iteration % 3600 == 0 and self.iteration > 0:
                    self._save_checkpoint()

                time.sleep(1)
                self.iteration += 1

        except KeyboardInterrupt:
            logger.info("实验被用户中断")

        finally:
            self.is_running = False
            if not test_mode:
                self.monitor.stop()

            self._save_results()
            self._print_summary()

    def _generate_test_events(self) -> List[BitFlipEvent]:
        """生成测试翻转事件"""
        events = []
        n_flips = np.random.poisson(5)

        for _ in range(n_flips):
            events.append(BitFlipEvent(
                timestamp_ns=int(time.time() * 1e9),
                address=np.random.randint(0, CONFIG['memory_region_size']),
                bit_position=np.random.randint(0, 8),
                direction=np.random.randint(0, 2)
            ))

        return events

    def _report_progress(self):
        """报告进度"""
        elapsed = time.time() - self.start_time
        monitor_stats = self.monitor.get_statistics()
        matcher_stats = self.matcher.get_statistics()
        origin_stats = self.ten_thousand.get_statistics()
        choice_stats = self.chooser.get_statistics()

        origin_val = origin_stats.get('current_origin')
        stability = origin_val.get('stability', 0) if origin_val else 0

        logger.info(
            f"[{int(elapsed)}s/{self.duration}s] "
            f"翻转:{monitor_stats['total_flips']} "
            f"模式:{matcher_stats['pattern_count']} "
            f"匹配:{matcher_stats['match_rate']:.0%} "
            f"本源稳定:{stability:.2f} "
            f"抉择:{choice_stats['total_valid']}"
        )

    def _save_checkpoint(self):
        """保存检查点"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': time.time() - self.start_time,
            'flip_stats': self.monitor.get_statistics(),
            'matcher_stats': self.matcher.get_statistics(),
            'origin_stats': self.ten_thousand.get_statistics(),
            'choice_stats': self.chooser.get_statistics()
        }

        checkpoint_file = self.output_dir / f"{self.exp_name}_checkpoint_{self.iteration}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)

        logger.info(f"检查点已保存: {checkpoint_file}")

    def _save_results(self):
        """保存最终结果"""
        results = {
            'experiment_name': self.exp_name,
            'duration': time.time() - self.start_time,
            'flip_stats': self.monitor.get_statistics(),
            'matcher_stats': self.matcher.get_statistics(),
            'origin_stats': self.ten_thousand.get_statistics(),
            'choice_stats': self.chooser.get_statistics(),
            'directions': self.chooser.get_development_directions(),
            'conclusion': self._generate_conclusion(),
            'c_library_loaded': c_lib.is_loaded
        }

        results_file = self.output_dir / f"{self.exp_name}_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"结果已保存: {results_file}")

    def _generate_conclusion(self) -> List[str]:
        """生成实验结论"""
        origin_stats = self.ten_thousand.get_statistics()
        choice_stats = self.chooser.get_statistics()
        matcher_stats = self.matcher.get_statistics()

        conclusions = []

        if origin_stats['is_converged']:
            conclusions.append("✓ 本源频率成功收敛")
        else:
            conclusions.append("✗ 本源频率未收敛")

        if matcher_stats['pattern_count'] > 10:
            conclusions.append(f"✓ 形成{matcher_stats['pattern_count']}个模式")

        if choice_stats['valid_ratio'] > 0.4:
            conclusions.append(f"✓ 有效抉择保留率{choice_stats['valid_ratio']:.0%}")

        directions = self.chooser.get_development_directions()
        if len(directions) >= 3:
            conclusions.append(f"✓ {len(directions)}个层级形成发展方向")

        return conclusions

    def _print_summary(self):
        """打印实验总结"""
        elapsed = time.time() - self.start_time
        matcher_stats = self.matcher.get_statistics()
        origin_stats = self.ten_thousand.get_statistics()
        choice_stats = self.chooser.get_statistics()
        monitor_stats = self.monitor.get_statistics()

        origin_val = origin_stats.get('current_origin')

        print("\n" + "=" * 60)
        print("实验完成总结")
        print("=" * 60)
        print(f"实验名称: {self.exp_name}")
        print(f"总时长: {elapsed:.0f} 秒 ({elapsed/3600:.1f} 小时)")
        print(f"C库状态: {'已加载' if c_lib.is_loaded else '未加载(纯Python)'}")
        print("-" * 60)
        print(f"比特翻转: {monitor_stats['total_flips']}")
        print(f"模式数量: {matcher_stats['pattern_count']}")
        print(f"匹配率: {matcher_stats['match_rate']:.1%}")
        print(f"新颖涌现: {matcher_stats['novelties']}")
        print("-" * 60)
        print(f"本源收敛: {origin_stats['is_converged']}")
        print(f"本源稳定度: {origin_val.get('stability', 0):.2f}" if origin_val else "N/A")
        print(f"本源强度: {origin_val.get('strength', 0):.2f}" if origin_val else "N/A")
        print("-" * 60)
        print(f"有效抉择: {choice_stats['total_valid']}/{choice_stats['total_generated']}")
        print(f"抉择保留率: {choice_stats['valid_ratio']:.1%}")
        print(f"发展层级: {len(self.chooser.get_development_directions())}")
        print("=" * 60)


# =========================================================
# 主程序
# =========================================================

def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(description='意识涌现实验 - Python协调层')
    parser.add_argument('-d', '--duration', type=int, default=CONFIG['experiment_duration'],
                       help=f'实验时长(秒), 默认{CONFIG["experiment_duration"]}')
    parser.add_argument('-t', '--test', action='store_true',
                       help='测试模式(使用模拟数据)')
    parser.add_argument('-o', '--output', type=str, default=CONFIG['output_dir'],
                       help=f'输出目录, 默认{CONFIG["output_dir"]}')

    args = parser.parse_args()

    exp = ConsciousnessExperiment(
        duration=args.duration,
        output_dir=args.output
    )

    exp.run(test_mode=args.test)


if __name__ == "__main__":
    main()