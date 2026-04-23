/**************************************************************
 * 특정한 온도 범위에 따라 에어컨을                           * 
 * 냉방 또는 난방으로 가동하는 프로그램                       * 
 **************************************************************/ 
#include <iostream>
using namespace std;

int main()
{
  // 변수 선언
  int temperature;
  bool hot;
  bool cold;
  // 입력받기
  cout << "현재 온도를 입력하세요: "; 
  cin >>  temperature;
  // 조건 구하기
  hot = temperature >= 23;
  cold = temperature <= 15;
  // 의사 결정
  if(hot || cold)
  {
    cout << "에어컨이 켜집니다." << endl;
    if(hot)
    {
      cout << "냉방 모드로 작동합니다." << endl;
    }
    else
    {
      cout << "난방 모드로 작동합니다." << endl;
    }
  }
  else
  {
    cout << "에어컨이 꺼집니다." << endl;
  }
  return 0;
}