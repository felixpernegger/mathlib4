/-
Copyright (c) 2024 Ben Eltschig. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Ben Eltschig, Joël Riou
-/
module

public import Mathlib.Topology.Compactness.DeltaGeneratedSpace
public import Mathlib.Topology.Convenient.Category
import Mathlib.Algebra.Order.Algebra
import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Algebra.Order.Floor.Ring
import Mathlib.Algebra.Order.Module.Field
import Mathlib.Analysis.Normed.Group.Basic
import Mathlib.Analysis.Real.Sqrt
import Mathlib.CategoryTheory.Category.Init
import Mathlib.Data.ENNReal.Real
import Mathlib.Data.EReal.Operations
import Mathlib.Data.Finset.Attr
import Mathlib.Data.Rat.Cast.Order
import Mathlib.Data.Rat.Floor
import Mathlib.Init
import Mathlib.Tactic.Bound.Init
import Mathlib.Tactic.Common
import Mathlib.Tactic.Finiteness.Attr
import Mathlib.Tactic.NormNum.Abs
import Mathlib.Tactic.NormNum.DivMod
import Mathlib.Tactic.NormNum.Eq
import Mathlib.Tactic.NormNum.Ineq
import Mathlib.Tactic.NormNum.OfScientific
import Mathlib.Tactic.NormNum.Pow
import Mathlib.Tactic.Positivity.Basic
import Mathlib.Tactic.SetLike
import Mathlib.Topology.MetricSpace.Bounded

/-!
# Delta-generated topological spaces

This file defines the category `DeltaGenerated` of delta-generated spaces.
This is a particular case of the construction in the file
`Mathlib/Topology/Convenient/Category.Lean`: this is the category of
`X`-generated spaces where `X` is the family of spaces `Fin n → ℝ`
for all `n : ℕ`.

## TODO
* `DeltaGenerated` is Cartesian closed (@joelriou).

## References
* https://ncatlab.org/nlab/show/Delta-generated+topological+space

-/

@[expose] public section

universe u

open CategoryTheory

/-- The category of delta-generated topological spaces. -/
abbrev DeltaGenerated := GeneratedByTopCat.{u} (fun n ↦ Fin n → ℝ)

/-- The faithful (but not full) functor taking each topological space to its delta-generated
  coreflection. -/
abbrev TopCat.toDeltaGenerated : TopCat.{u} ⥤ DeltaGenerated.{u} :=
  TopCat.toGeneratedByTopCat

namespace DeltaGenerated

/-- Constructor for objects of the category `DeltaGenerated` -/
abbrev of (X : Type u) [TopologicalSpace X] [DeltaGeneratedSpace X] : DeltaGenerated.{u} :=
  GeneratedByTopCat.of X

/-- The forgetful functor `DeltaGenerated ⥤ TopCat` -/
abbrev deltaGeneratedToTop : DeltaGenerated.{u} ⥤ TopCat.{u} :=
  GeneratedByTopCat.toTopCat

/-- `deltaGeneratedToTop` is fully faithful. -/
abbrev fullyFaithfulDeltaGeneratedToTop : deltaGeneratedToTop.{u}.FullyFaithful :=
  GeneratedByTopCat.fullyFaithfulToTopCat _

@[deprecated (since := "2026-04-23")] alias topToDeltaGenerated := TopCat.toDeltaGenerated

/-- The adjunction between the forgetful functor `DeltaGenerated ⥤ TopCat` and its coreflector. -/
abbrev coreflectorAdjunction : deltaGeneratedToTop ⊣ TopCat.toDeltaGenerated :=
  GeneratedByTopCat.adj

end DeltaGenerated
