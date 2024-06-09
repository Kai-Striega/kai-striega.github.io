+++
title = 'Matrix Multiplication 02 Memory Layout'
date = 2024-06-07T16:26:36+10:00
+++

To create a two-dimensional array an "array of arrays" approach is often suggested (e.g. [here][1], or [here][2] and
[here][3]). At first glance this appears intuitive and straightforward. We're simply nesting arrays to mimic rows and
columns. However, this approach has several pitfalls and is rarely used in practice. In this post I'll look over both
the theoretical and practical implications of using an array of arrays, then discuss how we can do it better.

## What is an array of arrays?

One way to implement a matrix is to use an array to store arrays of row values. In Rust, the ``vector`` data structure
provides a contiguous, growable array type. It is possible to represent a 3 by 3 matrix as an array of arrays as
follows:

```rust
let matrix = vec![
    vec![1, 2, 3],
    vec![4, 5, 6],
    vec![7, 8, 9],
];
```

It is possible to access the desired element simply by indexing, which looks similar to the notation used in
mathematics, e.g. we can find $A_{0,0}$ by accessing the $0^{th}$ element of the $0^{th}$ array (remember, Rust uses 0
based indexing).

```rust
let a00 = matrix[0][0];
assert_eq!(a00, 1);  // True
```

## How is an array of arrays represented in memory?

### Vectors

To understand how our data structure works, it is crucial to understand the underlying vector implementation. Vectors
are resizable arrays that store their associated data on the heap. A vector consists of three pieces of information:

* A pointer to the underlying data
* Length
* Capacity

The capacity is the amount of space allocated by the vector. This is different from the length, which is the number of
elements that the vector holds. What's important here is that if a vector's length exceeds its capacity the vector will
automatically reallocate the underlying data. In memory a vector with capacity 4 containing the numbers ``1`` and ``2``
(and therefore having a length of 2). Would look like this:

TODO: Insert image of memory layout

### Vectors of vectors

Now that we understand how a vector works, let's consider vectors of vectors. A vector of vector consists of two
levels of vectors, an outer vector that contains the inner vectors and the inner vectors themselves, each containing the
elements of a row of that matrix. In memory our ``matrix`` from the above example looks as follows:

TODO: Insert image of memory layout

## An alternative approach

Before continuing, I'd like to propose an alternative implementation of a matrix. This will allow us to compare and
contrast the alternative with our array of arrays approach. The alternative approach is to store the data as one,
contiguous, array and using mathematics to correctly index the array.

Let's consider the 3 x 3 matrix from before. An alternative way to represent this in memory is with a single vector,
such as:

```rust
let matrix = vec![
    1, 2, 3,
    4, 5, 6,
    7, 8, 9
];
```

We can now access $A_{i,j}$ by accessing the index at $i * \text{cols} + j$, where $cols$ is the number of
columns. For example, to access $A_{1, 1}$, we would need to access the $4^{th}$ element.

```rust
let index = 1 * 3 + 1;  // 4
let a11 = matrix[index];
assert_eq!(a11, 5);  // True
```

## Comparing our approaches

### Accessing elements

But this looks way more complicated. With the vector of vectors approach we didn't need to do any calculations at all!
That's almost true. **We** didn't make any calculations explicitly. But the CPU still did them. Let's consider the
following two functions:

```rust
pub fn get_element_vec_of_vec(matrix: &Vec<Vec<f64>>, i: usize, j: usize) -> f64 {
    matrix[i][j]
}

pub fn get_element_linear(matrix: &Vec<f64>, i: usize, j: usize, cols: usize) -> f64 {
    let index = i * cols + j;
    matrix[index]
}
```

#### Analysing Assembly

##### Vector of vectors

The ``get_element_vec_of_vec`` compiles to the following assembly:

```asm
push    rax
mov     rax, qword ptr [rdi + 16]
cmp     rax, rsi
jbe     .LBB0_3
mov     rax, qword ptr [rdi + 8]
lea     rcx, [rsi + 2*rsi]
mov     rsi, qword ptr [rax + 8*rcx + 16]
cmp     rsi, rdx
jbe     .LBB0_4
lea     rax, [rax + 8*rcx]
mov     rax, qword ptr [rax + 8]
movsd   xmm0, qword ptr [rax + 8*rdx]
pop     rax
ret
```

That's a lot of work!

At a high level, the CPU has to:

1. Get the address to ``matrix[i]`` in memory
2. Bounds check ``matrix[i]``
3. Load ``matrix[i]``
4. Get the address to ``matrix[i][j]`` in memory
5. Bounds check ``matrix[i][j]``
6. Load ``matrix[i][j]``

##### Linear Memory

What if we use a linear memory layout? This compiles to the following assembly:

```asm
imul    rsi, rcx
add     rsi, rdx
mov     rax, qword ptr [rdi + 16]
cmp     rsi, rax
jae     .LBB0_2
mov     rax, qword ptr [rdi + 8]
movsd   xmm0, qword ptr [rax + 8*rsi]
ret
```

That's significantly less work. Although we need to do some arithmetic, this can be done very quickly by the CPU. And
only need to calculate the address, perform a bounds check and load the memory once.

##### Profiling

We've seen that there is a difference in the compiled assembly, but does this make a measurable difference in
performance? I've set up a benchmark using [criterion](https://bheisler.github.io/criterion.rs/book/criterion_rs.html).

|     Method      | Time (ns) |
|:---------------:|-----------|
| Array of Arrays | 1.2270    |
|     Linear      | 0.8156    |

That's about 2/3 time savings. Although 400ps may seem trivial, these savings add up when performed
millions or billions of times.

### Memory Management

With arrays of arrays, each sub-array needs to be allocated and managed separately. This increases the complexity of
memory management, making operations like copying or resizing more cumbersome. For instance, copying a 2D array of
arrays requires deep copying each sub-array, which is more complex and error-prone compared to copying a single,
contiguous array.

Let's consider trying to clone each of our matrix representations. Luckily for us, Rust abstracts away the manual
process of copying memory. All we have to do is call the ``.clone()`` method on our matrix. After running the benchmark
for 4096 by 4096 matrices here are the results:

|     Method      | Time (ms) |
|:---------------:|-----------|
|     Linear      | 43.296    |
| Array of Arrays | 45.199    |

The linear layout is slightly (but statistically significantly) faster. What's interesting to me is the variability of
times. Let's take a look at those:

|     Method      | high mild outliers | high severe outliers |
|:---------------:|--------------------|----------------------|
|     Linear      | 0                  | 0                    |
| Array of Arrays | 4                  | 6                    |

Out of our 100 measurements, the array of array approach had a total of 10 outliers. This makes sense as the OS had to
assign memory once for each row (4096 times) instead of once. And each of these allocations introduces some variance.

## Conclusion

In this blog post, I have introduced the array of arrays approach to represent a matrix. This is often suggested to 
beginners, however this approach has several draw backs. I have presented some of these drawbacks by contrasting the
array of arrays approach with a linear memory, highlighting some of the differences in theory, by analysing the 
compiled assembly and by timing.

[1]: https://www.digitalocean.com/community/tutorials/two-dimensional-array-in-c-plus-plus

[2]: https://www.tutorialspoint.com/cplusplus/cpp_multi_dimensional_arrays.htm

[3]: https://www.programiz.com/cpp-programming/examples/add-matrix
  