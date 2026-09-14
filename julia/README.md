# TUPÃ — Julia version

This is a native Julia port of the Fortran HEM solver. It reads the shared
`common/*.json` studies, discretises line and mesh elements, builds the direct
and image geometry matrices, assembles the augmented HEM system, and runs
frequency- or time-domain simulations.

Transient synthesis includes a frequency-domain Tukey antialiasing low-pass
with **alpha = 0.75**. The response is flat through 25% of Nyquist and follows
a raised-cosine roll-off to zero at Nyquist. The existing record-tail taper is
also retained because it addresses FFT leakage, a different problem.

```sh
cd julia
julia --project=. -e 'using Pkg; Pkg.instantiate()'
julia --project=. bin/tupa.jl ../common/portela1997_transient.json
julia --project=. -e 'using Pkg; Pkg.test()'
```

For library use:

```julia
using Tupa
study, input = load_study("../common/portela1997_transient.json")
result = transient_response(study, input[:signal])
```
