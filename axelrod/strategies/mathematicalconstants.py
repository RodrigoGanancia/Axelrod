import math
from typing import List

from axelrod.action import Action
from axelrod.player import Player

C, D = Action.C, Action.D


class CotoDeRatio(Player):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the ratio as given in a sub class

    Names:

    - Co to Do Ratio: Original Name by Timothy Standen
    """

    classifier = {
        "stochastic": False,
        "memory_depth": float("inf"),  # Long memory
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy(self, opponent: Player) -> Action:
        """Actual strategy definition that determines player's action."""
        # Initially cooperate
        if len(opponent.history) == 0:
            return C
        # Avoid initial division by zero
        if not opponent.defections:
            return D
        # Otherwise compare ratio to golden mean
        cooperations = opponent.cooperations + self.cooperations
        defections = opponent.defections + self.defections
        if cooperations / defections > self.ratio:
            return D
        return C


class Golden(CotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the golden mean

    Names:

    - Golden: Original Name by Timothy Standen
    """

    name = "$\\phi$"
    ratio = (1 + math.sqrt(5)) / 2


class Pi(CotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the pi

    Names:

    - Pi: Original Name by Timothy Standen
    """

    name = "$\\pi$"
    ratio = math.pi


class e(CotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the e

    Names:

    - e: Original Name by Timothy Standen
    """

    name = "$e$"
    ratio = math.e

class SoftCotoDeRatio(Player):
    classifier = {
        "stochastic": False,
        "memory_depth": float("inf"),
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy_multi(self, opponents: List[Player]) -> Action:
         # Initially cooperate
        if len(self.history) == 0:
            return C
              
        if all(
            (op.cooperations + self.cooperations) / max(1, op.defections + self.defections) > self.ratio
            for op in opponents
        ):
            return D
        return C

class ToughCotoDeRatio(Player):
    classifier = {
        "stochastic": False,
        "memory_depth": float("inf"),
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy_multi(self, opponents: List[Player]) -> Action:
         # Initially cooperate
        if len(self.history) == 0:
            return C
              
        if any(
            (op.cooperations + self.cooperations) / max(1, op.defections + self.defections) > self.ratio
            for op in opponents
        ):
            return D
        return C
    
class SoftGolden(SoftCotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the golden mean

    Names:

    - Golden: Original Name by Timothy Standen
    """

    name = "Soft $\\phi$"
    ratio = (1 + math.sqrt(5)) / 2


class SoftPi(SoftCotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the pi

    Names:

    - Pi: Original Name by Timothy Standen
    """

    name = "Soft $\\pi$"
    ratio = math.pi


class SoftE(SoftCotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the e

    Names:

    - e: Original Name by Timothy Standen
    """

    name = "Soft $e$"
    ratio = math.e

class ToughGolden(ToughCotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the golden mean

    Names:

    - Golden: Original Name by Timothy Standen
    """

    name = "Tough $\\phi$"
    ratio = (1 + math.sqrt(5)) / 2


class ToughPi(ToughCotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the pi

    Names:

    - Pi: Original Name by Timothy Standen
    """

    name = "Tough $\\pi$"
    ratio = math.pi


class ToughE(ToughCotoDeRatio):
    """The player will always aim to bring the ratio of co-operations to
    defections closer to the e

    Names:

    - e: Original Name by Timothy Standen
    """

    name = "Tough $e$"
    ratio = math.e