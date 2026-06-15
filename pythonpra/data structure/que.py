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
