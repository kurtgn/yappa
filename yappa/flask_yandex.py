import json
import sys
from base64 import b64decode
from json import JSONDecodeError

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode



try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

try:
    from flask import Flask
    from werkzeug.wrappers import BaseRequest
except ImportError:
    raise ImportError('FlaskYandex requires Flask to be installed.')


def make_environ(event):
    environ = {}

    for hdr_name, hdr_value in event['headers'].items():
        hdr_name = hdr_name.replace('-', '_').upper()
        if hdr_name in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
            environ[hdr_name] = hdr_value
            continue

        http_hdr_name = 'HTTP_%s' % hdr_name
        environ[http_hdr_name] = hdr_value

    qs = event['queryStringParameters']

    environ['REQUEST_METHOD'] = event['httpMethod']
    environ['PATH_INFO'] = event['path']
    environ['QUERY_STRING'] = urlencode(qs) if qs else ''
    environ['REMOTE_ADDR'] = event['requestContext']['identity']['sourceIp']
    environ['HOST'] = '%(HTTP_HOST)s:%(HTTP_X_FORWARDED_PORT)s' % environ
    environ['SCRIPT_NAME'] = ''

    environ['SERVER_PORT'] = environ['HTTP_X_FORWARDED_PORT']
    environ['SERVER_PROTOCOL'] = 'HTTP/1.1'

    environ['CONTENT_LENGTH'] = str(
        len(event['body']) if event['body'] else ''
    )

    environ['wsgi.url_scheme'] = environ['HTTP_X_FORWARDED_PROTO']
    environ['wsgi.input'] = StringIO(event['body'] or '')
    environ['wsgi.version'] = (1, 0)
    environ['wsgi.errors'] = sys.stderr
    environ['wsgi.multithread'] = False
    environ['wsgi.run_once'] = True
    environ['wsgi.multiprocess'] = False

    BaseRequest(environ)

    return environ


class LambdaResponse(object):
    def __init__(self):
        self.status = None
        self.response_headers = None

    def start_response(self, status, response_headers, exc_info=None):
        self.status = int(status[:3])
        self.response_headers = dict(response_headers)


def patch_event(event):
    event['path'] = '/'
    event['headers'].update(
        {'HOST': '', 'X_FORWARDED_PORT': '', 'X_FORWARDED_PROTO': ''}
    )
    if event['httpMethod'] == 'POST':
        try:
            json.loads(event['body'])
        except JSONDecodeError:
            event['body'] = b64decode(event['body']).decode()

    return event


def patch_response(response):
    response['body'] = response['body'].decode()

    code, headers = response['statusCode'], response['headers']
    if code == 302 and headers['Location'].startswith(':///'):
        headers['Location'] = headers['Location'][4:]

    return response


class FlaskYandex(Flask):
    def __call__(self, event, context):
        if 'httpMethod' not in event:
            # In this "context" `event` is `environ` and
            # `context` is `start_response`, meaning the request didn't
            # occur via API Gateway
            return super(FlaskYandex, self).__call__(event, context)

        response = LambdaResponse()

        event = patch_event(event)

        body = next(self.wsgi_app(make_environ(event), response.start_response))

        lambda_response = {
            'statusCode': response.status,
            'headers': response.response_headers,
            'body': body,
        }

        lambda_response = patch_response(lambda_response)

        return lambda_response
