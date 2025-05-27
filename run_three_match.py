#!/usr/bin/env python3
# run_three_match.py
import axelrod as axl
from axelrod.strategies.cooperator import Cooperator
from axelrod.strategies.defector   import Defector
from axelrod.strategies.titfortat   import TitForTat
from axelrod.game                   import DefaultThreePlayerGame
from axelrod.match                  import ThreeMatch
C, D = axl.Action.C, axl.Action.D

def main():
    p1 = Cooperator()
    p2 = Defector()
    p3 = TitForTat()

    print("Running one 3-player match of 5 turns…")
    m = ThreeMatch(
        (p1, p2, p3),
        turns=5,
        game=DefaultThreePlayerGame
    )
    history = m.play()
    print("  History:")
    for t in history:
        print("   ", t)
    print("  Final scores:", m.final_score())

    print("\nSanity check with 3 cooperators:")
    m2 = ThreeMatch(
        (Cooperator(), Cooperator(), Cooperator()),
        turns=3,
        game=DefaultThreePlayerGame
    )
    _ = m2.play()
    print("  Expected (9,9,9), got:", m2.final_score())

if __name__ == "__main__":
    main()
