from stack import data_Stack

def bracketschk (s):
    chk= True
    ran = len(s)
    b_chk = data_Stack(ran)
    #문자열에서 문자 하나씩 받음
    for i in s :
        if i == '(' or i == '[' or i == '{':
            b_chk.push(i)
        elif (i == ')' or i == ']' or i == '}') and not(b_chk.isEmpty()) :
            b=b_chk.pop()
            a= b+i
            if a =="()"or a=="[]" or a=="{}":
                continue
            else : chk = False
        elif (i == ')' or i == ']' or i == '}') and (b_chk.isEmpty()) :
            chk = False

    # return ("Ok") if b_chk.isEmpty() else ("Error")
    if b_chk.isEmpty() :
        print("OK")
        return chk
    else :
        chk= False
        print("Error")
        return chk
    
def postfix(s):
     oper= {'+':1 ,"-":1 ,"*":2 , "/":2 ,"(":0 }
     ran = len(s)
     op_stack = data_Stack(ran)
     result=[]

     for i in s:
          if i == '(':
               op_stack.push(i)
          elif i == ')':
               while not op_stack.isEmpty():
                    top=op_stack.pop()
                    if top =='(' :
                         break
                    result +=[top]
          elif i in ['+','-','*','/']:
               while not op_stack.isEmpty():
                    top=op_stack.pop()
                    if oper[top]>= oper[i]:
                         result += [top]
                    else :
                         op_stack.push(top)
                         break
               op_stack.push(i)
          else:
               result += [i]
     while not op_stack.isEmpty():
          result += [op_stack.pop()]

     return ' '.join(result)

def fmaze(maze, size):
     stack = data_Stack(size * size)

    # e 위치 찾기
     for r in range(size):
        for c in range(size):
            if maze[r][c] == 'e':
                stack.push((r, c))

     while not stack.isEmpty():
        pos = stack.pop()
        r, c = pos

        # 이미 방문했거나 벽이면 skip
        if maze[r][c] == '1' or maze[r][c] == 'v':
            continue

        # 방문 표시
        print(f"방문: ({r}, {c})")

        # 출구 도달
        if maze[r][c] == 'x':
            print("탈출 성공!")
            while not stack.isEmpty():
                leftover = stack.pop()
                lr, lc = leftover
                if maze[lr][lc] != 'v' and maze[lr][lc] != '1':
                    print(f"방문 가능했던 곳: ({lr}, {lc})")
            return True
        maze[r][c] = 'v'


        # 상하좌우 탐색
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < size and 0 <= nc < size:
                if maze[nr][nc] == '0' or maze[nr][nc] == 'x':
                    stack.push((nr, nc))

     print("출구 없음")
     return False


map = [ ['1','1','1','1','1','1'],
        ['e','0','0','0','0','1'],
        ['1','0','1','0','1','1'],
        ['1','1','1','0','0','x'],
        ['1','1','1','0','1','1'],
        ['1','1','1','1','1','1']]

fmaze(map, 6)