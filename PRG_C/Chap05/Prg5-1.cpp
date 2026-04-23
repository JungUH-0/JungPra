/************************************************************
 * while 반복문을 사용해서 메시지를 10회 출력하기           *
 ************************************************************/
#include <iostream>
using namespace std;

int main()
{
  // 카운터 선언하고 초기화
  int counter = 0;
  // while 반복문
  while(counter < 10)   // 10회 반복
  {
    cout << "Hello world!" << endl;
    counter++;
  }
  return 0;      
}