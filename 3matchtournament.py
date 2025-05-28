import axelrod as axl
from axelrod.strategies import Cooperator, Defector, TitForTat
from axelrod.game import DefaultThreePlayerGame

# players
players = (Cooperator(), Defector(), Cooperator())

# build and run 3p tournament
tournament = axl.Tournament(
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