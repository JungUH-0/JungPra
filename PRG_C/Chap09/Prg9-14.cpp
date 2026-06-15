/**************************************************************
 * 힙 메모리에 크기가 유동적인 배열을 만들고                  *
 * 포인터로 요소에 접근하는 프로그램                          *
 **************************************************************/
#include <iostream>
using namespace std;

int main()
{
  // 스택에 배열에 대한 크기와 포인터 선언
  int size;
  int* pArray;
  // 사용자로부터 0보다 큰 배열의 크기 입력받기
  do 
  {
    cout << "0보다 큰 배열의 크기를 입력하세요:";
    cin >> size;
  } while(size <= 0);
  // 힙에 배열 생성
  pArray = new int[size];
  // 배열에 값 입력받기
  for(int i = 0; i < size ; i++)
  {
    cout << i << "번째 요소의 값을 입력하세요: ";
    cin  >> *(pArray + i);
  }
  // 배열의 요소 출력
  cout << "배열 내부의 요소:" << endl;
  for(int i = 0; i < size ; i++)
  {
    cout << *(pArray + i) << "   ";
  }
  // 힙에서 배열 제거
  delete [ ] pArray;
  return 0;      
}