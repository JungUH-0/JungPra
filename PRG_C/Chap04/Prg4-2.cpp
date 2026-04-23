/**************************************************************
 * if 조건문을 사용해서 초과 근무 시간이 있는 급여 계산하기   *
 **************************************************************/
#include <iostream>
#include <iomanip>;
using namespace std;

int main()  
{
  // 변수 선언
  double hours;
  double rate;
  double regularPay;
  double overPay;
  double totalPay;
  // 입력받기
  cout << "업무 시간을 입력하세요: ";
  cin >> hours;  
  cout << "시간당 급여를 입력하세요: ";
  cin >> rate;
  // 일반 급여 계산 
  regularPay = hours * rate;
  overPay = 0.0;
  // 40시간을 넘게 근무 했을 때 초과 근무에 대한 급여 계산
  if(hours > 40.0)  
  {
    overPay = (hours - 40.0) * rate * 0.30;  
  } // if 구문 종료
  // 전체 급여 계산
  totalPay = regularPay + overPay; 
  // 출력
  cout << fixed << showpoint;  
  cout << "일반 급여 = " << setprecision(2) << regularPay << endl;
  cout << "초과 근무에 대한 급여 = " << setprecision(2) << overPay << endl;
  cout << "전체 급여 = " << setprecision(2) << totalPay << endl;  
  return 0;
}