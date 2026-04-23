/***********************************************************
 * 매개변수가 있는 void 함수를 사용하여                    *
 * 패턴을 출력하는 프로그램                                *
 ***********************************************************/
#include <iostream>
using namespace std;

/*********************************************************** 
 * pattern 함수의 정의 * 
 * pattern 함수는 매개변수가 있는 void 함수   *
 * 함수가 호출될 때 매개변수로 패턴의 크기(size)를 전달받음* 
 * 이 매개변수는 패턴의 크기를 나타냄     *                   
 ***********************************************************/
  void pattern(int size)
  {
    for(int i = 0; i < size; i++)
    {
      for(int j = 0; j < size; j++)
      {
        cout << "*";
      }
      cout << endl;
    }
    return;
} 

int main()
{
  // 선언
  int patternSize;  // 함수에 전달할 값
  // 입력 유효성 검사
  do 
  {
    cout << "패턴의 크기를 입력하세요: ";
    cin >> patternSize;
  } while(patternSize <= 0);
  // 함수 호출
  pattern(patternSize); // 이때 patternSize는 인수(arguments)
  return 0;
}