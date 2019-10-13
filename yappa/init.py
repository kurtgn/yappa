import os
import os
import sys
from importlib import import_module
from uuid import uuid4

import click
import slugify
from botocore.session import Session as BotocoreSession

BOTO3_CONFIG_DOCS_URL = (
    'https://boto3.readthedocs.io/en/latest/guide/'
    'quickstart.html#configuration'
)

YANDEX_OBJECT_STORAGE_NAMING = (
    'https://boto3.readthedocs.io/en/latest/guide/'
    'quickstart.html#configuration'
)


def is_valid_bucket_name(name):
    """
    Checks if an S3 bucket name is valid according to
    https://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html#bucketnamingrules
    """
    # Bucket names must be at least 3 and no more than 63 characters long.
    if len(name) < 3 or len(name) > 63:
        return False
    # Bucket names must not contain uppercase characters or underscores.
    if any(x.isupper() for x in name):
        return False
    if "_" in name:
        return False
    # Bucket names must start with a lowercase letter or number.
    if not (name[0].islower() or name[0].isdigit()):
        return False
    # Bucket names must be a series of one or more labels.
    # Adjacent labels are separated by a single period (.).
    for label in name.split("."):
        # Each label must start and end with a lowercase letter or a number.
        if len(label) < 1:
            return False
        if not (label[0].islower() or label[0].isdigit()):
            return False
        if not (label[-1].islower() or label[-1].isdigit()):
            return False
    # Bucket names must not be formatted as an IP address
    # (for example, 192.168.5.4).
    looks_like_IP = True
    for label in name.split("."):
        if not label.isdigit():
            looks_like_IP = False
            break
    if looks_like_IP:
        return False

    return True


def get_project_name():
    default_name = slugify.slugify(os.getcwd().split(os.sep)[-1])[:20]
    profile_name = (
        input(f"Enter your project name (default '{default_name}'): ")
        or default_name
    )

    return profile_name


def get_entrypoint():
    while True:
        entrypoint = input(
            'Specify path to your FlaskYandex app or to your handler '
            '(for example: somemodule.app) '
        )
        if entrypoint:
            return entrypoint


def get_python_version():
    return 'python{}{}'.format(*sys.version_info)


def get_requirements_filename():

    default_filename = 'requirements.txt'

    return (
        input(f'Enter your requirements file (default {default_filename})')
        or default_filename
    )


def get_bucket_name():
    click.echo(
        "\nYour Yappa deployments will need to be uploaded to a "
        + click.style("private Object Storage bucket", bold=True)
        + "."
    )
    click.echo("If you don't have a bucket yet, we'll create one for you too.")
    default_bucket = "yappa-" + str(uuid4())[:8]
    while True:
        bucket = (
            input(
                f"What do you want to call your bucket? "
                f"(default '{default_bucket}'): "
            )
            or default_bucket
        )

        if is_valid_bucket_name(bucket):
            break

        click.echo(click.style("Invalid bucket name!", bold=True))
        click.echo(
            f"Object Storage buckets must be named according to the rules: "
            f"{YANDEX_OBJECT_STORAGE_NAMING}"
        )

    return bucket


def get_aws_profile_name():
    # Detect AWS profiles and regions
    # If anyone knows a more straightforward way to easily detect and parse
    # AWS profiles I'm happy to change this, feels like a hack
    session = BotocoreSession()
    config = session.full_config
    profiles = config.get("profiles", {})
    profile_names = list(profiles.keys())

    if not profile_names:
        profile_name, profile = None, None
        click.echo(
            "We couldn't find an AWS profile to use. Before using Zappa,"
            " you'll need to set one up. See here for more info: {}".format(
                click.style(BOTO3_CONFIG_DOCS_URL, fg="blue", underline=True)
            )
        )
    elif len(profile_names) == 1:
        profile_name = profile_names[0]
        profile = profiles[profile_name]
        click.echo(
            "Okay, using profile {}!".format(
                click.style(profile_name, bold=True)
            )
        )
    else:
        if "default" in profile_names:
            default_profile = [p for p in profile_names if p == "default"][0]
        else:
            default_profile = profile_names[0]

        while True:
            profile_name = (
                input(
                    "We found the following profiles: {}, and {}. "
                    "Which would you like us to use? (default '{}'): ".format(
                        ', '.join(profile_names[:-1]),
                        profile_names[-1],
                        default_profile,
                    )
                )
                or default_profile
            )
            if profile_name in profiles:
                profile = profiles[profile_name]
                break
            else:
                click.echo("Please enter a valid name for your AWS profile.")
    return profile_name, profile
