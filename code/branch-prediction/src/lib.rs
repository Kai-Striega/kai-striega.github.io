//! Branch prediction, measured.
//!
//! Two halves, because there are two different predictors involved.
//!
//! Part A is a conditional branch: count how many values exceed a threshold. The data generator lets us dial
//! the probability that the branch is taken, which is the same thing as dialling how predictable it is.
//!
//! Part B is an indirect branch: a small bytecode interpreter whose dispatch is a jump table. Here the thing
//! we dial is how repetitive the instruction stream is.

use std::hint::black_box;

// ---------------------------------------------------------------------------------------------------------
// Part A: conditional branches
// ---------------------------------------------------------------------------------------------------------

/// The obvious way to write it. Whether this actually contains a branch once compiled is exactly the question
/// - LLVM is entirely capable of turning it into a `cmov`, or of vectorising it into a SIMD compare and add.
/// Check the assembly before trusting any number that comes out of it.
#[inline(never)]
pub fn count_above_naive(values: &[i32], threshold: i32) -> u64 {
    let mut count = 0u64;
    for &value in values {
        if value > threshold {
            count += 1;
        }
    }
    count
}

/// The same loop, with an optimisation barrier inside the taken arm so that a real, data dependent
/// conditional branch survives into the machine code.
#[inline(never)]
pub fn count_above_branchy(values: &[i32], threshold: i32) -> u64 {
    let mut count = 0u64;
    for &value in values {
        if value > threshold {
            count = black_box(count + 1);
        }
    }
    count
}

/// No branch at all: turn the comparison into a 0 or 1 and add it unconditionally.
#[inline(never)]
pub fn count_above_branchless(values: &[i32], threshold: i32) -> u64 {
    let mut count = 0u64;
    for &value in values {
        count += (value > threshold) as u64;
    }
    count
}

/// Branchless, with the same barrier as [`count_above_branchy`] so the two are compared on equal terms. The
/// barrier stops the loop being vectorised in both cases, leaving the branch as the only difference.
#[inline(never)]
pub fn count_above_branchless_barrier(values: &[i32], threshold: i32) -> u64 {
    let mut count = 0u64;
    for &value in values {
        count = black_box(count + (value > threshold) as u64);
    }
    count
}

/// A tiny deterministic PRNG, so every run generates identical data without pulling in a dependency.
pub struct XorShift64(pub u64);

impl XorShift64 {
    pub fn new(seed: u64) -> Self {
        XorShift64(seed)
    }

    pub fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }

    /// Uniform in `0..n`.
    pub fn below(&mut self, n: usize) -> usize {
        (self.next() % n as u64) as usize
    }
}

/// The threshold every benchmark compares against.
pub const THRESHOLD: i32 = 0;

/// Generate `n` values of which a `taken` fraction exceed [`THRESHOLD`], in random order.
///
/// The values themselves are always drawn from the same two pools, so the only thing that changes across the
/// sweep is how often the branch is taken, never the data's size or distribution of magnitudes.
pub fn generate_values(n: usize, taken: f64, seed: u64) -> Vec<i32> {
    let mut rng = XorShift64::new(seed);
    let mut values: Vec<i32> = (0..n)
        .map(|i| {
            // Deterministically place exactly `taken * n` values above the threshold, then shuffle, so the
            // realised proportion matches the requested one exactly rather than approximately.
            if (i as f64) < taken * n as f64 {
                1 + (rng.next() % 1000) as i32
            } else {
                -1 - (rng.next() % 1000) as i32
            }
        })
        .collect();

    // Fisher-Yates.
    for i in (1..values.len()).rev() {
        let j = rng.below(i + 1);
        values.swap(i, j);
    }
    values
}

/// The same values, sorted. Same multiset, same count, but now the branch goes one way and then the other.
pub fn sorted(values: &[i32]) -> Vec<i32> {
    let mut sorted = values.to_vec();
    sorted.sort_unstable();
    sorted
}

// ---------------------------------------------------------------------------------------------------------
// Part B: indirect branches
// ---------------------------------------------------------------------------------------------------------

/// A tiny bytecode.
///
/// Every operation is total and stack neutral: it reads the accumulator and writes the accumulator, so any
/// sequence of these is a valid program and no sequence can overflow or underflow. That matters, because it
/// means the *only* thing that differs between the programs we generate is the order of the opcodes.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Op {
    Inc,
    Dec,
    Double,
    Negate,
    Xor,
    RotateLeft,
    Square,
    Complement,
}

/// The eight opcodes, in order. The dispatch is therefore an eight way indirect branch.
pub const OPS: [Op; 8] = [
    Op::Inc,
    Op::Dec,
    Op::Double,
    Op::Negate,
    Op::Xor,
    Op::RotateLeft,
    Op::Square,
    Op::Complement,
];

const XOR_CONST: i64 = 0x5DEECE66D;

/// Run a program with a `match` based dispatch loop. This is the shape of a switch interpreter, and LLVM
/// compiles it to a jump table: one indirect branch, taken once per instruction.
#[inline(never)]
pub fn run_match(code: &[Op]) -> i64 {
    let mut acc: i64 = 1;
    for &op in code {
        acc = match op {
            Op::Inc => acc.wrapping_add(1),
            Op::Dec => acc.wrapping_sub(1),
            Op::Double => acc.wrapping_mul(2),
            Op::Negate => acc.wrapping_neg(),
            Op::Xor => acc ^ XOR_CONST,
            Op::RotateLeft => acc.rotate_left(1),
            Op::Square => acc.wrapping_mul(acc),
            Op::Complement => !acc,
        };
    }
    acc
}

type Handler = fn(i64) -> i64;

fn op_inc(acc: i64) -> i64 {
    acc.wrapping_add(1)
}
fn op_dec(acc: i64) -> i64 {
    acc.wrapping_sub(1)
}
fn op_double(acc: i64) -> i64 {
    acc.wrapping_mul(2)
}
fn op_negate(acc: i64) -> i64 {
    acc.wrapping_neg()
}
fn op_xor(acc: i64) -> i64 {
    acc ^ XOR_CONST
}
fn op_rotate_left(acc: i64) -> i64 {
    acc.rotate_left(1)
}
fn op_square(acc: i64) -> i64 {
    acc.wrapping_mul(acc)
}
fn op_complement(acc: i64) -> i64 {
    !acc
}

/// The same interpreter, dispatching through a table of function pointers instead of a `match`. The indirect
/// branch is now an indirect *call*, which the hardware tracks with different structures.
#[inline(never)]
pub fn run_fnptr(code: &[Op]) -> i64 {
    const TABLE: [Handler; 8] = [
        op_inc,
        op_dec,
        op_double,
        op_negate,
        op_xor,
        op_rotate_left,
        op_square,
        op_complement,
    ];
    let mut acc: i64 = 1;
    for &op in code {
        acc = TABLE[op as usize](acc);
    }
    acc
}

/// Build a program of `len` instructions whose opcode sequence repeats with the given `period`.
///
/// `period` must be a multiple of 8 and divide `len`. Each period block contains each of the eight opcodes
/// exactly `period / 8` times, shuffled, so **every program this function returns executes exactly the same
/// number of each opcode** no matter the period. The only variable is the order, and therefore how learnable
/// the sequence is.
pub fn generate_program(len: usize, period: usize, seed: u64) -> Vec<Op> {
    assert!(period % 8 == 0, "period must be a multiple of 8");
    assert!(len % period == 0, "period must divide len");

    let mut rng = XorShift64::new(seed);

    let mut block: Vec<Op> = Vec::with_capacity(period);
    for &op in OPS.iter() {
        for _ in 0..period / 8 {
            block.push(op);
        }
    }
    for i in (1..block.len()).rev() {
        let j = rng.below(i + 1);
        block.swap(i, j);
    }

    let mut code = Vec::with_capacity(len);
    while code.len() < len {
        code.extend_from_slice(&block);
    }
    code
}

/// A program with no repeating structure at all: the opcode mix is still exactly uniform, but the order is
/// shuffled across the whole length rather than within a block.
pub fn generate_random_program(len: usize, seed: u64) -> Vec<Op> {
    generate_program(len, len, seed)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn histogram(code: &[Op]) -> [usize; 8] {
        let mut counts = [0usize; 8];
        for &op in code {
            counts[op as usize] += 1;
        }
        counts
    }

    #[test]
    fn counting_variants_agree() {
        for taken in [0.0, 0.25, 0.5, 0.75, 1.0] {
            let values = generate_values(10_000, taken, 42);
            let expected = values.iter().filter(|&&v| v > THRESHOLD).count() as u64;
            assert_eq!(count_above_naive(&values, THRESHOLD), expected);
            assert_eq!(count_above_branchy(&values, THRESHOLD), expected);
            assert_eq!(count_above_branchless(&values, THRESHOLD), expected);
            assert_eq!(count_above_branchless_barrier(&values, THRESHOLD), expected);
        }
    }

    #[test]
    fn generator_hits_the_requested_proportion() {
        for taken in [0.0, 0.1, 0.5, 0.9, 1.0] {
            let values = generate_values(10_000, taken, 7);
            let above = values.iter().filter(|&&v| v > THRESHOLD).count();
            assert_eq!(above, (taken * 10_000.0) as usize, "taken = {taken}");
        }
    }

    #[test]
    fn sorting_preserves_the_multiset() {
        let values = generate_values(10_000, 0.5, 1);
        let s = sorted(&values);
        let mut a = values.clone();
        a.sort_unstable();
        assert_eq!(a, s);
        assert_eq!(
            count_above_branchy(&values, THRESHOLD),
            count_above_branchy(&s, THRESHOLD)
        );
    }

    #[test]
    fn every_program_runs_the_same_opcode_mix() {
        let len = 1 << 16;
        let uniform = [len / 8; 8];
        for period in [8, 16, 32, 64, 128, 256, 512, 1024] {
            let code = generate_program(len, period, 3);
            assert_eq!(code.len(), len);
            assert_eq!(histogram(&code), uniform, "period = {period}");
        }
        assert_eq!(histogram(&generate_random_program(len, 3)), uniform);
    }

    #[test]
    fn program_really_repeats_with_its_period() {
        let len = 1 << 12;
        let period = 64;
        let code = generate_program(len, period, 5);
        for i in 0..len {
            assert_eq!(code[i], code[i % period]);
        }
    }

    #[test]
    fn dispatch_variants_agree() {
        for period in [8, 64, 1024] {
            let code = generate_program(1 << 12, period, 11);
            assert_eq!(run_match(&code), run_fnptr(&code), "period = {period}");
        }
    }
}
