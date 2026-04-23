import flet as ft


class Cal:
    def __init__(self, _in):
        self.list_num = _in
        self.chk()

    def flatten_sum(self, lst):
        total = 0
        for i in lst:
            if isinstance(i, list):
                total += self.flatten_sum(i)
            elif isinstance(i, int):
                total += i
        return total

    def chk(self):
        re_list = []
        for i in self.list_num:
            if isinstance(i, int):
                re_list.append(i)
            elif isinstance(i, list):
                re_list.append(self.flatten_sum(i))
        self.list_num = re_list

    def plus(self):
        result = 0
        for i in self.list_num:
            result += i
        return result

    def minus(self):
        result = self.list_num[0]
        for i in self.list_num[1:]:
            result -= i
        return result

    def multip(self):
        result = self.list_num[0]
        for i in self.list_num[1:]:
            result *= i
        return result

    def divi(self):
        result = self.list_num[0]
        for i in self.list_num[1:]:
            result /= i
        return result

    def avg(self):
        return int(self.plus() / len(self.list_num))

    def maxnum(self):
        return max(self.list_num)

    def mini(self):
        return min(self.list_num)


# -------- 파싱 --------

def smart_split(text):
    result = []
    buf = ""
    depth = 0

    for ch in text:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1

        if ch == ',' and depth == 0:
            result.append(buf.strip())
            buf = ""
        else:
            buf += ch

    if buf:
        result.append(buf.strip())

    return result


def parse_recursive(text):
    text = text.strip()

    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1]

    parts = smart_split(text)
    result = []

    for p in parts:
        if not p:
            continue
        if p.startswith('['):
            result.append(parse_recursive(p))
        else:
            try:
                result.append(int(p))
            except:
                pass

    return result


def parse_input(text):
    return parse_recursive(text)


# -------- UI --------

def main(page: ft.Page):
    page.title = "Cal App"
    page.theme_mode = ft.ThemeMode.LIGHT

    input_field = ft.TextField(label="입력: 1,2,[3,4]")
    result_text = ft.Text("결과: ")
    change_list = ft.Text(" ")
    
    

    def run_calc(e, mode):
        data = parse_input(input_field.value)

        if not data:
            result_text.value = "입력 오류"
            change_list.value = " "
            page.update()
            return
        
        

        cal = Cal(data)
        change_list.value = f"변경된 리스트 : {cal.list_num}"
        try:
            if mode == "plus":
                result = cal.plus()
            elif mode == "minus":
                result = cal.minus()
            elif mode == "multip":
                result = cal.multip()
            elif mode == "divi":
                result = cal.divi()
            elif mode == "avg":
                result = cal.avg()
            elif mode == "max":
                result = cal.maxnum()
            elif mode == "min":
                result = cal.mini()

            result_text.value = f"결과: {result}"
        except Exception as e:
            result_text.value = f"오류: {e}"

        page.update()

    page.add(
        input_field,
        change_list,
        ft.Row([
            ft.ElevatedButton("더하기", on_click=lambda e: run_calc(e, "plus")),
            ft.ElevatedButton("빼기", on_click=lambda e: run_calc(e, "minus")),
            ft.ElevatedButton("곱하기", on_click=lambda e: run_calc(e, "multip")),
            ft.ElevatedButton("나누기", on_click=lambda e: run_calc(e, "divi")),
        ]),
        ft.Row([
            ft.ElevatedButton("평균", on_click=lambda e: run_calc(e, "avg")),
            ft.ElevatedButton("최대", on_click=lambda e: run_calc(e, "max")),
            ft.ElevatedButton("최소", on_click=lambda e: run_calc(e, "min")),
        ]),
        result_text
    )


ft.app(target=main)