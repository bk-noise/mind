#!/bin/bash
# ============================================================
# 分层架构编译脚本
# ============================================================

set -e

echo "=== 分层架构编译 ==="

# 编译C库
echo "1. 编译C微观操作库..."
gcc -shared -fPIC -O3 -march=native -o libbit_ops.so bit_ops.c
echo "   完成: libbit_ops.so"

# 编译CUDA程序
echo "2. 编译CUDA比特翻转检测..."
if command -v nvcc &> /dev/null; then
    nvcc -O3 -o memory_bit_flip_test memory_bit_flip_test.cu
    echo "   完成: memory_bit_flip_test"
else
    echo "   警告: nvcc未找到，跳过CUDA编译"
fi

echo ""
echo "=== 编译完成 ==="
echo ""
echo "运行方式:"
echo "  测试模式: python3 consciousness_experiment.py -t"
echo "  真实模式: python3 consciousness_experiment.py -d 86400"
echo ""
echo "分层架构:"
echo "  Python层: consciousness_experiment.py (宏观调控)"
echo "  C层:      libbit_ops.so (微观操作)"
echo "  CUDA层:   memory_bit_flip_test (硬件直接操作)"
echo "  汇编层:   bit_atomic.h (原子位操作)"