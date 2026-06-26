#ifndef A90_MONITOR_H
#define A90_MONITOR_H

#include <stdint.h>

#define A90_MONITOR_M0_DEFAULT_SAMPLES 3U
#define A90_MONITOR_M0_MIN_SAMPLES 2U
#define A90_MONITOR_M0_MAX_SAMPLES 16U
#define A90_MONITOR_M0_DEFAULT_INTERVAL_MS 200U
#define A90_MONITOR_M0_MAX_INTERVAL_MS 5000U
#define A90_MONITOR_M1_DEFAULT_HOLD_MS 5000U
#define A90_MONITOR_M1_MAX_HOLD_MS 60000U
#define A90_MONITOR_GRAPH_MAX_POINTS 32U

struct a90_monitor_graph_point {
    long cpu_pct;
    long gpu_pct;
    long mem_pct;
    long temp_pct;
};

struct a90_monitor_graph_series {
    unsigned int count;
    unsigned int head;
    unsigned int cpu_count;
    unsigned int cluster_count;
    char gpu_model[64];
    long last_cpu_pct;
    long last_gpu_pct;
    long last_mem_pct;
    long last_temp_pct;
    struct a90_monitor_graph_point points[A90_MONITOR_GRAPH_MAX_POINTS];
};

int a90_monitor_m0_sampler_probe(unsigned int samples, unsigned int interval_ms);
int a90_monitor_m1_dashboard_probe(unsigned int samples,
                                    unsigned int interval_ms,
                                    unsigned int hold_ms);
void a90_monitor_graph_reset(struct a90_monitor_graph_series *series);
int a90_monitor_graph_sample(struct a90_monitor_graph_series *series);
unsigned int a90_monitor_graph_render_mono1(const struct a90_monitor_graph_series *series,
                                            uint8_t *frame,
                                            uint32_t width,
                                            uint32_t height,
                                            uint32_t stride);

#endif
