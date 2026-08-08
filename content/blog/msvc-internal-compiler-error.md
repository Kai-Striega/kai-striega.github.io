+++
title = 'One Line of C'
date = 2026-08-08T09:00:00+10:00
tags = ['compilers', 'c', 'numpy', 'msvc', 'windows']
+++

Here is a C file:

```c
int f(double x) { return __builtin_isnan(x); }
```

Here is what Microsoft's C compiler does with it:

```text
C:\Users\Kai\Documents>cl /c /Od isnan_ice.c
Microsoft (R) C/C++ Optimizing Compiler Version 19.51.36252 for x64
Copyright (C) Microsoft Corporation.  All rights reserved.

isnan_ice.c
C:\Users\Kai\Documents\isnan_ice.c : fatal error C1001: Internal compiler error.
(compiler file 'D:\a\_work\1\s\src\vctools\Compiler\Utc\src\p2\main.cpp', line 262)
 To work around this problem, try simplifying or changing the program near the locations listed above.
```

The process exits with `-1073741819`, which is `0xC0000005`, which is an access violation.
The compiler didn't decide to give up. It fell over.

I want to draw attention to the advice, because it is the part I have been quietly
delighted by. *Try simplifying or changing the program near the locations listed above.*
The only location listed above is the file, and the file is one
line long. There is no header, no template, no macro, no clever flag — the invocation is
`/Od` and nothing else. That is the entire program, and I cannot simplify it, because the
smallest C function that calls this builtin is the one I have already written.

I've been writing C on and off for years, mostly around NumPy and SciPy, and I have never
found one of these before. I've *hit* internal compiler errors, in the way you hit weather,
and gone around them. I have never had one shrink all the way down to a single line in my
hands. So this post is partly a bug report and mostly the story of the week I spent finding
out that a compiler I trusted is, on this one thing, comprehensively broken — and that the
project I care most about walks straight into it.

## What I was actually doing

None of this was the plan. The plan was to get a Windows development environment working,
because I do almost everything on Linux and "works on my machine" is not a maintenance
strategy when a good share of your users are on Windows. So: a fresh install of Visual
Studio Community 2026, the C++ workload, a virtual environment, and `pip install -e .` on a
NumPy checkout.

It died in ``npymath``, with the same `C1001` in three places: ``npy_spacing``, at
`ieee754.c.src:305`; ``npy_heaviside``, at `npy_math_internal.h.src:427`; and ``npy_csqrt``,
at `npy_math_complex.c.src:352`.

Three unrelated functions. `npy_spacing` computes the distance to the next representable
float, `npy_heaviside` is a step function, `npy_csqrt` is a complex square root. I stared at
those three for longer than I would like to admit looking for what they had in common, and
what they have in common is entirely boring: each of them, early on, asks whether its input
is a NaN.

I had also passed `-Doptimization=0`, because I wanted a debug build. That turns out to
matter a great deal, and I'll come back to it.

## Minimising

Going from a NumPy build failure to that one line took an afternoon, and it was the good
kind of afternoon. ``npy_isnan`` is a macro. Follow it into ``npy_math.h`` and, on a
compiler that has been probed as having them, it expands to ``__builtin_isnan``. So: write a
file that calls ``__builtin_isnan`` and nothing else. Compile it. Crash. Delete the
`#include`. Crash. Delete `/std:c11`. Crash. Put it all on one line.

```c
int f(double x) { return __builtin_isnan(x); }
```

Crash, in `p2\main.cpp` at line 262, every time.

It isn't just ``isnan``. Each of these one-line files dies identically at `/Od`, and both
`float` and `double` do it:

```c
int f(double x) { return __builtin_isnan(x);    }
int f(float  x) { return __builtin_isnan(x);    }
int f(double x) { return __builtin_isinf(x);    }
int f(double x) { return __builtin_isfinite(x); }
int f(double x) { return __builtin_signbit(x);  }
```

The whole floating-point classification family, then. Which is a neat little set: those four
builtins are how a great deal of numerical C asks the only questions you can ask about a
float that aren't arithmetic.

And at `/O1` and `/O2`, the crash goes away. That was the moment I stopped being pleased
with myself and started being worried, because a compiler bug that only exists at `/Od` is a
nuisance, and a compiler bug that *stops* existing when you turn on optimisation is very
rarely a compiler bug that has gone away.

## The half that's worse

It hasn't gone away. At `/O1` and `/O2` the builtins compile, and then they return nonsense.

```c
#include <stdio.h>

/* Same builtins numpy's npy_isnan/npy_isinf/npy_isfinite expand to. */
static int my_isnan(double x)    { return __builtin_isnan(x); }
static int my_isinf(double x)    { return __builtin_isinf(x); }
static int my_isfinite(double x) { return __builtin_isfinite(x); }

int main(void)
{
    volatile double one = 1.0;
    volatile double big = 1e308;
    volatile double inf = big * 10.0;   /* +inf */
    volatile double nan = inf - inf;    /* nan  */

    printf("isnan(1.0)    = %d  (expect 0)\n", my_isnan(one));
    printf("isnan(nan)    = %d  (expect 1)\n", my_isnan(nan));
    printf("isinf(1.0)    = %d  (expect 0)\n", my_isinf(one));
    printf("isinf(inf)    = %d  (expect 1)\n", my_isinf(inf));
    printf("isfinite(1.0) = %d  (expect 1)\n", my_isfinite(one));
    printf("isfinite(inf) = %d  (expect 0)\n", my_isfinite(inf));
    return 0;
}
```

The values are built at runtime through `volatile` doubles so there's no constant folding to
argue about; the compiler has to actually classify something. Built with `cl /O2` and run:

```text
isnan(1.0)    = 585252064  (expect 0)
isnan(nan)    = 585252064  (expect 1)
isinf(1.0)    = 585295456  (expect 0)
isinf(inf)    = 0          (expect 1)
isfinite(1.0) = 0          (expect 1)
isfinite(inf) = 0          (expect 0)
```

Six answers, and **not one of them is right**. Look at what the first two have in common:
`isnan(1.0)` and `isnan(nan)` return *the same number*. The builtin isn't giving a wrong
classification, it isn't classifying at all — it returns the identical value for a NaN and
for the number one. And 585252064 is not a `0`, a `1`, or anything a predicate is entitled to
return. I'm not going to claim I know what it is; what I can say is that it has the shape of
a register nobody bothered to write to.

`/O1` is wrong in the same way, with different garbage integers.

This is the half that matters. The ICE is loud: your build stops, you get a `C1001`, you go
and find out why. This one compiles clean, links clean, produces a working executable, and
answers "is this value a NaN?" with 585252064. Every guard you wrote against non-finite
input is now a coin toss that mostly comes up the same way.

## Two controls

Two things I checked before believing any of this, because a compiler this widely used being
this wrong about something this basic should be your last hypothesis, not your first.

Rename the file to `isnan_ice.cpp` and compile it exactly as before, so the same source goes
through the same driver with the same flags into the C++ front-end instead of the C one. It
compiles. Exit code 0. The runtime program, built as C++, prints the six results you'd
expect.

Then compile both with clang-cl — which is right there in the Visual Studio install, at
`VC\Tools\Llvm\x64\bin`, on the same machine with the same headers. Also fine, at every
optimisation level.

So it isn't my machine, it isn't the headers, and it isn't the flags. It's MSVC's C mode
specifically. I'm going to stop there rather than speculate about which phase of the
compiler is at fault, because I don't have the source and `p2\main.cpp` is a filename, not a
diagnosis.[^1]

## Why NumPy walks into it

Which brings me back to why I found this at all, and to the thing I find genuinely
interesting about it.

NumPy does not call `__builtin_isnan` because someone thought MSVC would like it. ``npymath``
maps ``npy_isnan``, ``npy_isinf`` and ``npy_isfinite`` onto the builtins when a
configure-time probe called `HAVE___BUILTIN_ISNAN` succeeds. On MSVC that probe used to fail,
so NumPy quietly took its own fallback path and nobody had to think about it. With 19.51 it
succeeds, because the compiler now advertises the builtins.

A feature probe compiles a tiny program and checks whether it built. That is the only
question it can ask. It cannot ask whether the thing it just detected *returns the right
answer* — and here, for the first time, those two questions have different answers. NumPy
asked "do you have `__builtin_isnan`?", got told yes, believed it, and it was true in every
sense except the one that matters.

The consequences split exactly along the optimisation boundary:

- At `/Od` — a debug build, `-Doptimization=0` — the compiler crashes in ``npymath`` and you
  get no NumPy at all. Loud, and honestly the merciful outcome.
- At the default `/O2` the build **succeeds**, and you get a NumPy whose ``npy_isnan`` and
  ``npy_isfinite`` are wrong.

That second one is a strange thing to hold in your hands. It imports. It mostly works. And
then ``arange`` raises `ValueError: arange: cannot compute length` — it computes its length,
checks the result is finite, is told it isn't, and refuses. ``linspace`` goes the same way.
Printing a float array gives you `inf` for perfectly ordinary finite data, because dragon4 —
the algorithm that turns a float into the shortest string that round-trips — asks `isinf`
first and takes that branch. And `import numpy` on its own emits a spurious
`RuntimeWarning: overflow encountered in cast`.

I've been around NumPy long enough to have a reflex for that failure mode, and the reflex is
wrong here. Nothing overflowed. Nothing is non-finite. The array is fine, the arithmetic is
fine, and every single one of those symptoms is one broken predicate, four layers down,
answering a yes/no question with 585252064.

## The workaround

Build with clang-cl. It ships inside Visual Studio, so there's nothing to install, and for
NumPy it's a native file:

```ini
[binaries]
c = 'clang-cl'
cpp = 'clang-cl'
ar = 'llvm-lib'
c_ld = 'lld-link'
cpp_ld = 'lld-link'
```

That's it. Builds at any optimisation level, and the resulting NumPy behaves.

## Conclusion

So: on cl.exe 19.51.36252, in C, `__builtin_isnan` and its three siblings crash the compiler
at `/Od` and return garbage at `/O1` and `/O2`. The same code is correct as C++ and correct
under clang-cl. NumPy hits it because a probe that can only ask "does this compile?" now gets
`yes` for a builtin that compiles and lies.

Let me be clear about what this isn't. It's one machine, one toolset, one afternoon. I
haven't looked inside the compiler, I have no idea *why* line 262 of `p2\main.cpp` is
unhappy, and "it looks like an uninitialised register" is me describing an integer, not
diagnosing a codegen bug. The next steps are the unglamorous ones: a report on Microsoft's
Developer Community with the one-liner attached. Whatever
Microsoft does about it, a build system that trusts a compile-only probe for this is going to
keep getting bitten. Neither is filed yet. When they are, I'll link them here.

But I'll admit the thing I keep coming back to isn't the impact. It's that there exists a
forty-seven byte file which, handed to one of the most heavily exercised compilers on Earth,
reliably kills it — and that I found it by trying to install NumPy.

Both reproducers and the full transcript are [in the repo for this blog][code], if you have a
19.51 to point them at. I'd be glad to hear whether it dies on yours too.

[^1]: The full environment, since it's the sort of thing that turns out to matter: compiler
19.51.36252 for x64, toolset MSVC 14.51.36231, Visual Studio Community 2026 v18.8.2, Windows
11 x64. It reproduces under `/std:c11` and under the default C settings alike.

[code]: https://github.com/Kai-Striega/kai-striega.github.io/tree/main/code/msvc-ice
