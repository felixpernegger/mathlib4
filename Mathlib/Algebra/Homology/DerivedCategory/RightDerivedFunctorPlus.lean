/-
Copyright (c) 2026 Joël Riou. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Joël Riou
-/
module

public import Mathlib.Algebra.Homology.DerivedCategory.Plus
public import Mathlib.CategoryTheory.Functor.Derived.RightDerived
import Mathlib.Algebra.Homology.DerivedCategory.DerivabilityStructureInjectives
import Mathlib.CategoryTheory.Category.Init
import Mathlib.Data.Finset.Attr
import Mathlib.Data.Rat.Cast.Order
import Mathlib.Init
import Mathlib.Tactic.Bound.Init
import Mathlib.Tactic.CategoryTheory.CategoryStar
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

/-!
# The right derived functor on the bounded below derived category

If `F : C ⥤ D` is an additive functor between abelian categories,
where `C` has enough injectives, we define the right derived functor
`F.rightDerivedFunctorPlus : DerivedCategory.Plus C ⥤ DerivedCategory.Plus D`
between the corresponding bounded below derived categories.

TODO(@joelriou): show that this functor is triangulated and refactor
the definiton of `Functor.rightDerived`

-/

@[expose] public section

namespace CategoryTheory

namespace Functor

variable {C D : Type*} [Category* C] [Category* D] [Abelian C] [Abelian D]
  [HasDerivedCategory C] [HasDerivedCategory D]
  (F : C ⥤ D) [F.Additive] [EnoughInjectives C]

/-- The right derived functor `DerivedCategory.Plus C ⥤ DerivedCategory.Plus D`
when `F : C ⥤ D` is an additive functor between abelian categories and
`C` has enough injectives. -/
noncomputable def rightDerivedFunctorPlus :
    DerivedCategory.Plus C ⥤ DerivedCategory.Plus D :=
  (F.mapHomotopyCategoryPlus ⋙ DerivedCategory.Plus.Qh).totalRightDerived DerivedCategory.Plus.Qh
    (HomotopyCategory.Plus.quasiIso C)

/-- The natural transformation that is part of the data of
the right derived functor `DerivedCategory.Plus C ⥤ DerivedCategory.Plus D`
when `F : C ⥤ D` is an additive functor between abelian categories and
`C` has enough injectives. -/
noncomputable def rightDerivedFunctorPlusUnit :
    F.mapHomotopyCategoryPlus ⋙ DerivedCategory.Plus.Qh ⟶
      DerivedCategory.Plus.Qh ⋙ F.rightDerivedFunctorPlus :=
  (F.mapHomotopyCategoryPlus ⋙ DerivedCategory.Plus.Qh).totalRightDerivedUnit
    DerivedCategory.Plus.Qh (HomotopyCategory.Plus.quasiIso C)

instance :
    F.rightDerivedFunctorPlus.IsRightDerivedFunctor
      F.rightDerivedFunctorPlusUnit (HomotopyCategory.Plus.quasiIso C) := by
  dsimp only [rightDerivedFunctorPlus, rightDerivedFunctorPlusUnit]
  infer_instance

example (X : HomotopyCategory.Plus (InjectiveObject C)) :
    IsIso (F.rightDerivedFunctorPlusUnit.app
      ((InjectiveObject.ι C).mapHomotopyCategoryPlus.obj X)) := by
  infer_instance

example (K : CochainComplex.Plus (InjectiveObject C)) :
    IsIso (F.rightDerivedFunctorPlusUnit.app
      ((HomotopyCategory.Plus.quotient C).obj
        ((InjectiveObject.ι C).mapCochainComplexPlus.obj K))) := by
  infer_instance

end Functor

end CategoryTheory
