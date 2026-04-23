/**************************************************************
 * 정수 리스트의 크기를 미리 알고 있을 때                     *
 * 정수 리스트 내부의 최소값과 최대값을 구하는 프로그램       *
 **************************************************************/
#include <iostream>
#include <limits>  // 자료형의 범위를 확인하기 위한 헤더 파일
using namespace std; 
 
int main()
{
  // 변수 선언
  int size;
  int number, smallest, largest;
  // 초기화
  smallest = numeric_limits<int>::max();
  largest = numeric_limits<int>::min();
  // 입력받기
  do
  {
    cout << "음수가 아닌 수로 리스트의 크기를 입력하세요: ";
    cin >> size;
  } while(size <= 0);
  // 처리
  for(int i = 1; i <= size; i++)
  {
    cout << "다음 숫자를 입력하세요: ";
    cin >> number;
    if(number < smallest)
    {
      smallest = number;
    } 
    if(number > largest)
    {
      largest = number;
    } 
  }
  // 결과 출력
  cout << "최소값 = " << smallest << endl;
  cout << "최대값 = " << largest << endl;
  return 0;
} 