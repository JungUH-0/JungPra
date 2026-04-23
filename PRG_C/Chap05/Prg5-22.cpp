/*************************************************************
 * 리스트 내부에 있는 요소 중 적어도 하나가 7로              *
 * 나눌 수 있는지 확인하는 프로그램                          *
 *************************************************************/
#include <iostream>
using namespace std; 

int main()
{
  // 선언
  bool success = false;
  int size;
  int item;
  // 입력받기
  do 
  {
    cout << "리스트의 크기를 입력하세요: ";
    cin >> size;
  } while(size < 0);
  // 처리
  for(int i = 0;(i < size ) &&(!success); i++)
  {
    cout << "다음 숫자를 입력해주세요: ";
    cin >> item; 
    success = (item %7 == 0);
  }
  // 조건 분기
  if(success)
  {
    cout << item << "은/는 7로 나눌 수 있습니다." << endl;
  }
  else
  {
      cout << "리스트 내부에 7로 나눌 수 있는 숫자가 없습니다." << endl;
  }
  return 0;
}