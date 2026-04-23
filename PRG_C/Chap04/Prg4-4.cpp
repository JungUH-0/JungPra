/*************************************************************
 * if-else 조건문을 사용해서 입력받은 더 큰 숫자 또는       * 
 * 숫자가 같을 경우 첫 번째 숫자를 출력하는 프로그램         *
 *************************************************************/ 
#include <iostream>
using namespace std;

int main()  
{
  // 변수 선언
  int num1, num2;
  int larger;
  // 입력받기
  cout << "첫 번째 숫자 입력: ";
  cin >> num1;
  cout << "두 번째 숫자 입력: ";
  cin >> num2;
  // 의사 결정  
  if(num1 >=  num2)
  {
    larger = num1;
  } // if 구문 종료
  else 
  {
    larger = num2;
  } // else 구문 종료
  // 결과 출력
  cout << "더 큰 숫자 = " << larger;
  return 0;
}