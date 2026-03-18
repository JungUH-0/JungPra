a=1+2+3+4+5+6\
+2

print(a)
for i in range(1,11) :
    print(i)
    if i ==5:
        break
b=a

if b==a:
    print(b)
else :
    print("false")
#파이선의 유연성
#한줄 주석 
# '''/"""" 3개의 따옴표 그 사이는 전체 주석
if False : print(10) ; print(1)

num = 2
def double():
    """Function to double the value"""
    print(num)
double()
print(double.__doc__)

#변수
#이렇게도 가능
"""a, b, c = 10, 5.2, "변수"
print(a)
print(b)
print(c)
"""
#어떻게 동작하는가?
#c="kopo"를 받고 c=10 -> b=c -> a=b
a=b=c="kopo"
print(a)
print(b)

print(c)
#id()는 각 메모리의 주소를 불러옴
print(id(10),id(a))
a=1
print(id(a))

a= a+1
print(id(a))