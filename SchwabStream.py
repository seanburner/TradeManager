from schwab.auth import easy_client, client_from_token_file
from schwab.client import Client
from schwab.streaming import StreamClient

import asyncio
import json

# Assumes you've already created a token. See the authentication page for more
# information.
client = client_from_token_file(  #easy_client(
        api_key='client_id', # CHANGE 
        app_secret='client_secret', #CHANGE
     #   callback_url='https://127.0.0.1:8080',
        token_path='/home/sean/Documents/Coding/python/day_trade/files/tokens.json',
        asyncio=False)

print("\n[SUCCESS] tokens.json has been written to your files directory!")

stream_client = StreamClient(client, account_id=1234567890) # CHANGE ACCOUNT

async def read_stream():
    await stream_client.login()

    def print_message(message):
      print(json.dumps(message, indent=4))

    # Always add handlers before subscribing because many streams start sending
    # data immediately after success, and messages with no handlers are dropped.
    stream_client.add_nasdaq_book_handler(print_message)
    await stream_client.nasdaq_book_subs(['GOOG'])

    while True:
        await stream_client.handle_message()

asyncio.run(read_stream())
