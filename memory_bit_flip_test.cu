#include <stdio.h>
#include <stdlib.h>
#include <cuda.h>

#define MEM_SIZE (1024 * 1024 * 100) // 100MB

__global__ void fill_memory(unsigned char *dev_mem, unsigned char pattern) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < MEM_SIZE) {
        dev_mem[idx] = pattern;
    }
}

int main() {
    unsigned char *dev_mem;
    unsigned char *host_mem = (unsigned char *)malloc(MEM_SIZE);
    
    // 分配GPU内存
    cudaMalloc((void **)&dev_mem, MEM_SIZE);
    
    // 填充测试模式
    fill_memory<<<(MEM_SIZE + 255) / 256, 256>>>(dev_mem, 0xAA);
    cudaDeviceSynchronize();
    
    // 读取回数据
    cudaMemcpy(host_mem, dev_mem, MEM_SIZE, cudaMemcpyDeviceToHost);
    
    // 检查比特翻转
    int error_count = 0;
    for (int i = 0; i < MEM_SIZE; i++) {
        if (host_mem[i] != 0xAA) {
            error_count++;
            if (error_count <= 10) { // 只显示前10个错误
                printf("Error at %d: expected 0xAA, got 0x%02X\n", i, host_mem[i]);
            }
        }
    }
    
    if (error_count == 0) {
        printf("No bit flips detected in %d bytes of memory\n", MEM_SIZE);
    } else {
        printf("Detected %d bit flips in %d bytes of memory\n", error_count, MEM_SIZE);
    }
    
    // 清理
    free(host_mem);
    cudaFree(dev_mem);
    
    return 0;
}