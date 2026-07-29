//! Workloads for the *Reasonable Benchmarking* series.
//!
//! None of these functions is interesting on its own. The series is not about making code fast; it is
//! about what happens when you try to *measure* it. So the workloads are deliberately dull and, above
//! all, deterministic: given the same input they return the same answer on every run and every machine.
//! That determinism is the whole trick. If the answer never changes but the runtime does, then every bit
//! of variation we see is a property of the measurement, not of the computation.

/// A tiny, fast, deterministic PRNG (xorshift64). We avoid `rand` on purpose: the generator is part of
/// the experiment, so it has to produce the exact same stream everywhere, forever, with no dependency
/// that might change under us.
pub struct XorShift64(u64);

impl XorShift64 {
    pub fn new(seed: u64) -> Self {
        // Any non-zero seed works; guard against the one degenerate value.
        XorShift64(seed | 1)
    }

    #[inline]
    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }
}

/// Sum of squares over a slice, with wrapping arithmetic so it never panics on overflow.
///
/// This is the victim for parts one and two. It is pure and total, which makes it the perfect subject
/// for two separate lessons. First, its runtime is a clean measurement target, because the answer is
/// fixed. Second, it is exactly the kind of loop an optimiser will *delete* if the caller ignores the
/// result, which is the entire point of experiment E2.
#[inline]
pub fn sum_of_squares(values: &[u64]) -> u64 {
    values
        .iter()
        .fold(0u64, |acc, &x| acc.wrapping_add(x.wrapping_mul(x)))
}

/// Deterministic input for the sum-of-squares workload.
pub fn generate_values(n: usize, seed: u64) -> Vec<u64> {
    let mut rng = XorShift64::new(seed);
    (0..n).map(|_| rng.next_u64()).collect()
}

/// Build a single random permutation cycle over `n` slots using Sattolo's algorithm, returning a `next`
/// array where `next[i]` is the slot to visit after `i`. Because it is one big cycle, following it visits
/// every slot exactly once before returning to the start.
///
/// This is the setup for a *pointer-chasing* workload. Each step reads a location whose address was only
/// just produced by the previous read, so the CPU cannot prefetch ahead: the loop runs at the mercy of
/// memory latency. Lemire uses exactly this shape to show that memory-bound timings are decidedly not
/// normally distributed, which is what we lean on in part two.
pub fn build_cycle(n: usize, seed: u64) -> Vec<usize> {
    let mut next: Vec<usize> = (0..n).collect();
    let mut rng = XorShift64::new(seed);
    // Sattolo: produces a permutation that is a single n-cycle.
    for i in (1..n).rev() {
        let j = (rng.next_u64() as usize) % i;
        next.swap(i, j);
    }
    next
}

/// Follow the cycle `steps` times, returning the final slot so the caller can consume it and keep the
/// optimiser honest.
#[inline]
pub fn chase(next: &[usize], start: usize, steps: usize) -> usize {
    let mut p = start;
    for _ in 0..steps {
        p = next[p];
    }
    p
}

/// The input shapes for the sort comparison in part three. A good benchmark *suite* deliberately covers
/// cases that stress an implementation differently, because a single input only illuminates one facet of
/// the system. These four do exactly that: `sort_unstable` (pattern-defeating quicksort) and the stable
/// merge `sort` trade places depending on which one they see.
#[derive(Clone, Copy, Debug)]
pub enum Pattern {
    /// Uniform random: the case everyone benchmarks and nobody actually has.
    Random,
    /// Already sorted: the adaptive algorithms love this.
    Sorted,
    /// Reverse sorted: a classic worst case for a naive quicksort pivot.
    Reversed,
    /// Only a handful of distinct values, heavily repeated.
    FewUnique,
}

impl Pattern {
    pub const ALL: [Pattern; 4] = [
        Pattern::Random,
        Pattern::Sorted,
        Pattern::Reversed,
        Pattern::FewUnique,
    ];

    pub fn name(self) -> &'static str {
        match self {
            Pattern::Random => "random",
            Pattern::Sorted => "sorted",
            Pattern::Reversed => "reversed",
            Pattern::FewUnique => "few_unique",
        }
    }
}

/// Deterministic input for the sort suite.
pub fn generate_pattern(n: usize, pattern: Pattern, seed: u64) -> Vec<u64> {
    let mut rng = XorShift64::new(seed);
    let mut v: Vec<u64> = match pattern {
        Pattern::Random => (0..n).map(|_| rng.next_u64()).collect(),
        Pattern::FewUnique => (0..n).map(|_| rng.next_u64() % 8).collect(),
        Pattern::Sorted | Pattern::Reversed => (0..n).map(|_| rng.next_u64()).collect(),
    };
    match pattern {
        Pattern::Sorted => v.sort_unstable(),
        Pattern::Reversed => {
            v.sort_unstable();
            v.reverse();
        }
        _ => {}
    }
    v
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sum_of_squares_is_deterministic() {
        let a = generate_values(1000, 0xC0FFEE);
        let b = generate_values(1000, 0xC0FFEE);
        assert_eq!(a, b);
        assert_eq!(sum_of_squares(&a), sum_of_squares(&b));
    }

    #[test]
    fn patterns_have_the_expected_shape() {
        let sorted = generate_pattern(1000, Pattern::Sorted, 1);
        assert!(sorted.windows(2).all(|w| w[0] <= w[1]));

        let reversed = generate_pattern(1000, Pattern::Reversed, 1);
        assert!(reversed.windows(2).all(|w| w[0] >= w[1]));

        let few = generate_pattern(1000, Pattern::FewUnique, 1);
        assert!(few.iter().all(|&x| x < 8));
    }
}
