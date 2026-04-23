/**************************************************************
 * 함수를 사용해서 정기 예금의                                *
 * 미래 가치를 찾는 프로그램                                  *
 **************************************************************/
#include <iostream>
#include <iomanip>
#include <cmath>
using namespace std; 

// 주요 함수 선언
void input(double& invest, double& rate, double& term);
void process(double invest, double rate, double term,
              double& multiplier, double& futureValue);
void output(double invest, double rate, double term, 
             double multiplier, double futureValue);
// 부가 함수 선언
double getInput(string message);
double findMultiplier(double rate, double period);
void printData(double invest, double rate, double term);
void printResult(double multiplier, double value);

int main()
{
  // 변수 선언
  double invest, rate, term;       // 입력 변수
  double multiplier, futureValue;  // 출력 변수
  // 주요 함수 호출
  input(invest, rate, term);
  process(invest, rate, term, multiplier, futureValue);
  output(invest, rate, term, multiplier, futureValue);
  return 0;
}
/**************************************************************
 * input 함수는 getInput 함수를 호출해서 3개의 입력을 받음    *
 * 참조로 전달을 사용해서 값을 main 함수로 전달               *
 * 함수가 종료되면 입력들이                                   *
 * invest, rate, term에 저장                                  *
 **************************************************************/
void input(double& invest, double& rate, double& term)
{
  invest = getInput("투자 금액을 입력하세요: ");
  rate = getInput("1년마다의 이율을 입력하세요: ");
  term = getInput("몇 년을 넣을지 입력하세요: ");
}
/***************************************************************
 * process 함수는 findMultiplier 함수를 사용해서 승수를 계산   *
 * 이어서 미래 가치를 계산                                     *
 * 참조로 전달로 받은 변수들로 값을 리턴                       *
 ***************************************************************/
void process(double invest, double rate, double term,
              double& multiplier, double& futureValue)
{
  multiplier = findMultiplier(rate, term);
  futureValue = multiplier * invest;  
}
 /**************************************************************
 * output 함수는 printData 함수를 호출해서 3개의 값을 출력     * 
 * printResult 함수를 호출해서 계산한 결과를 출력              * 
 **************************************************************/
void output(double invest, double rate, double term, 
             double multiplier, double futureValue)
{
  printData(invest, rate, term);
  printResult(multiplier, futureValue);
} 
/*************************************************************
 * getInput 함수는 사용자로부터 입력을 받는 함수             * 
 * 매개변수로 사용자에게 어떤 자료를 입력해달라고 요구할지,  * 
 * 메시지를 문자열 자료형의 객체로 전달받음                 * 
 * 그리고 입력이 양수인지 확인                               * 
 * 최종적으로 입력받은 값을 input 함수로 리턴               * 
 *************************************************************/
double getInput(string message)
{
  double input;
  do
  {
    cout << message;
    cin >> input;
  } while(input < 0.0);
  return input;
}
/**************************************************************************
 * findMultiplier 함수는 값으로 전달 메커니즘으로 이율, 기간을 전달받음   * 
 * 이어서 요소(factor)를 계산한 뒤,                                       * 
 * 이를 기간만큼 제곱해서 승수를 계산하고 리턴하는 함수                   *
 **************************************************************************/
double findMultiplier(double rate, double term)
{
  double factor = 1 + rate/100;
  return pow(factor, term);
} 
/**************************************************************
* printData 함수는 사용자로부터 입력받은                      * 
* 투자 금액(invest), 이율(rate), 기간(term)을 출력하는 함수   * 
* 이 함수는 부가 작용(화면에 출력)만 하는 void 함수           * 
***************************************************************/
void printData(double invest, double rate, double term)
{
  cout << endl << "투자 정보" << endl;
  cout << "투자 금액: " << fixed << setprecision(2) << invest << endl;
  cout << "이율: " << rate << fixed << setprecision(2);
  cout << "%(1년 기준)" << endl;
  cout << "기간: " << term << "년" << endl << endl;
}
/***************************************************************
 * printResult 함수는 프로그램의 최종적인 결과라고 할 수 있는  * 
 * 승수(multiplier)와 미래 가치(futureValue)를 출력            *
 * 이 함수는 부가 작용(화면에 출력)만 하는 void 함수           * 
 ***************************************************************/
void printResult(double multiplier, double futureValue)
{
  cout << "투자의 승수 = " << fixed << setprecision(8);
  cout << multiplier << endl;
  cout << "미래 가치 = " << fixed << setprecision(2);
  cout << futureValue << endl;
}