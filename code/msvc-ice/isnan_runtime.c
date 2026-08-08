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
