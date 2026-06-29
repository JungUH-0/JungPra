class data_List :
    def __init__(self,size):
        self.data_list= [None]*size
        self.maxsize=size
        self.length=0

    def isFull (self):
        if self.maxsize == self.length :
            return True
        else:
            return False

    def  isEmpty (self):
        if self.length == 0 :
            return True
        else:
            return False
    def Print(self,str):
        pass


    def insert (self,pos,e):

        if self.isFull() == True :
            print("size over")
            return

        if self.data_list[pos] != None :
            temp_ori = self.data_list[pos] #원본데이터
            self.data_list[pos]=e
            for i in range(pos, self.length-1):
                temp = self.data_list[i+1]
                self.data_list[i+1] = temp_ori
                temp_ori = temp

            self.data_list[self.length] = temp_ori # 마지막값
            self.length +=1
        else :
            self.data_list[pos] = e
            self.length +=1

    def delete (self,pos):
        if self.isEmpty() == True :
            print("empty")
            return
        if self.data_list[pos] == None :
            print("already None")
            return
        else :
            # 맨 뒤의 값을 가져와서 기억하고 당기기
            # temp_ori = self.data_list[self.length-1]
            # print(temp_ori)
            # for i in range(self.length-2,pos-1,-1):
            #     # print (i)
            #     temp = self.data_list[i]
            #     # print (temp)
            #     self.data_list[i] = temp_ori
            #     temp_ori=temp
            # self.data_list[self.length-1] = None
            #----------------------------------------
            # pos 부터 시작해서 다음 값을 기억할 필요없이 바로 대입
            for i in range(pos,self.length-1) :
                self.data_list[i]=self.data_list[i+1]
            self.data_list[self.length-1] = None
            self.length -=1

    def getEntry(self,pos):
        if self.data_list[pos] == None :
            print("None!")
            return
        else :
            return self.data_list[pos]

    def size(self):
        return self.length

    def clear(self):
        for i in range(self.length):
            self.data_list[i] = None

    def find(self,item):
        result = None
        for i in range(self.length):
            if self.data_list[i] == item :
                result = i
        if result != None :
            print(item,"의 위치는",result)
            return
        else :
            print("no data")
            return

    def replace(self,pos,item) :
        self.data_list[pos] = item

    def append(self,e):
        self.data_list[self.length] = e
        self.length += 1

    def display(self):
        print(self.data_list)

    def bigSort(self):
        #큰수
       for i in range(self.size()-1) :
            if (type(self.data_list[i])!= int):
                continue
            for j in range(i+1,self.size()):
                if (type(self.data_list[j])!= int):
                    continue
                if((self.data_list[i] is not None) and (self.data_list[j] is not None)):
                    if(self.data_list[i]<self.data_list[j]):
                        temp = self.data_list[i]
                        self.data_list[i]=self.data_list[j]
                        self.data_list[j]=temp
                        #self.data_list [i], self.data_list [j] = self.data_list [j], self.data_list [i]
                else:
                    continue
    def lowSort(self) :
        #작은수 
        for i in range(self.size()-1):
            if (type(self.data_list[i])!= int):
                continue
            for j in range(i+1,self.size()):
                if (type(self.data_list[j])!= int):
                    continue
                if((self.data_list[i] is not None) and (self.data_list[j] is not None)):
                    if(self.data_list[i]>self.data_list[j]):
                        temp = self.data_list[i]
                        self.data_list[i]=self.data_list[j]
                        self.data_list[j]=temp

my_list = data_List(10)
print(my_list.isEmpty())
print(my_list.isFull())

for i in range(10):
    my_list.insert(i,i*10)
print("chk")

print(my_list.isEmpty())
print(my_list.isFull())
my_list.display()

class node_List:
     def __init__(self,e,link=None):
        self.data = e
        self.next = link

class node_luse:
    def __init__(self,head=None):
        self.head = head
        self.length= 0
     
    def isEmpty(self):
         return self.length==0

    def size(self):
         return self.length
     
    def insert (self,pos,e):
        new_node = node_List(e)
        if pos == 0:
            new_node.next = self.head
            self.head = new_node
        else:   
            current = self.head
        
            for i in range(pos - 1):
                current = current.next

            new_node.next = current.next
            current.next = new_node
        
        self.length += 1

        

    def delete(self,pos):
        if self.head == None :
            nodata = "현재 정보가 없습니다."
            return nodata
        if pos ==0:
            temp = self.head.data
            self.head = self.head.next
            return temp
        else:
            current = self.head
            temp = None
            for i in range(pos-1):
                current = current.next
            temp = current.next.data
            current.next = current.next.next
        
            return temp
        
    def clear(self):
        self.head=None
    
    def replace(self,pos,e):
        if self.head == None :
            nodata = "현재 정보가 없습니다."
            return nodata
        if pos ==0 :
            self.head.data = e
        else:
            current = self.head
            for i in range(pos):
                current = current.next
            current.data = e

    def append(self,e):
        node = node_List(e)
        if self.head ==None:
            self.head = node
        else:
            l = self.size()
            current = self.head
            for i in range(l-1):
                current = current.next
            current.next = node

    def find(self,item) :
        nodata = "현재 정보가 없습니다."
        if self.head == None :
            return nodata
        
        
        current = self.head
        if current.data ==item:
            return 0
        l=self.size()
        count =0
        for i in range(l-1):
            count +=1
            current = current.next
            if current.data == item:
                return count
        return nodata
            


# =============================================
# # 방식 1: 노드를 직접 선언하고 연결
# # - 사용자가 직접 노드 객체를 만들고 연결
# # - 노드 하나하나를 직접 제어 가능
# # - 관리가 불편하고 실수 가능성이 높음
# # =============================================
# class node_List:
#     def __init__(self, e):
#         self.data = e
#         self.next = None  # 다음 노드를 가리키는 포인터, 기본값은 None

# # 노드 직접 생성
# first = node_List(10)   # 각 노드가 독립적인 메모리를 가짐
# second = node_List(20)  # 각 노드가 독립적인 메모리를 가짐
# third = node_List(30)   # 각 노드가 독립적인 메모리를 가짐

# # 사용자가 직접 연결
# first.next = second   # first → second
# second.next = third   # second → third
# # 결과: first(10) → second(20) → third(30) → None

# # 순회
# current = first
# while current:
#     print(current.data)
#     current = current.next


# # =============================================
# # 방식 2: LinkedList 클래스가 내부에서 노드를 생성하고 연결
# # - 사용자는 데이터만 넘기면 됨
# # - 내부에서 자동으로 노드 생성 및 연결
# # - 노드 하나하나도 독립적인 메모리를 가짐 (방식1과 동일)
# # - 관리가 편하고 실수 가능성이 낮음
# # =============================================
# class LinkedList:
#     def __init__(self):
#         self.head = None   # 첫 번째 노드를 가리킴
#         self.length = 0
    
#     def append(self, e):
#         new_node = node_List(e)  # 내부에서 자동으로 노드 생성
#         if self.head is None:
#             self.head = new_node  # 첫 번째 노드면 head로 설정
#         else:
#             current = self.head
#             while current.next:   # 마지막 노드까지 이동
#                 current = current.next
#             current.next = new_node  # 마지막 노드에 연결

#         self.length += 1

# # 사용자는 데이터만 넘기면 내부에서 알아서 노드 생성 및 연결
# ll = LinkedList()
# ll.append(10)  # 내부: node_List(10) 생성 → head 에 연결
# ll.append(20)  # 내부: node_List(20) 생성 → 10 뒤에 연결
# ll.append(30)  # 내부: node_List(30) 생성 → 20 뒤에 연결
# # 결과: head(10) → (20) → (30) → None

# current = ll.head
# while current:
#     print(current.data)
#     current = current.next
    