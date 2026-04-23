class Cal :
    def __init__(self, _in) :
        self.list_num = _in
        self.chk()

    def chk(self)  :
        re_list=[]
        for i in self.list_num :
            if type(i) == int :
                re_list.append(i)# 새 리스트에 저장
            elif type(i)==list: #만약 리스트가 있으면 리스트의 숫자를 더해서 1개의 숫자로 만들자 
                sum = 0
                for j in i:
                    sum+=j
                re_list.append(sum)
            else :
                continue
        self.list_num=re_list


    def plus (self):
        result = 0
        for i in self.list_num :
            result += i
        return result

    def minus (self):
        result = self.list_num[0]
        for i in self.list_num[1:] :
            result -= i
        return result

    def multip (self):
        result = self.list_num[0]
        for i in self.list_num[1:] :
            result *= i
        return result

    def divi (self):
        #예외처리
        result = self.list_num[0]
        for i in self.list_num[1:] :
            result /= i
        return result

    def avg(self):
        result = self.plus()
        return int(result/len(self.list_num))

    #최대
    def maxnum(self):
      
        return max(self.list_num)
     

    #최소
    def mini(self):
        return min(self.list_num)
        
