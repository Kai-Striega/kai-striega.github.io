//! A thin binary for `perf stat` to wrap around, so the hardware counters measure one workload and nothing
//! else.
//!
//! Usage:
//!   counters cond <branchy|branchless> <taken-percent|sorted> [repeats]
//!   counters interp <match|fnptr> <period|random> [repeats]
//!
//! The data is built before the timed region, and the region itself does nothing but run the kernel.

use std::hint::black_box;
use std::time::Instant;

use branch_prediction::{
    count_above_branchless_barrier, count_above_branchy, generate_program, generate_random_program,
    generate_values, run_fnptr, run_match, sorted, THRESHOLD,
};

const N: usize = 1 << 18;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let usage = "usage: counters cond <branchy|branchless> <taken-percent|sorted> [repeats]\n       counters interp <match|fnptr> <period|random> [repeats]";

    let Some(part) = args.get(1) else {
        eprintln!("{usage}");
        std::process::exit(1);
    };

    match part.as_str() {
        "cond" => {
            let variant = args.get(2).map(String::as_str).unwrap_or("branchy");
            let shape = args.get(3).map(String::as_str).unwrap_or("50");
            let repeats: usize = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(2000);

            let values = if shape == "sorted" {
                sorted(&generate_values(N, 0.5, 0x1234))
            } else {
                let pc: f64 = shape.parse().expect("taken-percent must be a number or 'sorted'");
                generate_values(N, pc / 100.0, 0x1234)
            };

            let kernel = match variant {
                "branchy" => count_above_branchy,
                "branchless" => count_above_branchless_barrier,
                other => {
                    eprintln!("unknown variant {other:?}");
                    std::process::exit(1);
                }
            };

            let mut total = 0u64;
            let start = Instant::now();
            for _ in 0..repeats {
                total = total.wrapping_add(black_box(kernel(black_box(&values), THRESHOLD)));
            }
            let elapsed = start.elapsed();

            let ops = N * repeats;
            println!(
                "part=cond variant={variant} shape={shape} n={N} repeats={repeats} elements={ops} \
                 per_pass={:.3}ms ns_per_element={:.4} checksum={total}",
                elapsed.as_secs_f64() * 1000.0 / repeats as f64,
                elapsed.as_secs_f64() * 1e9 / ops as f64,
            );
        }
        "interp" => {
            let variant = args.get(2).map(String::as_str).unwrap_or("match");
            let shape = args.get(3).map(String::as_str).unwrap_or("random");
            let repeats: usize = args.get(4).and_then(|s| s.parse().ok()).unwrap_or(2000);

            let code = if shape == "random" {
                generate_random_program(N, 0xABCD)
            } else {
                let period: usize = shape.parse().expect("period must be a number or 'random'");
                generate_program(N, period, 0xABCD)
            };

            let kernel = match variant {
                "match" => run_match,
                "fnptr" => run_fnptr,
                other => {
                    eprintln!("unknown variant {other:?}");
                    std::process::exit(1);
                }
            };

            let mut total = 0i64;
            let start = Instant::now();
            for _ in 0..repeats {
                total = total.wrapping_add(black_box(kernel(black_box(&code))));
            }
            let elapsed = start.elapsed();

            let ops = N * repeats;
            println!(
                "part=interp variant={variant} shape={shape} n={N} repeats={repeats} instructions={ops} \
                 per_pass={:.3}ms ns_per_op={:.4} checksum={total}",
                elapsed.as_secs_f64() * 1000.0 / repeats as f64,
                elapsed.as_secs_f64() * 1e9 / ops as f64,
            );
        }
        other => {
            eprintln!("unknown part {other:?}\n{usage}");
            std::process::exit(1);
        }
    }
}
