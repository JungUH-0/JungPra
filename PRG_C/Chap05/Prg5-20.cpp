/*************************************************************
 * 반복문을 사용해서 밑을 지수 번만큼 곱해서                 *
 * 거듭제곱을 구하는 프로그램                                *
 *************************************************************/
#include <iostream>
using namespace std; 
 
int main()
{
  // 변수 선언
  int base, exponent;
  unsigned long int power, temp;
  bool overflow;
  // 유효성 검사하면서 입력받기
  do
  {
    cout << "밑을 음수가 아닌 정수로 입력해주세요: ";
    cin >> base;
  } while(base < 0);
  // 유효성 검사하면서 입력받기  
  do
  {
    cout << "지수를 음수가 아닌 정수로 입력하세요: ";
    cin >> exponent;
  } while(exponent < 0);
  // 초기화
  power = 1; 
  temp = power;
  overflow = false;
  // 처리
  for(int i = 1;(i <= exponent) &&(!overflow); i++)
  {
    power *= base;
    if(power / base  != temp)
    {
      overflow = true; // 반복문 종료
    } 
    temp = power;
  }
  // 출력
  if(overflow)
  {
    cout << "오버플로우가 발생했습니다. 작은 값으로 시도하세요.";
  } 
  else
  {
    cout << base << "^" << exponent << " = " << power;
  }
  return 0;
}