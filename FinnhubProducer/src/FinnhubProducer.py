import os
import ast
import json
import websocket
from utils.functions import *


class FinnhubProducer:
    def __init__(self):
        print('Enviroment:')
        for k, v in os.environ.items():
            print(f'{k}={v}')

        self.finnhub_client = load_client(os.environ['FINNHUB_API_TOKEN'])
        self.producer = load_producer(
            f"{os.environ['KAFKA_SERVER']}:{os.environ['KAFKA_PORT']}")
        self.avro_schema = load_avro_schema('src/schemas/trades.avsc')
        self.tickers = ast.literal_eval(os.environ['FINNHUB_STOCKS_TICKERS'])
        self.validate = os.environ['FINNHUB_VALIDATE_TICKERS']

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            f"wss://ws.finnhub.io?token={os.environ['FINNHUB_API_TOKEN']}",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def on_message(self, ws, message):
        try:
            message = json.loads(message)
            if 'data' in message and message['type'] == 'trade':
                avro_message = avro_encode(
                    {
                        'data': message['data'],
                        'type': message['type']
                    },
                    self.avro_schema
                )
                self.producer.send(os.environ['KAFKA_TOPIC_NAME'], avro_message)
            else:
                print(f"Non-trade message received: {message}")
        except Exception as e:
            print(f"Error handling message: {message}")
            print(str(e))


    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print('### closed ###')

    def on_open(self, ws):
        for ticker in self.tickers:
            print('Trying ticker:', repr(ticker))  
            if self.validate == "1":
                if ticker_validator(self.finnhub_client, ticker):
                    msg = json.dumps({"type": "subscribe", "symbol": ticker})
                    self.ws.send(msg)
                    print('Subscription for {} succeeded'.format(ticker))
                else:
                    print('Subscription for {} failed - ticker not found'.format(ticker))
            else:
                msg = json.dumps({"type": "subscribe", "symbol": ticker})
                self.ws.send(msg)



if __name__ == '__main__':
    FinnhubProducer()
