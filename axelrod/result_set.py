import csv
import itertools
import warnings
from collections import Counter, namedtuple
from multiprocessing import cpu_count
from typing import List

import dask as da
import dask.dataframe as dd
import numpy as np
import tqdm

from axelrod.action import Action

from . import eigen

C, D = Action.C, Action.D


def update_progress_bar(method):
    """A decorator to update a progress bar if it exists"""

    def wrapper(*args, **kwargs):
        """Run the method and update the progress bar if it exists"""
        output = method(*args, **kwargs)

        try:
            args[0].progress_bar.update(1)
        except AttributeError:
            pass

        return output

    return wrapper


class ResultSet:
    """
    A class to hold the results of a tournament. Reads in a CSV file produced
    by the tournament class.
    """

    def __init__(
        self, filename, players, repetitions, processes=None, progress_bar=True
    ):
        """
        Parameters
        ----------
            filename : string
                the file from which to read the interactions
            players : list
                A list of the names of players. If not known will be efficiently
                read from file.
            repetitions : int
                The number of repetitions of each match. If not know will be
                efficiently read from file.
            processes : integer
                The number of processes to be used for parallel processing
            progress_bar: boolean
                If a progress bar will be shown.
        """
        self.filename = filename
        self.players, self.repetitions = players, repetitions
        self.num_players = len(self.players)

        if progress_bar:
            self.progress_bar = tqdm.tqdm(total=25, desc="Analysing")

        df = dd.read_csv(filename)
        dask_tasks = self._build_tasks(df)

        if processes == 0:
            processes = cpu_count()

        out = self._compute_tasks(tasks=dask_tasks, processes=processes)

        self._reshape_out(*out)

        if progress_bar:
            self.progress_bar.close()

    def _reshape_out(
        self,
        mean_per_reps_player_opponent_df,
        sum_per_player_opponent_df,
        sum_per_player_repetition_df,
        normalised_scores_series,
        initial_cooperation_count_series,
        interactions_count_series,
    ):
        """
        Reshape the various pandas series objects to be of the required form and
        set the corresponding attributes.
        """
        self.payoffs = self._reshape_three_dim_list(
            mean_per_reps_player_opponent_df["Score per turn"],
            first_dimension=range(self.num_players),
            second_dimension=range(self.num_players),
            third_dimension=range(self.repetitions),
            key_order=[2, 0, 1],
        )

        self.score_diffs = self._reshape_three_dim_list(
            mean_per_reps_player_opponent_df["Score difference per turn"],
            first_dimension=range(self.num_players),
            second_dimension=range(self.num_players),
            third_dimension=range(self.repetitions),
            key_order=[2, 0, 1],
            alternative=0,
        )

        self.match_lengths = self._reshape_three_dim_list(
            mean_per_reps_player_opponent_df["Turns"],
            first_dimension=range(self.repetitions),
            second_dimension=range(self.num_players),
            third_dimension=range(self.num_players),
            alternative=0,
        )

        self.wins = self._reshape_two_dim_list(
            sum_per_player_repetition_df["Win"]
        )
        self.scores = self._reshape_two_dim_list(
            sum_per_player_repetition_df["Score"]
        )
        self.normalised_scores = self._reshape_two_dim_list(
            normalised_scores_series
        )

        self.cooperation = self._build_cooperation(
            sum_per_player_opponent_df["Cooperation count"]
        )
        self.good_partner_matrix = self._build_good_partner_matrix(
            sum_per_player_opponent_df["Good partner"]
        )

        columns = ["CC count", "CD count", "DC count", "DD count"]
        self.state_distribution = self._build_state_distribution(
            sum_per_player_opponent_df[columns]
        )
        self.normalised_state_distribution = (
            self._build_normalised_state_distribution()
        )

        columns = [
            "CC to C count",
            "CC to D count",
            "CD to C count",
            "CD to D count",
            "DC to C count",
            "DC to D count",
            "DD to C count",
            "DD to D count",
        ]
        self.state_to_action_distribution = (
            self._build_state_to_action_distribution(
                sum_per_player_opponent_df[columns]
            )
        )
        self.normalised_state_to_action_distribution = (
            self._build_normalised_state_to_action_distribution()
        )

        self.initial_cooperation_count = self._build_initial_cooperation_count(
            initial_cooperation_count_series
        )
        self.initial_cooperation_rate = self._build_initial_cooperation_rate(
            interactions_count_series
        )
        self.good_partner_rating = self._build_good_partner_rating(
            interactions_count_series
        )

        self.normalised_cooperation = self._build_normalised_cooperation()
        self.ranking = self._build_ranking()
        self.ranked_names = self._build_ranked_names()

        self.payoff_matrix = self._build_summary_matrix(self.payoffs)
        self.payoff_stddevs = self._build_summary_matrix(
            self.payoffs, func=np.std
        )

        self.payoff_diffs_means = self._build_payoff_diffs_means()
        self.cooperating_rating = self._build_cooperating_rating()
        self.vengeful_cooperation = self._build_vengeful_cooperation()
        self.eigenjesus_rating = self._build_eigenjesus_rating()
        self.eigenmoses_rating = self._build_eigenmoses_rating()

    @update_progress_bar
    def _reshape_three_dim_list(
        self,
        series,
        first_dimension,
        second_dimension,
        third_dimension,
        alternative=None,
        key_order=[0, 1, 2],
    ):
        """
        Parameters
        ----------
            series : pandas.Series
            first_dimension : iterable
            second_dimension : iterable
            third_dimension : iterable
            alternative : int
                What to do if there is no entry at given position
            key_order : list
                Indices re-ording the dimensions to the correct keys in the
                series

        Returns:
        --------
            A three dimensional list across the three dimensions
        """
        series_dict = series.to_dict()
        output = []
        for first_index in first_dimension:
            matrix = []
            for second_index in second_dimension:
                row = []
                for third_index in third_dimension:
                    key = (first_index, second_index, third_index)
                    key = tuple([key[order] for order in key_order])
                    if key in series_dict:
                        row.append(series_dict[key])
                    elif alternative is not None:
                        row.append(alternative)
                matrix.append(row)
            output.append(matrix)
        return output

    @update_progress_bar
    def _reshape_two_dim_list(self, series):
        """
        Parameters
        ----------
            series : pandas.Series

        Returns:
        --------
            A two dimensional list across repetitions and opponents
        """
        series_dict = series.to_dict()
        out = [
            [
                series_dict.get((player_index, repetition), 0)
                for repetition in range(self.repetitions)
            ]
            for player_index in range(self.num_players)
        ]
        return out

    @update_progress_bar
    def _build_cooperation(self, cooperation_series):
        cooperation_dict = cooperation_series.to_dict()
        cooperation = []
        for player_index in range(self.num_players):
            row = []
            for opponent_index in range(self.num_players):
                count = cooperation_dict.get((player_index, opponent_index), 0)
                if player_index == opponent_index:
                    # Address double count
                    count = int(count / 2)
                row.append(count)
            cooperation.append(row)
        return cooperation

    @update_progress_bar
    def _build_good_partner_matrix(self, good_partner_series):
        good_partner_dict = good_partner_series.to_dict()
        good_partner_matrix = []
        for player_index in range(self.num_players):
            row = []
            for opponent_index in range(self.num_players):
                if player_index == opponent_index:
                    # The reduce operation implies a double count of self
                    # interactions.
                    row.append(0)
                else:
                    row.append(
                        good_partner_dict.get((player_index, opponent_index), 0)
                    )
            good_partner_matrix.append(row)
        return good_partner_matrix

    @update_progress_bar
    def _build_summary_matrix(self, attribute, func=np.mean):
        matrix = [
            [0 for opponent_index in range(self.num_players)]
            for player_index in range(self.num_players)
        ]

        pairs = itertools.product(range(self.num_players), repeat=2)

        for player_index, opponent_index in pairs:
            utilities = attribute[player_index][opponent_index]
            if utilities:
                matrix[player_index][opponent_index] = func(utilities)

        return matrix

    @update_progress_bar
    def _build_payoff_diffs_means(self):
        payoff_diffs_means = [
            [np.mean(diff) for diff in player] for player in self.score_diffs
        ]

        return payoff_diffs_means

    @update_progress_bar
    def _build_state_distribution(self, state_distribution_series):
        state_key_map = {
            "CC count": (C, C),
            "CD count": (C, D),
            "DC count": (D, C),
            "DD count": (D, D),
        }
        state_distribution = [
            [
                create_counter_dict(
                    state_distribution_series,
                    player_index,
                    opponent_index,
                    state_key_map,
                )
                for opponent_index in range(self.num_players)
            ]
            for player_index in range(self.num_players)
        ]
        return state_distribution

    @update_progress_bar
    def _build_normalised_state_distribution(self):
        """
        Returns:
        --------
            norm : list

            Normalised state distribution. A list of lists of counter objects:

            Dictionary where the keys are the states and the values are a
            normalized counts of the number of times that state occurs.
        """
        normalised_state_distribution = []
        for player in self.state_distribution:
            counters = []
            for counter in player:
                total = sum(counter.values())
                counters.append(
                    Counter(
                        {key: value / total for key, value in counter.items()}
                    )
                )
            normalised_state_distribution.append(counters)
        return normalised_state_distribution

    @update_progress_bar
    def _build_state_to_action_distribution(
        self, state_to_action_distribution_series
    ):
        state_to_action_key_map = {
            "CC to C count": ((C, C), C),
            "CC to D count": ((C, C), D),
            "CD to C count": ((C, D), C),
            "CD to D count": ((C, D), D),
            "DC to C count": ((D, C), C),
            "DC to D count": ((D, C), D),
            "DD to C count": ((D, D), C),
            "DD to D count": ((D, D), D),
        }
        state_to_action_distribution = [
            [
                create_counter_dict(
                    state_to_action_distribution_series,
                    player_index,
                    opponent_index,
                    state_to_action_key_map,
                )
                for opponent_index in range(self.num_players)
            ]
            for player_index in range(self.num_players)
        ]
        return state_to_action_distribution

    @update_progress_bar
    def _build_normalised_state_to_action_distribution(self):
        """
        Returns:
        --------
            norm : list

            A list of lists of counter objects.

            Dictionary where the keys are the states and the values are a
            normalized counts of the number of times that state goes to a given
            action.
        """
        normalised_state_to_action_distribution = []
        for player in self.state_to_action_distribution:
            counters = []
            for counter in player:
                norm_counter = Counter()
                for state in [(C, C), (C, D), (D, C), (D, D)]:
                    total = counter[(state, C)] + counter[(state, D)]
                    if total > 0:
                        for action in [C, D]:
                            if counter[(state, action)] > 0:
                                norm_counter[(state, action)] = (
                                    counter[(state, action)] / total
                                )
                counters.append(norm_counter)
            normalised_state_to_action_distribution.append(counters)
        return normalised_state_to_action_distribution

    @update_progress_bar
    def _build_initial_cooperation_count(
        self, initial_cooperation_count_series
    ):
        initial_cooperation_count_dict = (
            initial_cooperation_count_series.to_dict()
        )
        initial_cooperation_count = [
            initial_cooperation_count_dict.get(player_index, 0)
            for player_index in range(self.num_players)
        ]
        return initial_cooperation_count

    @update_progress_bar
    def _build_normalised_cooperation(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            normalised_cooperation = [
                list(np.nan_to_num(row))
                for row in np.array(self.cooperation)
                / sum(map(np.array, self.match_lengths))
            ]
            return normalised_cooperation

    @update_progress_bar
    def _build_initial_cooperation_rate(self, interactions_series):
        interactions_array = np.array(
            [
                interactions_series.get(player_index, 0)
                for player_index in range(self.num_players)
            ]
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            initial_cooperation_rate = list(
                np.nan_to_num(
                    np.array(self.initial_cooperation_count)
                    / interactions_array
                )
            )
            return initial_cooperation_rate

    @update_progress_bar
    def _build_ranking(self):
        ranking = sorted(
            range(self.num_players),
            key=lambda i: -np.nanmedian(self.normalised_scores[i]),
        )
        return ranking

    @update_progress_bar
    def _build_ranked_names(self):
        ranked_names = [str(self.players[i]) for i in self.ranking]
        return ranked_names

    @update_progress_bar
    def _build_eigenmoses_rating(self):
        """
        Returns:
        --------
        The eigenmoses rating as defined in:
        http://www.scottaaronson.com/morality.pdf
        """
        eigenvector, eigenvalue = eigen.principal_eigenvector(
            self.vengeful_cooperation
        )

        return eigenvector.tolist()

    @update_progress_bar
    def _build_eigenjesus_rating(self):
        """
        Returns:
        --------
        The eigenjesus rating as defined in:
        http://www.scottaaronson.com/morality.pdf
        """
        eigenvector, eigenvalue = eigen.principal_eigenvector(
            self.normalised_cooperation
        )

        return eigenvector.tolist()

    @update_progress_bar
    def _build_cooperating_rating(self):
        """
        Returns:
        --------
            The list of cooperation ratings
            List of the form:

            [ML1, ML2, ML3..., MLn]

            Where n is the number of players and MLi is a list of the form:

            [pi1, pi2, pi3, ..., pim]

            Where pij is the total number of cooperations divided by the total
            number of turns over all repetitions played by player i against
            player j.
        """

        plist = list(range(self.num_players))
        total_length_v_opponent = [
            zip(*[rep[player_index] for rep in self.match_lengths])
            for player_index in plist
        ]
        lengths = [
            [sum(e) for j, e in enumerate(row) if i != j]
            for i, row in enumerate(total_length_v_opponent)
        ]

        cooperation = [
            [col for j, col in enumerate(row) if i != j]
            for i, row in enumerate(self.cooperation)
        ]
        # Max is to deal with edge cases of matches that have no turns
        cooperating_rating = [
            sum(cs) / max(1, sum(ls)) for cs, ls in zip(cooperation, lengths)
        ]
        return cooperating_rating

    @update_progress_bar
    def _build_vengeful_cooperation(self):
        """
        Returns:
        --------
            The vengeful cooperation matrix derived from the
            normalised cooperation matrix:

                Dij = 2(Cij - 0.5)
        """
        vengeful_cooperation = [
            [2 * (element - 0.5) for element in row]
            for row in self.normalised_cooperation
        ]
        return vengeful_cooperation

    @update_progress_bar
    def _build_good_partner_rating(self, interactions_series):
        """
        At the end of a read of the data, build the good partner rating
        attribute
        """
        interactions_dict = interactions_series.to_dict()
        good_partner_rating = [
            sum(self.good_partner_matrix[player])
            / max(1, interactions_dict.get(player, 0))
            for player in range(self.num_players)
        ]
        return good_partner_rating

    def _compute_tasks(self, tasks, processes):
        """
        Compute all dask tasks
        """
        if processes is None:
            out = da.compute(*tasks, scheduler="single-threaded")
        else:
            out = da.compute(*tasks, num_workers=processes)
        return out

    def _build_tasks(self, df):
        """
        Returns a tuple of dask tasks
        """
        groups = ["Repetition", "Player index", "Opponent index"]
        columns = ["Turns", "Score per turn", "Score difference per turn"]
        
        mean_per_reps_player_opponent_task = df.groupby(groups)[columns].mean()
        groups = ["Player index", "Opponent index"]
        columns = [
            "Cooperation count",
            "CC count",
            "CD count",
            "DC count",
            "DD count",
            "CC to C count",
            "CC to D count",
            "CD to C count",
            "CD to D count",
            "DC to C count",
            "DC to D count",
            "DD to C count",
            "DD to D count",
            "Good partner",
        ]
        sum_per_player_opponent_task = df.groupby(groups)[columns].sum()

        ignore_self_interactions_task = (
            df["Player index"] != df["Opponent index"]
        )
        adf = df[ignore_self_interactions_task]

        groups = ["Player index", "Repetition"]
        columns = ["Win", "Score"]
        sum_per_player_repetition_task = adf.groupby(groups)[columns].sum()

        groups = ["Player index", "Repetition"]
        column = "Score per turn"
        normalised_scores_task = adf.groupby(groups)[column].mean()

        groups = ["Player index"]
        column = "Initial cooperation"
        initial_cooperation_count_task = adf.groupby(groups)[column].sum()
        interactions_count_task = adf.groupby("Player index")[
            "Player index"
        ].count()

        return (
            mean_per_reps_player_opponent_task,
            sum_per_player_opponent_task,
            sum_per_player_repetition_task,
            normalised_scores_task,
            initial_cooperation_count_task,
            interactions_count_task,
        )

    def __eq__(self, other):
        """
        Check equality of results set

        Parameters
        ----------
            other : axelrod.ResultSet
                Another results set against which to check equality
        """

        def list_equal_with_nans(v1: List[float], v2: List[float]) -> bool:
            """Matches lists, accounting for NaNs."""
            if len(v1) != len(v2):
                return False
            for i1, i2 in zip(v1, v2):
                if np.isnan(i1) and np.isnan(i2):
                    continue
                if i1 != i2:
                    return False
            return True

        return all(
            [
                self.wins == other.wins,
                self.match_lengths == other.match_lengths,
                self.scores == other.scores,
                self.normalised_scores == other.normalised_scores,
                self.ranking == other.ranking,
                self.ranked_names == other.ranked_names,
                self.payoffs == other.payoffs,
                self.payoff_matrix == other.payoff_matrix,
                self.payoff_stddevs == other.payoff_stddevs,
                self.score_diffs == other.score_diffs,
                self.payoff_diffs_means == other.payoff_diffs_means,
                self.cooperation == other.cooperation,
                self.normalised_cooperation == other.normalised_cooperation,
                self.vengeful_cooperation == other.vengeful_cooperation,
                #self.cooperating_rating == other.cooperating_rating,
                self.good_partner_matrix == other.good_partner_matrix,
                self.good_partner_rating == other.good_partner_rating,
                #list_equal_with_nans(
                #    self.eigenmoses_rating, other.eigenmoses_rating
                #),
                #list_equal_with_nans(
                #    self.eigenjesus_rating, other.eigenjesus_rating
                #),
            ]
        )

    def __ne__(self, other):
        """
        Check inequality of results set

        Parameters
        ----------
            other : axelrod.ResultSet
                Another results set against which to check inequality
        """
        return not self.__eq__(other)

    def summarise(self):
        """
        Obtain summary of performance of each strategy:
        ordered by rank, including median normalised score and cooperation
        rating.

        Output
        ------
            A list of the form:

            [[player name, median score, cooperation_rating],...]

        """

        median_scores = map(np.nanmedian, self.normalised_scores)
        median_wins = map(np.nanmedian, self.wins)

        original_index = [index for index, _player in enumerate(self.players)]

        self.player = namedtuple(
            "Player",
            [
                "Rank",
                "Name",
                "Median_score",
                "Cooperation_rating",
                "Wins",
                "Initial_C_rate",
                "Original_index",
                "CC_rate",
                "CD_rate",
                "DC_rate",
                "DD_rate",
                "CC_to_C_rate",
                "CD_to_C_rate",
                "DC_to_C_rate",
                "DD_to_C_rate",
            ],
        )

        states = [(C, C), (C, D), (D, C), (D, D)]
        state_prob = []
        for i, player in enumerate(self.normalised_state_distribution):
            counts = []
            for state in states:
                p = sum([opp[state] for j, opp in enumerate(player) if i != j])
                counts.append(p)
            try:
                counts = [c / sum(counts) for c in counts]
            except ZeroDivisionError:
                counts = [0 for c in counts]
            state_prob.append(counts)

        state_to_C_prob = []
        for player in self.normalised_state_to_action_distribution:
            rates = []
            for state in states:
                counts = [
                    counter[(state, C)]
                    for counter in player
                    if counter[(state, C)] > 0
                ]

                if len(counts) > 0:
                    rate = np.mean(counts)
                else:
                    rate = 0

                rates.append(rate)
            state_to_C_prob.append(rates)

        summary_measures = list(
            zip(
                self.players,
                median_scores,
                self.cooperating_rating,
                median_wins,
                self.initial_cooperation_rate,
                original_index,
            )
        )

        summary_data = []
        for rank, i in enumerate(self.ranking):
            data = (
                list(summary_measures[i]) + state_prob[i] + state_to_C_prob[i]
            )
            summary_data.append(self.player(rank, *data))

        return summary_data

    def write_summary(self, filename):
        """
        Write a csv file containing summary data of the results of the form:

            "Rank", "Name", "Median-score-per-turn", "Cooperation-rating", "Initial_C_Rate", "Wins", "CC-Rate", "CD-Rate", "DC-Rate", "DD-rate","CC-to-C-Rate", "CD-to-C-Rate", "DC-to-C-Rate", "DD-to-C-rate"


        Parameters
        ----------
            filename : a filepath to which to write the data
        """
        summary_data = self.summarise()
        with open(filename, "w") as csvfile:
            writer = csv.writer(csvfile, lineterminator="\n")
            writer.writerow(self.player._fields)
            for player in summary_data:
                writer.writerow(player)


class ThreeResultSet(ResultSet):
    def _build_tasks(self, df):
        print("DEBUG columns available: ", df.columns)
        print("amount of columns: ", len(df.columns))
        # mean per rep (player, opp1, opp2)
        groups = ['Repetition', 'Player index', 'Opponent1 index', 'Opponent2 index']
        columns = ['Turns', 'Score per turn', 'Score difference per turn']
        mean_per_reps = df.groupby(groups)[columns].mean()

        # sum per player, (opp1, opp2)
        groups = ['Player index', 'Opponent1 index', 'Opponent2 index']
        sum_cols = ['Cooperation count',
                    "CCC count", "CCD count", "CDC count", "CDD count",
                    "DCC count", "DCD count", "DDC count", "DDD count",
                    "CCC to C count", "CCC to D count",
                    "CCD to C count", "CCD to D count",
                    "CDC to C count", "CDC to D count",
                    "CDD to C count", "CDD to D count",
                    "DCC to C count", "DCC to D count",
                    "DCD to C count", "DCD to D count",
                    "DDC to C count", "DDC to D count",
                    "DDD to C count", "DDD to D count",
                    'Good partner']
        sum_per_player_opponent = df.groupby(groups)[sum_cols].sum()
        
        ignore_self_interactions = (
            (df['Player index'] != df['Opponent1 index']) &
            (df['Player index'] != df['Opponent2 index'])
        )
        adf = df[ignore_self_interactions]
        
        # sum per player per rep
        groups = ['Player index', 'Repetition']
        columns = ['Win', 'Score']
        sum_per_player_repetition = adf.groupby(groups)[columns].sum()

        # normalised score per turn per player per rep
        groups = ['Player index', 'Repetition']
        normalised_scores = df.groupby(groups)['Score per turn'].mean()

        # initial coop count per player
        initial_cooperation = df.groupby('Player index')['Initial cooperation'].sum()

        # interaction counts per player
        interactions_count = df.groupby('Player index')['Player index'].count()
        return (
            mean_per_reps,
            sum_per_player_opponent,
            sum_per_player_repetition,
            normalised_scores,
            initial_cooperation,
            interactions_count,
        )
    
    
    def _reshape_out(
        self,
        mean_df,
        sum_opp_df,
        sum_rep_df,
        norm_scores_series,
        init_coop_series,
        interaction_count_series,
    ):
        P, R = self.num_players, self.repetitions
        # payoff per turn ([player][opp1][opp2][repetition])
        self.payoffs = self._reshape_four_dim_list(
            mean_df['Score per turn'],
            dims=(range(P), range(P), range(P), range(R)),
            # player index, opp1, opp2, repetition
            key_order=[3,0,1,2],
        )
        
        self.payoff_stddevs = self._reshape_four_dim_list(
            mean_df['Score per turn'],
            dims=(range(P), range(P), range(P), None),
            # player index, opp1, opp2, repetition
            key_order=[3,0,1,2],
            func=np.std
        )
        
        # score difs: (s1-s2, s1-s3, s2-s3) stored per rep
        self.score_diffs = [[[ [
            self.payoffs[i][j][k][r] - self.payoffs[j][i][k][r] if i<j else
            self.payoffs[i][j][k][r] - self.payoffs[k][j][i][r]
            for r in range(R)
        ] for k in range(P)] for j in range(P)] for i in range(P)]

        # match lengths per turn (reuse turns)
        self.match_lengths = self._reshape_four_dim_list(
            mean_df['Turns'],
            dims=(range(P), range(P), range(P), range(R)),
            # player index, opp1, opp2, repetition
            key_order=[3,0,1,2] 
        )
        
        # total scores per player per rep
        # sum_rep_df: MultiIndex [(Player,Repetition)] to Score
        self.scores = [
            [ sum_rep_df.loc[(i, r)]['Score'] if (i, r) in sum_rep_df.index else 0
              for r in range(R)
            ] for i in range(P)
        ]
        #print("Scores: ", self.scores)
        #self.normalised_scores = self.scores
        turns_per_rep = []
        for i in range(P):
            rep_totals = [0]*R
            for j in range(P):
                if j == i:
                    continue
                for k in range(P):
                    if k == i or k == j:
                        continue
                    # list with length R
                    rep_list = self.match_lengths[i][j][k]
                    # accumulate
                    for r, t in enumerate(rep_list):
                        rep_totals[r] += t
            turns_per_rep.append(rep_totals)
            
        self.normalised_scores = [
            [ sc/tn if tn else 0
            for sc, tn in zip(self.scores[i], turns_per_rep[i]) ]
            for i in range(P)
        ]

        def get_sum(i,j,k, col):
            key = (i, j, k)
            return sum_opp_df.loc[key][col] if key in sum_opp_df.index else 0

        # coop count
        self.cooperation = [ 
            [ [ get_sum(i,j,k,'Cooperation count')
                for k in range(P)] 
                for j in range(P)] 
                for i in range(P)]

        # state dists
        # Counter({(C,C): get_sum(i,j,k,'CC count'),
            #          (C,D): get_sum(i,j,k,'CD count'),
            #          (D,C): get_sum(i,j,k,'DC count'),
            #          (D,D): get_sum(i,j,k,'DD count')})
        self.state_distribution = [ [ [
            Counter({(C,C,C): get_sum(i,j,k,'CCC count'),
                    (C,C,D): get_sum(i,j,k,'CCD count'),
                    (C,D,C): get_sum(i,j,k,'CDC count'),
                    (C,D,D): get_sum(i,j,k,'CDD count'),
                    (D,C,C): get_sum(i,j,k,'DCC count'),
                    (D,C,D): get_sum(i,j,k,'DCD count'),
                    (D,D,C): get_sum(i,j,k,'DDC count'),
                    (D,D,D): get_sum(i,j,k,'DDD count')})
            for k in range(P)] for j in range(P)] for i in range(P)]

        # normalised state distributions
        self.normalised_state_distribution = []
        for i in range(P):
            row_i = []
            for j in range(P):
                row_j = []
                for k in range(P):
                    sd = self.state_distribution[i][j][k]  # <-- Counter
                    total = sum(sd.values())
                    if total > 0:
                        # build normalized Counter(state - probability)
                        norm = Counter({ state: count / total for state, count in sd.items() })
                    else:
                        norm = Counter()
                    row_j.append(norm)
                row_i.append(row_j)
            self.normalised_state_distribution.append(row_i)

        # state - action dists
        # for each player and opp pair understand how often he transitions
        # from each state to C or D
        self.state_to_action_distribution = []
        for i in range(P):
            player_list = []
            for j in range(P):
                opp_list = []
                for k in range(P):
                    counter = Counter()
                    # for each state look up counts
                    for (triple, labels) in [
                        ((C,C,C), ("CCC to C count", "CCC to D count")),
                        ((C,C,D), ("CCD to C count", "CCD to D count")),
                        ((C,D,C), ("CDC to C count", "CDC to D count")),
                        ((C,D,D), ("CDD to C count", "CDD to D count")),
                        ((D,C,C), ("DCC to C count", "DCC to D count")),
                        ((D,C,D), ("DCD to C count", "DCD to D count")),
                        ((D,D,C), ("DDC to C count", "DDC to D count")),
                        ((D,D,D), ("DDD to C count", "DDD to D count")),
                    ]:
                        # transitions from cur state to C or D
                        c_count = get_sum(i, j, k, labels[0])
                        d_count = get_sum(i, j, k, labels[1])
                        if c_count > 0:
                            counter[(triple, C)] = c_count
                        if d_count > 0:
                            counter[(triple, D)] = d_count
                    opp_list.append(counter)
                player_list.append(opp_list)
            self.state_to_action_distribution.append(player_list)

        # normalised state - action distributions
        # raw counts -> probs per state
        self.normalised_state_to_action_distribution = []
        for i in range(P):
            player_norm = []
            for j in range(P):
                opp_norm = []
                for k in range(P):
                    raw_counter = self.state_to_action_distribution[i][j][k]
                    total = sum(raw_counter.values())
                    norm_counter = Counter()
                    if total > 0:
                        for key, cnt in raw_counter.items():
                            norm_counter[key] = cnt / total
                    opp_norm.append(norm_counter)
                player_norm.append(opp_norm)
            self.normalised_state_to_action_distribution.append(player_norm)

        # initial coop and rates
        self.initial_cooperation_count = [ init_coop_series.get(i,0)
                                           for i in range(P) ]
        self.initial_cooperation_rate = [ init_coop_series.get(i,0) / interaction_count_series.get(i,1)
                                          if interaction_count_series.get(i,0)>0 else 0
                                          for i in range(P) ]

        # good partner matrix & rating (useless?)
        self.good_partner_matrix = [ [ get_sum(i,j,k,'Good partner')
                                       for k in range(P)] for j in range(P)]
        self.good_partner_rating = [ sum(self.good_partner_matrix[i]) /
                                     max(1, interaction_count_series.get(i,0))
                                     for i in range(P) ]

        # vengeful coop: D_ij = 2*(p_CC - 0.5),
        # where p_CC: prob. of (C,C) from the normalized state distribution
        self.vengeful_cooperation = []
        for i in range(P):
            row_i = []
            for j in range(P):
                row_j = []
                for k in range(P):
                    # p_CC = normalized probability of state (C,C)
                    p_CC = self.normalised_state_distribution[i][j][k].get((C, C), 0)
                    row_j.append(2 * (p_CC - 0.5))
                row_i.append(row_j)
            self.vengeful_cooperation.append(row_i)
            
        self.normalised_cooperation = []
        for i in range(P):
            row_i = []
            for j in range(P):
                row_j = []
                for k in range(P):
                    coop = self.cooperation[i][j][k]
                    turns_list = self.match_lengths[i][j][k]
                    total_turns = sum(turns_list) if isinstance(turns_list, list) else turns_list
                    rate = coop / total_turns if total_turns else 0
                    row_j.append(rate)
                row_i.append(row_j)
            self.normalised_cooperation.append(row_i)
        # collapse into 2D adj. mat
        coop_matrix = [[0]*P for _ in range(P)]
        for i in range(P):
            for j in range(P):
                # average across all third players k != i,j
                total = 0
                count = 0
                for k in range(P):
                    if k in (i,j):
                        continue
                    total += self.normalised_cooperation[i][j][k]
                    count += 1
                coop_matrix[i][j] = total / count if count else 0

        self.normalised_cooperation = coop_matrix

        # eigen ratings and coop rating reuse parent
        #self.eigenjesus_rating = super()._build_eigenjesus_rating()
        #self.eigenmoses_rating = super()._build_eigenmoses_rating()
        # = super()._build_cooperating_rating()

        # ranking and names
        self.ranking = super()._build_ranking()
        self.ranked_names = super()._build_ranked_names()
        
        self.wins = [
        [
            sum_rep_df.loc[(i, r)]['Win']
            if (i, r) in sum_rep_df.index else 0
            for r in range(R)
        ]
        for i in range(P)
        ]
        #print("Wins: ", self.wins)
        
        self.match_lengths_3D = [
            [
                [
                    sum(self.match_lengths[i][j][k])
                    for k in range(P)
                ]
                for j in range(P)
            ]
            for i in range(P)
        ]
        
        cooperating_rating_3P = []
        for i in range(P):
            # sum_i_coops = sum_{j,k != i} self.cooperation[i][j][k]
            sum_i_coops = 0
            # sum_i_turns = sum_{j,k != i} self.match_lengths_3D[i][j][k]
            sum_i_turns = 0

            for j in range(P):
                if j == i:
                    continue
                for k in range(P):
                    if k == i or k == j:
                        continue
                    sum_i_coops += self.cooperation[i][j][k]
                    sum_i_turns += self.match_lengths_3D[i][j][k]

            # Avoid division by zero: if sum_i_turns==0, define rating=0
            if sum_i_turns > 0:
                cooperating_rating_3P.append(sum_i_coops / sum_i_turns)
            else:
                print("Warning: Player {} has no interactions.".format(i))
                cooperating_rating_3P.append(0)
        self.cooperating_rating = cooperating_rating_3P
        
        #print("Wins: ", self.wins)
        
        #self.payoff_matrix = self._build_summary_matrix(self.payoffs)
        
        
    def summarise(self):
        P = self.num_players
        
        self.player = namedtuple(
            "Player",
            ["Rank","Name","Median_score","Cooperation_rating",
             "Wins","Initial_C_rate","Original_index",
             "CCC_rate","CCD_rate","CDC_rate","CDD_rate",
             "DCC_rate","DCD_rate","DDC_rate","DDD_rate",
             "CCC_to_C_rate","CCC_to_D_rate", 
             "CCD_to_C_rate","CCD_to_D_rate",
             "CDC_to_C_rate","CDC_to_D_rate",
             "CDD_to_C_rate","CDD_to_D_rate",
             "DCC_to_C_rate","DCC_to_D_rate",
             "DCD_to_C_rate","DCD_to_D_rate",
             "DDC_to_C_rate","DDC_to_D_rate",
             "DDD_to_C_rate","DDD_to_D_rate",  
            ] 
        )
        
        # payoff ranking and median scores reuse parent logic
        median_scores = list(map(np.nanmedian, self.normalised_scores))
        # wins should already be set
        median_wins   = list(map(np.nanmedian, self.wins))
        original_index = [index for index, _player in enumerate(self.players)]
        #print("Median wins: ", median_wins)

        # build state_prob for 3p summing over all pairs
        states = [
            (C, C, C),
            (C, C, D),
            (C, D, C),
            (C, D, D),
            (D, C, C),
            (D, C, D),
            (D, D, C),
            (D, D, D),
        ]
        state_prob = []
        for i in range(P):
        # initialize an aggregator for each of the eight triple-states
            counts = { triple: 0 for triple in states }
            total = 0.0
        # sum over all ordered pairs (j,k) with j != i and k != i
            for j in range(P):
                for k in range(P):
                    if j == i or k == i:
                        continue
                    # ctr is a Counter of shape Counter({(C,C,C): p₁, (C,C,D): p₂, …})
                    ctr = self.normalised_state_distribution[i][j][k]
                    for triple in states:
                        val = ctr.get(triple, 0.0)
                        counts[triple] += val
                        total += val

            if total > 0:
                # normalize so that the eight sums add up to 1
                state_prob.append([counts[triple] / total for triple in states])
            else:
                # if no interactions, we just give 0 for each triple
                state_prob.append([0.0] * 8)

        # build state_to_C_prob by averaging likelihood of C given state
        # across pairs (and state_to_D_prob)
        state_to_C_prob = []
        state_to_D_prob = []
        for i in range(P):
            probs_C_lst, probs_D_lst = [], []
            for triple in states:
                sum_C = 0
                sum_D = 0
                count = 0
                for j in range(P):
                    for k in range(P):
                        if j==i or k==i: continue
                        
                        raw = self.state_to_action_distribution[i][j][k]
                        sum_C += raw.get((triple, C), 0)
                        sum_D += raw.get((triple, D), 0)
                        count += 1
                        
                # normalize
                total_for_state = sum_C + sum_D
                if total_for_state > 0:
                    probs_C = sum_C / total_for_state
                    probs_D = sum_D / total_for_state
                else:
                    probs_C = 0
                    probs_D = 0
                probs_C_lst.append(probs_C)
                probs_D_lst.append(probs_D)
            state_to_C_prob.append(probs_C_lst)
            state_to_D_prob.append(probs_D_lst)
            
        # summary rows
        summary = []
        for player in range(P):
            row = [
                # rank, name, medianscore, cooprating, wins, initial c rate, 
                # originalindex (useless?)
                self.ranking.index(player),
                str(self.players[player]),
                median_scores[player],
                self.cooperating_rating[player],
                median_wins[player],
                self.initial_cooperation_rate[player],
                original_index[player],
            ]
            # extend with state probs
            row.extend(state_prob[player])  # state probs
            # CCC to C, CCC to D, ...
            for idx_state in range(len(states)):
                row.append(state_to_C_prob[player][idx_state])
                row.append(state_to_D_prob[player][idx_state])

            summary.append(row)
        return summary
            
    
    # def _build_summary_matrix(self, attribute, func=np.mean):
    #     P = self.num_players
    #     R = self.repetitions
    #     payoff_matrix_2d = [[0.0] * P for _ in range(P)]

    #     for i in range(P):
    #         for j in range(P):
    #             if i == j:
    #                 payoff_matrix_2d[i][j] = 0.0
    #                 continue

    #             total_score = 0.0
    #             count: int = 0

    #             for k in range(P):
    #                 if k == i or k == j:
    #                     continue
    #                 for r in range(R):
    #                     total_score += self.payoffs[i][j][k][r]
    #                     count += 1

    #             if count > 0:
    #                 payoff_matrix_2d[i][j] = total_score / count
    #             else:
    #                 payoff_matrix_2d[i][j] = 0.0

    #     return payoff_matrix_2d
    
    
    def _reshape_four_dim_list(
        self,
        series,
        dims,
        key_order,
        func=np.mean
    ):
    
        result = []
        iters = dims
        for i in iters[0]:
            mat1 = []
            for j in iters[1]:
                mat2 = []
                for k in iters[2]:
                    vec = []
                    if iters[3] is not None:
                        for r in iters[3]:
                            # base_key is (i, j, k, r)
                            base_key = (i, j, k, r)

                            # reorder according to key_order = [3,0,1,2]
                            idx = tuple(base_key[pos] for pos in key_order)
                            if idx in series.index:
                                vec.append(series.loc[idx])
                            else:
                                vec.append(0)
                    else:
                        # collapse last dim: aggregate all reps
                        values = [series.loc[(i,j,k,r)]
                                  for r in range(self.repetitions)
                                  if (i,j,k,r) in series.index]
                        vec = func(values) if values else 0
                    mat2.append(vec)
                mat1.append(mat2)
            result.append(mat1)
        return result

def create_counter_dict(df, player_index, opponent_index, key_map):
    """
    Create a Counter object mapping states (corresponding to columns of df) for
    players given by player_index, opponent_index. Renaming the variables with
    `key_map`. Used by `ResultSet._reshape_out`

    Parameters
    ----------
        df : a multiindex pandas df
        player_index: int
        opponent_index: int
        key_map : a dict
            maps cols of df to strings

    Returns
    -------
        A counter dictionary
    """
    counter = Counter()
    if player_index != opponent_index:
        if (player_index, opponent_index) in df.index:
            for key, value in df.loc[player_index, opponent_index].items():
                if value > 0:
                    counter[key_map[key]] = value
    return counter
