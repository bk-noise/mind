#ifndef BIT_OPS_H
#define BIT_OPS_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// 比特操作常量
// ============================================================

#define BITS_PER_BYTE    8
#define BITS_PER_WORD    32
#define BITS_PER_DWORD   64

// ============================================================
// 数据结构
// ============================================================

typedef struct {
    uint64_t timestamp_ns;
    uint32_t address;
    uint8_t  bit_position;
    uint8_t  direction;       // 0: 0→1, 1: 1→0
    uint8_t  padding[2];
} BitFlipEvent;

typedef struct {
    uint64_t total_events;
    uint64_t total_bytes_scanned;
    uint64_t flips_0_to_1;
    uint64_t flips_1_to_0;
    double   flip_rate;        // flips per byte per second
    double   entropy;
    uint32_t bit_distribution[8];
} BitFlipStats;

typedef struct {
    uint8_t  data[32];
    uint32_t size;
    uint32_t checksum;
} MemorySnapshot;

typedef struct {
    uint64_t pattern_id;
    uint64_t frequency;
    uint8_t  spatial_entropy;
    uint8_t  burstiness;
    uint8_t  bit_pattern[8];
    uint64_t timestamp;
} FeatureVector;

typedef struct {
    double eigenvalue;
    double stability;
    double strength;
    uint8_t converged;
} OriginFrequency;

// ============================================================
// 内存操作
// ============================================================

int scan_memory_region(
    const uint8_t* memory,
    size_t size,
    BitFlipEvent* events,
    size_t max_events,
    uint64_t timeout_ns
);

int compare_snapshots(
    const uint8_t* old_data,
    const uint8_t* new_data,
    size_t size,
    BitFlipEvent* events,
    size_t max_events
);

// ============================================================
// 比特级操作
// ============================================================

static inline uint8_t flip_bit(uint8_t* byte, uint8_t bit) {
    *byte ^= (1 << bit);
    return *byte;
}

static inline uint8_t get_bit(const uint8_t* byte, uint8_t bit) {
    return (*byte >> bit) & 1;
}

static inline void set_bit(uint8_t* byte, uint8_t bit, uint8_t value) {
    *byte = (*byte & ~(1 << bit)) | (value << bit);
}

static inline uint64_t get_bits(const uint64_t* word, uint8_t start, uint8_t count) {
    uint64_t mask = (count >= 64) ? ~0ULL : ((1ULL << count) - 1);
    return (*word >> start) & mask;
}

static inline void set_bits(uint64_t* word, uint8_t start, uint8_t count, uint64_t value) {
    uint64_t mask = (count >= 64) ? ~0ULL : ((1ULL << count) - 1);
    *word = (*word & ~(mask << start)) | ((value & mask) << start);
}

// ============================================================
// 模式检测
// ============================================================

uint64_t find_bit_pattern(
    const uint8_t* data,
    size_t size,
    const uint8_t* pattern,
    size_t pattern_size
);

int detect_burst_pattern(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t* burst_start,
    uint32_t* burst_length
);

double calculate_entropy(
    const uint8_t* data,
    size_t size
);

void compute_spatial_distribution(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t region_count,
    uint32_t* distribution
);

// ============================================================
// 特征提取
// ============================================================

void extract_features(
    const BitFlipEvent* events,
    size_t event_count,
    FeatureVector* features
);

double compare_features(
    const FeatureVector* f1,
    const FeatureVector* f2
);

// ============================================================
// 本源计算
// ============================================================

void compute_origin_frequency(
    const FeatureVector* history,
    size_t history_size,
    OriginFrequency* origin
);

double compute_eigenvalue(
    const double* matrix,
    size_t size
);

// ============================================================
// 抉择过滤
// ============================================================

int filter_choices(
    const double* origin_vector,
    size_t dim,
    const double* candidates,
    size_t candidate_count,
    double threshold,
    int* valid_indices,
    size_t max_valid
);

double compute_similarity(
    const double* v1,
    const double* v2,
    size_t dim
);

// ============================================================
// 编码/解码
// ============================================================

void encode_events(
    const BitFlipEvent* events,
    size_t event_count,
    uint8_t* output,
    size_t* output_size
);

size_t decode_events(
    const uint8_t* input,
    size_t input_size,
    BitFlipEvent* events,
    size_t max_events
);

uint32_t crc32_checksum(
    const uint8_t* data,
    size_t size
);

// ============================================================
// 内存分配
// ============================================================

void* allocate_aligned_memory(size_t size, size_t alignment);

void free_aligned_memory(void* ptr);

#ifdef __cplusplus
}
#endif

#endif // BIT_OPS_H