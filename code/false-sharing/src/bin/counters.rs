//! A thin binary for `perf stat` and `perf c2c` to wrap around, so the counters measure one variant and
//! nothing else.
//!
//! Usage: counters <variant> <threads> [passes] [--siblings]
//!
//!   variant: single | shared | padded | local | readonly | true-shared
//!   passes:  how many times each thread sweeps its own slice
//!   --siblings: pin to CPUs 0,1,2,3... (SMT siblings) instead of 0,2,4,6... (distinct physical cores)
//!
//! The threads are spawned once and loop internally, so thread creation is not what gets measured.

use std::hint::black_box;
use std::time::Instant;

use false_sharing::*;

const N: usize = 1 << 18;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let variant = args.get(1).map(String::as_str).unwrap_or("shared");
    let threads: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(8);
    let passes: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(200);
    let siblings = args.iter().any(|a| a == "--siblings");

    let cpus = if siblings {
        sibling_cores(threads)
    } else {
        physical_cores(threads)
    };

    let readings = generate(N);

    let start = Instant::now();
    let total = match variant {
        "single" => sum_single(black_box(&readings), passes),
        "shared" => sum_shared(black_box(&readings), &cpus, passes),
        "padded" => sum_padded(black_box(&readings), &cpus, passes),
        "local" => sum_local(black_box(&readings), &cpus, passes),
        "readonly" => sum_readonly(black_box(&readings), &cpus, passes),
        "true-shared" => sum_true_shared(black_box(&readings), &cpus, passes),
        other => {
            eprintln!("unknown variant {other:?}");
            std::process::exit(1);
        }
    };
    let elapsed = start.elapsed();
    black_box(total);

    // If a variant ever disagrees, the benchmark is measuring nothing.
    let expected = sum_single(&readings, passes);
    assert_eq!(total, expected, "variant {variant} produced the wrong total");

    // Elements retired across all threads. For the threaded variants each thread walks N/threads elements
    // `passes` times, so the total is N * passes either way, which keeps ns-per-element comparable.
    let elems = N * passes;
    let pinning = if siblings { "smt-siblings" } else { "physical" };
    println!(
        "variant={variant} threads={threads} pinning={pinning} n={N} passes={passes} \
         wall={:.2}ms ns_per_element={:.4} total={total}",
        elapsed.as_secs_f64() * 1000.0,
        elapsed.as_secs_f64() * 1e9 / elems as f64,
    );
}
