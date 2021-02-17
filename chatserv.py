import asyncio
from lisp import *
import time, os


class ServerData:
    def __init__(self, socket_path):
        self.socket_path = socket_path
        self.channels = {}  # Channel objects indexed by name
        self.clients = []  # User objects

    def connect(self, nickname, writer):
        for client in self.clients:
            if client.nickname == nickname:
                return None
        user = User(nickname, writer)
        self.clients.append(user)
        return user
    
    def disconnect(self, user):
        self.clients.remove(user)


class User:
    def __init__(self, nickname, writer):
        self.nickname = nickname
        self.writer = writer
        self.channel = set()
        

class Channel:
    def __init__(self, name):
        self.name = name
        self.history = []  # (timestamp, message)

    def archive(self, stamp, name, text):
        self.history.append((stamp, name, text))


server = ServerData("./chatsock")


async def replay(writer, channel, time):
    for message in server.channels[channel].history:
        if message[0] >= time:
            await send_brodcast(writer, message[1], message[0], message[2], channel) 
    


async def send_brodcast(writer, name, stamp, text, channel):
    writer.write(("(message \"" + channel + "\" " + str(stamp) + " \"" + name + "\" \"" + text + "\")").encode('utf-8'))
    await writer.drain()    


async def brodcast(channel, stamp, author, text):
    server.channels[channel].archive(stamp, author.nickname, text)
    for client in server.clients:
        if channel in client.channel:
            await send_brodcast(client.writer, author.nickname, stamp, text, channel)


async def send_err(writer, message):
    writer.write(("(error \"" + message + "\")").encode('utf-8'))
    await writer.drain()


async def send_ok(writer, channel=None, time=None):
    writer.write(("(ok)").encode('utf-8'))
    await writer.drain()

    if channel is not None and time is not None:
        await replay(writer, channel, time)
        

async def handler(reader, writer):
    user = None
    command_list = []
    is_in = False
    in_string = False

    while True:
        read_byte = await reader.read(1)
        if read_byte == b'':
            if user in server.clients:
                server.disconnect(user)
            break

        if is_in and read_byte == b'"':
            in_string = not in_string
        
        if not is_in and read_byte == b'(':
            is_in = True


        if is_in:
            command_list.append(read_byte)

        if is_in and read_byte == b')' and not in_string:
            is_in = False

        if not is_in and len(command_list) != 0:        
        
            recieved = b''.join(command_list).decode()
            command = chat_parser(recieved)
            command_list = []

            if command is None:
                await send_err(writer, "Unknown or malformed command.")
                continue

            if user is None and not command.is_nick():
                await send_err(writer, "Unknown nickname.")
                continue

            if user is None and command.is_nick():
                obj = server.connect(command.value[1].value, writer)
                if obj is None:
                    await send_err(writer, "Nickname is used by another user.")
                else:
                    user = obj
                    await send_ok(writer)
                continue

            if user is not None and command.is_nick():
                nickX = command.value[1].value
                for client in server.clients:
                    if client.nickname == nickX:
                        await send_err(writer, "Nickname is used by another user.")
                        break
                else:
                    user.nickname = nickX
                    await send_ok(writer)

            if command.is_join():
                channel_name = command.value[1].value
                if channel_name in user.channel:
                    await send_err(writer, "You are already in this channel.")
                    continue
                if channel_name not in server.channels:
                    server.channels[channel_name] = Channel(channel_name)
                user.channel.add(channel_name)
                await send_ok(writer)
                continue

            if command.is_part():
                channel_name = command.value[1].value
                if channel_name not in user.channel:
                    await send_err(writer, "You must to be assigned to selected channel.")
                else:
                    user.channel.remove(channel_name)
                    await send_ok(writer)

            if command.is_message():
                stamp = int(time.time())
                channel_name = command.value[1].value
                text = command.value[2].value

                if channel_name not in server.channels:
                    await send_err(writer, "This channel doesn't exist.")
                    continue
                if channel_name not in user.channel:
                    await send_err(writer, "You are not assigned to selected channel.")
                    continue
                await brodcast(channel_name, stamp, user, text)
                continue

            if command.is_replay():
                stamp = int(time.time())
                channel_name = command.value[1].value
                timeX = command.value[2].value
                if channel_name not in user.channel:
                    await send_err(writer, "You are not assigned to selected channel.")
                    continue
                if stamp < timeX:
                    await send_err(writer, "Selected timestamp is in future.")
                    continue
                await send_ok(writer, channel_name, timeX)
                continue
            

async def main():
    if os.path.exists(server.socket_path):
        os.remove(server.socket_path)
    serverV = await asyncio.start_unix_server(handler, path=server.socket_path)
    await serverV.serve_forever()

#asyncio.run(main())
