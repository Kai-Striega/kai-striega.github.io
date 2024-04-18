+++
title = 'Matrix Multiplication 101'
date = 2024-04-19T08:40:29+10:00
draft = false
+++

_Matrix multiplication_ is a fundamental operation in mathematics. It is a binary operation (meaning it takes two
arguments) that takes two matrices $A$ and $B$ and produces another matrix, $C$, by taking the 
[dot product](https://en.wikipedia.org/wiki/Dot_product) of the $i^{\text{th}}$ row of $A$ with the $j^{\text{th}}$ 
column of $B$. More mathematically: 

$$C_{ij} = a_{i1}b_{1j} + a_{i2}b_{2j} + \ldots + a_{in}b_{nj} = \sum_{k=1}^{n} a_{ik}b_{kj} $$

Applications of matrix multiplication are widespread across all areas of mathematics, physics, chemistry, ML and many
other fields. The schoolbook algorithm provides a simple algorithm to compute the matrix product of two matrices. 
Realistically you wouldn't implement this algorithm yourself, rather you would use a library, like Python's 
[NumPy](https://numpy.org/) or [Eigen](https://eigen.tuxfamily.org/) in C++. These provide significantly more performant
implementations of matrix multiplication. In pure Python a simple implementation of the schoolbook algorithm looks like:

```python
import random
random.seed(42)
N = 1024

A = [[random.random() for row in range(n)] for col in range(N)]
B = [[random.random() for row in range(n)] for col in range(N)]
C = [[0 for row in range(n)] for col in range(N)]

for i in range(N):
    for j in range(N):
        for k in range(N):
            C[i][j] += A[i][k] * B[k][j]
```

In this series, I will develop a matrix multiplication function from scratch and investigate how various performance 
engineering techniques can be used to improve our algorithm. The goal is to learn how these techniques can effect
performance, and to have some fun with code that I normally wouldn't write myself.