#include "bit_ops.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ============================================================
// 内存操作
// ============================================================

int scan_memory_region(
    const uint8_t* memory,
    size_t size,
    BitFlipEvent* events,
    size_t max_events,
    uint64_t timeout_ns
) {
    if (!memory || !events || size == 0 || max_events == 0) {
        return -1;
    }

    uint64_t start_time = 0;
    size_t event_count = 0;

    for (size_t i = 0; i < size && event_count < max_events; i++) {
        if (timeout_ns > 0 && start_time >= timeout_ns) {
            break;
        }

        for (int bit = 0; bit < 8 && event_count < max_events; bit++) {
            events[event_count].timestamp_ns = start_time;
            events[event_count].address = (uint32_t)i;
            events[event_count].bit_position = (uint8_t)bit;
            events[event_count].direction = (memory[i] >> bit) & 1;
            events[event_count].padding[0] = 0;
            events[event_count].padding[1] = 0;
            event_count++;
        }

        start_time += 1000; // 1us per byte
    }

    return (int)event_count;
}

int compare_snapshots(
    const uint8_t* old_data,
    const uint8_t* new_data,
    size_t size,
    BitFlipEvent* events,
    size_t max_events
) {
    if (!old_data || !new_data || !events) {
        return -1;
    }

    size_t event_count = 0;
    uint64_t timestamp = 0;

    for (size_t i = 0; i < size && event_count < max_events; i++) {
        uint8_t diff = old_data[i] ^ new_data[i];

        for (int bit = 0; bit < 8 && event_count < max_events; bit++) {
            if (diff & (1 << bit)) {
                events[event_count].timestamp_ns = timestamp;
                events[event_count].address = (uint32_t)i;
                events[event_count].bit_position = (uint8_t)bit;
                events[event_count].direction = (new_data[i] >> bit) & 1;
                events[event_count].padding[0] = 0;
                events[event_count].padding[1] = 0;
                event_count++;
            }
        }

        timestamp += 1000; // 1us
    }

    return (int)event_count;
}

// ============================================================
// 模式检测
// ============================================================

uint64_t find_bit_pattern(
    const uint8_t* data,
    size_t size,
    const uint8_t* pattern,
    size_t pattern_size
) {
    if (!data || !pattern || size < pattern_size) {
        return 0;
    }

    for (size_t i = 0; i <= size - pattern_size; i++) {
        bool match = true;
        for (size_t j = 0; j < pattern_size; j++) {
            if (data[i + j] != pattern[j]) {
                match = false;
                break;
            }
        }
        if (match) {
            return (uint64_t)i;
        }
    }

    return 0;
}

int detect_burst_pattern(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t* burst_start,
    uint32_t* burst_length
) {
    if (!events || event_count < 2) {
        return -1;
    }

    uint32_t max_burst_start = 0;
    uint32_t max_burst_length = 1;
    uint32_t current_start = 0;
    uint32_t current_length = 1;

    for (size_t i = 1; i < event_count; i++) {
        uint64_t time_diff = events[i].timestamp_ns - events[i-1].timestamp_ns;

        if (time_diff < 10000) { // 10us threshold for burst
            current_length++;
        } else {
            if (current_length > max_burst_length) {
                max_burst_length = current_length;
                max_burst_start = current_start;
            }
            current_start = (uint32_t)i;
            current_length = 1;
        }
    }

    if (current_length > max_burst_length) {
        max_burst_length = current_length;
        max_burst_start = current_start;
    }

    if (burst_start) *burst_start = max_burst_start;
    if (burst_length) *burst_length = max_burst_length;

    return (int)(max_burst_length > 1 ? 0 : 1);
}

double calculate_entropy(const uint8_t* data, size_t size) {
    if (!data || size == 0) {
        return 0.0;
    }

    uint32_t count[256] = {0};

    for (size_t i = 0; i < size; i++) {
        count[data[i]]++;
    }

    double entropy = 0.0;
    for (int i = 0; i < 256; i++) {
        if (count[i] > 0) {
            double p = (double)count[i] / (double)size;
            entropy -= p * log2(p);
        }
    }

    return entropy;
}

void compute_spatial_distribution(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t region_count,
    uint32_t* distribution
) {
    if (!events || !distribution || region_count == 0) {
        return;
    }

    memset(distribution, 0, region_count * sizeof(uint32_t));

    uint32_t max_addr = 0;
    for (size_t i = 0; i < event_count; i++) {
        if (events[i].address > max_addr) {
            max_addr = events[i].address;
        }
    }

    if (max_addr == 0) max_addr = 1;

    uint32_t region_size = (max_addr + 1) / region_count;
    if (region_size == 0) region_size = 1;

    for (size_t i = 0; i < event_count; i++) {
        uint32_t region = events[i].address / region_size;
        if (region >= region_count) region = region_count - 1;
        distribution[region]++;
    }
}

// ============================================================
// 特征提取
// ============================================================

void extract_features(
    const BitFlipEvent* events,
    size_t event_count,
    FeatureVector* features
) {
    if (!events || !features || event_count == 0) {
        memset(features, 0, sizeof(FeatureVector));
        return;
    }

    // Frequency
    uint64_t time_span = events[event_count - 1].timestamp_ns - events[0].timestamp_ns;
    features->frequency = (time_span > 0) ?
        (double)event_count / ((double)time_span / 1e9) : 0.0;

    // Bit distribution
    memset(features->bit_pattern, 0, 8);
    for (size_t i = 0; i < event_count; i++) {
        if (events[i].bit_position < 8) {
            features->bit_pattern[events[i].bit_position]++;
        }
    }

    // Spatial entropy (simplified)
    uint32_t spatial_hist[16] = {0};
    for (size_t i = 0; i < event_count; i++) {
        uint32_t bucket = (events[i].address % 16);
        spatial_hist[bucket]++;
    }

    double entropy = 0.0;
    for (int i = 0; i < 16; i++) {
        if (spatial_hist[i] > 0) {
            double p = (double)spatial_hist[i] / (double)event_count;
            entropy -= p * log2(p + 1e-10);
        }
    }
    features->spatial_entropy = (uint8_t)(entropy * 10);

    // Burstiness
    if (event_count > 1) {
        uint64_t total_gap = 0;
        for (size_t i = 1; i < event_count; i++) {
            total_gap += events[i].timestamp_ns - events[i-1].timestamp_ns;
        }
        uint64_t avg_gap = total_gap / (event_count - 1);
        features->burstiness = (avg_gap > 1000000) ? 0 : (uint8_t)(255 - (avg_gap / 4000));
    } else {
        features->burstiness = 0;
    }

    // Pattern ID (hash of bit distribution)
    uint64_t hash = 0;
    for (int i = 0; i < 8; i++) {
        hash = hash * 31 + features->bit_pattern[i];
    }
    features->pattern_id = hash;
    features->timestamp = events[event_count - 1].timestamp_ns;
}

double compare_features(
    const FeatureVector* f1,
    const FeatureVector* f2
) {
    if (!f1 || !f2) {
        return 0.0;
    }

    // Frequency similarity
    double freq_max = f1->frequency > f2->frequency ? f1->frequency : f2->frequency;
    double freq_sim = (freq_max > 0) ?
        1.0 - fabs(f1->frequency - f2->frequency) / freq_max : 0.0;

    // Bit pattern similarity
    double pattern_diff = 0.0;
    for (int i = 0; i < 8; i++) {
        int d = (int)f1->bit_pattern[i] - (int)f2->bit_pattern[i];
        pattern_diff += (double)(d * d);
    }
    double pattern_sim = 1.0 / (1.0 + sqrt(pattern_diff) / 100.0);

    // Entropy similarity
    double entropy_diff = fabs((double)f1->spatial_entropy - (double)f2->spatial_entropy);
    double entropy_sim = 1.0 - entropy_diff / 25.5;

    // Weighted combination
    return 0.4 * freq_sim + 0.35 * pattern_sim + 0.25 * entropy_sim;
}

// ============================================================
// 本源计算
// ============================================================

void compute_origin_frequency(
    const FeatureVector* history,
    size_t history_size,
    OriginFrequency* origin
) {
    if (!history || !origin || history_size < 2) {
        if (origin) {
            origin->eigenvalue = 0.5;
            origin->stability = 0.5;
            origin->strength = 0.5;
            origin->converged = 0;
        }
        return;
    }

    // Build covariance matrix (simplified 3x3)
    double sum_f = 0.0, sum_e = 0.0, sum_b = 0.0;
    double sum_f2 = 0.0, sum_e2 = 0.0, sum_b2 = 0.0;
    double sum_fe = 0.0, sum_fb = 0.0, sum_eb = 0.0;

    for (size_t i = 0; i < history_size; i++) {
        double f = history[i].frequency;
        double e = history[i].spatial_entropy;
        double b = history[i].burstiness;

        sum_f += f; sum_e += e; sum_b += b;
        sum_f2 += f*f; sum_e2 += e*e; sum_b2 += b*b;
        sum_fe += f*e; sum_fb += f*b; sum_eb += e*b;
    }

    double n = (double)history_size;
    double cov_11 = (sum_f2 - sum_f*sum_f/n) / n;
    double cov_22 = (sum_e2 - sum_e*sum_e/n) / n;
    double cov_33 = (sum_b2 - sum_b*sum_b/n) / n;

    // Largest eigenvalue (simplified)
    double trace = cov_11 + cov_22 + cov_33;
    origin->eigenvalue = trace / 3.0;

    // Stability (based on variance)
    double var_f = cov_11 / (sum_f/n + 1e-10);
    double var_e = cov_22 / (sum_e/n + 1e-10);
    double var_b = cov_33 / (sum_b/n + 1e-10);
    origin->stability = 1.0 - (var_f + var_e + var_b) / 3.0;
    if (origin->stability < 0) origin->stability = 0;
    if (origin->stability > 1) origin->stability = 1;

    // Strength
    origin->strength = (sum_f + sum_e + sum_b) / (3.0 * n * 255.0);

    // Convergence
    origin->converged = (origin->stability > 0.8) ? 1 : 0;
}

double compute_eigenvalue(const double* matrix, size_t size) {
    if (!matrix || size == 0) {
        return 0.0;
    }

    if (size == 1) {
        return matrix[0];
    }

    if (size == 2) {
        double a = matrix[0], b = matrix[1], c = matrix[2], d = matrix[3];
        double trace = a + d;
        double det = a*d - b*c;
        double disc = trace*trace - 4*det;
        if (disc < 0) disc = 0;
        return (trace + sqrt(disc)) / 2.0;
    }

    // Power iteration for larger matrices
    double eigenvalue = 0.0;
    double* vector = (double*)calloc(size, sizeof(double));
    double* next = (double*)calloc(size, sizeof(double));

    if (!vector || !next) {
        free(vector);
        free(next);
        return 0.0;
    }

    // Initialize with ones
    for (size_t i = 0; i < size; i++) {
        vector[i] = 1.0;
    }

    for (int iter = 0; iter < 100; iter++) {
        // Multiply
        for (size_t i = 0; i < size; i++) {
            next[i] = 0.0;
            for (size_t j = 0; j < size; j++) {
                next[i] += matrix[i * size + j] * vector[j];
            }
        }

        // Normalize
        double norm = 0.0;
        for (size_t i = 0; i < size; i++) {
            norm += next[i] * next[i];
        }
        norm = sqrt(norm) + 1e-10;

        for (size_t i = 0; i < size; i++) {
            vector[i] = next[i] / norm;
        }

        eigenvalue = norm;
    }

    free(vector);
    free(next);
    return eigenvalue;
}

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
) {
    if (!origin_vector || !candidates || !valid_indices) {
        return -1;
    }

    size_t valid_count = 0;

    for (size_t i = 0; i < candidate_count && valid_count < max_valid; i++) {
        double sim = compute_similarity(origin_vector, candidates + i * dim, dim);
        if (sim >= threshold) {
            valid_indices[valid_count++] = (int)i;
        }
    }

    return (int)valid_count;
}

double compute_similarity(
    const double* v1,
    const double* v2,
    size_t dim
) {
    if (!v1 || !v2 || dim == 0) {
        return 0.0;
    }

    double dot = 0.0, norm1 = 0.0, norm2 = 0.0;

    for (size_t i = 0; i < dim; i++) {
        dot += v1[i] * v2[i];
        norm1 += v1[i] * v1[i];
        norm2 += v2[i] * v2[i];
    }

    double denom = sqrt(norm1) * sqrt(norm2);
    if (denom < 1e-10) {
        return 0.0;
    }

    double sim = dot / denom;
    if (sim > 1.0) sim = 1.0;
    if (sim < -1.0) sim = -1.0;

    return sim;
}

// ============================================================
// 编码/解码
// ============================================================

void encode_events(
    const BitFlipEvent* events,
    size_t event_count,
    uint8_t* output,
    size_t* output_size
) {
    if (!events || !output || !output_size) {
        return;
    }

    size_t offset = 0;

    // Header
    output[offset++] = 0xEF;
    output[offset++] = 0xBE;
    output[offset++] = (uint8_t)(event_count & 0xFF);
    output[offset++] = (uint8_t)((event_count >> 8) & 0xFF);

    // Events
    for (size_t i = 0; i < event_count && offset + 16 <= *output_size; i++) {
        memcpy(output + offset, &events[i], 16);
        offset += 16;
    }

    // Checksum
    uint32_t checksum = crc32_checksum(output, offset);
    memcpy(output + offset, &checksum, 4);
    offset += 4;

    *output_size = offset;
}

size_t decode_events(
    const uint8_t* input,
    size_t input_size,
    BitFlipEvent* events,
    size_t max_events
) {
    if (!input || !events || input_size < 20) {
        return 0;
    }

    // Verify header
    if (input[0] != 0xEF || input[1] != 0xBE) {
        return 0;
    }

    uint32_t event_count = input[2] | (input[3] << 8);
    if (event_count > max_events) {
        event_count = (uint32_t)max_events;
    }

    size_t offset = 4;

    for (size_t i = 0; i < event_count && offset + 16 <= input_size - 4; i++) {
        memcpy(&events[i], input + offset, 16);
        offset += 16;
    }

    return event_count;
}

uint32_t crc32_checksum(const uint8_t* data, size_t size) {
    uint32_t crc = 0xFFFFFFFF;

    for (size_t i = 0; i < size; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++) {
            crc = (crc >> 1) ^ (0xEDB88320 & -(crc & 1));
        }
    }

    return ~crc;
}

// ============================================================
// 内存分配
// ============================================================

void* allocate_aligned_memory(size_t size, size_t alignment) {
#ifdef __APPLE__
    return malloc(size);
#else
    void* ptr = NULL;
    if (posix_memalign(&ptr, alignment, size) != 0) {
        return NULL;
    }
    return ptr;
#endif
}

void free_aligned_memory(void* ptr) {
    if (ptr) {
        free(ptr);
    }
}