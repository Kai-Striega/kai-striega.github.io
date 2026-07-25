use std::hint::black_box;

use branch_prediction::{
    count_above_branchless_barrier, count_above_branchy, generate_program, generate_random_program,
    generate_values, run_fnptr, run_match, sorted, THRESHOLD,
};
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

/// 256K elements is 1 MB of i32, which fits in this core's 1.25 MB L2. That is deliberate: we are trying to
/// measure branch mispredictions, and a working set that spilled to DRAM would just measure part 1 again.
const N: usize = 1 << 18;

/// The proportion of values above the threshold, and therefore how often the branch is taken.
const PROBABILITIES: [f64; 11] = [0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0];

/// Repeat periods for the interpreter's instruction stream. All are multiples of 8 so that every program
/// executes exactly the same mix of opcodes.
const PERIODS: [usize; 8] = [8, 16, 32, 64, 128, 256, 512, 1024];

fn conditional_branches(c: &mut Criterion) {
    let mut group = c.benchmark_group("count_above");

    for taken in PROBABILITIES {
        let values = generate_values(N, taken, 0x1234);
        let label = format!("{:.0}pc", taken * 100.0);

        group.bench_with_input(BenchmarkId::new("branchy", &label), &values, |b, values| {
            b.iter(|| black_box(count_above_branchy(black_box(values), THRESHOLD)))
        });
        group.bench_with_input(BenchmarkId::new("branchless", &label), &values, |b, values| {
            b.iter(|| black_box(count_above_branchless_barrier(black_box(values), THRESHOLD)))
        });
    }

    group.finish();
}

/// The famous demonstration: exactly the same values as the 50% case, only sorted. Same multiset, same
/// answer, same amount of work. The only thing that changed is the order the branch sees them in.
fn sorted_versus_shuffled(c: &mut Criterion) {
    let mut group = c.benchmark_group("sorted_vs_shuffled");

    let shuffled = generate_values(N, 0.5, 0x1234);
    let ordered = sorted(&shuffled);
    assert_eq!(
        count_above_branchy(&shuffled, THRESHOLD),
        count_above_branchy(&ordered, THRESHOLD)
    );

    group.bench_with_input(BenchmarkId::new("branchy", "shuffled"), &shuffled, |b, v| {
        b.iter(|| black_box(count_above_branchy(black_box(v), THRESHOLD)))
    });
    group.bench_with_input(BenchmarkId::new("branchy", "sorted"), &ordered, |b, v| {
        b.iter(|| black_box(count_above_branchy(black_box(v), THRESHOLD)))
    });

    group.finish();
}

fn indirect_branches(c: &mut Criterion) {
    let mut group = c.benchmark_group("interpreter");

    for period in PERIODS {
        let code = generate_program(N, period, 0xABCD);
        let label = format!("period{period:04}");

        group.bench_with_input(BenchmarkId::new("match", &label), &code, |b, code| {
            b.iter(|| black_box(run_match(black_box(code))))
        });
        group.bench_with_input(BenchmarkId::new("fnptr", &label), &code, |b, code| {
            b.iter(|| black_box(run_fnptr(black_box(code))))
        });
    }

    let code = generate_random_program(N, 0xABCD);
    group.bench_with_input(BenchmarkId::new("match", "random"), &code, |b, code| {
        b.iter(|| black_box(run_match(black_box(code))))
    });
    group.bench_with_input(BenchmarkId::new("fnptr", "random"), &code, |b, code| {
        b.iter(|| black_box(run_fnptr(black_box(code))))
    });

    group.finish();
}

criterion_group!(
    benches,
    conditional_branches,
    sorted_versus_shuffled,
    indirect_branches
);
criterion_main!(benches);
