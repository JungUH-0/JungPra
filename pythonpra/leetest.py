import flet as ft
 
def main(page: ft.Page):
    # 페이지 설정
    page.title = "Acoustic AI Unified Monitor"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#111418"
    page.padding = 20
   
    # 헬퍼 함수: 플랫 카드 생성
    def create_card(title, content, expand=False):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color="#5B626A"),
                content
            ], spacing=10),
            bgcolor="#1A1D23",
            padding=15,
            border=ft.border.all(1, "#2D323A"),
            border_radius=0,
            expand=expand
        )
 
    # --- 1. 상단 헤더 ---
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.GRAPHIC_EQ, color="#3498DB"),
                    ft.Text("ACOUSTIC AI INTELLIGENCE MONITOR", size=22, weight="bold"),
                ]),
                ft.Text("주요기능: 음향 데이터 분석, 이벤트 알람, 저장 및 검색", size=11, color="#5B626A"),
            ], spacing=2),
            ft.Row([
                ft.Container(width=10, height=10, bgcolor="#2ECC71", border_radius=5),
                ft.Text("ENGINE ONLINE", size=13, color="#2ECC71"),
            ])
        ]
    )
 
    # --- 2. 좌측 섹션 (센서 맵 & 상태) ---
    # ft.alignment.center 에러 방지를 위해 Alignment(0,0) 사용
    sensor_map_box = ft.Container(
        bgcolor="black",
        height=250,
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(ft.Icons.GRID_3X3, color="#2D323A", size=100)
    )
 
    sensor_list = ft.Column(spacing=5, scroll=ft.ScrollMode.ADAPTIVE)
    for i in range(1, 11):
        sensor_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(f"SENSOR_{i:02d}", size=11),
                    ft.Text("ACTIVE", size=11, color="#3498DB")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="#232830", padding=8
            )
        )
   
    left_col = ft.Column([
        create_card("SENSOR MAP", sensor_map_box),
        create_card("SENSOR STATUS", ft.Container(content=sensor_list, height=250))
    ], width=280)
 
    # --- 3. 중앙 섹션 (분석 & 검색) ---
    spec_box = ft.Container(
        bgcolor="black",
        expand=True,
        content=ft.Stack([
            ft.Container(bgcolor="#3498DB", left=50, bottom=0, width=80, height=150, opacity=0.6),
            ft.Container(bgcolor="#E67E22", left=150, bottom=0, width=120, height=100, opacity=0.6),
            ft.Text("REAL-TIME WAVEFORM ANALYSIS", color="#5B626A", size=10, left=10, top=10)
        ])
    )
 
    # 검색 및 저장 기능 (요청하신 주요 기능)
    search_bar = ft.Row([
        ft.TextField(
            label="이벤트 로그 검색...",
            expand=True,
            height=45,
            border_radius=0,
            text_size=12
        ),
        ft.ElevatedButton(
            "검색",
            icon=ft.Icons.SEARCH,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))
        ),
        ft.ElevatedButton(
            "데이터 저장",
            icon=ft.Icons.SAVE,
            bgcolor="#3498DB",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=0))
        )
    ], spacing=10)
 
    center_col = ft.Column([
        create_card("ACOUSTIC SPECTROGRAM", spec_box, expand=True),
        create_card("EVENT SEARCH & SAVE", search_bar)
    ], expand=True)
 
    # --- 4. 우측 섹션 (알람 목록) ---
    alarm_list = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE)
    alarms = [
        ("13:20:01", "굴착 작업 감지", "HIGH"),
        ("12:45:12", "가스 누출 의심", "CRITICAL"),
        ("11:10:05", "침입 패턴 분석", "LOW")
    ]
    for t, m, l in alarms:
        color = "red" if l == "CRITICAL" else "orange" if l == "HIGH" else "blue"
        alarm_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Column([ft.Text(m, size=12, weight="bold"), ft.Text(t, size=10)], spacing=2),
                    ft.Text(l, size=10, color=color, weight="bold")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=10,
                bgcolor="#232830",
                border=ft.border.only(left=ft.border.BorderSide(3, color))
            )
        )
 
    right_col = ft.Column([
        create_card("EVENT ALARM LOG", alarm_list, expand=True)
    ], width=320)
 
    # 전체 레이아웃 구성
    page.add(
        header,
        ft.Divider(height=10, color="transparent"),
        ft.Row([
            left_col,
            center_col,
            right_col
        ], expand=True)
    )
 
if __name__ == "__main__":
    # 가장 안전한 실행 방식
    ft.app(target=main)