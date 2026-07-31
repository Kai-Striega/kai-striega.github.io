//! Exploratory only. Every number published in the post comes from `src/bin/counters.rs` instead, so that
//! the timings and the perf counters are measuring the same harness.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use pointer_chasing::*;

fn layouts(c: &mut Criterion) {
    let n = 1 << 20;
    let nodes = Nodes::new(n, 7);
    let contiguous = nodes.contiguous();
    let g = Gather::new(n, 11);

    let mut group = c.benchmark_group("layouts");
    group.throughput(Throughput::Elements(n as u64));
    group.bench_function("contiguous", |b| b.iter(|| sum_contiguous(&contiguous)));
    group.bench_function("boxed_ordered", |b| b.iter(|| sum_boxed_ordered(&nodes)));
    group.bench_function("boxed_shuffled", |b| b.iter(|| sum_boxed_shuffled(&nodes)));
    group.bench_function("list_chase", |b| b.iter(|| sum_list_chase(&nodes)));
    group.bench_function("gather_independent", |b| {
        b.iter(|| sum_gather_independent(&g))
    });
    group.bench_function("gather_dependent", |b| b.iter(|| sum_gather_dependent(&g)));
    group.finish();
}

/// The working set sweep behind the chart: where each layout crosses out of L2 and then out of L3.
fn sweep(c: &mut Criterion) {
    let mut group = c.benchmark_group("sweep");
    for shift in 10..=23 {
        let n = 1usize << shift;
        let nodes = Nodes::new(n, 7);
        let contiguous = nodes.contiguous();
        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("contiguous", n), &n, |b, _| {
            b.iter(|| sum_contiguous(&contiguous))
        });
        group.bench_with_input(BenchmarkId::new("boxed_shuffled", n), &n, |b, _| {
            b.iter(|| sum_boxed_shuffled(&nodes))
        });
        group.bench_with_input(BenchmarkId::new("list_chase", n), &n, |b, _| {
            b.iter(|| sum_list_chase(&nodes))
        });
    }
    group.finish();
}

criterion_group!(benches, layouts, sweep);
criterion_main!(benches);
