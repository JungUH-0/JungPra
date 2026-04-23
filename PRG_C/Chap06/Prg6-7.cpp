/*************************************************************
 * 랜덤 숫자를 사용한 추측 게임                              *
 *************************************************************/
#include <iostream>
#include <cstdlib>
#include <ctime>
using namespace std;

int main()
{
  // 선언과 초기화
  int low = 5;
  int high = 15;
  int tryLimit = 5;
  int guess;
  // 랜덤 숫자 생성
  srand(time(0));
  int temp = rand();
  int num = temp %(high - low + 1) + low;
  // 추측을 위한 반복
  int counter = 1;
  bool found = false;
  while(counter <= tryLimit  &&  !found)
  {
    do 
    {
       cout << "1~15 사이의 정수를 입력하세요: ";
       cin >> guess;
    } while(guess < 5 || guess > 15);
    
    if(guess == num)
    {
       found = true;
    }
    else if(guess > num)
    {
       cout << "더 작은 숫자입니다." << endl;
    }
    else 
    {
      cout << "더 큰 숫자입니다." << endl;
    }
    counter++;
  }
  // 추측에 성공한 경우
  if(found)
  {
    cout << "축하합니다. 추측에 성공했습니다. ";
    cout << "답 = " << num;
  }
  // 추측에 실패한 경우  
  else 
  {
    cout << "아쉽게 추측에 실패했습니다. "; 
    cout << "답 = " << num;
  }
  return 0;      
}