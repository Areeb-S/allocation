import pandas as pd
import numpy as np
import itertools
from typing import Generator


def get_rotation(
    df, always_raw, tethers_raw, num_weeks, filter_dates
):

    # Option for will not be there

    # Option for needs to be there

    # Option for guest spot

    # Get all unique names
    all_names = pd.unique(df.iloc[:, 1:].values.ravel("K"))
    # Convert to tuple, and filter out nans
    all_names = tuple(
        n for n in all_names if not pd.isna(n)
    )
    if filter_dates:
        df["Date (Monday)"] = pd.to_datetime(
            df["Date (Monday)"],
            dayfirst=True,
        )
        # Past allocations occuring before and including today
        past_allocs = (
            df[
                df["Date (Monday)"]
                <= np.datetime64("today")
            ]
            .iloc[:, 1:]
            .values
        )
    else:
        past_allocs = df.iloc[:, 1:].values

    # Convert to integer indexes
    if always_raw is not None:
        always = tuple(
            all_names.index(name) for name in always_raw
        )
        # names without 'always' members
        names_minus_raw = tuple(
            n for n in all_names if n not in always_raw
        )
    else:
        always = tuple()
        names_minus_raw = all_names
    if tethers_raw is not None:
        tethers = tuple(
            tuple(all_names.index(name) for name in tether)
            for tether in tethers_raw
        )
    else:
        tethers = tuple(tuple())

    names_minus_always = tuple(
        all_names.index(name) for name in names_minus_raw
    )

    past_allocs = tuple(
        tuple(all_names.index(name) for name in p)
        for p in past_allocs
    )

    # Number of desks to assign to
    n_desks = len(df.columns) - (1 + len(always))

    valid_combs = get_valid(
        itertools.combinations(names_minus_always, n_desks),
        tethers,
    )

    new_allocs = iterate_idxes(
        num_weeks,
        past_allocs,
        all_names,
        valid_combs,
        always,
    )
    df = pd.DataFrame(
        [
            sorted([all_names[i] for i in a])
            for a in new_allocs
        ]
    )
    return df


def check_sample(
    sample: tuple[int], tethers: tuple[tuple[int]]
) -> bool:
    # Check if a sample meets the requirements (no repeats,
    # tethers appear together or not at all)

    if len(set(sample)) < len(sample):
        return False
    for tether in tethers:
        tether_check = len(set(sample) & set(tether))
        if tether_check != 0 and tether_check != len(
            tether
        ):
            return False
    return True


def get_valid(
    gen: Generator[tuple[int], None, None],
    tethers: tuple[tuple[int, int]],
) -> list[tuple[int]]:
    # Get all combinations that meet requirements
    valid = []
    for i, sample in enumerate(gen):
        if check_sample(sample, tethers):
            valid.append(sample)
    return valid


# Store all valid combinations
# valid_combs = get_valid(
#     itertools.combinations(names_minus_always, n_desks)
# )


def get_counts(
    sample: list[list[int]], all_names: tuple[str]
):
    # Get matrix that has a 1 for each combination of people
    # who are meeting. E.g if person at index 1, and person
    # at index 2 will be in, then [1,2] and [2,1] will equal
    # 1
    to_add = np.zeros([len(all_names), len(all_names)])
    for idx in itertools.combinations(sample, 2):
        to_add[idx] = 1
        to_add[idx[::-1]] = 1
    return to_add


def get_best_var(
    past_counts: int,
    chosen_samples: list[int],
    all_names: tuple[str],
    valid_combs,
    always,
) -> tuple[int, int]:
    # Get sample which gives best iterative variance. Works
    # by brutforce checking each valid combination and
    # finding the one with the lowest variance
    min_var = 100
    for i, idx in enumerate(valid_combs):
        curr_idx = idx + always
        count = get_counts(curr_idx, all_names)
        var = (past_counts + count).var()
        if var < min_var:
            min_var = var
            best_idx = curr_idx
            best_count = count
    return best_count, best_idx


def iterate_idxes(
    num_weeks: int,
    past_allocs: tuple[tuple[int]],
    all_names,
    valid_combs,
    always,
):
    # Iterate one at a time, and sequentially find best
    # combinations
    running_count = np.zeros(
        [len(all_names), len(all_names)]
    )
    for alloc in past_allocs:
        running_count += get_counts(alloc, all_names)

    samples = []
    for _ in range(num_weeks):
        new_count, new_sample = get_best_var(
            running_count,
            samples,
            all_names,
            valid_combs,
            always,
        )
        samples.append(new_sample)
        running_count += new_count
    return samples
