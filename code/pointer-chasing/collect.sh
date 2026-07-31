#!/usr/bin/env bash
# Collects the numbers published in the blog post.
#
# perf stat counts the whole process, and building four million heap nodes costs far more than one walk over
# them, so every variant is measured twice: once with its real pass count and once with zero passes. The
# difference is the traversal. Without that subtraction the fast variants are mostly allocator.
#
# Events are collected in two small groups so that nothing is multiplexed; a scaled counter is not worth
# publishing.
#
# Needs: sudo sysctl -w kernel.perf_event_paranoid=1
set -euo pipefail

cd "$(dirname "$0")"
cargo build --release >/dev/null 2>&1
BIN=$PWD/target/release/counters
CPU=${CPU:-2}
N=${N:-4194304}

G1="cpu_core/cycles/,cpu_core/instructions/,cpu_core/mem_load_retired.l3_miss/,cpu_core/dtlb_load_misses.walk_completed/"
G2="cpu_core/l1d_pend_miss.pending/,cpu_core/l1d_pend_miss.pending_cycles/,cpu_core/l1d_pend_miss.fb_full/"

# Pass counts chosen so every variant runs for roughly three seconds.
run() {
    local variant=$1 passes=$2
    local out
    out=$(taskset -c "$CPU" "$BIN" "$variant" "$N" "$passes" 2>/dev/null | tail -1)
    local ns
    ns=$(awk '{for (i=1;i<=NF;i++) if ($(i+1)=="ns/element") print $i}' <<<"$out")

    local -A c=()
    for group in "$G1" "$G2"; do
        while IFS=, read -r value _ event _; do
            [[ -n ${event:-} ]] || continue
            c[${event//cpu_core\/}]=$value
        done < <(taskset -c "$CPU" perf stat -x, -e "$group" "$BIN" "$variant" "$N" "$passes" 2>&1 >/dev/null)
        while IFS=, read -r value _ event _; do
            [[ -n ${event:-} ]] || continue
            c[base_${event//cpu_core\/}]=$value
        done < <(taskset -c "$CPU" perf stat -x, -e "$group" "$BIN" "$variant" "$N" 0 2>&1 >/dev/null)
    done

    d() { echo $(( ${c[$1/]} - ${c[base_$1/]} )); }
    local cycles insns l3 walks pending pcycles fbfull
    cycles=$(d cycles); insns=$(d instructions); l3=$(d mem_load_retired.l3_miss)
    walks=$(d dtlb_load_misses.walk_completed); pending=$(d l1d_pend_miss.pending)
    pcycles=$(d l1d_pend_miss.pending_cycles); fbfull=$(d l1d_pend_miss.fb_full)

    awk -v v="$variant" -v p="$passes" -v n="$N" -v ns="$ns" -v cy="$cycles" -v ins="$insns" \
        -v l3="$l3" -v w="$walks" -v pe="$pending" -v pc="$pcycles" -v fb="$fbfull" 'BEGIN {
        el = n * p
        printf "%-19s %7.2f ns/el  IPC %5.2f  L3miss/el %6.3f  MLP %5.2f  fb_full %5.1f%%  walks/el %6.4f\n",
               v, ns, ins/cy, l3/el, pe/pc, 100*fb/cy, w/el
    }'
}

echo "n = $N, pinned to CPU $CPU, setup subtracted"
run contiguous          1500
run boxed-ordered        400
run boxed-shuffled        80
run list-chase             8
run gather-independent   150
run gather-dependent      12
