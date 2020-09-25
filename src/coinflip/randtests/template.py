# TODO format templates in results to match coinflip.cli.echo_series
from collections import Counter
from dataclasses import dataclass
from math import exp
from math import floor
from math import isclose
from math import log2
from math import sqrt
from random import choice
from typing import List

from scipy.special import gammaincc
from scipy.special import hyp1f1

from coinflip.randtests._decorators import randtest
from coinflip.randtests._result import TestResult
from coinflip.randtests._result import make_testvars_table
from coinflip.randtests._testutils import blocks
from coinflip.randtests._testutils import check_recommendations
from coinflip.randtests._testutils import slider

__all__ = ["non_overlapping_template_matching", "overlapping_template_matching"]


def make_template(series, blocksize):
    """Generate a random template"""
    template_size = min(max(floor(sqrt(blocksize)), 2), 12)

    values = series.unique()
    template = [choice(values) for _ in range(template_size)]

    return template


# ------------------------------------------------------------------------------
# Non-overlapping Template Matching Test


@randtest(rec_input=288)  # template_size=9, nblocks=8, blocksize=4*template_size
def non_overlapping_template_matching(series, template: List = None, nblocks=None):
    """Matches of template per block is compared to expected result

    The sequence is split into blocks, where the number of non-overlapping
    matches to the template in each block is found. This is referenced to the
    expected mean and variance in matches of a hypothetically truly random RNG.

    Parameters
    ----------
    sequence : array-like
        Output of the RNG being tested
    template : ``List``, optional
        Template to match with the sequence, randomly generated if not
        provided.
    nblocks : ``int``
        Number of blocks to split sequence into

    Returns
    -------
    TestResult
        Dataclass that contains the test's statistic and p-value.

    Raises
    ------
    TemplateContainsElementsNotInSequenceError
        If template contains values not present in sequence
    """
    n = len(series)

    if not nblocks:
        nblocks = min(floor(sqrt(n)), 100)
    blocksize = n // nblocks

    check_recommendations(
        {
            "nblocks ≤ 100": nblocks <= 100,
            "blocksize > 0.01 * n": blocksize > 0.01 * n,
            "nblocks ≡ ⌊n / blocksize⌋": nblocks == n // blocksize,
        }
    )

    if template is None:
        template = make_template(series, blocksize)
    template_size = len(template)

    matches_expect = (blocksize - template_size + 1) / 2 ** template_size
    variance = blocksize * (
        (1 / 2 ** template_size) - ((2 * template_size - 1)) / 2 ** (2 * template_size)
    )

    block_matches = []
    for block in blocks(series, blocksize=blocksize):
        matches = 0

        for window_tup in slider(block, template_size):
            if all(x == y for x, y in zip(window_tup, template)):
                matches += 1

        block_matches.append(matches)

    match_diffs = [matches - matches_expect for matches in block_matches]

    statistic = sum(diff ** 2 / variance for diff in match_diffs)
    p = gammaincc(nblocks / 2, statistic / 2)

    return NonOverlappingTemplateMatchingTestResult(
        statistic, p, template, matches_expect, variance, block_matches, match_diffs,
    )


@dataclass
class NonOverlappingTemplateMatchingTestResult(TestResult):
    template: List
    matches_expect: float
    variance: float
    block_matches: List[int]
    match_diffs: List[float]

    def __rich_console__(self, console, options):
        yield self._results_text("chi-square")

        yield ""

        yield f"template: {self.template}"

        f_matches_expect = round(self.matches_expect, 1)
        yield f"expected matches per block: {f_matches_expect}"

        matches_count = Counter(self.block_matches)
        table = sorted(matches_count.items())
        f_table = make_testvars_table("matches", "nblocks")
        for matches, nblocks in table:
            f_table.add_row(str(matches), str(nblocks))
        yield f_table


# ------------------------------------------------------------------------------
# Overlapping Template Matching Test


matches_ceil = 5


# TODO Review paper "Correction of Overlapping Template Matching Test Included in
#                    NIST Randomness Test Suite"
@randtest(rec_input=288)  # TODO appropiate min input
def overlapping_template_matching(series, template: List = None, nblocks=None, df=5):
    """Overlapping matches of template per block is compared to expected result

    The sequence is split into ``nblocks`` blocks, where the number of
    overlapping matches to the template in each block is found. This is
    referenced to the expected mean and variance in matches of a hypothetically
    truly random RNG.

    .. deprecated:: 0
        ``df`` will be removed once I figure out the correct value, as I don't
        quite understand what NIST wants (or if they're even correct!)

    Parameters
    ----------
    sequence : array-like
        Output of the RNG being tested
    template : ``List``, optional
        Template to match with the sequence, randomly generated if not
        provided.
    nblocks : ``int``
        Number of blocks to split sequence into
    df : ``int``, default ``5``
        Degrees of freedom to use in p-value calculation

    Returns
    -------
    TestResult
        Dataclass that contains the test's statistic and p-value.

    Raises
    ------
    TemplateContainsElementsNotInSequenceError
        If template contains values not present in sequence
    """
    n = len(series)

    if not nblocks:
        nblocks = floor(sqrt(n))
    blocksize = n // nblocks

    if not template:
        template = make_template(series, blocksize)
    template_size = len(template)

    lambda_ = (blocksize - template_size + 1) / 2 ** template_size
    eta = lambda_ / 2

    first_prob = exp(-eta)
    probabilities = [first_prob]
    for matches in range(1, matches_ceil):
        prob = ((eta * exp(-2 * eta)) / 2 ** matches) * hyp1f1(matches + 1, 2, eta)
        probabilities.append(prob)
    last_prob = 1 - sum(probabilities)
    probabilities.append(last_prob)

    check_recommendations(
        {
            "n ≥ nblocks * blocksize": n >= nblocks * blocksize,
            "nblocks * min(probabilities) > df": nblocks * min(probabilities) > df,
            "λ ≈ 2": isclose(lambda_, 2),
            "len(template) ≈ log2(nblocks)": isclose(template_size, log2(nblocks)),
            "df ≈ λ": isclose(template_size, log2(nblocks)),
        }
    )

    expected_tallies = [prob * nblocks for prob in probabilities]

    block_matches = []
    for block in blocks(series, blocksize=blocksize):
        matches = 0

        for window_tup in slider(block, template_size, overlap=True):
            if all(x == y for x, y in zip(window_tup, template)):
                matches += 1

        block_matches.append(matches)

    tallies = [0 for _ in range(matches_ceil + 1)]
    for matches in block_matches:
        i = min(matches, 5)
        tallies[i] += 1

    reality_check = []
    for tally_expect, tally in zip(expected_tallies, tallies):
        diff = (tally - tally_expect) ** 2 / tally_expect
        reality_check.append(diff)

    statistic = sum(reality_check)

    p = gammaincc(df / 2, statistic / 2)  # TODO should first param be df / 2

    return OverlappingTemplateMatchingTestResult(
        statistic, p, template, expected_tallies, tallies,
    )


@dataclass
class OverlappingTemplateMatchingTestResult(TestResult):
    template: List
    expected_tallies: List[int]
    tallies: List[int]

    def __post_init__(self):
        self.tally_diffs = []
        for expect, actual in zip(self.expected_tallies, self.tallies):
            diff = actual - expect
            self.tally_diffs.append(diff)

    def __rich_console__(self, console, options):
        yield self._results_text("chi-square")

        yield ""

        yield f"template: {self.template}"

        f_nmatches = [f"{x}" for x in range(matches_ceil + 1)]
        f_nmatches[-1] = f"{f_nmatches[-1]}+"

        table = zip(f_nmatches, self.tallies, self.expected_tallies, self.tally_diffs)
        f_table = make_testvars_table("matches", "count", "expected", "diff")
        for f_matches, count, count_expect, diff in table:
            f_count = str(count)
            f_count_expect = str(round(count_expect, 1))
            f_diff = str(round(diff, 1))
            f_table.add_row(f_matches, f_count, f_count_expect, f_diff)

        yield f_table
