from typing import List
from axelrod.action import Action
from axelrod.player import Player

C, D = Action.C, Action.D


class Forgiver(Player):
    """
    A player starts by cooperating however will defect if at any point
    the opponent has defected more than 10 percent of the time

    Names:

    - Forgiver: Original name by Thomas Campbell
    """

    name = "Forgiver"
    classifier = {
        "memory_depth": float("inf"),  # Long memory
        "stochastic": False,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy(self, opponent: Player) -> Action:
        """
        Begins by playing C, then plays D if the opponent has defected more
        than 10 percent of the time.
        """
        if opponent.defections > len(opponent.history) / 10.0:
            return D
        return C


class ForgivingTitForTat(Player):
    """
    A player starts by cooperating however will defect if at any point, the
    opponent has defected more than 10 percent of the time, and their most
    recent decision was defect.

    Names:

    - Forgiving Tit For Tat: Original name by Thomas Campbell
    """

    name = "Forgiving Tit For Tat"
    classifier = {
        "memory_depth": float("inf"),  # Long memory
        "stochastic": False,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy(self, opponent: Player) -> Action:
        """
        Begins by playing C, then plays D if the opponent has defected more than
        10 percent of the time and their most recent decision was defect.
        """
        if opponent.defections > len(opponent.history) / 10:
            return opponent.history[-1]
        return C

class SoftForgiver(Player):
    """
    Cooperates unless BOTH opponents have defected more than 10% of the time.
    """

    name = "Soft Forgiver"
    classifier = {
        "memory_depth": float("inf"),
        "stochastic": False,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy_multi(self, opponents: List[Player]) -> Action:
        def defect_rate(opponent: Player) -> float:
            return opponent.defections / len(opponent.history) if opponent.history else 0.0
        
        return D if all(defect_rate(opp) > 0.10 for opp in opponents) else C
    
class ToughForgiver(Player):
    """
    Cooperates unless one of the opponents have defected more than 10% of the time.
    """

    name = "Tough Forgiver"
    classifier = {
        "memory_depth": float("inf"),
        "stochastic": False,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy_multi(self, opponents: List[Player]) -> Action:
        def defect_rate(opponent: Player) -> float:
            return opponent.defections / len(opponent.history) if opponent.history else 0.0
        
        return D if any(defect_rate(opp) > 0.10 for opp in opponents) else C