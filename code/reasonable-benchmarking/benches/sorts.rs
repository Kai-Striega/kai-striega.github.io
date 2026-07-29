//! Experiment E7: comparing a small suite, not a single benchmark.
//!
//!     cargo bench --bench sorts
//!
//! Part three is about the step most performance claims skip: going from "this benchmark is faster" to
//! "this implementation is faster". We compare two standard-library sorts:
//!
//!   * `sort`, a stable, adaptive merge sort (allocates scratch space),
//!   * `sort_unstable`, pattern-defeating quicksort (in place),
//!
//! across four input shapes and two sizes. Neither wins everywhere: which one is faster depends on the
//! input, which is exactly why summarising a suite honestly needs a geometric mean rather than a race,
//! and why counting wins across benchmarks needs a multiple-comparison correction. The Python analysis in
//! `analysis/` reads these results back and works through both.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

use reasonable_benchmarking::{generate_pattern, Pattern};

const SIZES: [usize; 2] = [1_000, 100_000];

fn sorts(c: &mut Criterion) {
    let mut group = c.benchmark_group("sort");

    for &n in &SIZES {
        for pattern in Pattern::ALL {
            let input = generate_pattern(n, pattern, 0xA11CE);
            let id = format!("{}/{}", pattern.name(), n);

            group.bench_with_input(BenchmarkId::new("stable", &id), &input, |b, input| {
                b.iter_batched_ref(
                    || input.clone(),
                    |v| v.sort(),
                    criterion::BatchSize::LargeInput,
                )
            });
            group.bench_with_input(BenchmarkId::new("unstable", &id), &input, |b, input| {
                b.iter_batched_ref(
                    || input.clone(),
                    |v| v.sort_unstable(),
                    criterion::BatchSize::LargeInput,
                )
            });
        }
    }

    group.finish();
}

/// A null comparison for part three's multiple-comparison section. `left` and `right` run the *same*
/// algorithm on the *same* input, so any measured difference between them is noise by construction. Run
/// across every case, this is the honest way to show that uncorrected significance testing manufactures
/// winners out of thin air.
fn null_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("null");

    for &n in &SIZES {
        for pattern in Pattern::ALL {
            let input = generate_pattern(n, pattern, 0xA11CE);
            let id = format!("{}/{}", pattern.name(), n);

            group.bench_with_input(BenchmarkId::new("left", &id), &input, |b, input| {
                b.iter_batched_ref(
                    || input.clone(),
                    |v| v.sort_unstable(),
                    criterion::BatchSize::LargeInput,
                )
            });
            group.bench_with_input(BenchmarkId::new("right", &id), &input, |b, input| {
                b.iter_batched_ref(
                    || input.clone(),
                    |v| v.sort_unstable(),
                    criterion::BatchSize::LargeInput,
                )
            });
        }
    }

    group.finish();
}

criterion_group! {
    name = benches;
    config = Criterion::default().sample_size(200);
    targets = sorts, null_comparison
}
criterion_main!(benches);
