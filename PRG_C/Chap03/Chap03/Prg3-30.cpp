/* ************************************************************
 * 초 단위로 입력받은 시간을 시, 분, 초 단위로 나누어서       *
 * 출력하는 프로그램                                          *
 **************************************************************/
#include <iostream>
using namespace std;

int main()
{ 
  // 변수 선언
  unsigned long duration, hours, minutes, seconds; 
  // 입력받기
  cout <<"초 단위 시간을 양의 정수로 입력: ";
  cin >> duration;
  // 처리
  hours = duration / 3600L;
  minutes = (duration -(hours * 3600L)) / 60L;
  seconds = duration -(hours * 3600L) -(minutes * 60);
  // 출력
  cout << "입력된 초 단위 시간: " << duration << endl;
  cout << "결과: ";
  cout << hours << "시 ";
  cout << minutes << "분 ";
  cout << seconds << "초 ";
  return 0; 
}