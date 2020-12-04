#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

logging.basicConfig()

STATE = {"message_number": 0, 'message_text':'SEJA BEM VINDO! Digite /name <seu_nome> para ser liberado no chat. Digite /to <username> <sua_mensagem> para enviar uma mensagem privada', 'from_user_name':'Server', 'to_user_name':'you', 'pv_message':'False'}

USERS = dict()
count_users = 0

def state_event():
    return json.dumps({"type": "message", **STATE})


def users_event():
    return json.dumps({"type": "users", "count": len(USERS)})


async def notify_state():
    if USERS and STATE['pv_message'] == 'True':
        message = state_event()
        destino1 = None
        destino2 = None
        for key in USERS:
            if USERS[key] == STATE['to_user_name']:
                destino1 = key
            if USERS[key] == STATE['from_user_name']:
                destino2 = key

        try: await asyncio.wait([destino1.send(message), destino2.send(message)])
        except:pass


    elif USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def notify_users():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    USERS.update({websocket:None})
    await notify_users()


async def unregister(websocket):
    USERS.pop(websocket)
    await notify_users()



async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:

        await websocket.send(state_event())
        async for message in websocket:
            data = json.loads(message)

            if data['name_alter']=='True':
                repeated_name = False
                STATE["message_number"] += 1
                
                for key in USERS:
                    if USERS[key] == data['chat_message']:
                        STATE['message_text'] = 'Username already taken!'
                        STATE['to_user_name'] = USERS[websocket]
                        STATE['from_user_name'] = 'server'
                        STATE['pv_message'] = 'False'
                        repeated_name = True
                        await notify_state()

                if repeated_name == False:
                    STATE['message_text'] = 'Nome do usuário {} alterado para {}'.format(USERS[websocket], data['chat_message'])
                    STATE['to_user_name'] = 'all'
                    USERS.update({websocket:data['chat_message']})
                    STATE['from_user_name'] = USERS[websocket]
                    STATE['pv_message'] = 'False'
                    await notify_state()
            
            elif data['private'] == 'True' and USERS[websocket] != None:
                print('chefodf')
                STATE["message_number"] += 1
                STATE['message_text'] = data['chat_message']
                STATE['to_user_name'] = data['to_user_name']
                STATE['pv_message'] = 'True'
                STATE['from_user_name'] = USERS[websocket]
                await notify_state()

            elif data['normal'] == 'True' and USERS[websocket] != None :
                print('chefodf')
                STATE["message_number"] += 1
                STATE['message_text'] = data['chat_message']
                STATE['from_user_name'] = USERS[websocket]
                STATE['to_user_name'] = 'all'
                STATE['pv_message'] = 'False'
                await notify_state()

            #elif data["action"] == "plus":
             #   STATE["message_number"] += 1
              #  await notify_state()
            else:
                logging.error("unsupported event: {}")
    finally:
        await unregister(websocket)
start_server = websockets.serve(counter, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
