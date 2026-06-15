import flet as ft

allpin=[0,1,2,3,4,5,6,7,8,9,10]


def main(page : ft.page):
  page.title = "볼링계산기"
  page.window.width = 900
  page.window.height = 750
  page.theme_mode = ft.ThemeMode.LIGHT
  btn_style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))

  current_frame = {"idx": -1}
  frames = []

  def make_btn(text):
      return ft.ElevatedButton(text, style=btn_style, width=120, height=30, on_click=lambda e :click(text))
  
  def click(text):
      pass
  
  btn_values = [
  ["1","2","3","-"],
  ["4","5","6","/"],
  ["7","8","9","X"]
  ]
  btnsys_values =[["새게임","리셋","종료"]]

  btn_rows = [
    [make_btn(v) for v in row]
  for row in btn_values
  ]
  

  def make_frame(frame_num):
      idx = len(frames)
      
      box_count = 3 if frame_num == 10 else 2

      inputs = [
          ft.TextField(width=20, height=30, text_align=ft.TextAlign.CENTER)
          for _ in range(box_count)
      ]

      score = ft.Text("0", size=15)
      

      container = ft.Container(
          content=ft.Column(
              [
                  ft.Row(inputs, spacing=2),
                  score
              ],
              alignment=ft.MainAxisAlignment.CENTER,
              horizontal_alignment=ft.CrossAxisAlignment.CENTER
          ),
          border=ft.border.all(2, "grey"),
          bgcolor='red',
          padding=12,
          width=70 if frame_num != 10 else 90,
      )

      def on_click(e):
          current_frame["idx"] = idx
          
          update_highlight()

      container.on_click = on_click
      frames.append(container)

      return container

  def update_highlight():
      for i, f in enumerate(frames):
          if i == current_frame["idx"]:
              f.border = ft.border.all(3, "blue")
              f.bgcolor = "#e3f2fd"
          else:
              f.border = ft.border.all(2, "grey")
              
      page.update()

  frames = [make_frame(i) for i in range(1, 11)]

  board = ft.Row(frames, spacing=5)

  score_display = ft.Container(
      content=ft.Column([
          ft.Text("BOWLING SCOREBOARD", size=12, weight="bold", color='BLUE'),
        board
      ]),
      width=800,
      height=500,
      padding=10,
      border=ft.border.all(1,'grey'),
      border_radius=15,
      bgcolor='white'
  )
  
  
  page.add(score_display,
            ft.Divider(),
  *[ft.Row(row) for row in btn_rows]
)
ft.app(target=main)