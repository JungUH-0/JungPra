/*************************************************************
 * 변수의 초기화를 확인하는 프로그램                         *
 *************************************************************/ 
#include <iostream>
using namespace std;

int global;   // 전역 변수

int main()
{
  static int sLocal;   // 정적 지역 변수
  int aLocal;     // 자동 지역 변수
  // 출력
  cout << "전역 변수 = " << global << endl;
  cout << "정적 지역 변수 = " << sLocal << endl;
  cout << "자동 지역 변수 = " << aLocal << endl;
  return 0;
}