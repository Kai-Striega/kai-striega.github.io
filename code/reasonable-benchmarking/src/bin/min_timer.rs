//! A deliberately minimal, robust timer used for experiment E3.
//!
//! It reports the *minimum* per-iteration time over many rounds. The minimum is the most stable estimator
//! of a floor performance (noise is one-sided, it can only slow a run down), so if the minimum shifts
//! when we change something that should not matter, that shift is real and not just jitter. See part two
//! for why the minimum is a defensible, and contested, choice.
//!
//!     cargo run --release --bin min_timer
//!
//! E3 runs this same source built or invoked under different *incidental* conditions and compares the
//! minima: a different environment size (the Mytkowicz experiment), a different codegen-units count, or a
//! different target-cpu. None of them changes the answer. The question is whether they change the time.

use std::hint::black_box;
use std::time::Instant;

use reasonable_benchmarking::{generate_values, sum_of_squares};

const N: usize = 10_000;
const ITERS: u64 = 1_000;
const ROUNDS: usize = 300;

fn main() {
    let values = generate_values(N, 0xC0FFEE);

    let mut best = f64::INFINITY;
    for _ in 0..ROUNDS {
        let mut acc = 0u64;
        let start = Instant::now();
        for _ in 0..ITERS {
            acc = acc.wrapping_add(sum_of_squares(black_box(&values)));
        }
        let elapsed = start.elapsed();
        black_box(acc);
        let per_iter = elapsed.as_nanos() as f64 / ITERS as f64;
        if per_iter < best {
            best = per_iter;
        }
    }

    // Report the environment size too, so the Mytkowicz variant is self-documenting.
    let env_bytes: usize = std::env::vars().map(|(k, v)| k.len() + v.len() + 2).sum();
    println!("min {best:.3} ns/iter   (env ~{env_bytes} bytes)");
}
