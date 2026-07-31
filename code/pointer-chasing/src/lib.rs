//! Pointer chasing, measured.
//!
//! Two different things go wrong when your data is a graph of pointers, and they are usually conflated:
//!
//! 1. **Locality.** Objects scattered across the heap mean a cache miss per element instead of one per
//!    sixteen.
//! 2. **Dependency.** If the address of the next load comes *out of* the current load, the core cannot
//!    overlap the misses. Golden Cove can track 16 L1 misses at once; a pointer chain lets it use one.
//!
//! The variants here are arranged to separate those. `boxed_ordered`, `boxed_shuffled` and `list_chase` walk
//! exactly the same heap objects: the first in allocation order, the second and third in the same shuffled
//! order as each other. So `boxed_shuffled` against `list_chase` isolates the dependency, because the only
//! difference between them is whether the next address is read from a streamed array or from the node the
//! core is still waiting for.
//!
//! `gather_independent` and `gather_dependent` do the same thing again over one contiguous allocation, which
//! removes the allocator from the picture entirely and makes the two touch a provably identical set of cache
//! lines.

use std::hint::black_box;
use std::ptr;

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

/// A permutation of `0..n`, Fisher-Yates.
///
/// Read as a *visit order* rather than as a mapping, this is all we need: linking each element to the one
/// that follows it in the permutation, and wrapping the last back to the first, always produces a single
/// cycle of length `n`. That matters, because a chase built from an arbitrary index mapping would decompose
/// into several short cycles and quietly traverse a fraction of the data.
pub fn visit_order(n: usize, seed: u64) -> Vec<usize> {
    let mut rng = XorShift64::new(seed);
    let mut order: Vec<usize> = (0..n).collect();
    for i in (1..n).rev() {
        let j = (rng.next() % (i as u64 + 1)) as usize;
        order.swap(i, j);
    }
    order
}

/// One heap node. Sixteen bytes: a payload and a pointer to whatever comes next.
///
/// Every heap-allocated variant uses this same type, so they all allocate the same number of objects of the
/// same size at the same addresses. Only the route through them differs.
#[repr(C)]
pub struct Node {
    pub value: u64,
    pub next: *const Node,
}

/// The heap-object variants share one set of nodes, built once.
///
/// `nodes` owns them. `order` is the sequence of pointers to follow, and each node's `next` field points at
/// the same successor, so a chase and a walk of `order` visit identical addresses in identical order.
pub struct Nodes {
    // clippy suggests `Vec<Node>` here, which would be a contiguous block of nodes and would delete the
    // experiment. One separate allocation per node is the thing being measured.
    #[allow(clippy::vec_box)]
    nodes: Vec<Box<Node>>,
    pub order: Vec<*const Node>,
    pub head: *const Node,
}

impl Nodes {
    pub fn new(n: usize, seed: u64) -> Self {
        let mut rng = XorShift64::new(seed ^ 0x9e37_79b9);
        // Allocated in ascending index order, one at a time, exactly as an interpreter allocates boxed
        // integers as it builds a list. Shuffling happens afterwards and only to the pointers, so the object
        // set is identical between the ordered and shuffled variants.
        let mut nodes: Vec<Box<Node>> = (0..n)
            .map(|_| {
                Box::new(Node {
                    value: rng.next() >> 16,
                    next: ptr::null(),
                })
            })
            .collect();

        let perm = visit_order(n, seed);
        for k in 0..n {
            let succ: *const Node = &*nodes[perm[(k + 1) % n]];
            nodes[perm[k]].next = succ;
        }

        let order = perm.iter().map(|&i| &*nodes[i] as *const Node).collect();
        let head: *const Node = &*nodes[perm[0]];
        Nodes { nodes, order, head }
    }

    pub fn len(&self) -> usize {
        self.nodes.len()
    }

    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }

    /// The total every heap variant must agree on.
    pub fn expected(&self) -> u64 {
        self.nodes.iter().map(|n| n.value).sum()
    }

    /// A1's data: the same values, contiguous.
    pub fn contiguous(&self) -> Vec<u64> {
        self.nodes.iter().map(|n| n.value).collect()
    }
}

/// A1. One allocation, walked front to back. The prefetcher has nothing to work out.
pub fn sum_contiguous(values: &[u64]) -> u64 {
    let mut total = 0u64;
    for &v in values {
        total = total.wrapping_add(v);
    }
    black_box(total)
}

/// A2. A pointer per element, but dereferenced in allocation order, so the addresses still march upwards and
/// the prefetcher still mostly wins. This is a Python list that has never been reordered.
pub fn sum_boxed_ordered(nodes: &Nodes) -> u64 {
    let mut total = 0u64;
    for node in &nodes.nodes {
        total = total.wrapping_add(node.value);
    }
    black_box(total)
}

/// A3. The same objects, visited in shuffled order. Locality is gone, but the *addresses* still arrive in a
/// streamed array, so the core can run many of these misses at once.
pub fn sum_boxed_shuffled(nodes: &Nodes) -> u64 {
    let mut total = 0u64;
    for &p in &nodes.order {
        total = total.wrapping_add(unsafe { (*p).value });
    }
    black_box(total)
}

/// A4. The same objects again, in the same order again, but each address is read out of the node before it.
/// Nothing can start until the previous load lands.
pub fn sum_list_chase(nodes: &Nodes) -> u64 {
    let mut total = 0u64;
    let mut p = nodes.head;
    for _ in 0..nodes.len() {
        unsafe {
            total = total.wrapping_add((*p).value);
            p = (*p).next;
        }
    }
    black_box(total)
}

/// The contiguous version of the same isolation, with the allocator taken out of the picture.
///
/// `data[i]` holds the index to visit after `i`. Summing those values while following them (dependent) and
/// summing them while reading the indices from `order` (independent) touch precisely the same cache lines in
/// precisely the same sequence, and produce precisely the same total.
pub struct Gather {
    pub data: Vec<u64>,
    pub order: Vec<u64>,
    pub start: usize,
}

impl Gather {
    pub fn new(n: usize, seed: u64) -> Self {
        let perm = visit_order(n, seed);
        let mut data = vec![0u64; n];
        for k in 0..n {
            data[perm[k]] = perm[(k + 1) % n] as u64;
        }
        let order = perm.iter().map(|&i| i as u64).collect();
        Gather {
            data,
            order,
            start: perm[0],
        }
    }

    /// Each index is visited exactly once, so both variants sum every element of `data`.
    pub fn expected(&self) -> u64 {
        self.data.iter().copied().fold(0u64, u64::wrapping_add)
    }
}

/// B1. The addresses are known well in advance, so the core issues many loads before the first returns.
pub fn sum_gather_independent(g: &Gather) -> u64 {
    let mut total = 0u64;
    for &i in &g.order {
        total = total.wrapping_add(g.data[i as usize]);
    }
    black_box(total)
}

/// B2. Same addresses, same order, same count. The only change is that each one has to be waited for.
pub fn sum_gather_dependent(g: &Gather) -> u64 {
    let mut total = 0u64;
    let mut i = g.start;
    for _ in 0..g.data.len() {
        let next = g.data[i];
        total = total.wrapping_add(next);
        i = next as usize;
    }
    black_box(total)
}

#[cfg(test)]
mod tests {
    use super::*;

    const N: usize = 4096;

    #[test]
    fn visit_order_is_a_permutation() {
        let mut seen = vec![false; N];
        for i in visit_order(N, 42) {
            assert!(!seen[i], "index {i} appeared twice");
            seen[i] = true;
        }
        assert!(seen.into_iter().all(|s| s));
    }

    #[test]
    fn the_chase_is_one_full_cycle() {
        // A chase built from a permutation read as a mapping would break into short cycles and silently
        // traverse only part of the data, which looks like a very fast benchmark.
        let nodes = Nodes::new(N, 7);
        let mut p = nodes.head;
        let mut steps = 0usize;
        loop {
            p = unsafe { (*p).next };
            steps += 1;
            if p == nodes.head {
                break;
            }
            assert!(steps <= N, "cycle longer than the data");
        }
        assert_eq!(steps, N, "chase visits {steps} of {N} nodes");
    }

    #[test]
    fn every_heap_variant_agrees() {
        let nodes = Nodes::new(N, 7);
        let expected = nodes.expected();
        assert_eq!(sum_contiguous(&nodes.contiguous()), expected);
        assert_eq!(sum_boxed_ordered(&nodes), expected);
        assert_eq!(sum_boxed_shuffled(&nodes), expected);
        assert_eq!(sum_list_chase(&nodes), expected);
    }

    #[test]
    fn both_gathers_agree() {
        let g = Gather::new(N, 11);
        let expected = g.expected();
        assert_eq!(sum_gather_independent(&g), expected);
        assert_eq!(sum_gather_dependent(&g), expected);
    }

    #[test]
    fn a_node_is_sixteen_bytes() {
        assert_eq!(std::mem::size_of::<Node>(), 16);
    }

    #[test]
    fn the_generator_is_deterministic() {
        assert_eq!(Nodes::new(N, 3).expected(), Nodes::new(N, 3).expected());
    }
}
