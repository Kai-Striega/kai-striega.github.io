//! False sharing, measured.
//!
//! Every variant here computes exactly the same total over exactly the same readings, using the same number
//! of threads. The only thing that differs is *where in memory* each thread keeps its running total, and
//! therefore whether two threads end up fighting over one 64 byte cache line.
//!
//! A note on why the counters are atomics. The obvious way to write this hands each thread a `&mut u64` out
//! of a shared slice, but then LLVM keeps the accumulator in a register and only writes it back once at the
//! end, which quietly turns every variant into the fast one. A `Vec<AtomicU64>` of per-thread counters cannot
//! be register-promoted, and happens to be what people actually write when they want per-thread statistics.

use std::hint::black_box;
use std::sync::atomic::{AtomicU64, Ordering};

/// One reading from a weather station, as in part 1 of the series. Exactly 32 bytes.
#[derive(Clone, Copy, Debug)]
pub struct Reading {
    pub timestamp: u64,
    pub station_id: u32,
    pub temperature: i32,
    pub humidity: f32,
    pub pressure: f32,
    pub wind_speed: f32,
    pub rainfall: f32,
}

/// A `u64` that occupies a whole cache line all by itself.
///
/// `align(64)` forces both the size and the stride of an array of these up to 64 bytes, so no two of them can
/// ever land on the same line. The other 56 bytes are never read. That is the point.
#[repr(align(64))]
pub struct Padded(pub AtomicU64);

impl Padded {
    pub fn new(v: u64) -> Self {
        Padded(AtomicU64::new(v))
    }
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
}

pub fn generate(n: usize) -> Vec<Reading> {
    let mut rng = XorShift64::new(0x5DEECE66D);
    (0..n)
        .map(|i| {
            let r = rng.next();
            Reading {
                timestamp: 1_700_000_000 + i as u64,
                station_id: (r % 512) as u32,
                temperature: (r % 7001) as i32 - 2000,
                humidity: (r % 1001) as f32 / 10.0,
                pressure: 950.0 + (r % 1001) as f32 / 10.0,
                wind_speed: (r % 401) as f32 / 10.0,
                rainfall: (r % 201) as f32 / 10.0,
            }
        })
        .collect()
}

// ---------------------------------------------------------------------------------------------------------
// Thread pinning
// ---------------------------------------------------------------------------------------------------------

/// Pin the calling thread to one logical CPU.
///
/// This is not optional. On a 12900K the P-cores are logical CPUs 0-15 arranged as SMT pairs, so `(0,1)` are
/// two hyperthreads of one physical core sharing L1 and L2. Two threads there do not false-share in the way
/// we are trying to measure. [`physical_cores`] returns one CPU per physical core.
pub fn pin_to(cpu: usize) -> bool {
    unsafe {
        let mut set: libc::cpu_set_t = std::mem::zeroed();
        libc::CPU_ZERO(&mut set);
        libc::CPU_SET(cpu, &mut set);
        libc::sched_setaffinity(0, std::mem::size_of::<libc::cpu_set_t>(), &set) == 0
    }
}

/// Which CPU the calling thread is actually running on. Used to prove pinning took effect.
pub fn current_cpu() -> i32 {
    unsafe { libc::sched_getcpu() }
}

/// One logical CPU per physical P-core: 0, 2, 4, ... Siblings share a physical core, so we take every other.
pub fn physical_cores(n: usize) -> Vec<usize> {
    (0..n).map(|i| i * 2).collect()
}

/// Both hyperthreads of the first `n / 2` physical cores: 0, 1, 2, 3, ... Used only to show what going
/// through SMT siblings does to the result.
pub fn sibling_cores(n: usize) -> Vec<usize> {
    (0..n).collect()
}

// ---------------------------------------------------------------------------------------------------------
// The variants
// ---------------------------------------------------------------------------------------------------------

// Every variant takes `passes`: the number of times each thread sweeps its own slice. The threads are
// spawned once and loop internally, because spawning eight OS threads costs on the order of a hundred
// microseconds, which is more than the work itself and would be all we measured.

/// Single threaded reference.
pub fn sum_single(readings: &[Reading], passes: usize) -> u64 {
    let mut total = 0u64;
    for _ in 0..passes {
        for r in readings {
            total = total.wrapping_add(r.temperature as u64);
        }
    }
    total
}

/// The bug. `threads` counters packed into a `Vec<AtomicU64>`, so eight of them fit in one 64 byte line, and
/// every thread hammers its own counter on every element.
pub fn sum_shared(readings: &[Reading], cpus: &[usize], passes: usize) -> u64 {
    let counters: Vec<AtomicU64> = (0..cpus.len()).map(|_| AtomicU64::new(0)).collect();
    let chunk = readings.len() / cpus.len();

    std::thread::scope(|s| {
        for (tid, (&cpu, slice)) in cpus.iter().zip(readings.chunks(chunk)).enumerate() {
            let counter = &counters[tid];
            s.spawn(move || {
                pin_to(cpu);
                for _ in 0..passes {
                    for r in slice {
                        counter.fetch_add(r.temperature as u64, Ordering::Relaxed);
                    }
                }
            });
        }
    });

    counters.iter().map(|c| c.load(Ordering::Relaxed)).fold(0u64, u64::wrapping_add)
}

/// Fix one, the demonstration. Same code, but each counter gets a whole cache line to itself.
pub fn sum_padded(readings: &[Reading], cpus: &[usize], passes: usize) -> u64 {
    let counters: Vec<Padded> = (0..cpus.len()).map(|_| Padded::new(0)).collect();
    let chunk = readings.len() / cpus.len();

    std::thread::scope(|s| {
        for (tid, (&cpu, slice)) in cpus.iter().zip(readings.chunks(chunk)).enumerate() {
            let counter = &counters[tid].0;
            s.spawn(move || {
                pin_to(cpu);
                for _ in 0..passes {
                    for r in slice {
                        counter.fetch_add(r.temperature as u64, Ordering::Relaxed);
                    }
                }
            });
        }
    });

    counters.iter().map(|c| c.0.load(Ordering::Relaxed)).fold(0u64, u64::wrapping_add)
}

/// Fix two, the one you should actually write. Accumulate in a local and touch the shared line once.
pub fn sum_local(readings: &[Reading], cpus: &[usize], passes: usize) -> u64 {
    let counters: Vec<AtomicU64> = (0..cpus.len()).map(|_| AtomicU64::new(0)).collect();
    let chunk = readings.len() / cpus.len();

    std::thread::scope(|s| {
        for (tid, (&cpu, slice)) in cpus.iter().zip(readings.chunks(chunk)).enumerate() {
            let counter = &counters[tid];
            s.spawn(move || {
                pin_to(cpu);
                let mut local = 0u64;
                for _ in 0..passes {
                    for r in slice {
                        local = local.wrapping_add(r.temperature as u64);
                    }
                }
                counter.store(local, Ordering::Relaxed);
            });
        }
    });

    counters.iter().map(|c| c.load(Ordering::Relaxed)).fold(0u64, u64::wrapping_add)
}

/// Every thread *reads* the same cache line on every element, and writes nothing to it. Sharing a line is
/// only expensive when somebody writes.
pub fn sum_readonly(readings: &[Reading], cpus: &[usize], passes: usize) -> u64 {
    let shared = AtomicU64::new(1);
    let counters: Vec<Padded> = (0..cpus.len()).map(|_| Padded::new(0)).collect();
    let chunk = readings.len() / cpus.len();

    std::thread::scope(|s| {
        for (tid, (&cpu, slice)) in cpus.iter().zip(readings.chunks(chunk)).enumerate() {
            let counter = &counters[tid].0;
            let shared = &shared;
            s.spawn(move || {
                pin_to(cpu);
                let mut local = 0u64;
                for _ in 0..passes {
                    for r in slice {
                        // Read the shared line every iteration. black_box stops the load being hoisted out.
                        let scale = black_box(shared.load(Ordering::Relaxed));
                        local = local.wrapping_add((r.temperature as u64).wrapping_mul(scale));
                    }
                }
                counter.store(local, Ordering::Relaxed);
            });
        }
    });

    counters.iter().map(|c| c.0.load(Ordering::Relaxed)).fold(0u64, u64::wrapping_add)
}

/// True sharing: one counter, genuinely shared, every thread adding to it. The contention is real rather
/// than accidental, so there is no padding that can help.
pub fn sum_true_shared(readings: &[Reading], cpus: &[usize], passes: usize) -> u64 {
    let counter = AtomicU64::new(0);
    let chunk = readings.len() / cpus.len();

    std::thread::scope(|s| {
        for (&cpu, slice) in cpus.iter().zip(readings.chunks(chunk)) {
            let counter = &counter;
            s.spawn(move || {
                pin_to(cpu);
                for _ in 0..passes {
                    for r in slice {
                        counter.fetch_add(r.temperature as u64, Ordering::Relaxed);
                    }
                }
            });
        }
    });

    counter.load(Ordering::Relaxed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn padded_occupies_a_whole_line() {
        assert_eq!(std::mem::size_of::<Padded>(), 64);
        assert_eq!(std::mem::align_of::<Padded>(), 64);
        // And the stride of an array of them really is 64, which is what stops two sharing a line.
        let v = [Padded::new(0), Padded::new(0)];
        let a = &v[0] as *const Padded as usize;
        let b = &v[1] as *const Padded as usize;
        assert_eq!(b - a, 64);
    }

    /// How many distinct 64 byte cache lines a set of addresses covers.
    fn lines_covered(addrs: &[usize]) -> usize {
        let mut lines: Vec<usize> = addrs.iter().map(|a| a / 64).collect();
        lines.sort_unstable();
        lines.dedup();
        lines.len()
    }

    #[test]
    fn unpadded_counters_share_lines() {
        // Eight AtomicU64 in a row are packed into 56 bytes, 8 bytes apart.
        let v: Vec<AtomicU64> = (0..8).map(|_| AtomicU64::new(0)).collect();
        let addrs: Vec<usize> = v.iter().map(|c| c as *const AtomicU64 as usize).collect();
        assert_eq!(addrs[1] - addrs[0], 8, "counters should be 8 bytes apart");
        assert_eq!(addrs[7] - addrs[0], 56);

        // A Vec is only 8 byte aligned, so the eight can straddle a boundary and land on two lines rather
        // than one. Either way they cannot possibly get a line each, which is the bug.
        let lines = lines_covered(&addrs);
        assert!(lines <= 2, "expected 1 or 2 lines, got {lines}");
        assert!(lines < 8, "eight counters must not get a line each");
    }

    #[test]
    fn padded_counters_get_a_line_each() {
        let v: Vec<Padded> = (0..8).map(|_| Padded::new(0)).collect();
        let addrs: Vec<usize> = v.iter().map(|c| c as *const Padded as usize).collect();
        assert_eq!(lines_covered(&addrs), 8, "each padded counter should own its line");
    }

    #[test]
    fn every_variant_agrees() {
        let readings = generate(1 << 14);
        for passes in [1usize, 3] {
            let expected = sum_single(&readings, passes);
            for threads in [1usize, 2, 4] {
                let cpus = physical_cores(threads);
                let ctx = format!("{threads} threads, {passes} passes");
                assert_eq!(sum_shared(&readings, &cpus, passes), expected, "shared, {ctx}");
                assert_eq!(sum_padded(&readings, &cpus, passes), expected, "padded, {ctx}");
                assert_eq!(sum_local(&readings, &cpus, passes), expected, "local, {ctx}");
                assert_eq!(sum_true_shared(&readings, &cpus, passes), expected, "true shared, {ctx}");
                // readonly multiplies by a shared 1, so it totals the same.
                assert_eq!(sum_readonly(&readings, &cpus, passes), expected, "readonly, {ctx}");
            }
        }
    }

    #[test]
    fn pinning_takes_effect() {
        // Pin to a couple of specific CPUs and confirm the kernel actually moved us.
        for cpu in [2usize, 6] {
            let ok = std::thread::spawn(move || {
                assert!(pin_to(cpu), "sched_setaffinity failed for cpu {cpu}");
                // Give the scheduler a moment to migrate, then check.
                std::thread::yield_now();
                current_cpu()
            })
            .join()
            .unwrap();
            assert_eq!(ok, cpu as i32, "thread did not end up on cpu {cpu}");
        }
    }

    #[test]
    fn physical_cores_skips_smt_siblings() {
        assert_eq!(physical_cores(4), vec![0, 2, 4, 6]);
        assert_eq!(sibling_cores(4), vec![0, 1, 2, 3]);
    }
}
