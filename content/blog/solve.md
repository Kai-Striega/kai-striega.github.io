+++
title = "Exploring NumPy's solve function"
date = 2024-04-11
draft = true
+++


## What are linear equations



## Systems of Linear Equations

Consider the linear system of equations:

$$ Ax = b $$

Where:

* $A$ is a known $n\text{ x }n$ matrix
* $x$ is an unknown $n\text{ x }1$ matrix
* $b$ is a known $n\text{ x }1$ matrix

We also assume that $A$ is __invertible__, that is, there exists another $n\text{ x }n$ matrix, $B$, such that $BA = I_n$.

We want to be able to solve this system for $x$.
