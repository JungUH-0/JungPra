/**************************************************************
 * 참조로 전달 메커니즘을 사용해서                            *
 * 두 값을 스왑(swap)하는 프로그램                            *
 **************************************************************/
#include <iostream>
using namespace std;

void swap(int& first, int& second);   // 함수 선언

int main()
{
  // 선언
  int first = 10;
  int second = 20;
  swap(first, second);  // 함수 호출
  // 스왑 확인
  cout << "main 함수의 first 값 = " << first << endl;
  cout << "main 함수의 second 값 = " << second;
  return 0;
}
/**************************************************************
 * swap 함수는 참조로 전달 매커니즘으로                       *
 * 2개의 parameter를 받음                                     *
 * temp라는 임시 변수를 사용해서 fst와 snd의 값을 스왑        *
 * 참조로 전달 메커니즘으로 받은 parameter를 변경했으므로     *
 * argument(main 함수의 first와 second)에도 영향을 미침       *
 **************************************************************/
void swap(int& fst, int& snd)
{
  int temp = fst;
  fst = snd;
  snd = temp;
  return;
}