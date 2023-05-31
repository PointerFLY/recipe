def text2siao(text: str):
    hex = text.encode('utf-8').hex()
    hex_bytes = bytes(hex, encoding='ascii')
    ret = []

    for c in hex_bytes:
        if c >= ord('a'):
            n_siao = c - ord('a') + 10
        else:
            n_siao = c - ord('0')

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
            ret.append('siao')
        for _ in range(n_5):
            ret.append('siaomeh')
        for _ in range(n_10):
            ret.append('siaoleh')
        for _ in range(n_20):
            ret.append('siaoalready')
        ret.append(' ')

    ret = ret[:-1]
    return ''.join(ret)


def siao2text(siao_text: str):
    words = siao_text.split(' ')
    original_chars = []
    for word in words:
        n_siao = 0
        i = 0

        while i < len(word):
            if word[i] == 's':
                n_siao += 1
                i += 4
            elif word[i] == 'm':
                n_siao += 4
                i += 3
            elif word[i] == 'l':
                n_siao += 9
                i += 3
            elif word[i] == 'a':
                n_siao += 19
                i += 7
            else:
                raise ValueError('Illegal character')
        
        if n_siao > 10:
            c = n_siao - 10 + ord('a')
        else:
            c = n_siao + ord('0')
        original_chars.append(chr(c))

    return bytes.fromhex(''.join(original_chars)).decode('utf-8')