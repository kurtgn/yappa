import json
import os
import subprocess

import click

from . import init, deploy, undeploy

YAPPA_SETTINGS_FILE = 'yappa_settings.json'


@click.group()
def cli():
    pass


@cli.command(name='deploy')
def deploy_cmd():
    with open(YAPPA_SETTINGS_FILE) as f:
        config = json.load(f)

    function_name = config["project_name"]

    cmd = f'yc serverless function create --name={function_name}'
    try:
        subprocess.check_call(cmd.split(' '))
    except subprocess.CalledProcessError:
        error = click.style('ERROR:', fg="red", bold=True)
        click.echo(
            f'{error} if your function already exists, update your code with '
            + click.style('yappa update', fg="yellow", bold=True)
            + '.'
        )
        return

    cmd = (
        f'yc serverless function allow-unauthenticated-invoke '
        f'--name={function_name}'
    )
    subprocess.check_call(cmd.split(' '))

    deploy.do_upload(config)
    deploy.yc_get_function_info(function_name)

    click.echo(
        click.style('SUCCESS: ', fg='green', bold=True)
        + 'app deployed to Yandex Cloud!'
    )
    click.echo(
        'To update your app, run '
        + click.style('yappa update', fg="yellow", bold=True)
        + '.'
    )


@cli.command(name='status')
def status_cmd():
    with open(YAPPA_SETTINGS_FILE) as f:
        config = json.load(f)

    function_name = config["project_name"]
    deploy.yc_get_function_info(function_name)


@cli.command(name='logs')
@click.option('--since')
@click.option('--until')
def logs_cmd(since, until):
    with open(YAPPA_SETTINGS_FILE) as f:
        config = json.load(f)

    function_name = config['project_name']
    cmd = f'yc serverless function logs {function_name}'

    if since:
        cmd += f' --since={since}'

    if until:
        cmd += f' --until={until}'

    subprocess.check_call(cmd.split())


@cli.command(name='update')
def update_cmd():
    with open(YAPPA_SETTINGS_FILE) as f:
        config = json.load(f)
    deploy.do_upload(config)
    function_name = config['project_name']
    deploy.yc_get_function_info(function_name)


@cli.command(name='undeploy')
def undeploy_cmd():
    with open(YAPPA_SETTINGS_FILE) as f:
        config = json.load(f)

    undeploy.yc_delete_function(config['project_name'])


@cli.command(name='init')
def init_cmd():
    error = click.style('ERROR:', fg="red", bold=True)

    if os.path.exists(YAPPA_SETTINGS_FILE):
        error = click.style('ERROR', fg="red", bold=True)
        click.echo(f'{error} {YAPPA_SETTINGS_FILE} already exists.')
        return

    if 'VIRTUAL_ENV' not in os.environ:
        click.echo(
            f'{error}: Please activate your virtual environment '
            'before running Yappa.'
        )
        return

    project_name = init.get_project_name()
    python_version = init.get_python_version()
    aws_profile_name, aws_profile = init.get_aws_profile_name()
    requirements_filename = init.get_requirements_filename()
    bucket_name = init.get_bucket_name()
    entrypoint = init.get_entrypoint()

    config_dict = {
        'project_name': project_name,
        'runtime': python_version,
        'profile': aws_profile_name,
        'requirements_file': requirements_filename,
        'bucket': bucket_name,
        'entrypoint': entrypoint,
    }

    with open(YAPPA_SETTINGS_FILE, 'w') as f:
        json.dump(config_dict, f, indent=4)

    click.echo(
        'Initialization finished. Check '
        + click.style('yappa_settings.json', fg='blue', bold=True)
        + ' in your project folder.'
    )


if __name__ == '__main__':
    cli()
