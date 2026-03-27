/************************************************************
 * 부호 없는 정수 자료형의 오버플로우와 언더플로우 확인하기 *
*************************************************************/
#include <iostream>
#include <limits>
using namespace std;

int main()
{
  // 부호 없는 정수의 최대값과 최소값 검색
  unsigned int num1 = numeric_limits<unsigned int>::max();
  unsigned int num2 = numeric_limits<unsigned int>::min();
  // 최대값과 최소값 출력
  cout << "부호 없는 정수의 최대값: " << num1 << endl;
  cout << "부호 없는 정수의 최소값: " << num2 << endl;
  // 강제로 오버플로우와 언더플로우 발생 
  num1 += 1;
  num2 -= 1;
  // 오버플로우와 언더플로우된 값 출력
  cout << "오버플로우가 일어난 num1 + 1의 값: " << num1 << endl;
  cout << "언더플로우가 일어난 num2 - 1의 값: " << num2 << endl;
  return 0;      
}