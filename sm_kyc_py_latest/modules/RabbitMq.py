import pika


class ProducerQueue:
    def __init__(self, host, vhost, port, username, password, exchange_name, queue_name):
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.hostName = host
        self.vhost = vhost
        self.qport = port
        self.credentials = pika.PlainCredentials(username, password)

    def connect_to_queue(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.hostName, virtual_host=self.vhost, port=self.qport,
                                      credentials=self.credentials))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.queue_bind(queue=self.queue_name, exchange=self.exchange_name, routing_key=self.queue_name)

    def publish_message(self, message):
        self.connect_to_queue()
        try:
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=self.queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json',
                ))
        except Exception as e:
            print("Exception publishing message to queue", e)

        else:
            print("Message published successfully", message)
        finally:
            self.connection.close()