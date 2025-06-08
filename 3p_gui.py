import pygame
import itertools

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
from axelrod.match import ThreeMatch
from axelrod.action import Action

players = (SoftTifForTat(), ToughTifForTat(), Defector(), ToughFoolMeOnce(), Cooperator(),
           SoftFoolMeOnce(), BackStabber(), DoubleCrosser(), ToughGradualKiller(), SoftGradualKiller(),
           AntiTitForTat(), GoByMajority5(), GoByMajority40(), SoftTitFor2Tats(), ToughTitFor2Tats(),
           SuperToughTitFor2Tats(), SoftGrudger3p(), ToughGrudger(), ShortMem(), SoftForgiver(),
           ToughForgiver(), Grumpy(), VeryBad(), SoftDefectorHunter(), ToughDefectorHunter(),
           SoftCooperatorHunter(), ToughCooperatorHunter(), TrickyCooperator(), TrickyDefector(),
           SoftGolden(), SoftPi(), SoftE(), ToughGolden(), ToughPi(), ToughE(), Rodrigo())

TURNS_PER_MATCH = 30
MILLIS_PER_TURN = 500
pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH  = info.current_w
SCREEN_HEIGHT = info.current_h
SCREEN_WIDTH  = 2000
SCREEN_HEIGHT = 2000
BG_COLOR     = (220, 220, 220)   # light gray background
COOP_COLOR   = ( 50, 150, 250)   # blue = “Cooperate”
DEFECT_COLOR = (250,  50,  50)   # red  = “Defect”
TEXT_COLOR   = (  0,   0,   0)   # black for text

PAUSE_BETWEEN_TRIPLES = 1.0
# if you want to show a limited number of triples:
MAX_TRIPLES_TO_SHOW = None


def animate_3p_match(screen, clock, players_triple):
    # for each triple, runs a match and animates the results
    # (based on the history)

    # play match and get history
    match = ThreeMatch(
        players=players_triple,
        turns=TURNS_PER_MATCH,
        game=DefaultThreePlayerGame,
        noise=0,
        seed=42,
        prob_end=None
    )
    history = match.play()
    T = len(history)

    # grid layout
    num_rows = 3
    cell_width  = SCREEN_WIDTH  // T
    cell_height = SCREEN_HEIGHT // num_rows
    #fonts_size = 24
    fonts_size = 50
    font = pygame.font.SysFont(None, fonts_size)
    score_font = pygame.font.SysFont(None, 48)
    #rendered_names = [font.render(str(p), True, TEXT_COLOR) for p in players_triple]
    rendered_names = [font.render(p.short_name, True, TEXT_COLOR) for p in players_triple]
    
    cumulative_scores = []
    running = [0] * num_rows
    for t in range(T):
        turn_triple = history[t]
        s1, s2, s3 = match.game3.score(turn_triple)
        running[0] += s1
        running[1] += s2
        running[2] += s3
        cumulative_scores.append((running[0], running[1], running[2]))

    # animation loop
    for turn_index in range(T):
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return False
            if evt.type == pygame.KEYDOWN and evt.key in (pygame.K_SPACE, pygame.K_n):
                return True

        screen.fill(BG_COLOR)

        for t in range(turn_index + 1):
            for row in range(num_rows):
                act = history[t][row]
                color = COOP_COLOR if act == Action.C else DEFECT_COLOR

                rect = pygame.Rect(
                    t * cell_width + 1,
                    row * cell_height + 1,
                    cell_width  - 2,
                    cell_height - 2
                )
                pygame.draw.rect(screen, color, rect)

                #name_surf = rendered_names[row]
                #screen.blit(name_surf, (t * cell_width + 4, row * cell_height + 4))
                
                score_value = cumulative_scores[t][row]
                # Format as integer if whole, else one decimal place:
                if abs(score_value - round(score_value)) < 1e-8:
                    score_text = f"{int(round(score_value))}"
                else:
                    score_text = f"{score_value:.1f}"
                score_surf = score_font.render(score_text, True, TEXT_COLOR)
                # Position it near the top-right inside that cell, with 4px padding:
                #screen.blit(
                #    score_surf,
                #    (
                #        t * cell_width + cell_width - score_surf.get_width() - 4,
                #        row * cell_height + 4,
                #    ),
                #)
                
                name_surf = rendered_names[row]
                screen.blit(name_surf, (t * cell_width + 4,
                                        row * cell_height + 4))

                # compute where to place score under name
                name_bottom = (row * cell_height + 4) + name_surf.get_height()
                score_pos = (
                    t * cell_width + 4,                 # same x offset as the name
                    name_bottom + 4                     # 4 pixels below the bottom of the name
                )
                screen.blit(score_surf, score_pos)

        # update display and wait
        pygame.display.flip()
        pygame.time.wait(MILLIS_PER_TURN)
        clock.tick(60)

    # pause after turns end
    pygame.time.wait(int(PAUSE_BETWEEN_TRIPLES * 1000))
    return True


def main():
    pygame.init()
    
    SCREEN_WIDTH  = 3800 #info.current_w
    SCREEN_HEIGHT = 2000 #info.current_h
    print(f"Screen size: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("3-Player Tournament Animator")
    clock = pygame.time.Clock()

    # generate all unique combinations of triples (players)
    all_triples = list(itertools.combinations(players, 3))
    # slice list if a maximum is set
    if isinstance(MAX_TRIPLES_TO_SHOW, int) and MAX_TRIPLES_TO_SHOW < len(all_triples):
        all_triples = all_triples[:MAX_TRIPLES_TO_SHOW]

    for idx, triple in enumerate(all_triples, start=1):
        # which triple we're animating
        names = [str(p) for p in triple]
        print(f"\nAnimating triple #{idx} of {len(all_triples)}: {names}")

        ok = animate_3p_match(screen, clock, triple)
        if not ok:
            break 

    pygame.quit()
    print("\nAll done!")


if __name__ == "__main__":
    main()
