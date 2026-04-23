/*************************************************************
 * 반복문을 중첩해서 숫자를 정해진 패턴으로                  *
 * 출력하는 프로그램                                         *
 *************************************************************/ 
#include <iostream>
using namespace std;

int main()
{
  // 선언
  int rows;     // 행의 수
  int cols;     // 열의 수
  // 입력받기
  cout << "행의 수를 입력하세요: ";
  cin >> rows;
  cout << "열의 수를 입력하세요: ";
  cin >> cols;
  // 중첩 반목문
  for(int i = 1; i <= rows; i++)
  {
     for(int j = i; j <= i + cols -1; j++)
     { 
       cout << j << " "; 
     } 
     cout << endl;
  }  
  return 0; 
}