from axelrod.strategies.cooperator import Cooperator
from axelrod.strategies.defector   import Defector
from axelrod.game             import DefaultThreePlayerGame
from axelrod.match            import ThreeMatch

def test_all_cooperate():
    p1, p2, p3 = Cooperator(), Cooperator(), Cooperator()
    m = ThreeMatch((p1,p2,p3), turns=4, game=DefaultThreePlayerGame)
    m.play()
    assert m.final_score() == (12,12,12)

def test_one_coop_two_defect():
    p1 = Cooperator(); p2 = Defector(); p3 = Defector()
    m = ThreeMatch((p1,p2,p3), turns=3, game=DefaultThreePlayerGame)
    m.play()
    assert m.final_score() == (3,6,6)
