/*************************************************************
 * 3개의 변수를 선언하고                                     * 
 * 값과 주소를 출력하는 프로그램                             *
 *************************************************************/
#include <iostream>
using namespace std;

int main()
{
  // 3개의 데이터 변수 선언
  bool flag = true;
  int score = 92;
  double average = 82.56;
  // flag 변수의 크기, 값, 주소 출력
  cout << "불 자료형의 변수" << endl;
  cout << "크기: " << sizeof(flag) << "\t";
  cout << "값: " << flag << "\t";
  cout << "주소: " << &flag << endl << endl;
  // score 변수의 크기, 값, 주소 출력
  cout << "int 자료형의 변수" << endl;
  cout << "크기: " << sizeof(score) << "\t";
  cout << "값: " << score << "\t";
  cout << "주소: " << &score << endl << endl;
  // average 변수의 크기, 값, 주소 출력
  cout << "double 자료형의 변수" << endl;
  cout << "크기: " << sizeof(average) << "\t";
  cout << "값: " << average << "\t";
  cout << "주소: " << &average << endl;
  return 0;      
}