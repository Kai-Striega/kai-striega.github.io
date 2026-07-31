#!/usr/bin/env bash
# Working set sweep behind the chart: nanoseconds per element against how much data there is.
#
# Timing only, no perf needed. The binary starts its clock after the data is built, so no baseline
# subtraction is required here.
set -euo pipefail

cd "$(dirname "$0")"
cargo build --release >/dev/null 2>&1
BIN=$PWD/target/release/counters
CPU=${CPU:-2}

printf '%10s %12s %12s %12s\n' elements contiguous boxed-shuffled list-chase
for shift in $(seq 10 23); do
    n=$((1 << shift))
    # Roughly constant work per point, floored so the small sizes still take a measurable time.
    fast=$(( 400000000 / n )); [ "$fast" -lt 20 ] && fast=20
    slow=$((   4000000 / n )); [ "$slow" -lt 3  ] && slow=3

    ns() { taskset -c "$CPU" "$BIN" "$1" "$n" "$2" | awk '{for (i=1;i<=NF;i++) if ($(i+1)=="ns/element") print $i}'; }
    printf '%10d %12s %12s %12s\n' "$n" "$(ns contiguous "$fast")" "$(ns boxed-shuffled "$slow")" "$(ns list-chase "$slow")"
done
