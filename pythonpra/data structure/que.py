class data_Queue:
    def __init__(self, size):
        self.my_queue = [None] * size
        self.maxsize = size
        self.front = 0
        self.rear = 0
        self.length = 0

    def isFull(self):
        return self.maxsize == self.length

    def isEmpty(self):
        return self.length == 0

    def Enqueue(self, e):
        if self.isFull():
            return "Full"
        self.my_queue[self.rear] = e
        self.rear += 1
        self.length += 1

    def Dequeue(self):
        if self.isEmpty():
            return "Empty"
        val = self.my_queue[self.front]
        self.my_queue[self.front] = None
        self.front += 1
        self.length -= 1
        return val

    def Peek(self):
        if self.isEmpty():
            return "Empty"
        return self.my_queue[self.front]

    def Size(self):
        return self.length

    def Clear(self):
        self.my_queue = [None] * self.maxsize
        self.front = 0
        self.rear = 0
        self.length = 0

class cir_Queue:
    def __init__(self, size):
        self.my_queue = [None] * size
        self.maxsize = size
        self.front = 0
        self.rear = 0
        self.length = 0

    def isFull(self):
        return self.front == (self.rear+1)%self.maxsize

    def isEmpty(self):
        return self.length == 0

    def Enqueue(self, e):
        if self.isFull():
            return "Full"
        self.my_queue[self.rear] = e
        self.rear= (self.rear+1)%self.maxsize
        self.length += 1

    def Dequeue(self):
        if self.isEmpty():
            return "Empty"
        val = self.my_queue[self.front]
        self.my_queue[self.front] = None
        self.front= (self.front+1)%self.maxsize
        self.length -= 1
        return val

    def Peek(self):
        if self.isEmpty():
            return "Empty"
        return self.my_queue[self.front]

    def Size(self):
        return self.length

    def Clear(self):
        self.my_queue = [None] * self.maxsize
        self.front = 0
        self.rear = 0
        self.length = 0


class priority_Queue:
    def __init__(self, size):
        self.my_queue = [None] * size
        self.maxsize = size
        self.length = 0

    def isFull(self):
        return self.maxsize == self.length

    def isEmpty(self):
        return self.length == 0

    def Enqueue(self, e, priority):
        if self.isFull():
            return "Full"
        
        item = (priority, e)
        #  숫자 작을수록 우선순위 높음
        pos = self.length
        for i in range(self.length):
            if item[0] < self.my_queue[i][0]:
                pos = i
                break
        # pos 이후 데이터를 뒤로 밀기
        for i in range(self.length, pos, -1):
            self.my_queue[i] = self.my_queue[i-1]
        self.my_queue[pos] = item
        self.length += 1

    def Dequeue(self):
        if self.isEmpty():
            return "Empty"
        val = self.my_queue[0]
        for i in range(self.length-1):
            self.my_queue[i] = self.my_queue[i+1]
        self.my_queue[self.length-1] = None
        self.length -= 1
        return val

    def Peek(self):
        if self.isEmpty():
            return "Empty"
        return self.my_queue[0]

    def Size(self):
        return self.length
