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
    RodrigoDefector,
    Alternator,
) 
from axelrod.game import DefaultThreePlayerGame
from axelrod.tournament import ThreePlayerTournament
from axelrod import Plot
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("results/standard", exist_ok=True)
os.makedirs("results/earlystop", exist_ok=True)
os.makedirs("results/noisy", exist_ok=True)
os.makedirs("results/noisy_earlystop", exist_ok=True)

# players
players = (SoftTifForTat(), ToughTifForTat(), Defector(), ToughFoolMeOnce(), Cooperator(),
           SoftFoolMeOnce(), BackStabber(), DoubleCrosser(), ToughGradualKiller(), SoftGradualKiller(),
           AntiTitForTat(), GoByMajority5(), GoByMajority40(), SoftTitFor2Tats(), ToughTitFor2Tats(),
           SuperToughTitFor2Tats(), SoftGrudger3p(), ToughGrudger(), ShortMem(), SoftForgiver(),
           ToughForgiver(), Grumpy(), VeryBad(), SoftDefectorHunter(), ToughDefectorHunter(),
           SoftCooperatorHunter(), ToughCooperatorHunter(), TrickyCooperator(), TrickyDefector(),
           SoftGolden(), SoftPi(), SoftE(), ToughGolden(), ToughPi(), ToughE(), Rodrigo(), 
           RodrigoDefector(), Alternator())

#players = (Defector(), Cooperator(), SoftTifForTat())

def run_tournament(label, noise, prob_end, outdir):
    tournament = ThreePlayerTournament(
        players             = players,
        turns               = 100,
        repetitions         = 10,
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
    return results
    # plot = Plot(results)
    # fig1 = plot.boxplot(title=f"{label} Tournament Score Distributions")
    # fig1.savefig(os.path.join(outdir, f"boxplot_{label}.png"), bbox_inches="tight", dpi=150)

    # fig2 = plot.winplot(title=f"{label} Win Distributions")
    # fig2.savefig(os.path.join(outdir, f"win_distributions_{label}.png"), bbox_inches="tight", dpi=150)
    
    # #fig3 = plot.payoff(title=f"{label} Payoff Heatmap")
    # #fig3.savefig(os.path.join(outdir, f"payoff_heatmap_{label}.png"), bbox_inches="tight", dpi=150)
    
    # print(f"Plots written to {outdir}:")
    # print(f"- {label}_boxplot.png")
    # print(f"- {label}_winplot.png")
    # #print(f"- {label}_payoff_heatmap.png")


if __name__ == "__main__":
    # standard
    standard_res = run_tournament("standard", noise=0, prob_end=0, outdir="results/standard")
    # early stop tournament
    earlystop_res = run_tournament("earlystop", noise=0, prob_end=0.05, outdir="results/earlystop")
    # noisy tournament
    noisy_res = run_tournament("noisy", noise=0.1, prob_end=0, outdir="results/noisy")
    # noise + early stop tournament
    combined_res = run_tournament("noisy_earlystop", noise=0.1, prob_end=0.05, outdir="results/noisy_earlystop")
    
    all_labels    = ["Standard", "Early stop (p=0.1)", "Noisy (p=0.1)", "Noisy and early stop (p=0.1 for both)"]
    all_results   = [standard_res, earlystop_res, noisy_res, combined_res]

    # two by two fig w/ same y-scale
    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=(14, 10),
        sharey=False
    )

    axes = axes.flatten()
    for idx, (results, title) in enumerate(zip(all_results, all_labels)):
        ax = axes[idx]
        plot = Plot(results)

        # one violinplot per strategy
        # doing a single one with all is unreadable
        data = [
            list(np.nan_to_num(results.normalised_scores[i]))
            for i in results.ranking
        ]
        # use full names for labels
        names = [ str(results.players[i]) for i in results.ranking ]

        # override ax, use Plot from Axelrod
        positions = np.arange(len(names)) + 1
        ax.violinplot(
            data,
            positions=positions,
            widths=0.8,
            showmedians=True,
            showextrema=False
        )
        ax.set_xticks(positions)
        ax.set_xticklabels(names, rotation=90, fontsize=7)
        ax.set_xlim(0, len(names) + 1)
        ax.set_title(title, fontsize=12)
        
    fig.tight_layout()
    # save
    fig.savefig("results/violin_plots.png", bbox_inches="tight", dpi=150)
    print("Violin plots saved to results/violin_plots.png")