DEBUG_ON = False


class Expression:
    def is_compound(self):
        return False

    def is_atom(self):
        return not self.is_compound()

    def is_literal(self):
        return self.is_bool() or self.is_number() or self.is_string()

    def is_bool(self):
        return False

    def is_number(self):
        return False

    def is_string(self):
        return False

    def is_identifier(self):
        return False


class Number(Expression):
    def __init__(self, in_value, sign):
        self.value = None
        self.sign = sign

        if "." in in_value:
            self.value = float(in_value)
        else:
            self.value = int(in_value)

    def __add__(self, other):
        if type(other) == Number:
            return self.value + other.value
        return self.value + other

    def __sub__(self, other):
        if type(other) == Number:
            return self.value - other.value
        return self.value - other

    def __mul__(self, other):
        if type(other) == Number:
            return self.value * other.value
        return self.value * other

    def __truediv__(self, other):
        if type(other) == Number:
            return self.value / other.value
        return self.value / other

    def __radd__(self, other):
        if type(other) == Number:
            return other.value + self.value
        return other + self.value

    def __rsub__(self, other):
        if type(other) == Number:
            return other.value - self.value
        return other - self.value

    def __rmul__(self, other):
        if type(other) == Number:
            return other.value * self.value
        return other * self.value

    def __rtruediv__(self, other):
        if type(other) == Number:
            return other.value / self.value
        return other / self.value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __eq__(self, other):
        if type(other) == Number:
            return self.value == other.value
        return self.value == other

    def __lt__(self, other):
        if type(other) == Number:
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other):
        if type(other) == Number:
            return self.value >= other.value
        return self.value >= other

    def is_number(self):
        return True

    def is_timestamp(self):
        return type(self.value) == int and self.value >= 0

    def __repr__(self):
        if DEBUG_ON:
            return "{Number: isS:" + str(self.sign) + " " + str(self.value) + "}"
        additional_sign = ""
        if self.value >= 0:
            additional_sign = "+" if self.sign else ""
        return additional_sign + str(self.value)


class Identifier(Expression):
    def __init__(self, in_value):
        self.value = in_value

    def is_identifier(self):
        return True

    def __repr__(self):
        if DEBUG_ON:
            return "{Identifier: " + self.value + "}"
        return self.value

    def eq(self, value):
        return self.value == value

    def __eq__(self, other):
        if type(other) == Identifier:
            return self.value == other.value
        return False


class Bool(Expression):
    def __init__(self, in_value):
        self.value = (in_value == "#t")

    def is_bool(self):
        return True

    def __bool__(self):
        return self.value

    def __repr__(self):
        if DEBUG_ON:
            return "{Bool: " + str(self.value) + "}"
        return "#t" if self.value else "#f"

    def __eq__(self, other):
        if type(other) == Bool:
            return self.value == other.value
        return self.value == other


class Compound(Expression):
    def __init__(self, in_value):
        self.value = []
        locked_string = False
        start_bracket = ""
        bracket_dic = {"(": [")", 0], "[": ["]", 0]}
        char_before = ""
        actual_part = ""
        for char in in_value[1:-1]:
            if (char == "\n" or char == " ") and (char_before == "\n" or char_before == " ") and len(actual_part) == 0:
                continue

            if (char == "\n" or char == " ") and not locked_string and len(start_bracket) != 1:
                self.value.append(try_parse(actual_part))
                actual_part = ""
                char_before = char
                continue

            if len(start_bracket) != 1 and char == "\"" and char_before != "\\":
                locked_string = not locked_string

            if len(start_bracket) == 1 and start_bracket == char:
                bracket_dic[start_bracket][1] += 1

            if len(start_bracket) != 1 and not locked_string and (char == "(" or char == "["):
                bracket_dic[char][1] += 1
                start_bracket = char

            if len(start_bracket) == 1 and bracket_dic[start_bracket][0] == char:
                bracket_dic[start_bracket][1] -= 1
                if bracket_dic[start_bracket][1] == 0:
                    start_bracket = ""

            actual_part += char
            char_before = char
        else:
            self.value.append(try_parse(actual_part))

    def __iter__(self):
        for val in self.value:
            yield val

    def evaluate_message(self):
        if len(self.value) == 2:
            if self.value[0].is_identifier() and self.value[1].is_string():
                if (self.value[0].eq("nick") and self.value[1].is_nickname()) or \
                        (self.value[0].eq("join") and self.value[1].is_chanel()) or \
                        (self.value[0].eq("part") and self.value[1].is_chanel()):
                    return self
        elif len(self.value) == 3:
            if self.value[0].is_identifier() and self.value[1].is_string() and self.value[1].is_chanel():
                if (self.value[0].eq("message") and self.value[2].is_string() and self.value[2].is_message()) or \
                        (self.value[0].eq("replay") and self.value[2].is_number() and self.value[2].is_timestamp()):
                    return self
        return None

    def is_compound(self):
        return True

    def is_nick(self):
        return self.value[0].eq("nick")

    def is_join(self):
        return self.value[0].eq("join")

    def is_message(self):
        return self.value[0].eq("message")

    def is_part(self):
        return self.value[0].eq("part")

    def is_replay(self):
        return self.value[0].eq("replay")

    def __repr__(self):
        if DEBUG_ON:
            return "{Expression: " + str(self.value) + "}"
        out_string = "("
        for i in range(len(self.value)):
            out_string += str(self.value[i])
            if i < len(self.value) - 1:
                out_string += " "
        return out_string + ")"

    def __eq__(self, other):
        if type(other) == Compound:
            return self.value == other.value


class String(Expression):
    def __init__(self, in_value):
        self.value = in_value

    def is_string(self):
        return True

    def is_message(self):
        return "\n" not in self.value

    def is_nickname(self, chanel=False):
        data = self.value if not chanel else self.value[1:]
        return data.isalnum() and len(data.split()) == 1 and not data.startswith(" ") and not data.endswith(" ")

    def is_chanel(self):
        return self.is_nickname(True) and self.value.startswith("#")

    def __repr__(self):
        if DEBUG_ON:
            return "{String: " + self.value + "}"
        return "\"" + self.value + "\""

    def __eq__(self, other):
        if type(other) == String:
            return self.value == other.value
        return self.value == other


def is_init(char):
    return char in ['!', '$', '%', '&', '*', '/', ':', '<', '=', '>', '?', '_', '~'] or char.isalpha()


def is_subsequence(char):
    return is_init(char) or char.isdigit() or char in ['+', '-', '.', '@', '#']


def try_parse(in_value):
    if (in_value.startswith("(") and in_value.endswith(")")) or (in_value.startswith("[") and in_value.endswith("]")):
        object_val = Compound(in_value)
        if None in object_val.value:
            return None
        return object_val

    if in_value == "#f" or in_value == "#t":
        return Bool(in_value)

    if in_value == "+" or in_value == "-":
        return Identifier(in_value)

    if len(in_value) >= 1 and (in_value.startswith("-") or in_value.startswith("+") or in_value[0].isdigit()):
        start_with = 1 if in_value.startswith("-") or in_value.startswith("+") else 0
        if len(in_value) >= start_with + 1 and in_value[start_with].isdigit():
            for i in range(start_with + 1, len(in_value)):
                if not in_value[i].isdigit() and in_value[i] != ".":
                    break
            else:
                if in_value.count(".") <= 1 and not in_value.endswith("."):
                    return Number(in_value, start_with == 1)

    if len(in_value) >= 2 and in_value.startswith("\"") and in_value.endswith("\""):
        found_backslash = False
        value_string = in_value[1:-1]
        for char in value_string:
            if char == "\"" and not found_backslash:
                break
            if char == "\\" or (char == "\"" and found_backslash):
                found_backslash = not found_backslash
        else:
            if not found_backslash:
                return String(value_string)

    if len(in_value) >= 1 and is_init(in_value[0]):
        for i in range(1, len(in_value)):
            if not is_subsequence(in_value[i]):
                break
        else:
            return Identifier(in_value)
    return None
