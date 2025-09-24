import pandas as pd


def read_excel_sheet(path, sheet_name=None):
    # Если явно не указали лист, берём первый
    if sheet_name is None:
        df_dict = pd.read_excel(path, sheet_name=None, dtype=str)
        # берём первый лист
        first_sheet = list(df_dict.keys())[0]
        df = df_dict[first_sheet]
    else:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)

    # чистим NaN -> ''
    df = df.fillna('')
    return df


def write_excel_report(path, sheets: dict):
    # sheets: {'sheetname': dataframe}
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
