/**************************************************************
 * 입력된 정수의 첫 번째 자릿수를 추출해서 출력하는 프로그램  *
 **************************************************************/
#include <iostream>
using namespace std;

int main()
{ 
  // 변수 선언
  unsigned int givenInt, firstDigit;
  // 입력받기
  cout << "양의 정수 입력: ";
  cin >> givenInt;
  // 처리
  firstDigit = givenInt % 10;
  // 출력
  cout << "입력한 정수 " << givenInt << endl;
  cout << "첫 번째 자리수 추출: " << firstDigit << endl;    
  return 0;
}