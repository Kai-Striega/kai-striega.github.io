//! A thin binary for `perf stat` to wrap around, so the counters measure one variant and nothing else.
//!
//! Usage: counters <variant> [elements] [passes]
//!
//!   variant:  contiguous | boxed-ordered | boxed-shuffled | list-chase
//!             gather-independent | gather-dependent
//!   elements: how many values, default 4194304 (nodes then occupy well over 100 MB)
//!   passes:   how many times to walk them, default 5
//!
//! Every published Rust number in the post comes from this binary. Criterion is kept for exploratory work
//! only: mixing the two is how part 2 nearly published a figure that was three times wrong.
//!
//! `perf stat` counts the whole process, and building four million nodes costs far more than walking them
//! once. So `passes = 0` is supported deliberately: it does the setup and skips the loop, which gives a
//! baseline to subtract. Without that subtraction the fast variants are almost entirely setup, and the
//! counters describe the allocator rather than the traversal.

use std::hint::black_box;
use std::time::Instant;

use pointer_chasing::*;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let variant = args.get(1).map(String::as_str).unwrap_or("contiguous");
    let n: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(1 << 22);
    let passes: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(5);

    let gather = variant.starts_with("gather");

    // Built outside the timed region: allocating four million nodes takes far longer than walking them.
    let nodes = if gather { None } else { Some(Nodes::new(n, 7)) };
    let contiguous = nodes.as_ref().map(|ns| ns.contiguous());
    let g = if gather { Some(Gather::new(n, 11)) } else { None };

    let start = Instant::now();
    let mut total = 0u64;
    for _ in 0..passes {
        total = total.wrapping_add(match variant {
            "contiguous" => sum_contiguous(black_box(contiguous.as_ref().unwrap())),
            "boxed-ordered" => sum_boxed_ordered(black_box(nodes.as_ref().unwrap())),
            "boxed-shuffled" => sum_boxed_shuffled(black_box(nodes.as_ref().unwrap())),
            "list-chase" => sum_list_chase(black_box(nodes.as_ref().unwrap())),
            "gather-independent" => sum_gather_independent(black_box(g.as_ref().unwrap())),
            "gather-dependent" => sum_gather_dependent(black_box(g.as_ref().unwrap())),
            other => {
                eprintln!("unknown variant {other:?}");
                std::process::exit(1);
            }
        });
    }
    let elapsed = start.elapsed();
    black_box(total);

    // If a variant ever disagrees, the benchmark is measuring nothing.
    let expected = if gather {
        g.as_ref().unwrap().expected()
    } else {
        nodes.as_ref().unwrap().expected()
    }
    .wrapping_mul(passes as u64);
    assert_eq!(total, expected, "variant {variant} produced the wrong total");

    let elements = (n * passes) as f64;
    let bytes = if gather {
        n * 8
    } else {
        n * std::mem::size_of::<Node>()
    };
    let per_element = if passes == 0 {
        f64::NAN
    } else {
        elapsed.as_secs_f64() * 1e9 / elements
    };
    println!(
        "{variant:<19} {n} elements x {passes} passes  {:>9.1} ms  {per_element:>7.2} ns/element  working set {:.1} MB",
        elapsed.as_secs_f64() * 1e3,
        bytes as f64 / 1e6,
    );
}
