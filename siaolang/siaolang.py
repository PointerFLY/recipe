import base64


def text2siao(text: str):
    hex = text.encode("utf-8").hex().encode("ascii")
    b64 = base64.b32encode(hex)
    ret = []

    for c in b64:
        if c == ord("="):
            continue
        if c >= ord("A"):
            n_siao = c - ord("A") + 7
        else:
            n_siao = c - ord("1")

        n_20 = 0
        n_10 = 0
        n_5 = 0

        siaos = n_siao // 20
        remain = n_siao % 20
        while siaos:
            n_20 += 1
            siaos = siaos // 20
            remain = remain % 20

        siaos = remain // 10
        remain = remain % 10
        while siaos:
            n_10 += 1
            siaos = siaos // 10
            remain = remain % 10

        siaos = remain // 5
        remain = remain % 5
        while siaos:
            n_5 += 1
            siaos = siaos // 5
            remain = remain % 5

        for _ in range(remain):
            ret.append("siao")
        for _ in range(n_5):
            ret.append("siaomeh")
        for _ in range(n_10):
            ret.append("siaoleh")
        for _ in range(n_20):
            ret.append("siaoalready")
        ret.append(" ")

    ret = ret[:-1]
    return "".join(ret)


def siao2text(siao_text: str):
    words = siao_text.split(" ")
    original_chars = []
    for word in words:
        n_siao = 0
        i = 0

        while i < len(word):
            if word[i] == "s":
                n_siao += 1
                i += 4
            elif word[i] == "m":
                n_siao += 4
                i += 3
            elif word[i] == "l":
                n_siao += 9
                i += 3
            elif word[i] == "a":
                n_siao += 19
                i += 7
            else:
                raise ValueError("Illegal character")

        if n_siao >= 7:
            c = n_siao - 7 + ord("A")
        else:
            c = n_siao + ord("1")
        original_chars.append(c)

    padding = 8 - len(original_chars) % 8
    for _ in range(padding):
        original_chars.append(ord("="))

    return bytes.fromhex(
        base64.b32decode(bytes(original_chars)).decode("ascii")
    ).decode("utf-8")
