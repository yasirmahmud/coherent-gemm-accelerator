#include <stdio.h>
#include <stdlib.h>

#include "aladdin_sys_connection.h"
#include "aladdin_sys_constants.h"

#ifndef N
#define N 16
#endif
#ifndef REPS
#define REPS 1
#endif
#define BYTES (N * N * sizeof(int))

#if N % 4 != 0
#error N must be divisible by 4
#endif

// Four output columns share each A load and expose four independent sums.
#ifndef GEM5_HARNESS
void gemm_kernel(const int *A, const int *B, int *C) {
  loop_i: for (int i = 0; i < N; i++) {
    loop_j: for (int j = 0; j < N; j += 4) {
      int s0 = 0, s1 = 0, s2 = 0, s3 = 0;
      loop_k: for (int k = 0; k < N; k++) {
        int a = A[i * N + k];
        s0 += a * B[k * N + j];
        s1 += a * B[k * N + j + 1];
        s2 += a * B[k * N + j + 2];
        s3 += a * B[k * N + j + 3];
      }
      C[i * N + j] = s0;
      C[i * N + j + 1] = s1;
      C[i * N + j + 2] = s2;
      C[i * N + j + 3] = s3;
    }
  }
}
#endif

int main(void) {
  int *A = NULL, *B = NULL, *C = NULL;
  if (posix_memalign((void **)&A, 64, BYTES) ||
      posix_memalign((void **)&B, 64, BYTES) ||
      posix_memalign((void **)&C, 64, BYTES)) {
    fprintf(stderr, "Allocation failed\n");
    return 2;
  }
  for (int i = 0; i < N * N; i++) {
    A[i] = (i % 7) - 3;
    B[i] = (i % 5) - 2;
    C[i] = 0;
  }

#ifdef GEM5_HARNESS
  mapArrayToAccelerator(INTEGRATION_TEST, "A", A, BYTES);
  mapArrayToAccelerator(INTEGRATION_TEST, "B", B, BYTES);
  mapArrayToAccelerator(INTEGRATION_TEST, "C", C, BYTES);
  for (int rep = 0; rep < REPS; rep++) {
    if (REPS > 1)
      A[rep % (N * N)] += 1;
#ifdef INVOCATION_STATS
    resetGem5Stats();
#endif
    invokeAcceleratorAndBlock(INTEGRATION_TEST);
#ifdef INVOCATION_STATS
    dumpGem5Stats("gemm invocation");
#endif
  }
#else
#ifdef LLVM_TRACE
  gemm_kernel(A, B, C);
#else
  for (int rep = 0; rep < REPS; rep++) {
    if (REPS > 1)
      A[rep % (N * N)] += 1;
    gemm_kernel(A, B, C);
  }
#endif
#endif

  int failures = 0;
#ifdef FAST_CHECK
  long long checksum = 0;
  for (int i = 0; i < N * N; i++)
    checksum += C[i];
  printf("GEMM checksum: %lld\n", checksum);
#else
  for (int i = 0; i < N; i++) {
    for (int j = 0; j < N; j++) {
      int expected = 0;
      for (int k = 0; k < N; k++)
        expected += A[i * N + k] * B[k * N + j];
      if (C[i * N + j] != expected)
        failures++;
    }
  }
  printf("GEMM %s: %d mismatches\n", failures ? "FAILED" : "passed", failures);
#endif
  free(A);
  free(B);
  free(C);
  return failures ? 1 : 0;
}
