## Slide 5 Wider output tiles

The improvement starts with sharing an input value. At width 1, the accelerator computes 1 output at a time, repeatedly loading the same value from matrix A for different outputs.

At width 4, it computes 4 neighboring outputs together and shares 1 A load across them. That reduces repeated loads and exposes parallel arithmetic, while preserving the same mathematical result.

The tradeoff is greater hardware demand and more simultaneous memory requests. A narrow interface limits the benefit, and the fixed invocation overhead remains.

## Slide 6 Offload latency

First, wider tiles reduce offload latency at every tested size. Width 4 saves 11.8% at N equals 24, and 25.1% at 32. Most of the gain comes from moving from width 1 to width 2.

## Slide 7 Loads and cache requests

Second, fewer program loads do not necessarily reduce cache traffic. At N equals 24, width 4 cuts A loads by a factor of 4, yet all widths issue the same cache requests.

The counts are 36 A loads, 36 B loads, and 576 C stores. Cache-line merging explains the unchanged traffic. Better scheduling reduces stalls.

## Slide 8 Memory interface

Third, interface capacity matters. With 1 request per cycle, width 4 saves 4.6%. With 2, it saves 7.1%. With 4, the saving reaches 11.8%.

Offload time also includes about 1.25 microseconds of fixed overhead. These local gains therefore need a system-level comparison.
