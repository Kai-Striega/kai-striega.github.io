//! The same two workloads as `distribution.rs`, measured with divan instead of criterion.
//!
//!     cargo bench --bench distribution_divan
//!
//! The point of running both is that the tools embody different answers to "which summary is the truth".
//! Criterion reports a mean with a bootstrap confidence interval; divan leads with the *median* (and
//! shows min/mean/max alongside it). On a skewed sample those numbers do not agree, and part two is about
//! why that disagreement is a real methodological choice rather than a rounding error.

use reasonable_benchmarking::{build_cycle, chase, generate_values, sum_of_squares};

const COMPUTE_N: usize = 10_000;
const MEMORY_N: usize = 8 << 20;
const CHASE_STEPS: usize = 20_000;

fn main() {
    divan::main();
}

#[divan::bench(sample_count = 500)]
fn compute_bound(bencher: divan::Bencher) {
    let values = generate_values(COMPUTE_N, 0xC0FFEE);
    bencher.bench_local(|| sum_of_squares(divan::black_box(&values)));
}

#[divan::bench(sample_count = 500)]
fn memory_bound(bencher: divan::Bencher) {
    let next = build_cycle(MEMORY_N, 0x5EED);
    bencher.bench_local(move || chase(divan::black_box(&next), 0, CHASE_STEPS));
}
