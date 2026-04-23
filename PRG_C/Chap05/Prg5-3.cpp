/************************************************************
 * while 반복문을 사용해서 0부터 n-1까지 출력하는 프로그램  *
 ************************************************************/
#include <iostream>
using namespace std;

int main()  
{
  // 선언
  int n, count;
  // 변수 n 입력 받기
  cout << "출력할 정수를 입력하세요: ";
  cin >> n;
  // 정수 출력
  count = 0;
  while(count < n)   
  {
    cout << count << endl;  
    count++; 
  }
  return 0;  
}