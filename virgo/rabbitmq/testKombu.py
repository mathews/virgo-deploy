# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 16:48:27 2016

@author: mathews
"""

import threading
from kombu import Connection, Exchange, Queue,Consumer, eventloop
from pprint import pformat


def pretty(obj):
    return pformat(obj, indent=4)

#: This is the callback applied when a message is received.
def handle_message(body, message):
    print('Received message: %r' % (body,))
    print('  properties:\n%s' % (pretty(message.properties),))
    print('  delivery_info:\n%s' % (pretty(message.delivery_info),))
    message.ack()

def loop(mqURL,queue_name):

    #: By default messages sent to exchanges are persistent (delivery_mode=2),
    #: and queues and exchanges are durable.
    exchange = Exchange(queue_name, type='direct',durable=True,auto_delete=False)
    queue = Queue(queue_name, exchange, routing_key=queue_name,durable=True,auto_delete=False)

    #: Create a connection and a channel.
    #: If hostname, userid, password and virtual_host is not specified
    #: the values below are the default, but listed here so it can
    #: be easily changed.
    with Connection(mqURL) as connection:
        #channel = connection.channel()
        #exchange.bind(channel)
        print exchange.is_bound
        #exchange.declare()

        #: Create consumer using our callback and queue.
        #: Second argument can also be a list to consume from
        #: any number of queues.
        with Consumer(connection, queue, auto_declare=False, callbacks=[handle_message]) as consumer:


            #: Each iteration waits for a single event.  Note that this
            #: event may not be a message, or a message that is to be
            #: delivered to the consumers channel, but any event received
            #: on the connection.
            for _ in eventloop(connection):
                pass

t1 = threading.Thread(target=loop,args=('amqp://guest:guest@localhost:5672//','jenkins_job_notif'))
t1.start()
#t1.join()
