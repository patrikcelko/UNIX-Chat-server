import asyncio
from chatserv import *

BYTES_OK = bytes("(ok)" , encoding="utf-8")
BYTES_RPAR = bytes(")" , encoding="utf-8")

BYTES_ERR = bytes("(error \"", encoding="utf-8")

commands_first = "(nick \"aaa\")(join \"#lala\")"
commands_second = "(nick \"bbb\")(join \"#lala\")"

commands_format = "(nick \"format\")(join \"#lala\")"

commands_msg_a = "(message \"#lala\" \"its ya boi, \\\"skinny peen\\\"\")"
commands_msg_b = "(message \"#awawa\" \"dobre\")"
commands_nick_a = "(nick \"aaa\")"
commands_nick_b = "(nick \"bbb\")"
commands_nick_c = "(nick \"ccc\")"
commands_join_a = "(join \"#lala\")"
commands_part_a = "(part \"#lala\")"
commands_part_b = "(part \"#awawa\")"
commands_replay = "(replay  \"#lala\" 0)"
commands_replay_future = "(replay \"#lala\" 999999999999999)"

commands_bad_nick_1 = "(nick \"format2\n\")"
commands_bad_nick_2 = "(nick \"#format2\")"
commands_bad_chan = "(join \"format2\")"
commands_msg_newline = "(message \"#lala\" \"its \n" \
                       "ya boi, \\\"skinny peen\\\"\")"
commands_replay_neg = "(replay  \"#lala\" -1)"
commands_replay_dec = "(replay  \"#lala\" 1.1)"


commands_nested_1 = "(nick (nick \"format2\"))"
commands_nested_2 = "(message \"#lala\" \"(nick \"format2\")\")"

commands_sanity = "(nick \"foo\")(join \"#chan\")" \
                  "(message \"#chan\" \"hello world\")(part \"#chan\")"

commands_spam = "(message \"#lala\" \"1\")" \
                "(message \"#lala\" \"2\")(message \"#lala\" \"3\")" \
                "(message \"#lala\" \"4\")(message \"#lala\" \"5\")" \
                "(replay  \"#lala\" 0)(replay  \"#lala\" 0)" \
                "(message \"#lala\" \"6\")(message \"#lala\" \"7\")"

commands_spec = "(nick \"foo\")(join \"#chan\")" \
                "(message \"#chan\" \"hello world\")(part \"#chan\")" \
                "(part \"#chan\")(part \"#chan\")(join \"#chan\")"

print("HERE")

def assert_eq_print(client: str, a, b):
    print("testing for {}: {} == {}".format(client, a, b))
    assert a == b


def assert_err(client: str, a):
    print("testing for {}: {}; should be error message".format(client, a))
    assert len(a) > 2
    assert a[:8:] == BYTES_ERR


async def test_basic(client: str, reader, writer, commands):
    writer.write(bytes(commands, encoding="utf-8"))
    await writer.drain()
    a = await reader.read(4)
    assert_eq_print(client, a, BYTES_OK)
    a = await reader.read(4)
    assert_eq_print(client, a, BYTES_OK)


async def test_msg(r1, w1, r2, w2):
    w1.write(bytes(commands_msg_a, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    b = await r2.readuntil(BYTES_RPAR)
    assert_eq_print("both clients", a, b)


async def test_not_in_channel_msg(client: str, r1, w1):
    w1.write(bytes(commands_msg_b, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_err(client, a)


async def test_already_joined(client: str, r1, w1):
    w1.write(bytes(commands_join_a, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_err(client, a)


async def test_nick_in_use(client: str, r1, w1):
    w1.write(bytes(commands_nick_b, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_err(client, a)

    # same nick error as well??
    w1.write(bytes(commands_nick_a, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_err(client, a)


async def test_part(client: str, r1, w1):
    w1.write(bytes(commands_part_a, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_eq_print(client, a, BYTES_OK)

    # test sending a message to the channel
    w1.write(bytes(commands_msg_a, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_err(client, a)

    # rejoin
    w1.write(bytes(commands_join_a, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_eq_print(client, a, BYTES_OK)


async def test_part_not_joined(client: str, r1, w1):
    w1.write(bytes(commands_part_b, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_err(client, a)


async def test_nick_change(client: str, r1, w1):
    w1.write(bytes(commands_nick_c, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_eq_print(client, a, BYTES_OK)

    w1.write(bytes(commands_nick_a, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_eq_print(client, a, BYTES_OK)


async def test_replay(r1, w1, r2, w2):
    w1.write(bytes(commands_replay, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_eq_print("client \"aaa\"", a, BYTES_OK)

    w2.write(bytes(commands_replay, encoding="utf-8"))
    await w2.drain()
    b = await r2.readuntil(BYTES_RPAR)
    assert_eq_print("client \"bbb\"", b, BYTES_OK)

    a = await r1.readuntil(BYTES_RPAR)
    b = await r2.readuntil(BYTES_RPAR)
    assert_eq_print("both clients", a, b)


async def test_replay_future(client, r1, w1):
    w1.write(bytes(commands_replay_future, encoding="utf-8"))
    await w1.drain()
    a = await r1.readuntil(BYTES_RPAR)
    assert_err(client, a)


async def test_main():
    await asyncio.sleep(1)
    print("--basic tests, setup")
    client1 = "client \"aaa\""
    client2 = "client \"bbb\""
    r1, w1 = await asyncio.open_unix_connection(path="chatsock")
    r2, w2 = await asyncio.open_unix_connection(path="chatsock")
    await asyncio.gather(test_basic(client1, r1, w1, commands_first),
                         test_basic(client2, r2, w2, commands_second))

    print("\n--message test")
    await test_msg(r1, w1, r2, w2)
    print("\n--nick change test, (and back)")
    await test_nick_change(client1, r1, w1)
    print("\n--nick in use test")
    await asyncio.gather(test_nick_in_use(client1, r1, w1),
                         test_nick_in_use(client2, r2, w2))
    print("\n--join test; already joined test")
    await asyncio.gather(test_already_joined(client1, r1, w1),
                         test_already_joined(client2, r2, w2))
    print("\n--msg fail because not in channel test")
    await asyncio.gather(test_not_in_channel_msg(client1, r1, w1),
                         test_not_in_channel_msg(client2, r2, w2))
    print("\n--part test (with msg fail and rejoin)")
    await asyncio.gather(test_part(client1, r1, w1), test_part(client2, r2, w2))
    print("\n--part test; not joined yet")
    await asyncio.gather(test_part_not_joined(client1, r1, w1),
                         test_part_not_joined(client2, r2, w2))
    print("\n--replay test")
    await test_replay(r1, w1, r2, w2)
    print("\n--future replay")
    await asyncio.gather(test_replay_future(client1, r1, w1),
                         test_replay_future(client2, r2, w2))

    await test_formats()


async def test_formats():
    client1 = "client \"format\""
    r, w = await asyncio.open_unix_connection(path="chatsock")
    await test_basic(client1, r, w, commands_format)

    print("\n----FORMAT TESTS----\n")
    print("--newline in nick")
    w.write(bytes(commands_bad_nick_1, encoding="utf-8"))
    await w.drain()
    a = await r.readuntil(BYTES_RPAR)
    assert_err(client1, a)

    print("\n--nick starts with #")
    w.write(bytes(commands_bad_nick_2, encoding="utf-8"))
    await w.drain()
    a = await r.readuntil(BYTES_RPAR)
    assert_err(client1, a)

    print("\n--chan name starts without #")
    w.write(bytes(commands_bad_chan, encoding="utf-8"))
    await w.drain()
    a = await r.readuntil(BYTES_RPAR)
    assert_err(client1, a)

    print("\n--message with newline")
    w.write(bytes(commands_msg_newline, encoding="utf-8"))
    await w.drain()
    a = await r.readuntil(BYTES_RPAR)
    assert_err(client1, a)

    print("\n--replay with negative number")
    w.write(bytes(commands_replay_neg, encoding="utf-8"))
    await w.drain()
    a = await r.readuntil(BYTES_RPAR)
    assert_err(client1, a)

    print("\n--replay with decimal number")
    w.write(bytes(commands_replay_dec, encoding="utf-8"))
    await w.drain()
    a = await r.readuntil(BYTES_RPAR)
    assert_err(client1, a)

    # deprecated, nested structures will not appear
    # print("\n--nick command nested in nick command")
    # w.write(bytes(commands_nested_1, encoding="utf-8"))
    # await w.drain()
    # a = await r.readuntil(BYTES_RPAR)
    # assert_err(client1, a)
    #
    # print("\n--nick command nested in message text")
    # w.write(bytes(commands_nested_2, encoding="utf-8"))
    # await w.drain()
    # a = await r.readuntil(BYTES_RPAR)
    # assert_err(client1, a)


async def test_manual():
    print("---MANUAL---")
    client1 = "client \"foo\""
    r, w = await asyncio.open_unix_connection(path="chatsock")
    w.write(bytes(commands_sanity, encoding="utf-8"))
    await w.drain()
    w.write_eof()
    await w.drain()
    print(await r.read())


async def test_heavy_run(client, r, w):
    w.write(bytes(commands_spam, encoding="utf-8"))
    await w.drain()
    w.write_eof()
    await w.drain()
    print(client, await r.read())


async def test_heavy():
    print("---HEAVY LOAD---")
    client1 = "client \"aaa\""
    client2 = "client \"bbb\""
    r1, w1 = await asyncio.open_unix_connection(path="chatsock")
    r2, w2 = await asyncio.open_unix_connection(path="chatsock")
    await asyncio.gather(test_basic(client1, r1, w1, commands_first),
                         test_basic(client2, r2, w2, commands_second))
    await asyncio.gather(test_heavy_run(client1, r1, w1),
                         test_heavy_run(client2, r2, w2))


async def run_tests():
    print("start...")
    await asyncio.gather(main(), test_main())
    #await asyncio.gather(main(), test_manual())
    await asyncio.gather(main(), test_heavy())

if __name__ == '__main__':
    print("nah")
    asyncio.run(run_tests())

print("out")