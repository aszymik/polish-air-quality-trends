import pandas as pd
import pytest

@pytest.fixture
def sample_df():
    data = {
        ('Data',''): pd.to_datetime([
            '2022-01-01', '2022-01-02',
            '2022-02-01', '2022-02-02'
        ]),
        ('Rok',''): [2022, 2022, 2022, 2022],
        ('Miesiąc',''): [1, 1, 2, 2],
        ('Warszawa','stacja1'): [10, None, 30, 40],
        ('Warszawa','stacja2'): [20, 30, 40, 50],
        ('Kraków','stacja1'): [5, 15, 25, None],
    }
    df = pd.DataFrame(data)
    df.columns = pd.MultiIndex.from_tuples(
        df.columns,
        names=["Miejscowość", "Kod stacji"]
    )
    return df