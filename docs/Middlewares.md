You can add middleware to **Panini** applications.

A *"middleware"* (in common meaning) is a function that works with every **request** before it is processed by any specific path operation. And also with every **response** before returning it.

## Quck overview:

```python
import time

from panini.middleware import Middleware

class ProcessTimeMiddleware(Middleware):
    async def send_request(self, subject: str, message, request_func, *args, **kwargs):
        start_time = time.time()
        response = await request_func(subject, message, *args, **kwargs)
        process_time = time.time() - start_time
        response["process-time"] = str(process_time)
        return response

# app.add_middleware(ProcessTimeMiddleware)
# response = await app.request("subject", message)
# response: {"some_data": 12345, "process-time": '0.0051320'}
```

## Full overview

In Panini we have 2 core **operations** to communicate between microservices:

- send_operation (publish or request)
- listen_operation (listen any of send_operations)

Using Panini Middleware we can apply modifications to both of these operations "**before**" and "**after**" they are called.

**Main idea:**

- It takes each **operation** in your application.
- It can then do something to that **operation** or run any needed code (**before** the operation is called).
- Then it passes the **operation** to be processed by the rest of the application.
- It then takes the **response** generated by the application.
- It can do something to that **response** or run any needed code
(**after** operation is called**)**.
- Then it returns the **response.**

## Middleware Interface:

The basic interface of Panini Middleware looks like this:

```python
class Middleware:
		def __init__(self, *args, **kwargs):
        pass

    async def send_publish(self, subject: str, message, publish_func, *args, **kwargs):
        """
        :param subject: str
        :param message: any of supported types
        :param publish_func: Callable for publish
        :return: None
        """

    async def listen_publish(self, msg, callback):
        """
        :param msg: Msg
        :param callback: Callable, that will be called on receive message
        :return: None
        """

    async def send_request(self, subject: str, message, request_func, *args, **kwargs):
        """
        :param subject: str
        :param message: any of supported types
        :param request_func: Callable for request
        :return: any of supported types
        """

    async def listen_request(self, msg, callback):
        """
        :param msg: Msg
        :param callback: Callable, that will be called on receive message
        :return: any of supported types
        """

		# and composed functions for better user experience:
		async def send_any(self, subject: str, message, send_func, *args, **kwargs):
        """
        :param subject: str
        :param message: any of supported types
        :param send_func: Callable for send
        :return: None or any of supported types
        """

    async def listen_any(self, msg, callback):
        """
        :param msg: Msg
        :param callback: Callable, that will be called on receive message
        :return: None or any of supported types
        """
```

*Note here, that `send_any` will do the job for `send_request` and `send_publish`, if they are not implemented, but won't override them, if they exist. And the same stuff with `listen_any`.

## Examples

### ProcessTimeMiddleware

To create a middleware to add `process-time` parameter to response, that contains the time in seconds that it took to send & process the request and generate a response

The `send_request` function receives:

- The `subject` & `message`: such as common request function.
- A function `request_func` , that recieves subject, message & args, kwargs as parameters.
    - This function will send `request` to the corresponding subject with message provided.
    - This function will also call all other `middlewares` (if they exist) inside the app.
    - Then it returns the `response` before returning it.
- You can then modify further the `response` before returning it.

```python
import time

from panini.middleware import Middleware

class ProcessTimeMiddleware(Middleware):
    async def send_request(self, subject: str, message, request_func, *args, **kwargs):
        start_time = time.time()
        response = await request_func(subject, message, *args, **kwargs)
        process_time = time.time() - start_time
        response["process-time"] = str(process_time)
        return response
```

We will override only `send_request` function, so each time `app.request()` is called in our application - the processing time is calculated.

You just need to add ProcessTimeMiddleware before app.start()

```python
app.add_middleware(ProcessTimeMiddleware)
```

### TestingMiddleware

Imagine, that you want to easily switch to *test mode* in your application, which means:

- You want to always send to different subjects (the same subject, but with `test` prefix)
- You want to remove some `meaningful data` from requests & responses

```python
from panini.middleware import Middleware

class TestingMiddleware(Middleware):
    def __init__(self, meaningful_key):
        self.meaningful_key = meaningful_key

    async def send_any(self, subject: str, message, send_func, *args, **kwargs):
				subject = "test." + subject
        if self.meaningful_key in message:
            del message[self.meaningful_key]

        response = await send_func(subject, message, *args, **kwargs)

        if self.meaningful_key in response:
            del response[self.meaningful_key]
        return response

    async def listen_any(self, msg, callback):
        if self.meaningful_key in msg.data:
            del msg.data[self.meaningful_key]

        response = await callback(msg)

        if self.meaningful_key in response:
            del response[self.meaningful_key]
        return response
```

Then, you need to add TestingMiddleware and specify the meaningful_key parameter like this:

```python
app.add_middleware(TestingMiddleware, "meaningful_key")
```

**Please, notice, that you should use `async` interface for creating Middlewares 
(as written in examples)**

## Advanced Middlewares

- You can use some [built-in middlewares](https://github.com/lwinterface/panini/tree/master/panini/middleware) for common cases, already implemented in panini
- If you want to make hierarchical middleware, with more than 1 inheritance - 
please, re-call methods, from your base middleware:

```python
class FooMiddleware(Middleware):
    async def send_publish(self, subject: str, message, publish_func, *args, **kwargs):
        print("In Foo Middleware: publish")
        await publish_func(subject, message, *args, **kwargs)

class BarMiddleware(FooMiddleware):
    async def send_request(self, subject: str, message, request_func, *args, **kwargs):
        print("In Bar Middleware: request")
        return await request_func(subject, message, *args, **kwargs)

    async def send_publish(self, subject: str, message, publish_func, *args, **kwargs):
        return await super(BarMiddleware, self).send_publish(subject, message, *args, **kwargs)
```