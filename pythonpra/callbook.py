import flet as ft
import random as ran


class base_dic:
    def __init__(self):
        self.data_dic = {}


class func_dic(base_dic):
    def __init__(self):
        super().__init__()

    def data_set(self, namev, agev, emailv, phonev, jobv):
        keynum = len(self.data_dic) + 1
        self.data_dic[keynum] = {
            "이름": namev,
            "나이": agev,
            "이메일": emailv,
            "핸드폰": phonev,
            "직장명": jobv
        }
        return keynum

    def name_chk(self, fname):
        result_dic = []
        for i in self.data_dic.keys():
            if self.data_dic[i]["이름"] == fname:
                result_dic.append(self.data_dic[i])
        return result_dic


book = func_dic()


def main(page: ft.Page):
    page.title = "주소록"
    page.theme_mode = ft.ThemeMode.LIGHT

    name = ft.TextField(label="이름")
    age = ft.TextField(label="나이")
    email = ft.TextField(label="이메일 (아이디만 입력)")
    phone = ft.TextField(label="핸드폰")
    alert =ft.TextField(" ")

    result = ft.Text("")

    # 스크롤 영역
    result_column = ft.Column(
        [result],
        scroll=ft.ScrollMode.AUTO,
        height=200,
        width=300
    )

    def add_data(e):
        try:
            a = int(age.value)
        except:
            alert.value = "나이는 숫자만 입력해주세요"
            page.update()
            return

        email_list = ['@naver.com', '@gmail.com', '@daum.net', '@kakao.com']
        job_list = ['폴리', '정수', '하이', '테크']

        femail = email.value + email_list[ran.randint(0, 3)]
        jobname = job_list[ran.randint(0, 3)]

        key = book.data_set(name.value, a, femail, phone.value, jobname)
        result.value = f"{key}번 저장됨"
        page.update()

    search_name = ft.TextField(label="검색 이름")

    def search(e):
        people = book.name_chk(search_name.value)

        if not people:
            result.value = "없음"
        else:
            text = ""
            for p in people:
                text += "\n"
                for k, v in p.items():
                    text += f"{k} : {v}\n"
            result.value = text

        page.update()

    page.add(
    ft.Row([
        ft.Column([
            ft.Text("정보 입력"),
            name, age, email, phone,
            ft.ElevatedButton("저장", on_click=add_data),
            alert,
            ft.Divider(),

            ft.Text("검색"),
            search_name,
            ft.ElevatedButton("검색", on_click=search),
        ]),

        result_column   # 오른쪽으로 이동
    ])
)


ft.app(target=main)