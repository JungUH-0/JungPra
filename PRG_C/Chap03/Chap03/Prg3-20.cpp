/********************************************************** 
 * double 자료형의 오버플로우와 언더플로우 확인하기       *
 **********************************************************/
#include <iostream>
#include <limits>
using namespace std;

int main()
{
  // double 자료형의 최대값과 최소값 검색
  double num1 =  +numeric_limits<double>::max();
  double num2 =  -numeric_limits<double>::max();
  // double 자료형의 최대값과 최소값 출력
  cout << "double의 최대값: " << num1 << endl;
  cout << "double의 최소값: " << num2 << endl;
 // 값에 1000.00 곱하기  
 num1 *= 1000.00;
 num2 *= 1000.00;
 // 오버플로우와 언더플로우된 값 출력
 cout << "오버플로우가 일어난 num1 * 1000의 값: " << num1 << endl;
 cout << "언더플로우가 일어난 num2 * 1000의 값: " << num2 << endl;
 return 0;      
}