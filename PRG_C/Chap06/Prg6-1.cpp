/*********************************************************
 * <cmath> 헤더 파일에 정의되어 있는                     * 
 * 숫자 함수들을 사용하는 프로그램                       *
 *********************************************************/
#include <iostream>
#include <cmath>
using namespace std;

int main()
{
  // abs 함수 사용
  cout << "abs(8) = " << abs(8) << endl;
  cout << "abs(-8) = " << abs(-8) << endl;
  // floor, ceil 함수 사용
  cout << "floor(12.78) = " << floor(12.78) << endl;
  cout << "ceil(12.78) = " << ceil(12.78) << endl;
  // log, log10 함수 사용
  cout << "log(100) = " << log(100) << endl;
  cout << "log10(100) = " << log10(100) << endl;
  // exp, pow 함수 사용
  cout << "exp(5) = " << exp(5) << endl;
  cout << "pow(2, 3) = " << pow(2,3) << endl;
  // sqrt 함수 사용
  cout << "sqrt(100) = " << sqrt(100); 
  return 0;   
}