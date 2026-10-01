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

#if N % 2 != 0
#error N must be divisible by 2
#endif

// Two output columns share each A load and expose two independent sums.
#ifndef GEM5_HARNESS
void gemm_kernel(const int *A, const int *B, int *C) {
  loop_i: for (int i = 0; i < N; i++) {
    loop_j: for (int j = 0; j < N; j += 2) {
      int s0 = 0, s1 = 0;
      loop_k: for (int k = 0; k < N; k++) {
        int a = A[i * N + k];
        s0 += a * B[k * N + j];
        s1 += a * B[k * N + j + 1];
      }
      C[i * N + j] = s0;
      C[i * N + j + 1] = s1;
    }
  }
}
#endif

#ifdef PER_CALL_CHECK
// Full elementwise check against a fresh CPU reference computed from the
// CURRENT A/B, printed with a caller-supplied label. Only for the dedicated
// repeated-correctness runner (scripts/run_repeated.sh) -- never defined for
// the fair/roi/invocation timing stages, since the O(N^3) check itself would
// otherwise be folded into the measured gem5 stats window.
static int check_output(const int *A, const int *B, const int *C,
                         const char *label) {
  int failures = 0;
  for (int i = 0; i < N; i++) {
    for (int j = 0; j < N; j++) {
      int expected = 0;
      for (int k = 0; k < N; k++)
        expected += A[i * N + k] * B[k * N + j];
      if (C[i * N + j] != expected)
        failures++;
    }
  }
  printf("GEMM %s %s: %d mismatches\n", label, failures ? "FAILED" : "passed",
         failures);
  return failures;
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
#ifdef PER_CALL_CHECK
  int per_call_failures = 0;
#endif
  for (int rep = 0; rep < REPS; rep++) {
    if (REPS > 1) {
#ifdef INDEPENDENT_MUTATION
      // A genuinely different runtime mutation than the one the trace was
      // generated with below (LLVM_TRACE always uses `A[rep % (N*N)] += 1`,
      // regardless of this macro) -- different index formula, different
      // (including negative) delta, so this is not the same predetermined
      // pattern the tracer saw. TESTED AND FAILS (results/diagnostics/
      // repeated_n24_reps3_base_independent/): mismatches on every call,
      // including call 0. Aladdin's trace replay is NOT purely structural
      // for this path -- it is sensitive to the specific values recorded
      // at trace time, not just live memory contents at replay time. The
      // Gate 1 fix is verified only for the case where the runtime
      // mutation exactly matches the one baked into the trace; do not
      // assume it generalizes to arbitrary/unpredictable runtime input.
      A[(rep * 7 + 3) % (N * N)] += (rep % 5) - 2;
#else
      A[rep % (N * N)] += 1;
#endif
    }
#ifdef INVOCATION_STATS
    resetGem5Stats();
#endif
    invokeAcceleratorAndBlock(INTEGRATION_TEST);
#ifdef INVOCATION_STATS
    dumpGem5Stats("gemm invocation");
#endif
#ifdef PER_CALL_CHECK
    {
      char label[32];
      snprintf(label, sizeof(label), "call %d", rep);
      per_call_failures += check_output(A, B, C, label);
    }
#endif
  }
#else
  for (int rep = 0; rep < REPS; rep++) {
    if (REPS > 1)
      A[rep % (N * N)] += 1;
    gemm_kernel(A, B, C);
  }
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
#if defined(GEM5_HARNESS) && defined(PER_CALL_CHECK)
  printf("GEMM per-call total: %d mismatches across %d calls\n",
         per_call_failures, REPS);
  failures += per_call_failures;
#endif
  free(A);
  free(B);
  free(C);
  return failures ? 1 : 0;
}
