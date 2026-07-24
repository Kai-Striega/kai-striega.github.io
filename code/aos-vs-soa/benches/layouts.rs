use std::hint::black_box;

use aos_vs_soa::{generate_aos, generate_soa, total_temperature_aos, total_temperature_soa};
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};

/// Working set sizes chosen to walk down the cache hierarchy on a 12900K:
/// 1_000 readings = 32 KB (fits in L1d), 100_000 = 3.2 MB (L2), 1_000_000 = 32 MB (around the 30 MB L3
/// boundary), 16_000_000 = 512 MB (comfortably DRAM).
const SIZES: [usize; 4] = [1_000, 100_000, 1_000_000, 16_000_000];

fn total_temperature(c: &mut Criterion) {
    let mut group = c.benchmark_group("total_temperature");

    for n in SIZES {
        let aos = generate_aos(n);
        let soa = generate_soa(n);

        // Sanity check: if the two layouts ever disagree the benchmark is meaningless.
        assert_eq!(total_temperature_aos(&aos), total_temperature_soa(&soa));

        // Throughput is reported over the logically useful bytes (4 per reading), so that both layouts are
        // measured against the same denominator.
        group.throughput(Throughput::Bytes((n * 4) as u64));

        group.bench_with_input(BenchmarkId::new("aos", n), &aos, |b, aos| {
            b.iter(|| black_box(total_temperature_aos(black_box(aos))))
        });
        group.bench_with_input(BenchmarkId::new("soa", n), &soa, |b, soa| {
            b.iter(|| black_box(total_temperature_soa(black_box(soa))))
        });
    }

    group.finish();
}

criterion_group!(benches, total_temperature);
criterion_main!(benches);
