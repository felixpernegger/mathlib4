/-
Copyright (c) 2022 Michael Stoll. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Michael Stoll
-/
module

public import Mathlib.NumberTheory.LegendreSymbol.AddCharacter
import Mathlib.Algebra.Order.Algebra
import Mathlib.Algebra.Order.BigOperators.Expect
import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Algebra.Order.Field.Power
import Mathlib.Algebra.Order.Floor.Ring
import Mathlib.Algebra.Order.Module.Field
import Mathlib.Analysis.Complex.Polynomial.Basic
import Mathlib.CategoryTheory.Category.Init
import Mathlib.Combinatorics.Matroid.Init
import Mathlib.Data.ENNReal.Real
import Mathlib.Data.EReal.Inv
import Mathlib.Data.Finset.Attr
import Mathlib.Data.Rat.Cast.Order
import Mathlib.Data.Rat.Floor
import Mathlib.Data.Sym.Sym2.Init
import Mathlib.Init
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.MeasureTheory.Measure.Real
import Mathlib.Tactic.ArithMult.Init
import Mathlib.Tactic.Bound.Init
import Mathlib.Tactic.Common
import Mathlib.Tactic.ContinuousFunctionalCalculus
import Mathlib.Tactic.Finiteness.Attr
import Mathlib.Tactic.Measurability.Init
import Mathlib.Tactic.NormNum.Abs
import Mathlib.Tactic.NormNum.BigOperators
import Mathlib.Tactic.NormNum.DivMod
import Mathlib.Tactic.NormNum.Eq
import Mathlib.Tactic.NormNum.GCD
import Mathlib.Tactic.NormNum.Ineq
import Mathlib.Tactic.NormNum.NatFactorial
import Mathlib.Tactic.NormNum.OfScientific
import Mathlib.Tactic.Positivity.Basic
import Mathlib.Tactic.Positivity.Finset
import Mathlib.Tactic.SetLike

/-!
# Additive characters on finite fields

We construct a primitive additive character on a finite field `F` with values in `ℂ`.
This file is kept separate from `Mathlib.NumberTheory.LegendreSymbol.AddCharacter` to avoid
importing the fundamental theorem of algebra and Bochner integral into that file.
-/

namespace AddChar

section Field

variable (F : Type*) [Field F] [Finite F]

lemma ringChar_ne : ringChar ℂ ≠ ringChar F := by
  simpa only [ringChar.eq_zero] using (CharP.ringChar_ne_zero_of_finite F).symm

/-- A primitive additive character on the finite field `F` with values in `ℂ`. -/
public noncomputable def FiniteField.primitiveChar_to_Complex : AddChar F ℂ := by
  letI ch := primitiveChar F ℂ <| by exact ringChar_ne F
  refine MonoidHom.compAddChar ?_ ch.char
  exact (IsCyclotomicExtension.algEquiv {(ch.n : ℕ)} ℂ (CyclotomicField ch.n ℂ) ℂ).toMonoidHom

public lemma FiniteField.primitiveChar_to_Complex_isPrimitive :
    (primitiveChar_to_Complex F).IsPrimitive := by
  refine IsPrimitive.compMulHom_of_isPrimitive (PrimitiveAddChar.prim _) ?_
  let nn := (primitiveChar F ℂ <| ringChar_ne F).n
  exact (IsCyclotomicExtension.algEquiv {(nn : ℕ)} ℂ (CyclotomicField nn ℂ) ℂ).injective

end Field

end AddChar
