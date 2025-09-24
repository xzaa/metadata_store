"""Сравнение атрибутов новой задачи с cm_atts и task_attributes.

Для каждого атрибута из входного Excel формируем строку с полями:
  task_id, att_code, att_path, att_desc, status (найден/не найден), path_diff
"""
import pandas as pd
from db import fetch_all
from excel_utils import read_excel_sheet, write_excel_report


def _load_cm_atts(cm_id: str) -> pd.DataFrame:
    query = '''SELECT cm_id, att_code, att_path, att_desc, att_source FROM cm_atts WHERE cm_id = %s'''
    rows = fetch_all(query, (cm_id,))
    return pd.DataFrame(rows)


def compare_task_attributes(excel_path: str, cm_id: str, output_path: str):
    df = read_excel_sheet(excel_path)
    for col in ['task_id', 'att_code', 'att_path', 'att_desc']:
        if col not in df.columns:
            df[col] = ''

    report_rows = []
    cm_atts_df = _load_cm_atts(cm_id)
    cm_lookup = {}
    for _, r in cm_atts_df.iterrows():
        code = str(r.get('att_code', '')).strip()
        cm_lookup.setdefault(code, []).append(r)

    for _, r in df.iterrows():
        task_id = str(r.get('task_id', '')).strip()
        att_code = str(r.get('att_code', '')).strip()
        att_path = str(r.get('att_path', '')).strip()
        att_desc = str(r.get('att_desc', '')).strip()

        path_diff = ''
        status = 'не найден'

        candidates = cm_lookup.get(att_code, [])
        if candidates:
            status = 'найден'
            found_same_path = False
            for c in candidates:
                if str(c.get('att_path', '')).strip() == att_path:
                    found_same_path = True
                    break
            if not found_same_path:
                path_diff = ';'.join([str(c.get('att_path', '')) for c in candidates])

        report_rows.append({
            'task_id': task_id,
            'att_code': att_code,
            'att_path': att_path,
            'att_desc': att_desc,
            'status': status,
            'path_diff': path_diff
        })

    report_df = pd.DataFrame(report_rows)
    write_excel_report(output_path, {'task_compare': report_df})
