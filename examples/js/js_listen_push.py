from panini import app as panini_app
from functools import partial

app = panini_app.App(
    service_name="js_listen_push",
    host="127.0.0.1",
    port=4222,
    enable_js=True
)

log = app.logger
NUM = 0


@app.on_start_task()
async def on_start_task():
    # Persist messages on 'test.*.stream' subject.
    await app.nats.js_client.add_stream(name="sample-stream-1", subjects=["test.*.stream"])


def get_message():
    return {
        "id": app.nats.client.client_id,
    }


@app.timer_task(interval=0.05)
async def publish_periodically():
    subject = "test.app2.stream"
    message = get_message()
    global NUM
    NUM += 1
    message['counter'] = NUM
    await app.publish(subject=subject, message=message)
    # log.info(f"sent {message}")


def get_message():
    return {
        "id": app.nats.client.client_id,
    }

# Multiple subscribers
@app.task()
async def subscribe_to_js_stream_push(workers_count=10):
    async def cb(msg, worker_uuid=None):
        log.info(f"got JS message {worker_uuid}! {msg.subject}:{msg.data}")
        await msg.ack()

    for _ in range(workers_count):
        await app.nats.js_client.subscribe("test.*.stream", queue='consumer', cb=partial(cb, worker_uuid=_), durable='consumer')


# One subscribers
@app.task()
async def subscribe_to_js_stream_push():
    async def cb(msg):
        log.info(f"got JS message ! {msg.subject}:{msg.data}")

    await app.nats.js_client.subscribe("test.*.stream", cb=cb, durable='consumer-1', stream="sample-stream-1")


if __name__ == "__main__":
    app.start()
