class data_Set :
     def __init__(self,size) :
          self.data_set = []
          self.maxsize=size
          self.length = 0

     def isFull(self) :
          if self.maxsize == self.length :
               return True
          else:
               return False

     def  isEmpty (self) :
          if self.length == 0 :
               return True
          else:
               return False

     def Contain(self,e) :
          if self.isEmpty() :
               return False
          else :
               for i in  self.data_set :
                    if e == i :
                         return True
               return False

     def insert(self, e) :
          chk = self.Contain(e)
          # print("-------------------------------")
          # print("chk",chk)
          chk1= self.isFull()
          # print("chk1",chk1)
          if  chk1 == False :
               if chk == False :
                    self.data_set += [e]
                    self.length +=1
               else :
                    # print(e)
                    print ("중복")
          else :
               print("Full")

     def delete(self, e):
          if self.isEmpty():
               print("Empty")
               return
          if self.Contain(e) == False:
               print("no data")
               return
          for i in range(self.length):
               if self.data_set[i] == e:
                    for j in range(i, self.length-1):
                         self.data_set[j] = self.data_set[j+1]
                    self.data_set[self.length-1] = None
                    self.length -= 1
                    self.data_set = self.data_set[:self.length]
                    return

     def Union(self,setB) :
          len1 = self.length
          len2 = setB.length
          setC = data_Set(len1+len2)
          for i in self.data_set :
               if i == None :
                    continue
               setC.insert(i)
          for i in setB.data_set :
               if i == None :
                    continue
               setC.insert(i)
          return setC

     def intersect(self,setB) :
          # if self.length < setB.length :
          #     len = self.length
          # else : len = setB.length
          min_len = self.length if self.length < setB.length else setB.length
          setC = data_Set(min_len)
          for i in setB.data_set :
               for j in self.data_set:
                    if i == j :
                         setC.insert(i)
          return setC

     def difference(self,setB) :
          setC = data_Set(self.length)
          for i in self.data_set:
               if setB.Contain(i) :
                    continue
               else :
                    setC.insert(i)
          return setC
     
     def display(self):
          print(self.data_set)
     

A = data_Set(5)
A.insert(1)
A.insert(2)
A.insert(3)
A.insert(2)  
A.display()
print(A.Contain(1))
print(A.Contain(9))

B = data_Set(5)
B.insert(4)
B.insert(5)
B.insert(3)
B.display()

print("union 시작")
C = A.Union(B)
print(C.data_set)      

D = A.intersect(B)
print(D.data_set)      

E = A.difference(B)
print(E.data_set)    

class node_set : 
     def __init__(self,e,link=None):
        self.data = e
        self.next = link

class node_setuse :
     def __init__(self,head=None):
        self.head = head
        self.length= 0

     def isEmpty(self):
         return self.length==0

     def size(self):
         return self.length
     
     def contain(self,e):
          if (self.isEmpty()):
               return False
          else :
               current = self.head
               

                         

                    

