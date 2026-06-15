/**************************************************************
 * Fraction 객체를 사용하는 app.cpp 애플리케이션 파일         *
 **************************************************************/
#include "fraction.h"
#include <iostream>
using namespace std;

int main()
{
  // 객체 인스턴스화
  Fraction fract1 ;
  Fraction fract2(14, 21);
  Fraction fract3(11, -8);
  Fraction fract4(fract3);
  // 객체 출력
  cout << "생성한 분수 4개를 출력합니다: " << endl;
  cout << "fract1: ";
  fract1. print();
  cout << "fract2: ";
  fract2. print();
  cout << "fract3: ";
  fract3. print();
  cout << "fract4: ";
  fract4. print();
  // 설정자 사용
  cout << "두 분수를 변경하고 출력합니다: " << endl;
  fract1.setNumer(4);
  cout << "fract1: ";
  fract1.print();
  fract2.setDenom(-5);
  cout << "fract2: ";
  fract2.print();
  // 접근자 사용
  cout << "접근자로 분자와 분모 따로 확인하기: " << endl;
  cout << "fract1의 분자: " << fract1.getNumer() << endl;
  cout << "fract2의 분모: " << fract2.getDenom() << endl; 
  return 0;
}