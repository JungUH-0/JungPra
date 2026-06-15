/*************************************************************
 * 주어진 범위의 랜덤한 숫자를                               *
 * 생성하는 클래스를                                         *
 * 선언, 정의하고 사용하는 프로그램                          *
 *************************************************************/
#include <iostream>
#include <cstdlib>
#include <ctime>
using namespace std;

/**************************************************************
 * RandoInteger 클래스의 정의                                 *
 *(데이터 멤버 선언과 멤버 함수 정의)                        *
 **************************************************************/
class RandomInteger
{
  private:
    int low;       // 데이터 멤버
    int high;      // 데이터 멤버    
    int value;     // 데이터 멤버
  public:
    RandomInteger(int low, int high);  // 생성자
    ~RandomInteger();  // 소멸자
    // 합성 복사 생성자의 생성 막기
    RandomInteger(const RandomInteger& random) = delete;  
    void print() const;   // 접근자 멤버 함수
};
/**************************************************************
 * RandomInteger 클래스의                                     *
 * 생성자, 소멸자, 접근자 멤버 함수 정의                      *
 **************************************************************/
// 생성자
RandomInteger::RandomInteger(int lw, int hh) 
:low(lw), high(hh)    
{
  srand(time(0));
  int temp = rand();
  value = temp %(high - low + 1) + low;
}
// 소멸자
RandomInteger::~RandomInteger()
{
}
// 접근자 멤버 함수
void RandomInteger::print() const
{
  cout << value << endl;
}
/**************************************************************
 * 랜덤 숫자 객체를 인스터스화 하고 값(랜덤한 숫자)을         *
 * 출력하는 애플리케이션                                      *
 **************************************************************/
int main()
{
  // 100~200 범위의 랜덤 숫자 생성
  RandomInteger r1(100, 200);
  cout << "100~200 사이의 랜덤한 숫자: ";
  r1.print();
  // 400~600 범위의 랜덤 숫자 생성
  RandomInteger r2(400, 600);
  cout << "400~600 사이의 랜덤한 숫자: ";
  r2.print();
  // 1500~2000 범위의 랜덤 숫자 생성 
  RandomInteger r3(1500, 2000);
  cout << "1500~2000 사이의 랜덤한 숫자: ";
  r3.print();
  return 0;
}