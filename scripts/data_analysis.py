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
    # Filtrowanie po miastach i latach
    city_cols = [col for col in df.columns if col[0] in chosen_cities]
    year_rows = df[('Data', '')].dt.year.isin(chosen_years)
    
    # Tworzymy format długi do grupowania
    df_long = df.loc[year_rows, [('Data', '')] + city_cols].melt(
        id_vars=[('Data', '')],
        var_name='Miejscowość',
        value_name='PM2.5'
    )

    # Średnie miesięczne po miastach
    df_monthly = (
        df_long.groupby([
            df_long[('Data', '')].dt.year.rename('Rok'),
            df_long[('Data', '')].dt.month.rename('Miesiąc'),
            'Miejscowość'
        ])['PM2.5']
        .mean()
        .reset_index()
    )
    return df_monthly

def get_monthly_means_for_cities(df: pd.DataFrame) -> pd.DataFrame:
    """Oblicza miesięczne średnie PM2.5 uśrednione dla wszystkich stacji miasta."""
    # Wybieramy kolumny z danymi
    data_cols = [col for col in df.columns if col[0] != 'Data']
    df_num = df[data_cols].apply(pd.to_numeric, errors='coerce')

    # Grupowanie po miejscowości (poziom 0 indeksu) i uśrednienie
    df_city = df_num.groupby(level=0, axis=1).mean()

    # Uśrednienie po miesiącu w każdym roku
    df_means = (
        df_city.groupby([
            df[('Data', '')].dt.year.rename('Rok'),
            df[('Data', '')].dt.month.rename('Miesiąc')
        ])
        .mean()
        .reset_index()
    )
    return df_means

def get_who_norm_exceeding_days(df: pd.DataFrame) -> pd.DataFrame:
    """Zwraca liczbę dni w miesiącu, w których średnie dzienne PM2.5 przekroczyły normę WHO (15 µg/m³)."""
    # Ustawiamy indeks czasowy i resamplujemy dane do częstotliwości dziennej ('D')
    df[('Data', '')] = pd.to_datetime(df[('Data', '')], format="mixed")
    # Ustawiamy datę jako indeks
    df_daily = df.set_index(('Data', ''))
    daily_means = df_daily.resample('D').mean()

    exceeded_mask = daily_means > 15
    yearly_counts = exceeded_mask.groupby(daily_means.index.year).sum()

    return yearly_counts.T  # stacje w wierszach, lata w kolumnach

def get_max_and_min_k_stations(yearly_counts: pd.DataFrame, chosen_year: int, k: int=3) -> pd.DataFrame:
    """Zwraca DataFrame z k stacjami o najwyższych i najniższych liczbach dni 
    z przekroczeniem normy WHO w wybranym roku."""
    if chosen_year not in yearly_counts.columns:
        return pd.DataFrame()
        
    sorted_results = yearly_counts.sort_values(by=chosen_year)
    return pd.concat([sorted_results.head(k), sorted_results.tail(k)])