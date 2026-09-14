#!/usr/bin/env julia
using Tupa
isempty(ARGS) && error("usage: julia --project=. bin/tupa.jl <study.json>")
Tupa.run_file(ARGS[end])
