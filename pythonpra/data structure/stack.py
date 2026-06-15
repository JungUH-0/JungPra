class data_Stack :
    def __init__(self,size):
        self.my_stack=[None]*size
        self.maxsize=size
        self.length=0

    def isFull(self):
        #return True if self.maxsize == self.length else False
        return self.maxsize == self.length

    def isEmpty(self):
        #return True if self.length == 0 else False
        return self.length == 0

    def push(self,e):
        if self.isFull() : return("Full")
        else :
            self.my_stack[self.length] = e
            self.length +=1
    def pop(self):
        if self.isEmpty() : return ("Empty")

        else :
            b=self.my_stack[self.length-1]
            self.my_stack[self.length-1] = None
            self.length -=1
            return b
    def peek(self):
        if self.isEmpty() : return ("Empty")
        else:
            print(self.my_stack[self.length-1])
            return self.my_stack[self.length-1]
    def size(self):
        return self.length
    def clear(self):
        if self.isEmpty() : return ("Empty")
        else:
            self.my_stack = [None]*self.maxsize