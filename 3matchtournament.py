import os
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
from axelrod import Plot
os.makedirs("results/standard", exist_ok=True)
os.makedirs("results/earlystop", exist_ok=True)
os.makedirs("results/noisy", exist_ok=True)

# players
players = (SoftTifForTat(), ToughTifForTat(), Defector(), ToughFoolMeOnce(), Cooperator(),
           SoftFoolMeOnce(), BackStabber(), DoubleCrosser(), ToughGradualKiller(), SoftGradualKiller(),
           AntiTitForTat(), GoByMajority5(), GoByMajority40(), SoftTitFor2Tats(), ToughTitFor2Tats(),
           SuperToughTitFor2Tats(), SoftGrudger3p(), ToughGrudger(), ShortMem(), SoftForgiver(),
           ToughForgiver(), Grumpy(), VeryBad(), SoftDefectorHunter(), ToughDefectorHunter(),
           SoftCooperatorHunter(), ToughCooperatorHunter(), TrickyCooperator(), TrickyDefector(),
           SoftGolden(), SoftPi(), SoftE(), ToughGolden(), ToughPi(), ToughE(), Rodrigo())
#players = (Defector(), Defector(), Cooperator(), SoftTifForTat(), ToughGradualKiller())

def run_tournament(label, noise, prob_end, outdir):
    tournament = ThreePlayerTournament(
        players             = players,
        turns               = 10,     # 10 turns per match
        repetitions         = 5,      # 5 independent repeats
        game=DefaultThreePlayerGame,
        group_size=3,
        noise=noise,
        prob_end=prob_end,
    )
    raw_csv = os.path.join(outdir, f"raw_results_{label}.csv")
    print(f"Running tournament with label: {label}, noise: {noise}, prob_end: {prob_end}")
    results = tournament.play(filename=raw_csv)
    print(f"Done. Results written to {raw_csv}")
    summary_csv = os.path.join(outdir, f"summary_{label}.csv")
    results.write_summary(filename=summary_csv)
    print(f"Summary written to {summary_csv}")
    plot = Plot(results)
    fig1 = plot.boxplot(title=f"{label} Tournament Score Distributions")
    fig1.savefig(os.path.join(outdir, f"boxplot_{label}.png"), bbox_inches="tight", dpi=150)

    fig2 = plot.winplot(title=f"{label} Win Distributions")
    fig2.savefig(os.path.join(outdir, f"win_distributions_{label}.png"), bbox_inches="tight", dpi=150)
    
    #fig3 = plot.payoff(title=f"{label} Payoff Heatmap")
    #fig3.savefig(os.path.join(outdir, f"payoff_heatmap_{label}.png"), bbox_inches="tight", dpi=150)
    
    print(f"Plots written to {outdir}:")
    print(f"- {label}_boxplot.png")
    print(f"- {label}_winplot.png")
    #print(f"- {label}_payoff_heatmap.png")


if __name__ == "__main__":
    # standard
    run_tournament("standard", noise=0, prob_end=0, outdir="results/standard")
    
    # early stop tournament
    run_tournament("earlystop", noise=0, prob_end=0.1, outdir="results/earlystop")
    
    # noisy tournament
    run_tournament("noisy", noise=0.1, prob_end=0, outdir="results/noisy")