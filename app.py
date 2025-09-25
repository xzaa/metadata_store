"""CLI для операций сравнения и обновления модели метаданных.

Примеры:
  python app.py compare_features --file new_model.xlsx --output report.xlsx
  python app.py update_features --file report.xlsx
  python app.py compare_task --file task.xlsx --cm_id CV --output task_report.xlsx
  python app.py update_task --file task_report.xlsx --cm_id CV
"""
import click
from features_service import compare_features, update_features_from_report
from tasks_service import compare_task_attributes, update_task


@click.group()
def cli():
    pass


@cli.command(name="compare_features")
@click.option('--file', 'file_path', required=True, help='Excel файл с моделью фичей')
@click.option('--output', 'out_path', default='features_report.xlsx', help='Путь для отчёта')
def compare_features_cmd(file_path, out_path):
    compare_features(file_path, out_path)
    click.echo(f"Отчёт сохранён: {out_path}")


@cli.command(name="update_features")
@click.option('--file', 'file_path', required=True, help='Excel-отчёт из compare_features')
def update_features_cmd(file_path):
    update_features_from_report(file_path)
    click.echo('Обновление завершено')


@cli.command(name="compare_task")
@click.option('--file', 'file_path', required=True, help='Excel файл с задачей')
@click.option('--cm_id', required=True, help='Идентификатор канонической модели')
@click.option('--output', 'out_path', default='task_report.xlsx', help='Путь для отчёта')
def compare_task_cmd(file_path, cm_id, out_path):
    compare_task_attributes(file_path, cm_id, out_path)
    click.echo(f"Отчёт по задаче сохранён: {out_path}")




@cli.command(name="update_task")
@click.option('--file', 'file_path', required=True, help='Excel отчёт по задаче (из compare_task)')
@click.option('--cm_id', required=True, help='Идентификатор канонической модели')
def update_task_cmd(file_path, cm_id):
    update_task(file_path, cm_id)
    click.echo("Обновление задачи завершено")



if __name__ == '__main__':
    cli()
