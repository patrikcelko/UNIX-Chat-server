from classes import *


def parse(in_value):
    if type(in_value) != str:
        raise RuntimeError("Invalid input type.")
    return try_parse(in_value)


def chat_parser(in_value):
    parsed_data = try_parse(in_value)
    if parsed_data is not None and parsed_data.is_compound():
        return parsed_data.evaluate_message()
    return None


def test_chat_commands():
    assert chat_parser("8") is None

    assert chat_parser("(nick \"apple\")") is not None
    assert chat_parser("(nick \"pear apple\")") is None
    assert chat_parser("(nick \"#Hehhehhe\")") is None
    assert chat_parser("(nick \" apple\")") is None
    assert chat_parser("(nick \"apple \")") is None
    assert chat_parser("(nick \"apple\" \"redundant\")") is None

    assert chat_parser("(join \"pear apple\")") is None
    assert chat_parser("(join \"apple\")") is None
    assert chat_parser("(join \"apple#\")") is None
    assert chat_parser("(join \"#apple\")") is not None

    assert chat_parser("(message \"#apple\" \"apple\npear\")") is None
    assert chat_parser("(message \"#apple\" \"apple pear\")") is not None

    assert chat_parser("(replay \"#apple\" -25)") is None
    assert chat_parser("(replay \"#apple\" 2.5)") is None
    assert chat_parser("(replay \"#apple\" +2.5)") is None
    assert chat_parser("(replay \"#apple\" 25)") is not None
    assert chat_parser("(replay \"#apple\" +25)") is not None


def test_basic_arithmetic():
    a = parse("8")
    b = parse("8.1")
    assert a != b
    assert a < b

    a = parse("9.1")
    b = parse("9")
    assert a > b


def test_spec():
    a = parse("(+ 1 2 3)")
    assert a == (parse(str(a)))

    a = parse("(eq? [quote a b c] (quote a c b))")
    assert a.is_compound()
    assert not a.is_atom()
    assert not a.is_literal()
    assert a == (parse(str(a)))

    a = parse("12.7")

    assert a == (parse(str(a)))
    assert not a.is_compound()
    assert a.is_number()
    assert a.is_atom()
    assert a.is_literal()
    assert a - a + a == a
    assert a * a / a == a

    a = parse("(concat \"abc\" \"efg\" \"ugly \\\"string\\\"\")")
    assert a == (parse(str(a)))

    a = parse("(set! var ((stuff) #t #f))")
    assert a == (parse(str(a)))

    a = parse("(< #t #t)")
    assert a == (parse(str(a)))


def test_none():
    assert parse("1.25a") is None
    assert parse("9.") is None
    assert parse("(stuff))") is None
    assert parse("\"\\\"") is None
    assert parse("\"\\\\\"") is not None
    assert parse("(sample text (9.9))") is not None
    assert parse("(sample text (9.))") is None
    assert parse("(sample]") is None
    assert parse("(sample )") is None
    assert parse("\"sample") is None
    assert parse("NotAnIdentifier\"") is None
    assert parse("()") is None
    assert parse(" ") is None
    assert parse(" sample text") is None


def test_fail_sanity():
    assert parse("(id id)") == parse("(id  id)")
    assert parse("(id id id)") == parse("(id \n\n id \n      \n id)")


if __name__ == "__main__":
    test_none()
    test_basic_arithmetic()
    test_spec()
    test_fail_sanity()
    test_chat_commands()
