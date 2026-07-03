# Cross-folder import fixes

Tracks cases where running `minimize_imports.py` / `fixup_broken_imports.py` on
one top-level `Mathlib/` folder required restoring an import in a file that
lives under a *different* top-level folder. Entries are appended here (append,
don't rewrite past entries) as each new folder gets processed by the pipeline.

Use this list when splitting the accumulated changes into separate PRs per
folder: any row below means those two folders' PRs are coupled — either land
them together, land the "restored in" PR first, or fold the specific restored
line into the "removed from" PR even though it's outside that folder.

Folders processed with **zero** cross-folder fixes (safe to PR fully
independently): `InformationTheory`, `Testing`, `Condensed`, `Computability`,
`RepresentationTheory`. (`AlgebraicGeometry`'s 3 restores were all internal to
`AlgebraicGeometry`; `ModelTheory`'s 1 restore was internal to `ModelTheory`.)

| Removed from (folder) | File | Restored in (folder) | File | Import |
|---|---|---|---|---|
| LinearAlgebra | `Mathlib/LinearAlgebra/Matrix/ToLin.lean` | ModelTheory | `Mathlib/ModelTheory/Arithmetic/Presburger/Semilinear/Basic.lean` | `Mathlib.Data.Finite.Sum` |
