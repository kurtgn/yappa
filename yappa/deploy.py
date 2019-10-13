import logging
import os
import shutil
import subprocess
import sys
from contextlib import suppress

import boto3
from botocore.session import Session as BotocoreSession

logger = logging.getLogger(__name__)


def get_s3_resource(profile_name):
    session = BotocoreSession()
    config = session.full_config
    profile = config['profiles'][profile_name]

    resource = boto3.resource(
        's3',
        aws_access_key_id=profile['aws_access_key_id'],
        aws_secret_access_key=profile['aws_secret_access_key'],
        endpoint_url='https://storage.yandexcloud.net',
    )
    return resource


def upload_to_bucket(bucket_name, profile_name, zipfile_path, bucket_key):
    """create bucket if it does not exist, upload package """

    # create bucket, break on any exception except BucketAlreadyOwnedByYou
    # (can't import BucketAlreadyOwnedByYou because it's generated dynamically)
    s3 = get_s3_resource(profile_name)
    bucket = s3.Bucket(bucket_name)
    try:
        bucket.create()
    except Exception as e:
        if e.__class__.__name__ != 'BucketAlreadyOwnedByYou':
            raise

    bucket.upload_file(zipfile_path, bucket_key)


def copy_source_code(temp_folder_name):
    with suppress(FileNotFoundError):
        shutil.rmtree(temp_folder_name)
    shutil.copytree(os.getcwd(), temp_folder_name)

    for path in ('.idea', '.git'):
        with suppress(FileNotFoundError):
            shutil.rmtree(os.path.join(temp_folder_name, path))


def install_requirements(requirements_file, temp_folder_name):
    logger.warning('installing requrements...')
    cmd = (
        f'{sys.executable} -m pip install '
        f'-r {requirements_file} -t {temp_folder_name} --upgrade --quiet'
    )
    subprocess.check_call(cmd.split())


def yc_create_function_version(
    bucket_name, bucket_key, entrypoint, runtime, function_name
):
    cmd = (
        f'yc serverless function version create '
        f'--function-name={function_name} '
        f'--runtime {runtime} '
        f'--entrypoint {entrypoint} '
        f'--memory 128m '
        f'--execution-timeout 5s '
        f'--package-bucket-name {bucket_name} '
        f'--package-object-name {bucket_key}'
    )
    subprocess.check_call(cmd.split())

    cmd = f'yc serverless function get --name={function_name}'
    subprocess.check_call(cmd.split())


def do_upload(config):

    temp_folder_name = os.path.join(os.getcwd(), 'yappa_package')

    try:
        copy_source_code(temp_folder_name)
        install_requirements(config['requirements_file'], temp_folder_name)

        logger.warning('Creating a zip package...')
        shutil.make_archive(temp_folder_name, 'zip', temp_folder_name)
        shutil.rmtree(temp_folder_name)

        logger.warning('Uploading to bucket...')
        upload_to_bucket(
            bucket_name=config['bucket'],
            profile_name=config['profile'],
            zipfile_path=f'{temp_folder_name}.zip',
            bucket_key='yappa_package.zip',
        )
        logger.warning('Updating function from bucket...')
        yc_create_function_version(
            bucket_name=config['bucket'],
            bucket_key='yappa_package.zip',
            entrypoint=config['entrypoint'],
            runtime=config['runtime'],
            function_name=config['project_name'],
        )
    finally:
        with suppress(FileNotFoundError):
            os.remove(f'{temp_folder_name}.zip')


if __name__ == '__main__':
    copy_source_code(os.path.join(os.getcwd(), 'packaged'))
    # ensure_bucket('xxxxx', 'yandex')
