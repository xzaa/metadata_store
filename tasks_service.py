"""Сравнение атрибутов новой задачи с cm_atts и task_attributes.

Для каждого атрибута из входного Excel формируем строку с полями:
  task_id, att_code, att_path, att_desc, status (найден/не найден), path_diff
"""
import pandas as pd
from db import fetch_all, execute
from excel_utils import read_excel_sheet, write_excel_report


def _load_cm_atts(cm_id: str) -> pd.DataFrame:
    query = '''SELECT cm_id, att_code, att_path, att_desc, att_source FROM cm_atts WHERE cm_id = %s'''
    rows = fetch_all(query, (cm_id,))
    return pd.DataFrame(rows)


def compare_task_attributes(excel_path: str, cm_id: str, output_path: str):
    df = read_excel_sheet(excel_path)

    # маппинг русские → служебные имена
    col_map = {
        "Название стратегии": "task_id",
        "Наименование поля на входе в стратегию": "att_code",
        "Полный путь до атрибута": "att_path",
        "Описание поля на входе в стратегию": "att_desc",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # гарантируем, что все нужные колонки есть
    for col in ['task_id', 'att_code', 'att_path', 'att_desc']:
        if col not in df.columns:
            df[col] = ''

    # сравнение
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




def update_task(report_path: str, cm_id: str):
    """
    Обновляет задачу и её атрибуты на основе отчёта compare_task_attributes.

    Правила:
      - Для всех строк отчёта создаётся задача (если её нет).
      - Для status = 'не найден':
          вставляем задачу (если нет),
          добавляем атрибут в cm_atts,
          добавляем связь task_attributes.
      - Для status = 'найден':
          вставляем задачу (если нет),
          добавляем только связь task_attributes.
    """
    df = read_excel_sheet(report_path, sheet_name="task_compare")

    if df.empty:
        print("Отчёт пустой")
        return

    for _, r in df.iterrows():
        task_id = str(r.get('task_id', '')).strip()
        att_code = str(r.get('att_code', '')).strip()
        att_path = str(r.get('att_path', '')).strip()
        att_desc = str(r.get('att_desc', '')).strip()
        status = str(r.get('status', '')).strip()

        if not task_id:
            continue

        # 1. Вставляем задачу, если её нет
        rows = fetch_all("SELECT 1 FROM tasks WHERE task_id = %s", (task_id,))
        if not rows:
            execute("INSERT INTO tasks (task_id) VALUES (%s)", (task_id,))
            print(f"Добавлена задача: {task_id}")

        # 2. Если атрибут "не найден" → вставляем в cm_atts
        if status == "не найден" and att_code and att_path:
            rows = fetch_all(
                "SELECT 1 FROM cm_atts WHERE cm_id = %s AND att_code = %s",
                (cm_id, att_code)
            )
            if not rows:
                execute(
                    """INSERT INTO cm_atts (cm_id, att_code, att_path, att_desc)
                       VALUES (%s, %s, %s, %s)""",
                    (cm_id, att_code, att_path, att_desc)
                )
                print(f"Добавлен атрибут: {att_code} ({att_path})")

        # 3. Создаём связь задача ↔ атрибут (для всех статусов)
        if att_path:
            rows = fetch_all(
                "SELECT 1 FROM task_attributes WHERE task_id = %s AND att_path = %s",
                (task_id, att_path)
            )
            if not rows:
                execute(
                    "INSERT INTO task_attributes (task_id, att_path) VALUES (%s, %s)",
                    (task_id, att_path)
                )
                print(f"Создана связь task={task_id} ↔ att_path={att_path}")
