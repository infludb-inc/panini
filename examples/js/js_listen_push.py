from examples.js.js_validator import Validator
from panini import app as panini_app

app = panini_app.App(
    service_name="js_listen_push",
    host="127.0.0.1",
    port=4222,
    enable_js=True
)

log = app.logger
NUM = 0


def get_message():
    return {
        "id": app.nats.client.client_id,
    }


def validation_error_cb(msg, error):
    print("Message: ", msg, "\n\n Error: ", error)


# Multiple subscribers
@app.listen("test.*.stream", workers_count=10, validator=Validator,
            validation_error_cb=validation_error_cb)
async def print_msg(msg, worker_uuid):
    print(f"got JS message {worker_uuid}! {msg.subject}:{msg.data}")
    await msg.ack()


if __name__ == "__main__":
    app.start()
