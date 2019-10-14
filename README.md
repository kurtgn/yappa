# Yappa: Serverless Python for Yandex Cloud Functions

Деплоим Python в [Yandex Cloud Functions](https://cloud.yandex.ru/services/functions) легко и быстро.

<img src="ycf_logo.jpg" width="300" height="300">


## Демо

![](demo.gif)

- [Первый запуск](#первый-запуск)
- [Использование](#использование)
    - [Обновление функции](#обновление-функции)
    - [Просмотр логов](#просмотр-логов)
    - [Удаление функции](#удаление-функции)
- [Ограничения](#ограничения)
    - [Ограничения Яндекса](#ограничения-яндекса)
    - [Только один роут Flask](#только-один-роут-flask)
- [Разработка навыков для Алисы](#разработка-навыков-для-алисы)
- [Благодарности](#благодарности)
- [Если что-то не работает](#если-что-то-не-работает)


## Первый запуск


### 1. Настраиваем CLI

Для начала нужно скачать и настроить два CLI: яндексовский и амазоновский.

- Настраиваем [Yandex CLI](https://cloud.yandex.ru/docs/cli/quickstart)
- Настраиваем [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)


### 2. Ставим yappa и flask

```
pip install yappa
pip install flask
```


### 3. Создаем Flask-приложение


```python
from yappa.flask_yandex import FlaskYandex

app = FlaskYandex(__name__)


@app.route('/')
def main():
    return 'Hello from Yappa!'



```

### 4. Фиксируем requirements
```
pip freeze > requirements.txt
```

### 5. Деплоим

Инициализация и создание конфиг-файла:

```
yappa init
```

Деплой:
```
yappa deploy
```

**Профит!** Яндекс выдаст URL вида
`https://functions.yandexcloud.net/xxxxx`, на котором будет работать наша функция.


## Использование


### Обновление функции

После первого деплоя обновление функции выполняется командой:

 
```
yappa update
```



### Просмотр логов


```
yappa logs
```

Команда принимает два необязательных параметра `--since` и `--until` (синтаксис [см. здесь](https://cloud.yandex.ru/docs/functions/operations/function/function-logs)). 
Например, так можно просмотреть логи за последнюю минуту:

```
yappa logs --since 1m

```


### Удаление функции


```
yappa undeploy
```

Это удалит функцию из YCF.


## Ограничения

### Ограничения Яндекса
В одном облаке не может быть более 10 функций. Все ограничения [см. здесь](https://cloud.yandex.ru/docs/functions/concepts/limits)

### Только один роут Flask

Единственный URL, который может быть у приложения, выглядит так:

```
https://functions.yandexcloud.net/xxxxxx
```

В отличие от AWS Lambda, здесь нет возможности создавать роуты, например:

```
https://functions.yandexcloud.net/xxxxxx/dashboard
https://functions.yandexcloud.net/xxxxxx/users
```


Поэтому единственный роут, который может быть у вашего Flask-приложения, - это `/`:

```python
@app.route('/', methods=[...])

```

И весь роутинг внутри приложения необходимо делать на **GET-параметрах**:


```python

from flask import request, render_template

@app.route('/', methods=[...])
def main:
    if request.args.get('dashboard'):
        return render_template('dashboard.html')
    elif request.args.get('user'): 
        return render_template('user.html')
    ...        

```


## Разработка навыков для Алисы

Yappa позволяет деплоить можно не только Flask-приложения, но и обычные функции 
из [документации](https://cloud.yandex.ru/docs/functions/quickstart/function-quickstart#python-func).  

Именно такие функции и используются в Алисе. 

Для создания навыка Алисы можно написать такую функцию:

```python
def handler(event, context):
    """
    Entry-point for Serverless Function.
    :param event: request payload.
    :param context: information about current execution context.
    :return: response to be serialized as JSON.
    """
    text = 'Hello! I\'ll repeat anything you say to me.'
    if 'request' in event and \
            'original_utterance' in event['request'] \
            and len(event['request']['original_utterance']) > 0:
        text = event['request']['original_utterance']
    return {
        'version': event['version'],
        'session': event['session'],
        'response': {
            # Respond with the original request or welcome the user if this is the beginning of the dialog and the request has not yet been made.
            'text': text,
            # Don't finish the session after this response.
            'end_session': 'false'
        },
    }
```

и деплоить его точно так же командами `yappa init` / `yappa deploy`.

При деплое функции, а не Flask-приложения, 
необходимо изменить файл `yappa-settings.json` так, чтобы поле `entrypoint` указывало на эту функцию, например: 


```
{
    "project_name": "messageboard-yandex2",
    "entrypoint": "myapp.handler",
    ...
}


```



## Благодарности

Проект представляет собой смесь [Flask-Lambda](https://github.com/techjacker/flask-lambda) 
и [Zappa](https://github.com/Miserlou/Zappa), адаптированных под особенности YCF.


## Если что-то не работает

Проект тестировался только по Mac OS. Если что-то не работает под Windows/Linux - присылайте PR.
