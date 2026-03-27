/**************************************************************
 * 3개의 정수를 입력 받고, 이를 더하고 평균을 찾은 뒤         *
 * 각 숫자의 분산을 구하는 프로그램                           *
 **************************************************************/
#include <iostream>
#include <iomanip>
using namespace std;

int main()
{
  // 변수 선언
  int num1, num2, num3;
  int sum;
  double average;
  double dev1, dev2, dev3;
  // 입력받기
  cout << "첫 번째 숫자 입력: "; 
  cin >> num1; 
  cout << "두 번째 숫자 입력: "; 
  cin >> num2;
  cout << "세 번째 숫자 입력: "; 
  cin >> num3; 
  // 처리
  sum = num1 + num2 + num3; 
  average = static_cast<double>(sum) / 3; 
  dev1 = num1 - average; 
  dev2 = num2 - average; 
  dev3 = num3 - average;
  // 출력
  cout <<  fixed << setprecision(2);
  cout << "세 숫자의 합: " << sum << endl;
  cout << "평균: " << setw(9) << average << endl; 
  cout << "첫 번째 숫자의 분산: " << setw(9) << dev1 << endl; 
  cout << "두 번째 숫자의 분산: " << setw(9) << dev2 << endl; 
  cout << "세 번째 숫자의 분산: " << setw(9) << dev3 << endl;  
  return 0;
}