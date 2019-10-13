import subprocess


def yc_delete_function(function_name):
    cmd = f'yc serverless function delete {function_name}'
    subprocess.check_call(cmd.split())
