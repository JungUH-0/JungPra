/**************************************************************
 * 0부터 n-1까지 for 반복문으로 출력하기                      *
 **************************************************************/
#include <iostream>
using namespace std;

int main()  
{
  // 선언
  int n;
  // 변수 n 입력받기
  cout << "출력할 정수를 입력하세요: ";
  cin >> n;
  // 반복문
  for(int counter = 0; counter < n; counter++)   
  {
    cout << counter << " "; 
  }
  return 0; 
}