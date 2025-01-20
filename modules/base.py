import sys
import yaml

import abc
import pika
import json

import time, uuid

class RemdisUpdateType:
    EMPTY = 'empty'
    ADD = 'add'
    REVOKE = 'revoke'
    COMMIT = 'commit'

class RemdisState:
    transition = {'talking':
                  {'SYSTEM_BACKCHANNEL': 'talking',
                   'USER_BACKCHANNEL': 'talking',
                   'BOTH_BACKCHANNEL': 'talking',
                   'SYSTEM_TAKE_TURN': 'talking',
                   'USER_TAKE_TURN': 'idle',
                   'BOTH_TAKE_TURN': 'idle',
                   'BOTH_SILENCE': 'idle',
                   'TTS_COMMIT': 'idle',
                   'ASR_COMMIT': 'talking'},
                  'idle':
                  {'SYSTEM_BACKCHANNEL': 'idle',
                   'USER_BACKCHANNEL': 'idle',
                   'BOTH_BACKCHANNEL': 'idle',
                   'SYSTEM_TAKE_TURN': 'talking',
                   'USER_TAKE_TURN': 'idle',
                   'BOTH_TAKE_TURN': 'idle',
                   'BOTH_SILENCE': 'idle',
                   'TTS_COMMIT': 'idle',
                   'ASR_COMMIT': 'talking'}
                  }

class RemdisModule:
    def __init__(self,
                 config_filename='../config/config.yaml',
                 host='localhost',
                 pub_exchanges=[],
                 sub_exchanges=[]):

        self.config_filename = config_filename
        self.pub_exchanges = pub_exchanges
        self.sub_exchanges = sub_exchanges
        self.host = host
        self._is_running = False

        # Load configuration file
        self.config = self.load_config(self.config_filename)
        self.language = self.config['BASE']['language']

        # Create publish channels
        self.pub_connections = {}
        for pub_exchange in self.pub_exchanges:
            self.pub_connections[pub_exchange] = self.mk_pub_connection(pub_exchange)

        # Create subscribe channels
        self.sub_connections = {}
        for sub_exchange in self.sub_exchanges:
            self.sub_connections[sub_exchange] = self.mk_sub_connection(sub_exchange)

    # General message publishing function
    def publish(self, message, exchange):
        self.pub_connections[exchange]['channel'].basic_publish(exchange=exchange,
                                                                routing_key='',
                                                                body=json.dumps(message))

    # General message subscribing function
    def subscribe(self, exchange, callback):
        self.sub_connections[exchange]['channel'].basic_consume(queue='',
                                                                auto_ack=True,
                                                                on_message_callback=callback)
        self.sub_connections[exchange]['channel'].start_consuming()

    # Function to create a publish channel
    def mk_pub_connection(self, exchange):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange, 'fanout')
        return {'connection': connection, 'channel': channel}

    # Function to create a subscribe channel
    def mk_sub_connection(self, exchange):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange, 'fanout')
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=exchange, queue=queue_name)
        return {'connection': connection, 'channel': channel}

    @abc.abstractmethod
    def run(self):
        pass

    # General IU creation function
    def createIU(self, body, exchange, update_type):
        iu = {}
        iu['timestamp'] = time.time()
        iu['id'] = str(uuid.uuid1())
        iu['producer'] = str(self.__class__.__name__)
        iu['update_type'] = str(update_type)
        #iu['data_type'] = data_type
        iu['exchange'] = exchange
        iu['body'] = body
        return iu

    # General IU print function
    def printIU(self, iu):
        sys.stdout.write('[%s] Body: %s, Update_type: %s, ID: %s\n'
                         % (iu['timestamp'], iu['body'],
                            iu['update_type'], iu['id']))

    # YAML configuration file loading function
    def load_config(self, config_filename):
        with open(config_filename) as f:
            config = yaml.safe_load(f)
        return config

    # General message parsing function
    def parse_msg(self, message):
        return json.loads(message)

class RemdisUtil:
    def remove_revoked_ius(self, iu_buffer):
        revoked_iu_ids = [iu['id'] for iu in iu_buffer if iu['update_type'] == RemdisUpdateType.REVOKE]
        
        output_iu_buffer = []
        for iu in iu_buffer:
            if iu['id'] not in revoked_iu_ids:
                output_iu_buffer.append(iu)
        return output_iu_buffer

    def concat_ius_body(self, iu_buffer, spacer=''):
        concat_body = ''
        for iu in iu_buffer:
           concat_body += iu['body'] + spacer
        return concat_body

    def check_buffer_empty(self, in_buffer):
        return len(in_buffer) == 0

class MMDAgentEXLabel:
    id2expression = {
        0: 'normal',
        1: 'joy',
        2: 'impressed',
        3: 'convinced',
        4: 'thinking',
        5: 'sleepy',
        6: 'suspicion',
        7: 'compassion',
        8: 'embarrassing',
        9: 'anger'
    }
    id2action = {
        0: 'wait',
        1: 'listening',
        2: 'nod',
        3: 'head_tilt',
        4: 'thinking',
        5: 'light_greeting',
        6: 'greeting',
        7: 'wavehand',
        8: 'wavehands',
        9: 'lookaround'
    }
