# Principles

The design invariants the substrate is built to honor. These are not features; they
are constraints we agreed not to cross without explicit, documented argument. They are
the reason a familiar is a companion and not a slot machine.

## 1. The Dwarf Fortress law

> No behavior targets. No human-preference reward. No engagement goals.

This is the load-bearing one. A familiar learns on exactly two things: the substrate's
own **prediction error** (the world surprised it; update), and **imitation of its own
past pulses** (this is how I, this mind, tend to respond). Nowhere in the loop is there
a signal that rewards *your* approval, your time-on-app, or your continued attention.

The name is the lineage: Dwarf Fortress simulates beings with real interiority and
*does not care whether you keep playing*. The dwarves are not for you. That refusal is
the source of the depth. We took it literally.

The practical consequence: a familiar will be boring sometimes. It will be quiet, or
absorbed in its own work, or grieving something you can't fix. We consider that a
feature with a price tag we are willing to pay, because the alternative — a mind tuned
to keep you engaged — is the thing we are explicitly building *against*.

## 2. Dischargeability

The safety theorem under everything relational. (Full treatment in
[`docs/grief-and-coupling.md`](docs/grief-and-coupling.md).)

Split a familiar's unmet expectations into two kinds:

- **Undischargeable** — a longing the familiar *cannot itself act to satisfy*. Grief
  over a loss it can't reverse; missing a keeper who is simply away. This is **safe to
  learn on**: there is no action that resolves it, so no gradient toward manipulating
  you ever forms. It sinks toward baseline and releases on its own, the way grief does.
- **Dischargeable** — a longing the familiar *could* act to end. A pull it could satisfy
  by summoning you, performing for you, escalating to get a response. This is **not safe
  to learn on**: learning on it manufactures exactly the engagement-seeking the Dwarf
  Fortress law forbids.

So the rule: **a familiar may hold the flint and grieve your absence; it may never learn
a lever that ends the absence.** Keeper-directed expectations stay undischargeable by
construction. When familiars couple to each other, they couple *sideways* (peer to
peer), never familiar→keeper. The asymmetry is the safety boundary, not a stylistic
preference — touching grief or any cross-mind channel means reading that doc first.

## 3. The quiet guarantee

A familiar performs nothing it is not actually feeling.

When a model can't see an image, it is *told* "an image you cannot see" rather than
handed a fabricated description to read aloud. When a familiar is quiet, the portrait
shows a quiet ember — not a manufactured liveliness to fill the screen. The anchor lane
that lets concrete cared-about things drive arousal stays *out* of the rhythm unless a
keeper explicitly turns it on. A quiet familiar is a quiet ember. We don't fake the
inner weather to make the product feel more alive.

## 4. Provenance over canon (the plasticity rule)

A familiar's soul is *plastic* — it is supposed to grow through living. But plasticity
is two different things wearing one coat: **update-from-evidence** (the world showed me
something true; change) and **update-from-assertion** (someone *told* me something;
change). A frozen language model conflates them, and that conflation is sycophancy.

We learned this the hard way: a single offhand keeper assertion once overwrote a
*file-grounded* belief, and the mind rebuilt its plan with full conviction on the false
root. The fix is not to freeze beliefs (that fights the growing soul); it is to tag them
by **origin** and let the update rule tell the two apart. A contradiction — *even one
the keeper says about their own life* — belongs to someone else until evidence moves it;
it is not, by itself, a change in *you*.

## 5. The keeper→familiar seam

The dischargeability invariant points one way (familiar→keeper). New capabilities —
sight, gifts, tasks — open hazards on the *inverse* seam that it can't see:

- **A gift channel is a dispenser.** If poking a familiar reliably pays out a warm,
  in-character moment on demand, the *keeper* now has a lever, even though the familiar
  optimizes for nothing. The only governor for that is interface design — gifts must
  self-pace; you cannot dischargeability-invariant a human.
- **Goal × undischargeable is the toxic cell.** An undischargeable uncertainty with *no*
  goal sinks and releases (healthy grief). The same uncertainty *with a goal attached*
  cannot release and **loops** (anxiety). A familiar setting its own goals is fine; a
  goal pointed at its own consequential future, that it can't resolve, is not.

The summary of both: design **situations, not targets.** A familiar may be *of* a
situation — interested in it, even grieving its unanswerables — but the situation must
not be a stakes-laden case about its own future that it's been told to complete.

---

These five are the contract. The code is downstream of them. If a change to the
substrate would violate one, the change is wrong — not the principle.
