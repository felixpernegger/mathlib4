/-
Copyright (c) 2026 Jack McKoen. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Jack McKoen
-/
module

public import Mathlib.CategoryTheory.Monoidal.Braided.Basic
public import Mathlib.CategoryTheory.Monoidal.Closed.Basic
import Mathlib.CategoryTheory.Adjunction.Limits
import Mathlib.CategoryTheory.Adjunction.ParametrizedLimits
import Mathlib.CategoryTheory.Category.Init
import Mathlib.Data.Finset.Attr
import Mathlib.Init
import Mathlib.Tactic.CategoryTheory.CategoryStar
import Mathlib.Tactic.Common
import Mathlib.Tactic.Finiteness.Attr
import Mathlib.Tactic.SetLike
import Mathlib.Util.CompileInductive

/-!
# Closed braided monoidal categories

Interactions between monoidal closed and braided category structures.

-/

public section

namespace CategoryTheory

open Category MonoidalCategory Limits

variable {C : Type*} [Category* C] [MonoidalCategory C] [BraidedCategory C]

namespace ihom

instance (A : C) [Closed A] :
    (tensorRight A).IsLeftAdjoint :=
  Functor.isLeftAdjoint_of_iso (BraidedCategory.tensorLeftIsoTensorRight A)

instance (A : C) [MonoidalClosed C] (J : Type*) [Category* J] :
    PreservesLimitsOfShape J (MonoidalClosed.internalHom.flip.obj A) :=
  MonoidalClosed.internalHomAdjunction₂.preservesLimitsOfShape_flip_obj _ _

end ihom

end CategoryTheory
