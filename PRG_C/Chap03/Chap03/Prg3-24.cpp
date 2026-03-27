/************************************************************* 
 *부동 소수점 관련 조정자 사용하기                           *                                                
 *************************************************************/
#include <iostream>
#include <iomanip>
using namespace std;

int main()
{
  // 선언
  double x = 1237234.1235;
  // 기본 출력 방식 조정
  cout << fixed << setprecision(2) << showpos << setfill('*');
  // x를 3가지 형식으로 출력
  cout << setw(15) << left << x << endl;
  cout << setw(15) << internal << x << endl;
  cout << setw(15) << right << x;
  return 0;      
}