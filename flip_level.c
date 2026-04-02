#include "flip_level.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ============================================================
// 翻转层级检测
// ============================================================

FlipLevel detect_flip_level(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t time_window_ns
) {
    if (events == NULL || event_count == 0) {
        return FLIP_LEVEL_SINGLE;
    }

    if (event_count == 1) {
        return FLIP_LEVEL_SINGLE;
    }

    if (event_count == 2) {
        return FLIP_LEVEL_CHOICE;
    }

    return FLIP_LEVEL_HALLUCINATION;
}

int cluster_flip_events(
    const BitFlipEvent* events,
    size_t event_count,
    uint32_t time_window_ns,
    FlipCluster* clusters,
    size_t max_clusters
) {
    if (!events || !clusters || event_count == 0 || max_clusters == 0) {
        return -1;
    }

    size_t cluster_idx = 0;
    uint64_t last_timestamp = events[0].timestamp_ns;

    clusters[0].events[0] = events[0];
    clusters[0].flip_count = 1;
    clusters[0].timestamp = events[0].timestamp_ns;
    clusters[0].level = FLIP_LEVEL_SINGLE;

    for (size_t i = 1; i < event_count && cluster_idx < max_clusters; i++) {
        uint64_t time_diff = events[i].timestamp_ns - last_timestamp;

        if (time_diff <= time_window_ns) {
            if (clusters[cluster_idx].flip_count < 8) {
                clusters[cluster_idx].events[clusters[cluster_idx].flip_count] = events[i];
                clusters[cluster_idx].flip_count++;
            }
        } else {
            clusters[cluster_idx].level = detect_flip_level(
                clusters[cluster_idx].events,
                clusters[cluster_idx].flip_count,
                time_window_ns
            );

            cluster_idx++;
            clusters[cluster_idx].events[0] = events[i];
            clusters[cluster_idx].flip_count = 1;
            clusters[cluster_idx].timestamp = events[i].timestamp_ns;
            last_timestamp = events[i].timestamp_ns;
        }
    }

    if (cluster_idx < max_clusters) {
        clusters[cluster_idx].level = detect_flip_level(
            clusters[cluster_idx].events,
            clusters[cluster_idx].flip_count,
            time_window_ns
        );
    }

    return (int)(cluster_idx + 1);
}

// ============================================================
// 单翻转自悟迭代处理
// ============================================================

int process_single_flip(
    const BitFlipEvent* event,
    const uint64_t* entanglement_state,
    SingleFlipResult* result
) {
    if (!event || !result) {
        return -1;
    }

    result->hamming_distance = 1.0;
    result->entanglement_bits = compute_entanglement_hash(event, 1);
    result->self_feedback = 0.5;

    if (entanglement_state) {
        uint64_t diff = (*entanglement_state) ^ (result->entanglement_bits);
        int bit_count = __builtin_popcountll(diff);
        result->hamming_distance = (double)bit_count / 64.0;

        double feedback = 1.0 - result->hamming_distance;
        result->self_feedback = feedback;
    }

    return 0;
}

uint64_t compute_entanglement_hash(
    const BitFlipEvent* events,
    size_t count
) {
    uint64_t hash = 0x123456789ABCDEF0ULL;

    for (size_t i = 0; i < count; i++) {
        hash ^= ((uint64_t)events[i].address << events[i].bit_position);
        hash = (hash * 31) + events[i].direction;
        hash = (hash << 1) | (hash >> 63);
    }

    return hash;
}

void update_entanglement_state(
    uint64_t* state,
    const BitFlipEvent* event,
    double feedback_strength
) {
    if (!state || !event) {
        return;
    }

    uint64_t flip_mask = (1ULL << event->bit_position);
    uint64_t flip_value = ((uint64_t)event->direction) << event->bit_position;

    uint64_t current = *state;
    uint64_t mask = flip_mask | (flip_mask << 32);
    uint64_t update = flip_value | (flip_value << 32);

    uint64_t new_state = (current & ~mask) | (update & mask);

    double alpha = feedback_strength;
    uint64_t interpolated = ((uint64_t)(alpha * 1000)) * (new_state - current) / 1000;

    *state = current + interpolated;
}

// ============================================================
// 双翻转抉择处理
// ============================================================

int process_double_flip(
    const BitFlipEvent* event_a,
    const BitFlipEvent* event_b,
    uint32_t region_size,
    DoubleFlipResult* result
) {
    if (!event_a || !event_b || !result) {
        return -1;
    }

    int addr_diff = abs((int)event_a->address - (int)event_b->address);
    double spatial_relation = 1.0 - ((double)addr_diff / (double)region_size);

    int bit_diff_a = event_a->bit_position ^ event_b->bit_position;
    double temporal_relation = 1.0 / (1.0 + fabs((double)(event_a->timestamp_ns - event_b->timestamp_ns)) / 1000.0);

    double convergence_a = spatial_relation * temporal_relation;
    double convergence_b = spatial_relation * (1.0 - temporal_relation);

    result->branch_a_expanded = (uint32_t)(region_size * convergence_a);
    result->branch_b_expanded = (uint32_t)(region_size * convergence_b);
    result->convergence_a = convergence_a;
    result->convergence_b = convergence_b;
    result->selected_branch = (convergence_a >= convergence_b) ? 0 : 1;

    return 0;
}

// ============================================================
// 三翻转幻觉复数处理
// ============================================================

int process_triple_flip(
    const BitFlipEvent* events,
    size_t event_count,
    double* tensor_output,
    size_t tensor_size,
    TripleFlipResult* result
) {
    if (!events || !result || event_count < 3) {
        return -1;
    }

    size_t dim = event_count;
    if (dim > tensor_size / dim) {
        dim = (size_t)sqrt((double)tensor_size);
    }

    if (dim < 2) {
        dim = 2;
    }

    size_t tensor_elements = dim * dim;
    memset(tensor_output, 0, tensor_elements * sizeof(double));

    for (size_t i = 0; i < dim; i++) {
        for (size_t j = 0; j < dim; j++) {
            double spatial = 1.0 / (1.0 + abs((int)events[i % event_count].address -
                                              (int)events[j % event_count].address));
            double temporal = exp(-fabs((double)(events[i % event_count].timestamp_ns -
                                                events[j % event_count].timestamp_ns)) / 1e9);
            double bit_correlation = (events[i % event_count].bit_position ==
                                     events[j % event_count].bit_position) ? 1.0 : 0.5;

            tensor_output[i * dim + j] = spatial * temporal * bit_correlation;
        }
    }

    double trace = 0.0;
    for (size_t i = 0; i < dim && i < tensor_elements; i++) {
        trace += tensor_output[i * dim + i];
    }
    result->tensor_trace = trace;

    double eigenvalue_max = 0.0;
    for (size_t i = 0; i < tensor_elements; i++) {
        eigenvalue_max += fabs(tensor_output[i]);
    }
    result->eigenvalue_max = eigenvalue_max / (double)dim;

    double frequency = 0.0;
    if (event_count >= 3) {
        double dt1 = (double)(events[1].timestamp_ns - events[0].timestamp_ns);
        double dt2 = (double)(events[2].timestamp_ns - events[1].timestamp_ns);
        if (dt1 > 0 && dt2 > 0) {
            frequency = 1.0 / ((dt1 + dt2) / 2.0);
        }
    }
    result->hallucination_frequency = frequency * 1e9;

    result->tensor_rank = (uint32_t)dim;

    return 0;
}

// ============================================================
// 相似度计算
// ============================================================

double compute_hamming_similarity(
    const BitFlipEvent* f1,
    const BitFlipEvent* f2
) {
    if (!f1 || !f2) {
        return 0.0;
    }

    int addr_diff = abs((int)f1->address - (int)f2->address);
    double addr_sim = 1.0 / (1.0 + (double)addr_diff / 1000.0);

    int bit_diff = (f1->bit_position == f2->bit_position) ? 0 : 1;
    double bit_sim = 1.0 - (double)bit_diff;

    int dir_diff = (f1->direction == f2->direction) ? 0 : 1;
    double dir_sim = 1.0 - (double)dir_diff;

    return (addr_sim + bit_sim + dir_sim) / 3.0;
}

// ============================================================
// 张量运算
// ============================================================

int compute_flip_tensor(
    const BitFlipEvent* events,
    size_t event_count,
    double* tensor,
    size_t tensor_rank
) {
    if (!events || !tensor || event_count == 0 || tensor_rank == 0) {
        return -1;
    }

    size_t dim = tensor_rank;
    size_t total_size = dim * dim * dim;

    for (size_t i = 0; i < dim && i < event_count; i++) {
        for (size_t j = 0; j < dim; j++) {
            for (size_t k = 0; k < dim; k++) {
                double v1 = (double)events[i].bit_position / 8.0;
                double v2 = (double)events[j % event_count].bit_position / 8.0;
                double v3 = (double)events[k % event_count].bit_position / 8.0;

                double spatial = exp(-fabs((double)(events[i].address -
                                                   events[j % event_count].address)) / 10000.0);
                double temporal = exp(-fabs((double)(events[i].timestamp_ns -
                                                    events[j % event_count].timestamp_ns)) / 1e9);

                tensor[i * dim * dim + j * dim + k] = v1 * v2 * v3 * spatial * temporal;
            }
        }
    }

    return 0;
}

double compute_tensor_eigenvalue(
    const double* tensor,
    size_t size
) {
    if (!tensor || size == 0) {
        return 0.0;
    }

    double eigenvalue = 0.0;

    for (size_t i = 0; i < size; i++) {
        eigenvalue += fabs(tensor[i]);
    }

    return eigenvalue / (double)size;
}

double compute_expansion_frequency(
    const double* eigenvalue_history,
    size_t history_size
) {
    if (!eigenvalue_history || history_size < 2) {
        return 0.0;
    }

    double sum_dlambda = 0.0;
    for (size_t i = 1; i < history_size; i++) {
        sum_dlambda += eigenvalue_history[i] - eigenvalue_history[i-1];
    }

    return sum_dlambda / (double)(history_size - 1);
}

// ============================================================
// 统计
// ============================================================

void init_flip_level_stats(FlipLevelStats* stats) {
    if (!stats) {
        return;
    }

    memset(stats, 0, sizeof(FlipLevelStats));
    stats->total_self_iterations = 0;
    stats->total_coherence_gain = 0.0;
}

void update_flip_level_stats(
    FlipLevelStats* stats,
    FlipLevel level,
    const void* result
) {
    if (!stats) {
        return;
    }

    stats->total_self_iterations++;

    switch (level) {
        case FLIP_LEVEL_SINGLE:
            if (result) {
                const SingleFlipResult* sr = (const SingleFlipResult*)result;
                stats->total_coherence_gain += sr->self_feedback;
            }
            break;

        case FLIP_LEVEL_CHOICE:
            if (result) {
                const DoubleFlipResult* dr = (const DoubleFlipResult*)result;
                double avg_conv = (dr->convergence_a + dr->convergence_b) / 2.0;
                stats->total_coherence_gain += avg_conv;
            }
            break;

        case FLIP_LEVEL_HALLUCINATION:
            if (result) {
                const TripleFlipResult* tr = (const TripleFlipResult*)result;
                stats->total_coherence_gain += tr->eigenvalue_max / 100.0;
            }
            break;
    }
}