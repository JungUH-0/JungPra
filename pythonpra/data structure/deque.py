class data_Deque:
    def __init__(self, size):
        self.my_deque = [None] * size
        self.maxsize = size
        self.front = 0
        self.rear = 0
        self.length = 0

    def isFull(self):
        return self.maxsize == self.length

    def isEmpty(self):
        return self.length == 0

    def Size(self):
        return self.length

    def Clear(self):
        self.my_deque = [None] * self.maxsize
        self.front = 0
        self.rear = 0
        self.length = 0

    def addFront(self, e):
        if self.isFull():
            return "Full"
        self.front = (self.front - 1 + self.maxsize) % self.maxsize
        self.my_deque[self.front] = e
        self.length += 1

    def addRear(self, e):
        if self.isFull():
            return "Full"
        self.my_deque[self.rear] = e
        self.rear = (self.rear + 1) % self.maxsize
        self.length += 1

    def removeFront(self):
        if self.isEmpty():
            return "Empty"
        val = self.my_deque[self.front]
        self.my_deque[self.front] = None
        self.front = (self.front + 1) % self.maxsize
        self.length -= 1
        return val

    def removeRear(self):
        if self.isEmpty():
            return "Empty"
        self.rear = (self.rear - 1 + self.maxsize) % self.maxsize
        val = self.my_deque[self.rear]
        self.my_deque[self.rear] = None
        self.length -= 1
        return val
    def getFront(self):
        if self.isEmpty():
          return "Empty"
        return self.my_deque[self.front]

    def getRear(self):
        if self.isEmpty():
            return "Empty"
        return self.my_deque[(self.rear - 1 + self.maxsize) % self.maxsize]


d = data_Deque(5)
d.addRear(1)
d.addRear(2)
d.addRear(3)
d.addFront(0)
print(d.my_deque)       # [0, 1, 2, 3, None]
print(d.getFront())     # 0
print(d.getRear())      # 3
print(d.removeFront())  # 0
print(d.removeRear())   # 3
print(d.Size())         # 2
