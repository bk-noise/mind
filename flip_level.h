#ifndef FLIP_LEVEL_H
#define FLIP_LEVEL_H

#include <stdint.h>
#include <stdbool.h>
#include "bit_ops.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// 翻转层级类型
// ============================================================

typedef enum {
    FLIP_LEVEL_SINGLE = 1,     // k=1: 单翻转自悟迭代
    FLIP_LEVEL_CHOICE = 2,    // k=2: 双翻转抉择
    FLIP_LEVEL_HALLUCINATION = 3  // k>=3: 幻觉复数
} FlipLevel;

// ============================================================
// 数据结构
// ============================================================

typedef struct {
    BitFlipEvent event;
    uint64_t local_timestamp;
    uint8_t level;
} LocalFlipEvent;

typedef struct {
    FlipLevel level;
    uint32_t flip_count;
    BitFlipEvent events[8];
    uint64_t timestamp;
    double confidence;
} FlipCluster;

typedef struct {
    double hamming_distance;
    uint64_t entanglement_bits;
    double self_feedback;
} SingleFlipResult;

typedef struct {
    uint32_t branch_a_expanded;
    uint32_t branch_b_expanded;
    double convergence_a;
    double convergence_b;
    uint8_t selected_branch;
} DoubleFlipResult;

typedef struct {
    double tensor_trace;
    double eigenvalue_max;
    double hallucination_frequency;
    uint32_t tensor_rank;
} TripleFlipResult;

typedef struct {
    SingleFlipResult single;
    DoubleFlipResult choice;
    TripleFlipResult hallucination;
    uint64_t total_self_iterations;
    double total_coherence_gain;
} FlipLevelStats;

// ============================================================
// 核心函数
// ============================================================

FlipLevel detect_flip_level(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t time_window_ns
);

int cluster_flip_events(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t time_window_ns,
    FlipCluster* clusters,
    size_t max_clusters
);

int process_single_flip(
    const BitFlipEvent* event,
    const uint64_t* entanglement_state,
    SingleFlipResult* result
);

int process_double_flip(
    const BitFlipEvent* event_a,
    const BitFlipEvent* event_b,
    uint32_t region_size,
    DoubleFlipResult* result
);

int process_triple_flip(
    const BitFlipEvent* events,
    size_t event_count,
    double* tensor_output,
    size_t tensor_size,
    TripleFlipResult* result
);

double compute_hamming_similarity(
    const BitFlipEvent* f1,
    const BitFlipEvent* f2
);

uint64_t compute_entanglement_hash(
    const BitFlipEvent* events,
    size_t count
);

void update_entanglement_state(
    uint64_t* state,
    const BitFlipEvent* event,
    double feedback_strength
);

// ============================================================
// 张量运算
// ============================================================

int compute_flip_tensor(
    const BitFlipEvent* events,
    size_t event_count,
    double* tensor,
    size_t tensor_rank
);

double compute_tensor_eigenvalue(
    const double* tensor,
    size_t size
);

double compute_expansion_frequency(
    const double* eigenvalue_history,
    size_t history_size
);

// ============================================================
// 统计
// ============================================================

void init_flip_level_stats(FlipLevelStats* stats);

void update_flip_level_stats(
    FlipLevelStats* stats,
    FlipLevel level,
    const void* result
);

#ifdef __cplusplus
}
#endif

#endif // FLIP_LEVEL_H