/-
Copyright (c) 2022 Joseph Myers. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Joseph Myers
-/
module

public import Mathlib.LinearAlgebra.Complex.Module
public import Mathlib.LinearAlgebra.Determinant
import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Data.Finset.Attr
import Mathlib.Data.Nat.Totient
import Mathlib.Data.Rat.Cast.Order
import Mathlib.Data.Sym.Sym2.Init
import Mathlib.Init
import Mathlib.Tactic.Bound.Init
import Mathlib.Tactic.Common
import Mathlib.Tactic.ContinuousFunctionalCalculus
import Mathlib.Tactic.Finiteness.Attr
import Mathlib.Tactic.NormNum.Abs
import Mathlib.Tactic.NormNum.DivMod
import Mathlib.Tactic.NormNum.Eq
import Mathlib.Tactic.NormNum.GCD
import Mathlib.Tactic.NormNum.Ineq
import Mathlib.Tactic.NormNum.OfScientific
import Mathlib.Tactic.NormNum.Pow
import Mathlib.Tactic.Positivity.Basic
import Mathlib.Tactic.SetLike

/-!
# Determinants of maps in the complex numbers as a vector space over `ℝ`

This file provides results about the determinants of maps in the complex numbers as a vector
space over `ℝ`.

-/

public section


namespace Complex

/-- The determinant of `conjAe`, as a linear map. -/
@[simp]
theorem det_conjAe : conjAe.toLinearEquiv.toLinearMap.det = -1 := by
  rw [← LinearMap.det_toMatrix basisOneI, toMatrix_conjAe, Matrix.det_fin_two_of]
  simp

/-- The determinant of `conjAe`, as a linear equiv. -/
@[simp]
theorem linearEquiv_det_conjAe : conjAe.toLinearEquiv.det = -1 := by simp [← Units.val_inj]

end Complex
