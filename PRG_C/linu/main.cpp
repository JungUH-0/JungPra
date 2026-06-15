#include <stdio.h>

extern int add(int a, int b);
extern int sub(int a, int b);

int main()
{
     int n1 = 30;
     int n2 = 15;

     // 선언된 extern 함수들을 호출함
     printf("연산 대상: %d, %d\n", n1, n2);
     printf("더하기 결과: %d\n", add(n1, n2));
     printf("빼기 결과: %d\n", sub(n1, n2));

}