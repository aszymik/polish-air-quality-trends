import pandas as pd

def get_monthly_means_for_stations(df: pd.DataFrame) -> pd.DataFrame:
    """Oblicza miesięczne średnie wartości PM2.5 dla każdej stacji."""
    # Konwersja tylko kolumn stacji
    df_num = df.drop(columns=[('Data', '')]).apply(
        pd.to_numeric, errors="coerce"
    )
    monthly_means = (
        df_num
        .groupby([
            df[('Data', '')].dt.year.rename("Rok"),
            df[('Data', '')].dt.month.rename("Miesiąc"),
        ])
        .mean()
    )
    return monthly_means

def get_chosen_monthly_means(df: pd.DataFrame, chosen_years: list, chosen_cities: list) -> pd.DataFrame:
    """Oblicza miesięczne średnie wartości PM2.5 dla wybranych miast i lat."""
    df = df.copy()
    df[('Rok', '')] = df[('Data', '')].dt.year
    df[('Miesiąc', '')] = df[('Data', '')].dt.month

    # Filtrowanie wierszy i kolumn po latach i miastach
    df = df[df[('Rok', '')].isin(chosen_years)]
    city_cols = [col for col in df.columns if col[0] in chosen_cities]

    # Przekształcamy do długiego formatu długiego żeby ułatwić grupowanie
    df_long = df.melt(
        id_vars=[('Rok', ''), ('Miesiąc', '')],
        value_vars=city_cols,
        var_name='Miejscowość',
        value_name='PM2.5',
    )

    # Średnie miesięczne po miastach
    df_monthly = (
        df_long
        .groupby([('Rok', ''), ('Miesiąc', ''), 'Miejscowość'], as_index=False)
        ['PM2.5']
        .mean()
    )
    df_monthly.columns = ['Rok', 'Miesiąc', 'Miejscowość', 'PM2.5']
    return df_monthly

def get_monthly_means_for_cities(df: pd.DataFrame) -> pd.DataFrame:
    """Oblicza miesięczne średnie PM2.5 uśrednione dla wszystkich stacji miasta."""
    # Wybieramy kolumny z danymi
    data_cols = [col for col in df.columns if col[0] not in ['Data', 'Rok', 'Miesiąc']]
    meta_cols = [('Data', ''), ('Rok', ''), ('Miesiąc', '')]

    for col in data_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Grupowanie po miejscowości (poziom 0 indeksu) i uśrednienie
    df_means = df[data_cols].T.groupby(level=0).mean().T
    df_means

    # Dodanie kolumn meta z powrotem
    df_means[('Rok', '')] = df[('Rok', '')]
    df_means[('Miesiąc', '')] = df[('Miesiąc', '')]
    df_means = df_means[[('Rok', ''), ('Miesiąc', '')] + [col for col in df_means.columns if col not in meta_cols]]
    df_means

    # Uśrednienie po miesiącu w każdym roku
    df_means = (
        df_means.groupby([('Rok', ''), ('Miesiąc', '')])
        .mean()
        .reset_index()
        .rename(columns={('Rok', ''): 'Rok', ('Miesiąc', ''): 'Miesiąc'})
    )
    return df_means

def get_who_norm_exceeding_days(df: pd.DataFrame) -> pd.DataFrame:
    """Zwraca liczbę dni w miesiącu, w których średnie dzienne PM2.5 przekroczyły normę WHO (15 µg/m³)."""
    # Ustawiamy indeks czasowy i resamplujemy dane do częstotliwości dziennej ('D')
    df[('Data', '')] = pd.to_datetime(df[('Data', '')], format="mixed")
    # Ustawiamy datę jako indeks i usuwamy zbędne kolumny tekstowe (Rok, Miesiąc)
    df_daily = df.set_index(('Data', '')).drop(columns=[('Rok', ''), ('Miesiąc', '')])
    daily_means = df_daily.resample('D').mean()

    exceeded_mask = daily_means > 15
    yearly_counts = exceeded_mask.groupby(daily_means.index.year).sum()

    return yearly_counts.T

def get_max_and_min_k_stations(yearly_counts: pd.DataFrame, chosen_year: int, k: int=3) -> pd.DataFrame:
    """Zwraca DataFrame z k stacjami o najwyższych i najniższych liczbach dni 
    z przekroczeniem normy WHO w wybranym roku."""
    sorted_results = yearly_counts.sort_values(by=chosen_year)
    best_k = sorted_results.head(k)
    worst_k = sorted_results.tail(k)
    return pd.concat([best_k, worst_k])
