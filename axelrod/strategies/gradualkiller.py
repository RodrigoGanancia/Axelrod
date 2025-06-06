from axelrod.action import Action
from axelrod.player import Player
from axelrod.strategy_transformers import InitialTransformer
from typing import List

C, D = Action.C, Action.D


@InitialTransformer((D, D, D, D, D, C, C), name_prefix=None)
class GradualKiller(Player):
    """
    It begins by defecting in the first five moves, then cooperates two times.
    It then defects all the time if the opponent has defected in move 6 and 7,
    else cooperates all the time.
    Initially designed to stop Gradual from defeating TitForTat in a 3 Player
    tournament.

    Names

    - Gradual Killer: [Prison1998]_
    """

    # These are various properties for the strategy
    name = "Gradual Killer"
    classifier = {
        "memory_depth": float("Inf"),
        "stochastic": False,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy(self, opponent: Player) -> Action:
        """Actual strategy definition that determines player's action."""
        if opponent.history[5:7] == [D, D]:
            return D
        return C


@InitialTransformer((D, D, D, D, D, C, C), name_prefix=None)
class SoftGradualKiller(Player):
    """
    It begins by defecting in the first five moves, then cooperates two times.
    It then defects all the time if the opponent has defected in move 6 and 7,
    else cooperates all the time.
    Initially designed to stop Gradual from defeating TitForTat in a 3 Player
    tournament.

    Names

    - Gradual Killer: [Prison1998]_
    """

    # These are various properties for the strategy
    name = "Soft Gradual Killer"
    short_name = "SGK"
    classifier = {
        "memory_depth": float("Inf"),
        "stochastic": False,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy_multi(self, opponents: List[Player]) -> Action:
        """If any of the players defected in both rounds, defect forever"""
        if opponents[0].history[5:7] == [D, D] and opponents[1].history[5:7] == [D, D]:
            return D
        return C
    


@InitialTransformer((D, D, D, D, D, C, C), name_prefix=None)
class ToughGradualKiller(Player):
    """
    It begins by defecting in the first five moves, then cooperates two times.
    It then defects all the time if the opponent has defected in move 6 and 7,
    else cooperates all the time.
    Initially designed to stop Gradual from defeating TitForTat in a 3 Player
    tournament.

    Names

    - Gradual Killer: [Prison1998]_
    """

    # These are various properties for the strategy
    name = "Tough Gradual Killer"
    short_name = "TGK"
    classifier = {
        "memory_depth": float("Inf"),
        "stochastic": False,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }
    
    def strategy_multi(self, opponents: List[Player]) -> Action:
        """If any of the players defected in both rounds, defect forever"""
        if opponents[0].history[5:7] == [D, D] or opponents[1].history[5:7] == [D, D]:
            return D
        return C
