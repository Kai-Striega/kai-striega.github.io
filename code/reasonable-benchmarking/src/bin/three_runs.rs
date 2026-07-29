//! Experiment E1: the same benchmark, three times, three answers.
//!
//! This is the Rust port of the talk's opening slide, where `python -m timeit` prints 343 ms, then
//! 310 ms, then 312 ms for the *identical* command and asks which one is the true time. We do the same
//! by hand: time one fixed, deterministic workload three separate times and print what we get.
//!
//!     cargo run --release --bin three_runs
//!
//! The answer the workload computes is byte-for-byte identical across all three rounds. Only the runtime
//! moves. That gap is the entire reason the rest of the series exists.

use std::hint::black_box;
use std::time::Instant;

use reasonable_benchmarking::{generate_values, sum_of_squares};

const N: usize = 10_000;
const ITERS: u64 = 100_000;
const ROUNDS: usize = 3;

fn main() {
    let values = generate_values(N, 0xC0FFEE);

    // The answer never changes. Print it once so the point is unmissable: the computation is settled,
    // only the clock disagrees with itself.
    let answer = sum_of_squares(&values);
    println!("answer (identical every run): {answer}");
    println!("workload: sum_of_squares over {N} u64, {ITERS} iterations per round\n");

    for round in 1..=ROUNDS {
        let mut acc = 0u64;
        let start = Instant::now();
        for _ in 0..ITERS {
            // black_box on the input stops the optimiser hoisting this loop-invariant call out of the
            // loop; folding the result into `acc` stops it deleting the call outright. Without both, we
            // would be timing nothing, which is exactly experiment E2.
            acc = acc.wrapping_add(sum_of_squares(black_box(&values)));
        }
        let elapsed = start.elapsed();
        black_box(acc);

        let per_iter_ns = elapsed.as_nanos() as f64 / ITERS as f64;
        println!("round {round}: {elapsed:>12.3?}  ({per_iter_ns:8.2} ns / iteration)");
    }

    println!("\nSame code, same input, same answer. Which round was the \"real\" time?");
}
