def split_once(text: str, separate: str):  # 相当于另类的pop
    out_text = ""
    quotation_stack = []
    is_split = True
    for char in text:
        if char in "'\"":
            if quotation_stack:
                is_split = True
                quotation_stack.pop(-1)
            else:
                is_split = False
                quotation_stack.append(char)
        if separate == char and is_split:
            break
        out_text += char
    return out_text, text.replace(out_text, "", 1).replace(separate, "", 1)


def split(text: str, separate: str = " ", max_split: int = -1):
    text_list = []
    quotation_stack = []
    is_split = True
    while all([text, max_split]):
        out_text = ""
        for char in text:
            if char in "'\"":
                if quotation_stack:
                    is_split = True
                    quotation_stack.pop(-1)
                else:
                    is_split = False
                    quotation_stack.append(char)
            if separate == char and is_split:
                break
            out_text += char
        text_list.append(out_text)
        text = text.replace(out_text, "", 1).replace(separate, "", 1)
        max_split -= 1
    if text:
        text_list.append(text)
    return text_list