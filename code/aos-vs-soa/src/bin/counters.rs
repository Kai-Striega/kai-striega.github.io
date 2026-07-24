//! A thin binary for `perf stat` to wrap around, so the hardware counters measure one layout and nothing
//! else.
//!
//! Usage: counters <aos|soa> [n] [repeats]
//!
//! The data is built before the timed region, and the region itself does nothing but run the kernel.

use std::hint::black_box;
use std::time::Instant;

use aos_vs_soa::{generate_aos, generate_soa, total_temperature_aos, total_temperature_soa};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let layout = args.get(1).map(String::as_str).unwrap_or("aos");
    let n: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(16_000_000);
    let repeats: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(20);

    let mut total: i64 = 0;

    match layout {
        "aos" => {
            let readings = generate_aos(n);
            let start = Instant::now();
            for _ in 0..repeats {
                total = total.wrapping_add(black_box(total_temperature_aos(black_box(&readings))));
            }
            report(layout, n, repeats, start.elapsed(), total);
        }
        "soa" => {
            let readings = generate_soa(n);
            let start = Instant::now();
            for _ in 0..repeats {
                total = total.wrapping_add(black_box(total_temperature_soa(black_box(&readings))));
            }
            report(layout, n, repeats, start.elapsed(), total);
        }
        other => {
            eprintln!("unknown layout {other:?}, expected aos or soa");
            std::process::exit(1);
        }
    }
}

fn report(layout: &str, n: usize, repeats: usize, elapsed: std::time::Duration, total: i64) {
    let per_pass = elapsed.as_secs_f64() / repeats as f64;
    println!("layout={layout} n={n} repeats={repeats} per_pass={:.3}ms total={total}", per_pass * 1000.0);
}
