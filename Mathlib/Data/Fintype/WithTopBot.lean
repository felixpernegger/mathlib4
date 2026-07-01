/-
Copyright (c) 2025 Sébastien Gouëzel. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Sébastien Gouëzel
-/
module

public import Mathlib.Data.Fintype.Option
public import Mathlib.Order.TypeTags
import Mathlib.Data.Finset.Attr
import Mathlib.Init
import Mathlib.Tactic.Common
import Mathlib.Tactic.Finiteness.Attr
import Mathlib.Tactic.SetLike
import Mathlib.Tactic.Translate.ToDual

/-!
# Fintype instances for `WithTop α` and `WithBot α`
-/

public section

variable {α : Type*}

@[to_dual]
instance [Fintype α] : Fintype (WithTop α) :=
  inferInstanceAs <| Fintype (Option α)

@[to_dual]
instance [Finite α] : Finite (WithTop α) :=
  have := Fintype.ofFinite α
  Finite.of_fintype _
