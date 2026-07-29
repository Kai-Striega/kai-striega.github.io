//! Experiment E2: the benchmark the compiler deleted.
//!
//!     cargo run --release --bin dce
//!
//! In Python, the noise in a measurement mostly *adds* work you did not ask for: the interpreter, the
//! garbage collector, other processes. In a compiled language the sharpest pitfall runs the other way:
//! the optimiser *removes* work you did ask for. `sum_of_squares` is pure, so if the caller ignores the
//! result, LLVM is free to conclude the whole loop has no observable effect and erase it. You are then
//! benchmarking an empty loop and reporting a spectacular, entirely fictional throughput.
//!
//! `std::hint::black_box` is the fix: it is an optimisation barrier that forces the compiler to assume a
//! value is used. This experiment runs the identical loop twice, with and without the barrier, so the
//! difference is nothing but dead-code elimination.

use std::hint::black_box;
use std::time::Instant;

use reasonable_benchmarking::{generate_values, sum_of_squares};

const N: usize = 10_000;
const ITERS: u64 = 1_000_000;

fn main() {
    let values = generate_values(N, 0xC0FFEE);

    // ---- No barrier: the result is computed and immediately dropped. ----
    // The compiler can see that nothing downstream depends on the return value, so it is entitled to
    // delete the call, then the now-empty loop body, then the loop.
    let start = Instant::now();
    for _ in 0..ITERS {
        sum_of_squares(&values);
    }
    let without_barrier = start.elapsed();

    // ---- With barrier: the input is laundered through black_box each iteration and the result is
    // folded into an accumulator that we then black_box. Now the compiler must actually do the work. ----
    let mut acc = 0u64;
    let start = Instant::now();
    for _ in 0..ITERS {
        acc = acc.wrapping_add(sum_of_squares(black_box(&values)));
    }
    let with_barrier = start.elapsed();
    black_box(acc);

    let ns = |d: std::time::Duration| d.as_nanos() as f64 / ITERS as f64;
    let gbytes_per_s = |d: std::time::Duration| {
        (ITERS as f64 * N as f64 * 8.0) / d.as_secs_f64() / 1e9
    };

    println!("workload: sum_of_squares over {N} u64, {ITERS} iterations\n");
    println!(
        "no black_box : {without_barrier:>12.3?}  ({:8.3} ns/iter, {:8.1} GB/s of \"work\")",
        ns(without_barrier),
        gbytes_per_s(without_barrier),
    );
    println!(
        "black_box    : {with_barrier:>12.3?}  ({:8.3} ns/iter, {:8.1} GB/s)",
        ns(with_barrier),
        gbytes_per_s(with_barrier),
    );

    let ratio = with_barrier.as_secs_f64() / without_barrier.as_secs_f64().max(f64::MIN_POSITIVE);
    println!(
        "\nThe barrier-free loop looks {ratio:.0}x faster. It is not faster. It does not exist."
    );
}
