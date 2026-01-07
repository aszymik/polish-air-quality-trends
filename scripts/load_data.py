import pandas as pd
import requests
import zipfile
import io
from typing import Tuple

# id archiwum dla poszczególnych lat
gios_archive_url = "https://powietrze.gios.gov.pl/pjp/archives/downloadFile/"
gios_url_ids = {2015: '236', 2018: '603', 2021: '486', 2024: '582'}
gios_pm25_file = {2015: '2015_PM25_1g.xlsx', 2018: '2018_PM25_1g.xlsx', 2021: '2021_PM25_1g.xlsx', 2024: '2024_PM25_1g.xlsx'}

def download_gios_archive(year, gios_id, filename):
    """Pobiera podane archiwum."""
    # Pobranie archiwum ZIP do pamięci
    url = f"{gios_archive_url}{gios_id}"
    response = requests.get(url)
    response.raise_for_status()  # jeśli błąd HTTP, zatrzymaj
    
    # Otwórz zip w pamięci
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        # znajdź właściwy plik z PM2.5
        if not filename:
            print(f"Błąd: nie znaleziono {filename}.")
        else:
            # wczytaj plik do pandas
            with z.open(filename) as f:
                try:
                    df = pd.read_excel(f, header=None)
                except Exception as e:
                    print(f"Błąd przy wczytywaniu {year}: {e}")
    return df

def download_metadata():
    """Pobiera metadane o stacjach."""
    url = "https://powietrze.gios.gov.pl/pjp/archives/downloadFile/622"
    response = requests.get(url)
    response.raise_for_status()
    df = pd.read_excel(io.BytesIO(response.content), header=0)
    return df

def get_metadata():
    """Pobiera i preprocesuje metadane o stacjach."""
    metadata = download_metadata()
    metadata['Stary kod stacji'] = metadata['Stary Kod stacji \n(o ile inny od aktualnego)']
    metadata = metadata[['Kod stacji', 'Stary kod stacji', 'Miejscowość']]
    metadata['Stary kod stacji'] = metadata['Stary kod stacji'].replace({' ': pd.NA})  # zamieniamy spacje na nan
    return metadata

def get_code_mappings(metadata: pd.DataFrame) -> Tuple[dict, dict]:
    """Tworzy słowniki mapujące stare kody na nowe i kody na miasta."""
    old_to_new_code = {}  # słownik mapujący stare kody na nowe

    for _, row in metadata.dropna(subset=['Stary kod stacji']).iterrows():
        old_codes = str(row['Stary kod stacji']).split(',')  # rozdzielamy stare kody po przecinku
        for code in old_codes:
            code = code.strip()
            if code:
                old_to_new_code[code] = row['Kod stacji']
    
    code_to_city = ( # słownik mapujący kody na miasta
        metadata.set_index('Kod stacji')['Miejscowość']
        .to_dict()
    )
    return old_to_new_code, code_to_city

def rename_columns(df: pd.DataFrame, old_to_new_code: dict) -> pd.DataFrame:
    """Zmienia nazwy kolumn na nowe kody stacji."""
    new_col_names = []
    for col in df.columns:
        if col in old_to_new_code:
            new_col_names.append(old_to_new_code[col])
        else:
            new_col_names.append(col)
    df.columns = new_col_names
    return df

def add_multiindex(df, code_dict: dict) -> pd.DataFrame:
    """Dodaje miasto do multiindeksu."""
    # Pomijamy kolumnę 'Data'
    data_col = df['Data']
    data_values = df.drop(columns=['Data'])
    
    # Tworzymy MultiIndex na podstawie słownika metadanych
    for col in data_values.columns:
        if col not in code_dict:  # check, czy wszystkie kody są w słowniku
            print(col)

    tuples = [(code_dict.get(col, 'Nieznane'), col) for col in data_values.columns]
    multi_index = pd.MultiIndex.from_tuples(tuples, names=['Miejscowość', 'Kod stacji'])
    data_values.columns = multi_index
    
    # Dodajemy z powrotem kolumnę Data
    data_values.insert(0, 'Data', data_col)
    return data_values

def change_midnight_measurements(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Przesuwa pomiary o północy o jeden dzień wstecz."""
    df = df.copy()
    if year == 2015:
        # Nietypowy format daty w 2015
        df['Data'] = pd.to_datetime(df['Data'], format='%m/%d/%y %H:%M', errors='coerce')
    else:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

    # Przesuwamy pomiary o północy o -1
    midnight_dates = df['Data'].dt.time == pd.Timestamp('00:00:00').time()
    df.loc[midnight_dates, 'Data'] = df.loc[midnight_dates, 'Data'] - pd.Timedelta(seconds=1)

    return df

def download_and_preprocess_data(year: int, code_to_city: dict, old_to_new_code: dict, header_index: int=0) -> pd.DataFrame:
    """Pobiera i przygotowuje dane z archiwum GIOŚ dla podanego roku."""
    df = download_gios_archive(year, gios_url_ids[year], gios_pm25_file[year])

    # Zmieniamy nazwy kolumn na kody stacji
    col_names = df.iloc[header_index]
    col_names[0] = 'Data'
    df.columns = col_names
    df = df.drop(df.index[header_index])  # usuwamy wiersz nagłówka

    # Ujednolicamy nazwy kolumn
    df = rename_columns(df, old_to_new_code)

    # Usuwamy niepotrzebne wiersze nagłówkowe
    df = df[~df['Data'].isin(('Nr', 'Wskaźnik', 'Czas uśredniania', 'Jednostka', 'Kod stanowiska'))]

    # Przesuwamy pomiary z północy
    df = change_midnight_measurements(df, year)

    # Dodajemy multiindex: (miejscowość, kod stacji)
    df = add_multiindex(df, code_to_city)

    # Dodajemy rok i miesiąc
    df['Rok'] = year
    df['Miesiąc'] = df['Data'].dt.month
    return df

def join_data_on_common_stations(dfs: list[pd.DataFrame]) -> tuple[pd.DataFrame, list]:
    """Łączy DataFrame'y, zachowując tylko wspólne stacje."""
    return pd.concat(dfs, ignore_index=True, join="inner")

def read_data_from_csv(file_path: str) -> pd.DataFrame:
    """Wczytuje przetworzone dane z pliku CSV."""
    df = pd.read_csv(file_path, header=[0,1])
    df.columns = pd.MultiIndex.from_tuples(
        [(a, "" if "Unnamed" in str(b) else b) for a, b in df.columns],
        names=["Miejscowość", "Kod stacji"]
    )
    return df

