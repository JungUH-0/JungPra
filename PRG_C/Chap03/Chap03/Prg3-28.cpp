/* ************************************************************
 * 주어진 부동 소수점의 정수 부분과 소수점 아래 부분을        *
 * 추출해서 출력하는 프로그램                                 *
 **************************************************************/
#include <iostream>
#include <iomanip>
using namespace std;

int main()
{
  // 변수 선언
  double number;
  int intPart;
  double fractPart;
  // 입력받기
  cout << "부동 소수점 입력: ";
  cin >> number;
  // 처리
  intPart = static_cast<int>(number); 
  fractPart = number - intPart;
  // 출력
  cout << fixed << showpoint << setprecision(2);
  cout << "원래 값: " << number << endl;  
  cout << "정수 부분: " << intPart << endl;
  cout << "소수점 아래 부분: " << fractPart;
  return 0;
} 