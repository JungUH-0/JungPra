/**************************************************************
 * switch 조건문을 사용해서 특정 요일부터 마지막 요일까지     *
 * 출력하는 프로그램                                          *
 **************************************************************/
#include <iostream>
using namespace std;

int main()  
{
  // 변수 선언
  int day;
  // 입력받기
  cout << "0~6 범위의 정수를 입력하세요: ";
  cin >> day;
  // switch 조건문(의사 결정하고 출력)
  switch(day)
  {
  case 0: cout << "일요일" << endl;
  case 1: cout << "월요일" << endl;
  case 2: cout << "화요일" << endl;
  case 3: cout << "수요일" << endl;
  case 4: cout << "목요일" << endl;
  case 5: cout << "금요일" << endl;
  case 6: cout << "토요일" << endl;  
  } // switch 구문 종료
  return 0;  
}