import pandas as pd


def read_excel_sheet(path, sheet_name=None):
    # возвращает DataFrame
    df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
    if df is None:
        return pd.DataFrame()
    # чистим NaN -> None/''
    df = df.fillna('')
    return df


def write_excel_report(path, sheets: dict):
    # sheets: {'sheetname': dataframe}
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
