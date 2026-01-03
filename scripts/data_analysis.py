import pandas as pd

def get_monthly_means_for_stations(df: pd.DataFrame) -> pd.DataFrame:
    """Oblicza miesięczne średnie wartości PM2.5 dla każdej stacji."""
    # Usuwamy datę, zostawiamy liczby
    df_number = df.drop(columns=[('Data', '')])
    monthly_means = df_number.groupby([('Rok', ''), ('Miesiąc', '')]).mean()
    return monthly_means

def get_chosen_monthly_means(df: pd.DataFrame, chosen_years: list, chosen_cities: list) -> pd.DataFrame:
    """Oblicza miesięczne średnie wartości PM2.5 dla wybranych miast i lat."""
    # Filtrowanie wierszy: czy są z wybranych lat
    df_trend = df[df['Rok'].isin(chosen_years)].copy()
    results = []

    # Iterujemy po miastach, korzsystając z kolumn należnych do danych miast
    for city in chosen_cities:
        city_col = df_trend.xs(city, level='Miejscowość', axis=1)
        
        years = df_trend[('Rok', '')]
        months = df_trend[('Miesiąc', '')]
        
        city_mean = city_col.mean(axis=1)
        for_now_df = pd.DataFrame({
            'Rok': years,
            'Miesiąc': months,
            'PM2.5': city_mean,
            'Miasto': city
        })
        # Średnie miesięczne
        monthly = for_now_df.groupby(['Rok', 'Miesiąc', 'Miasto'])['PM2.5'].mean().reset_index()
        results.append(monthly)

    final_df = pd.concat(results)
    return final_df

def get_monthly_means_for_cities(df: pd.DataFrame) -> pd.DataFrame:
    """Oblicza miesięczne średnie PM2.5 uśrednione dla wszystkich stacji miasta."""
    # Wybieramy kolumny z danymi
    data_cols = [col for col in df.columns if col[0] not in ['Data', 'Rok', 'Miesiąc']]
    meta_cols = [('Data', ''), ('Rok', ''), ('Miesiąc', '')]

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
    df[('Data', '')] = pd.to_datetime(df[('Data', '')])
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
