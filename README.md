# Yappa: Serverless Python for Yandex Cloud Functions

## About

Deploy your Flask apps to [Yandex Cloud Functions](https://cloud.yandex.ru/services/functions) like a boss.


![](demo.gif)


## Usage

```
pip install yappa
pip install flask
```


Create an app:

```python
from yappa.flask_yandex import FlaskYandex

app = FlaskYandex(__name__)


@app.route('/')
def main():
    return 'Hello from Yappa!'


```

Initialize Yappa:

```
yappa init
```

Deploy:
```
yappa deploy
```

After first deploy, you can update your function with `yappa update`



### Prerequisites

- Install and configure [Yandex CLI](https://cloud.yandex.ru/docs/cli/quickstart)
- Install and configure [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)


### 
