#!/usr/bin/env python
from requests.utils import unquote

from compair.manage.database import database_cli
from compair.manage.report import report_cli
from compair.manage.grades import grades_cli
from compair.manage.score import score_cli
from compair.manage.user import user_cli
from compair.manage.utils import util_cli
from compair.manage.kaltura import kaltura_cli
from compair import create_app

app = create_app(skip_assets=True)

app.cli.add_command(database_cli)
app.cli.add_command(report_cli)
app.cli.add_command(grades_cli)
app.cli.add_command(score_cli)
app.cli.add_command(user_cli)
app.cli.add_command(util_cli)
app.cli.add_command(kaltura_cli)

@app.cli.command('list-routes')
def list_routes():
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = unquote("{:60s} {:30s} {}".format(rule.endpoint, methods, rule))
        output.append(line)

    for line in sorted(output):
        print(line)
