/************************************************************
 * 리스트의 크기를 처음부터 정했을 때                       *  
 * 리스트 내부 숫자의 합과 곱을 구하는 프로그램             *
 ************************************************************/
#include <iostream>
#include <iomanip>
using namespace std; 
 
int main()
{
  // 변수 선언
  int size;
  long double number;
  long double sum, product;
  // 입력받고 유효성 검사
  do 
  {
    cout << "입력할 숫자의 수를 음수가 아닌 정수로 입력하세요: " ;
    cin >> size;
  } while(size < 0);
  // 초기화
  sum = 0; 
  product = 1;
  // 처리
  for(int i = 1; i <= size; i++)
  {
    cout << "다음 숫자를 입력하세요: ";
    cin >> number; 
    sum += number;
    product *= number;
  }
  // 출력
  cout << fixed << setprecision(2);
  cout << "합 =  " << sum << endl;  
  cout << "곱 =  " << product;  
  return 0;   
}