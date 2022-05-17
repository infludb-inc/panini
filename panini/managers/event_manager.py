import asyncio
from functools import partial
from types import FunctionType

from panini import exceptions
from panini.exceptions import NotReadyError, ValidationError
from panini.validator import Validator


class EventManager:
    """
    Collect all functions from each module wrapped by @app.subscription or @EventManager.subscribe
    """

    def __init__(self):
        self._subscriptions = {}

    @property
    def subscriptions(self):
        return self._subscriptions

    def listen(
            self,
            subject: list or str,
            consumer_queue=None,
            data_type="json",
            validator: type = None,
            validator_schema=None,
            validation_error_cb: FunctionType = None,
            workers_count=None,
            app=None
    ):

        def wrapper(function):
            function = self.wrap_function_by_validator(
                function,
                subject,
                consumer_queue,
                workers_count,
                app,
                validator,
                validator_schema,
                validation_error_cb)
            if isinstance(subject, list):
                for t in subject:
                    self._check_subscription(t)
                    self._subscriptions[t].append(function)
            else:
                self._check_subscription(subject)
                self._subscriptions[subject].append(function)
            function.data_type = data_type
            return function

        return wrapper

    def wrap_function_by_validator(
            self,
            function,
            subject,
            consumer_queue,
            workers_count,
            app,
            validator,
            validator_schema,
            validation_error_cb):
        def validate_message(msg, validator_schema):
            try:
                if validator is not None:
                    validator.validated_message(msg.data, validator_schema)
            except exceptions.ValidationError as se:
                if validation_error_cb:
                    return validation_error_cb(msg, se)
                error = f"subject: {msg.subject} error: {str(se)}"
                return {"success": False, "error": error}
            except Exception as e:
                raise ValidationError(e)
            return True

        def wrapper(msg):
            validation_result = validate_message(msg)
            if validation_result is not True:
                return validation_result
            return function(msg)

        async def wrapper_async(msg):
            validation_result = validate_message(msg, validator_schema)
            if validation_result is not True:
                return validation_result

            async def cb(msg, worker_uuid=None):
                return await function(msg, worker_uuid)

            for _ in range(workers_count):
                await app.nats.js_client.subscribe(subject,
                                                   queue=consumer_queue,
                                                   cb=partial(cb, worker_uuid=_),
                                                   durable=consumer_queue
                                                   )

        if asyncio.iscoroutinefunction(function):
            return wrapper_async
        else:
            return wrapper

    def _check_subscription(self, subscription):
        if subscription not in self._subscriptions:
            self._subscriptions[subscription] = []
