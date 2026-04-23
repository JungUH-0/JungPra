/**************************************************************
 * 몇 월 며칠을 입력 받았을 때                                *
 * 해당 날짜가 올해 몇 번째 날짜인지 구하는 프로그램          *
 **************************************************************/
#include <iostream>
using namespace std;

int main()
{
  // 변수 선언
  int month;
  int day;
  int totalDays = 0;
  // 입력받기
  cout << "몇 월인지 입력하세요: ";
  cin >> month;
  cout << "며칠인지 입력하세요: "; 
  cin >> day;
  // 각 월의 날 수
  int m01 = 31;
  int m02 = 28;
  int m03 = 31;
  int m04 = 30;
  int m05 = 31;
  int m06 = 30;
  int m07 = 31;
  int m08 = 31;
  int m09 = 30;
  int m10 = 31;
  int m11 = 30;
  // switch 조건문을 사용해서 특정 달까지의 날 수를 계산
  switch(month)
  {
    case 12 : totalDays += m11;
    case 11 : totalDays += m10;
    case 10 : totalDays += m09;
    case 9  : totalDays += m08;
    case 8  : totalDays += m07;
    case 7  : totalDays += m06;
    case 6  : totalDays += m05;
    case 5  : totalDays += m04;
    case 4  : totalDays += m03;
    case 3  : totalDays += m02;
    case 2  : totalDays += m01;
    case 1  : totalDays += 0;
  }
  // 최종 결과를 구함
  totalDays +=  day;
  // 결과를 출력  
  cout << "올해의 " << totalDays << "번째 날입니다.";
  return 0;      
}