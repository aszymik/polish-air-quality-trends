import pandas as pd
from scripts.data_analysis import (
    get_monthly_means_for_stations,
    get_chosen_monthly_means,
    get_monthly_means_for_cities,
    get_who_norm_exceeding_days,
    get_max_and_min_k_stations,
)

from scripts.load_data import (
    get_code_mappings,
    rename_columns,
    add_multiindex,
    change_midnight_measurements
    )

def test_get_monthly_means_for_stations(sample_df):
    result = get_monthly_means_for_stations(sample_df)

    assert len(result) == 2

    jan_mean = 10.0  # styczeń 2022
    assert result.loc[(2022, 1), ('Warszawa','stacja1')] == jan_mean
    assert result.loc[(2022, 1), ('Warszawa','stacja2')] == 25.0
    assert result.loc[(2022, 1), ('Kraków','stacja1')] == 10.0  
    assert result.loc[(2022, 2), ('Warszawa','stacja1')] == 35.0

def test_get_monthly_means_for_stations_none(sample_df):
    sample_df[('Warszawa','stacja1')] = [None, None, None, None]
    sample_df[('Kraków','stacja1')] = [None, None, None, None]
    result = get_monthly_means_for_stations(sample_df)
    assert pd.isna(result.loc[(2022, 1), ('Warszawa','stacja1')])
    assert pd.isna(result.loc[(2022, 1), ('Kraków','stacja1')])

def test_get_chosen_monthly_means(sample_df):
    result = get_chosen_monthly_means(
        sample_df,
        chosen_years=[2022],
        chosen_cities=['Warszawa']
    )

    assert len(result) == 2  # 2 miesiące
    assert set(result['Miasto']) == {'Warszawa'}

    jan_value = result.loc[result['Miesiąc'] == 1, 'PM2.5'].iloc[0]  # średnia za styczeń
    assert jan_value == (10 + 20 + 30) / 3

def test_get_monthly_means_for_cities(sample_df):
    result = get_monthly_means_for_cities(sample_df)

    assert len(result) == 2
    assert 'Rok' in result.columns
    assert 'Miesiąc' in result.columns

def test_get_who_norm_exceeding_days(sample_df):
    result = get_who_norm_exceeding_days(sample_df)

    assert 2022 in result.columns
    assert result.loc[('Warszawa','stacja2'), 2022] == 4

def test_get_max_and_min_k_stations():

    data = {
        2022: [5, 10, 2, 20]
    }
    df = pd.DataFrame(
        data,
        index=['A', 'B', 'C', 'D']
    )

    result = get_max_and_min_k_stations(df, chosen_year=2022, k=1)

    assert list(result.index) == ['C', 'D']

def test_rename_columns():
    df = pd.DataFrame({
        'Data': [1, 2],
        'old1': [3, 4],
        'old2': [5, 6],
        'new3': [7, 8]
    })

    old_to_new_code = {
        'old1': 'A',
        'old2': 'B'
    }

    result = rename_columns(df, old_to_new_code)

    assert list(result.columns) == ['Data', 'A', 'B', 'new3']

def test_change_midnight_measurements(midnight):
    result = change_midnight_measurements(midnight, 2023)

    assert result.loc[1, 'Data'] == pd.Timestamp('2021-01-14 23:59:59')
    assert result.loc[2, 'Data'] == pd.Timestamp('2023-01-17 23:59:59') 
    assert result.loc[0, 'Data'] == pd.Timestamp('2021-01-15 14:30:00')

def test_change_midnight_measurements_2015(midnight_2015):
    result = change_midnight_measurements(midnight_2015, 2015)

    assert pd.notna(result.loc[0, 'Data'])
    assert result.loc[0, 'Data'] == pd.Timestamp('2015-01-15 14:00:00')
    assert result.loc[1, 'Data'] == pd.Timestamp('2015-01-15 23:59:59')
    assert result.loc[2, 'Data'] == pd.Timestamp('2015-01-17 23:59:00')

def test_change_midnight_measurements_none(midnight):
    midnight['Data'] = [pd.NaT, '2023-01-15 14:30:00', '2023-01-17 23:59:59']
    result = change_midnight_measurements(midnight, 2023)
    assert pd.isna(result.loc[0, 'Data'])
    assert pd.notna(result.loc[1, 'Data'])

def test_get_code_mappings(sample_metadata):
    old_to_new, code_to_city = get_code_mappings(sample_metadata)

    assert old_to_new == {
        'old1': 'stacja1',
        'old2': 'stacja1',
        'old3' : 'stacja3'
    }
    assert code_to_city == {
        'stacja1': 'Warszawa',
        'stacja2': 'Kraków',
        'stacja3': 'Gdańsk'
    }

def test_get_code_mappings_whitespaces():
    metadata = pd.DataFrame({
        'Kod stacji': ['stacja1'],
        'Stary kod stacji': [' old1, old2 '],
        'Miejscowość': [' Warszawa ']
    })
    old_to_new, code_to_city = get_code_mappings(metadata)
    assert 'old1' in old_to_new
    assert 'old2' in old_to_new
    assert old_to_new['old1'] == 'stacja1'
    assert ' old1 ' not in old_to_new

    
    

def test_get_code_mappings_no_old_codes(sample_metadata):

    sample_metadata['Stary kod stacji'] = [pd.NA, pd.NA, pd.NA]

    old_to_new, code_to_city = get_code_mappings(sample_metadata)
    assert len(old_to_new) == 0
    assert code_to_city['stacja1'] == 'Warszawa'
    assert code_to_city['stacja2'] == 'Kraków'

def test_add_multiindex(df_without_multiindex, code_to_city_dict):
    result = add_multiindex(df_without_multiindex, code_to_city_dict)
    assert ('Warszawa','stacja1') in result.columns
    assert ('Kraków','stacja2') in result.columns
    assert ('Nieznane','stacja3') in result.columns