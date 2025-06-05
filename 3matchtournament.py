from axelrod.strategies import (
    Cooperator,
    Defector,
    SoftTifForTat,
    SoftFoolMeOnce,
    ToughTifForTat,
    ToughFoolMeOnce,
    BackStabber,
    DoubleCrosser,
    SoftGradualKiller,
    ToughGradualKiller,
    AntiTitForTat,
    GoByMajority5,
    GoByMajority40,
    SoftTitFor2Tats,
    ToughTitFor2Tats,
    SuperToughTitFor2Tats,
    SoftGrudger3p,
    ToughGrudger,
    ShortMem,
    SoftForgiver,
    ToughForgiver,
    Grumpy,
    VeryBad,
    SoftDefectorHunter,
    ToughDefectorHunter,
    SoftCooperatorHunter,
    ToughCooperatorHunter,
    TrickyCooperator,
    TrickyDefector,
    SoftGolden,
    SoftPi,
    SoftE,
    ToughGolden,
    ToughPi,
    ToughE,
    Rodrigo,
) 
from axelrod.game import DefaultThreePlayerGame
from axelrod.tournament import ThreePlayerTournament
# players
#players = (Cooperator(), Defector(), ToughTifForTat())
players = (Cooperator(), SoftTifForTat(), ToughTifForTat(), Defector(), ToughFoolMeOnce(), 
           SoftFoolMeOnce(), BackStabber(), DoubleCrosser(), ToughGradualKiller(), SoftGradualKiller(),
           AntiTitForTat(), GoByMajority5(), GoByMajority40(), SoftTitFor2Tats(), ToughTitFor2Tats(),
           SuperToughTitFor2Tats(), SoftGrudger3p(), ToughGrudger(), ShortMem(), SoftForgiver(),
           ToughForgiver(), Grumpy(), VeryBad(), SoftDefectorHunter(), ToughDefectorHunter(),
           SoftCooperatorHunter(), ToughCooperatorHunter(), TrickyCooperator(), TrickyDefector(),
           SoftGolden(), SoftPi(), SoftE(), ToughGolden(), ToughPi(), ToughE(), Rodrigo())

# build and run 3p tournament
tournament = ThreePlayerTournament(
    players             = players,
    turns               = 10,     # 10 turns per match
    repetitions         = 5,      # 5 independent repeats
    group_size          = 3,      # <-- NEW FLAG
    game=DefaultThreePlayerGame,
)

results = tournament.play()
print(f"Result: {results}")

# inspect results
#print("Average scores per player:")
#for name, score in zip(results.ranked_names(), results.ranked_scores()):
#    print(f"  {name:12s} → {score:.2f}")

#results.to_csv("three_player_results.csv")
results.write_summary(filename="test3.csv")