# MSVC 19.51 `__builtin_isnan` internal compiler error

Reproducers for the post [One Line of C](https://kaistriega.com/blog/msvc-internal-compiler-error/).

In C mode, cl.exe 19.51.36252 crashes with `C1001` on the floating-point classification
builtins at `/Od`, and miscompiles them at `/O1` and `/O2`. The same code is correct when
built as C++, and correct under clang-cl.

## Environment

Everything here was observed on one machine:

- Compiler: `Microsoft (R) C/C++ Optimizing Compiler Version 19.51.36252 for x64`
- Toolset: MSVC 14.51.36231
- IDE: Visual Studio Community 2026 (v18.8.2)
- OS: Windows 11 x64
- Language mode: C. Reproduces with `/std:c11` and with the default C settings.

## `isnan_ice.c` — the crash

The whole file is one line:

```c
int f(double x) { return __builtin_isnan(x); }
```

Run from a Visual Studio developer command prompt:

```
cl /c /Od isnan_ice.c
```

Expected: an object file. Actual: `fatal error C1001: Internal compiler error.` in
`...\Utc\src\p2\main.cpp, line 262`, with process exit code `-1073741819` (`0xC0000005`,
access violation). The full transcript is in `ice_error_message.txt`.

Each of these crashes identically at `/Od`:

```c
int f(double x) { return __builtin_isnan(x);    }
int f(float  x) { return __builtin_isnan(x);    }
int f(double x) { return __builtin_isinf(x);    }
int f(double x) { return __builtin_isfinite(x); }
int f(double x) { return __builtin_signbit(x);  }
```

Renaming the file to `isnan_ice.cpp` and compiling it the same way succeeds.

## `isnan_runtime.c` — the miscompile

```
cl /O2 isnan_runtime.c
isnan_runtime.exe
```

Expected six `0`/`1` answers. Actual, at `/O2`:

```
isnan(1.0)    = 585252064  (expect 0)
isnan(nan)    = 585252064  (expect 1)
isinf(1.0)    = 585295456  (expect 0)
isinf(inf)    = 0          (expect 1)
isfinite(1.0) = 0          (expect 1)
isfinite(inf) = 0          (expect 0)
```

`/O1` is also wrong, with different garbage integers. Built as C++, or with clang-cl, the
program prints the expected results.

## Workaround for building NumPy

Use the clang-cl that ships with Visual Studio, at `VC\Tools\Llvm\x64\bin`:

```ini
[binaries]
c = 'clang-cl'
cpp = 'clang-cl'
ar = 'llvm-lib'
c_ld = 'lld-link'
cpp_ld = 'lld-link'
```
