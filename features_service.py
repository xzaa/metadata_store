"""Логика сравнения моделей фичей и обновления маппингов.

Ожидаемая структура входного Excel-файла (поля указаны пользователем):
  - Код витрины (mart)
  - Код сущности (tabl)
  - Код атрибута (fld)
  ... остальные колонки используем для описаний

feature_id формируется как "mart.tabl.fld"
"""
from typing import Tuple
import pandas as pd
from db import fetch_all, execute
from excel_utils import read_excel_sheet, write_excel_report


def _load_features_from_db() -> pd.DataFrame:
    query = '''
    SELECT feature_id, mart, tabl, fld, data_type, feature_nm_status
    FROM features
    '''
    rows = fetch_all(query)
    return pd.DataFrame(rows)


def _build_features_df_from_excel(path: str) -> pd.DataFrame:
    df = read_excel_sheet(path)
    col_map = {
        'Код витрины': 'mart',
        'Код сущности': 'tabl',
        'Код атрибута': 'fld',
        'Тип данных атрибута': 'data_type',
        'Описание атрибута': 'desc'
    }
    for orig, new in col_map.items():
        if orig not in df.columns:
            df[orig] = ''
    df = df.rename(columns={k: v for k, v in col_map.items()})
    df['feature_id'] = df['mart'].astype(str).str.strip() + '.' + df['tabl'].astype(str).str.strip() + '.' + df['fld'].astype(str).str.strip()
    df = df[df['feature_id'].str.strip() != '..']
    return df


def compare_features(excel_path: str, output_path: str):
    excel_df = _build_features_df_from_excel(excel_path)
    db_df = _load_features_from_db()

    excel_set = set(excel_df['feature_id'].dropna().astype(str))
    db_set = set(db_df['feature_id'].dropna().astype(str))

    inserts = excel_set - db_set
    deletes = db_set - excel_set

    df_inserts = excel_df[excel_df['feature_id'].isin(inserts)].copy()
    df_deletes = db_df[db_df['feature_id'].isin(deletes)].copy()

    orphan_mappings = []
    if len(deletes) > 0:
        placeholders = ','.join(['%s'] * len(deletes))
        query = f"SELECT feature_id, att_path FROM cm_to_fts_maping WHERE feature_id IN ({placeholders})"
        rows = fetch_all(query, list(deletes))
        orphan_mappings = pd.DataFrame(rows)
    else:
        orphan_mappings = pd.DataFrame(columns=['feature_id', 'att_path'])

    sheets = {
        'inserts': df_inserts.reset_index(drop=True),
        'deletes': df_deletes.reset_index(drop=True),
        'orphan_mappings': orphan_mappings.reset_index(drop=True)
    }
    write_excel_report(output_path, sheets)


def update_features_from_report(report_path: str):
    df_maps = read_excel_sheet(report_path, sheet_name='orphan_mappings')
    if df_maps is None or df_maps.empty:
        print('Нет удаляемых маппингов в отчёте')
        return

    for idx, row in df_maps.iterrows():
        old_feature = str(row.get('feature_id', '')).strip()
        att_path = str(row.get('att_path', '')).strip()
        new_feature = str(row.get('new_feature_id', '')).strip() if 'new_feature_id' in row else ''

        if new_feature:
            query = "UPDATE cm_to_fts_maping SET feature_id = %s WHERE feature_id = %s AND att_path = %s"
            execute(query, (new_feature, old_feature, att_path))
        else:
            query = "DELETE FROM cm_to_fts_maping WHERE feature_id = %s AND att_path = %s"
            execute(query, (old_feature, att_path))

    print('Обновление маппингов завершено')
