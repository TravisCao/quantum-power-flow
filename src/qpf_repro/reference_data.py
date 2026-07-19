"""Values transcribed from the source paper's Test I table."""

from __future__ import annotations

import numpy as np
import pandas as pd

PAPER_TABLE_I_QPF = np.asarray(
    [
        [1, 1.0141, 1.0282, -0.1143, -0.0368],
        [2, 0.9946, 1.0181, -0.1139, -0.0340],
        [3, 0.9950, 1.0183, -0.1144, -0.0393],
        [4, 0.9948, 1.0182, -0.1144, -0.0393],
        [5, 0.9948, 1.0182, -0.1144, -0.0393],
        [6, 0.9948, 1.0182, -0.1144, -0.0393],
    ],
    dtype=float,
)


def paper_table_i_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        PAPER_TABLE_I_QPF.copy(),
        columns=["iteration", "V3", "V4", "theta3_rad", "theta4_rad"],
    )
