from enum import Enum
from typing import Tuple, Union

import numpy as np
import numpy.typing as npt

from axelrod import Action

C, D = Action.C, Action.D

Score = Union[int, float]


class AsymmetricGame(object):
    """Container for the game matrix and scoring logic.

    Attributes
    ----------
    scores: dict
        The numerical score attribute to all combinations of action pairs.
    """

    # pylint: disable=invalid-name
    def __init__(self, A: npt.NDArray, B: npt.NDArray) -> None:
        """
        Creates an asymmetric game from two matrices.

        Parameters
        ----------
        A: np.array
            the payoff matrix for player A.
        B: np.array
            the payoff matrix for player B.
        """

        if A.shape != B.transpose().shape:
            raise ValueError(
                "AsymmetricGame was given invalid payoff matrices; the shape "
                "of matrix A should be the shape of B's transpose matrix."
            )

        self.A = A
        self.B = B

        self.scores = {
            pair: self.score(pair) for pair in ((C, C), (D, D), (C, D), (D, C))
        }

    def score(
        self, pair: Union[Tuple[Action, Action], Tuple[int, int]]
    ) -> Tuple[Score, Score]:
        """Returns the appropriate score for a decision pair.
        Parameters
        ----------
        pair: tuple(int, int) or tuple(Action, Action)
            A pair of actions for two players, for example (0, 1) corresponds
            to the row player choosing their first action and the column
            player choosing their second action; in the prisoners' dilemma,
            this is equivalent to player 1 cooperating and player 2 defecting.
            Can also be a pair of Actions, where C corresponds to '0'
            and D to '1'.

        Returns
        -------
        tuple of int or float
            Scores for two player resulting from their actions.
        """

        # if an Action has been passed to the method,
        # get which integer the Action corresponds to
        def get_value(x):
            if isinstance(x, Enum):
                return x.value
            return x

        row, col = map(get_value, pair)

        return (self.A[row][col], self.B[row][col])

    def __repr__(self) -> str:
        return "Axelrod game with matrices: {}".format((self.A, self.B))

    def __eq__(self, other):
        if not isinstance(other, AsymmetricGame):
            return False
        return self.A.all() == other.A.all() and self.B.all() == other.B.all()


class Game(AsymmetricGame):
    """
    Simplification of the AsymmetricGame class for symmetric games.
    Takes advantage of Press and Dyson notation.

    Can currently only be 2x2.

    Attributes
    ----------
    scores: dict
        The numerical score attribute to all combinations of action pairs.
    """

    def __init__(
        self, r: Score = 4, s: Score = 0, t: Score = 4, p: Score = 1
    ) -> None:
        """Create a new game object.

        Parameters
        ----------
        r: int or float
            Score obtained by both players for mutual cooperation.
        s: int or float
            Score obtained by a player for cooperating against a defector.
        t: int or float
            Score obtained by a player for defecting against a cooperator.
        p: int or float
            Score obtained by both player for mutual defection.
        """
        A = np.array([[r, s], [t, p]])

        super().__init__(A, A.transpose())

    def RPST(self) -> Tuple[Score, Score, Score, Score]:
        """Returns game matrix values in Press and Dyson notation."""
        R = self.scores[(C, C)][0]
        P = self.scores[(D, D)][0]
        S = self.scores[(C, D)][0]
        T = self.scores[(D, C)][0]
        return R, P, S, T

    def __repr__(self) -> str:
        return "Axelrod game: (R,P,S,T) = {}".format(self.RPST())

    def __eq__(self, other):
        if not isinstance(other, Game):
            return False
        return self.RPST() == other.RPST()


class ThreePlayerGame:
    """
    3p extension of the standard PD payoff.
    Expects a dictionary mapping (action1,action2,action3) 
    to (score1,score2,score3) (e.g. {(C,C,C): (4,4,4), ...}).       
    """
    def __init__(self, payoff_map):
        # payoff_map: Dict[Tuple[Action,Action,Action], Tuple[float,float,float]]
        self.payoff_map = payoff_map
        print(f"Payoff map: {self.payoff_map}")

    def score(self, triple):
        """
        triple: (A1, A2, A3), each ∈ {C, D}
        returns (s1, s2, s3)
        """
        try:
            return self.payoff_map[triple]
        except KeyError:
            raise ValueError(f"No payoff defined for {triple}")

    def __repr__(self):
        return f"ThreePlayerGame({len(self.payoff_map)} entries)"


# # default payoff based on pairwise sum of scores
# def make_pairwise_sum_payoff_map(game, normalize=False):
#     payoff_map = {}
#     for a1 in (C,D):
#       for a2 in (C,D):
#         for a3 in (C,D):
#           s12,_ = game.scores[(a1,a2)]
#           s13,_ = game.scores[(a1,a3)]
#           s21,_ = game.scores[(a2,a1)]
#           s23,_ = game.scores[(a2,a3)]
#           s31,_ = game.scores[(a3,a1)]
#           s32,_ = game.scores[(a3,a2)]
#           t1, t2, t3 = s12+s13, s21+s23, s31+s32
#           if normalize:
#             t1/=2; t2/=2; t3/=2
#           payoff_map[(a1,a2,a3)] = (t1,t2,t3)
#     #print(f"Payoff map created: {payoff_map}")
#     return payoff_map

payoff_map = {
    (C, C, C): (4.0, 4.0, 4.0),
    (C, C, D): (2.0, 2.0, 6.0),
    (C, D, C): (2.0, 6.0, 2.0),
    (D, C, C): (6.0, 2.0, 2.0),
    (C, D, D): (0.0, 2.5, 2.5),
    (D, C, D): (2.5, 0.0, 2.5),
    (D, D, C): (2.5, 2.5, 0.0),
    (D, D, D): (1.0, 1.0, 1.0),
}

#DefaultThreePlayerGame = ThreePlayerGame(make_pairwise_sum_payoff_map(Game(), normalize=True))
DefaultThreePlayerGame = ThreePlayerGame(payoff_map)
DefaultGame = Game()