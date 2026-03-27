/*************************************************************
 * 산술 연산자가 없는 자료형(bool, char, short, float)에     *
 * 산술 연산자를 적용해서 암묵적 자료형 변환하기             *
 *************************************************************/
#include <iostream>
#include <typeinfo>
using namespace std;

int main()
{
  // 선언
  bool x = true; // true =1 false =0
  char y = 'A';  // 아스키 코드 활용 대문자 'A'
  short z = 14;
  float t = 24.5;
  // bool에서 int로 자료형 변환
  cout << "x + 100의 자료형: " << typeid(x + 100).name() << endl;
  cout << "x + 100의 값: " << x + 100 << endl;
  // char에서 int로 자료형 변환
  cout << "y + 1000의 자료형: " << typeid(y + 1000).name() << endl;
  cout << "y + 1000의 값: " << y + 1000 << endl;
  // short에서 int로 자료형 변환
  cout << "z * 100의 자료형: " << typeid(z * 100).name() << endl;
  cout << "z * 100의 값: " << z * 100 << endl;
  // float에서 double로 자료형 변환
  cout << "t + 15000.2의 자료형: " << typeid(t + 15000.2).name() << endl;
  cout << "t + 15000.2의 값: " << t + 15000.2;
  return 0;
}