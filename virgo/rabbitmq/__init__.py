from kombu import Connection, Exchange, Queue,Consumer, eventloop
from pprint import pformat
import threading, logging

log = logging.getLogger("rabbitmq")

def pretty(obj):
    return pformat(obj, indent=4)

#: This is the callback applied when a message is received.
def handle_message(body, message):
    log.debug('Received message: %r' % (body,))
    log.debug('  properties:\n%s' % (pretty(message.properties),))
    log.debug('  delivery_info:\n%s' % (pretty(message.delivery_info),))
    if message.acknowledged == False:
        message.ack()

class RabbitmqClient:
    def __init__(self,mqURL='amqp://guest:guest@localhost:5672//',queue_name='jenkins_job_notif'):
        #: By default messages sent to exchanges are persistent (delivery_mode=2),
        #: and queues and exchanges are durable.

        self.service_url = mqURL
        self.queueName = queue_name
        self.exchange = Exchange(self.queueName, type='direct',durable=True,auto_delete=False)
        self.queue = Queue(self.queueName, self.exchange, routing_key=self.queueName,durable=True,auto_delete=False)
        self.started = True

    def decoratedCallback(self,body, message):

        right_message = self._callback(body,message)

        if right_message:
            handle_message(body,message)
            if self._consumer != None:
                self._consumer.cancel()

            if self._connection!=None:
                self._connection.release()


    def loopDrainEvents(self, connection):
        while self.started:
            log.debug('drain events....')
            try:
                connection.drain_events()
            except TypeError:
                break

    def stop(self):
        self.started = False

    def registerCallback(self,callback=None):
        """
        open a connection to MQ and register a listener.
        The callback function should return a boolean value,
        True to ack messsage and close connection.

        :param callback:
        :return:
        """

        self._callback = callback


        self._connection = Connection(self.service_url)
        self._connection.connect()
        channel = self._connection.channel()

        self._consumer = Consumer(channel, self.queue, no_ack=None,auto_declare=False,
                          callbacks=[self.decoratedCallback])
        self._consumer.consume()

        t1 = threading.Thread(target=self.loopDrainEvents,args=[self._connection])
        t1.start()

        return t1
