from typing import List
import numpy as np
import matplotlib as mpl
from collections import OrderedDict


def get_colors(colormap_name: str,
               inverse: bool = False,
               n_segments: int = 7,
               ) -> List[str]:
    """get the colorramp"""
    cmap = mpl.colormaps.get(colormap_name)
    if not cmap:
        raise ValueError(f'colormap {colormap_name} not defined')
    crange = np.linspace(0, cmap.N, n_segments + 2)[1:-1].astype(int)
    if inverse:
        crange = crange[::-1]
    colors = [mpl.colors.to_hex(cmap(i)) for i in crange]
    return colors


def round_legend(value):
    rules = OrderedDict({1: 2,
                         10: 1,
                         100: 0,
                         1000: -1,
                         10000: -2,
                         100000: -3,
                         10000000000000: -3, })
    for limit, ndigits in rules.items():
        if value < limit:
            break
    return round(value, ndigits)


round_legend_values = np.vectorize(round_legend)


def get_percentiles(iterable,
                    percentiles: List[int]) -> List[float]:
    """get the percentiles of the values"""
    try:
        first_item = iterable[0]
    except IndexError:
        return None

    if isinstance(first_item, dict):
        values = np.array([row['value'] for row in iterable
                            if not row['value'] is None])
    else:
        values = np.array([row.value for row in iterable
                           if not row.value is None])

    result = np.nanpercentile(values, percentiles, method='closest_observation')
    rounded_results = round_legend_values(result)
    unique_results = np.unique(rounded_results)
    return unique_results
