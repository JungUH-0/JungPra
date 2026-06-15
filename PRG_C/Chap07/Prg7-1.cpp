/*************************************************************
 * 객체 지향 프로그래밍에서 클래스를 사용하는 프로그램       *
 *************************************************************/
#include <iostream>
using namespace std;

/************************************************************
 * 클래스 정의                                              *
 * 데이터 멤버와 멤버 함수를 선언                           *
 ************************************************************/
class Circle
{
private:
  double radius;

public:
  double getRadius() const;
  double getArea() const;
  double getPerimeter() const;
  void setRadius(double value);
};
/**************************************************************
 * 멤버 함수 정의 부분                                        *
 * 멤버 함수들은 클래스 선언 부분에서 선언                    *
 **************************************************************/
// getRadius 멤버 함수의 정의
double Circle::getRadius() const
{
  return radius;
}
// getArea 멤버 함수의 정의
double Circle::getArea() const
{
  const double PI = 3.14;
  return (PI * radius * radius);
}
// getPerimeter 멤버 함수의 정의
double Circle::getPerimeter() const
{
  const double PI = 3.14;
  return (2 * PI * radius);
}
// setRadius 멤버 함수의 정의
void Circle::setRadius(double value)
{
  radius = value;
}
/********************************************************
 * 애플리케이션 부분                                    *
 * 클래스를 인스턴스화해서 객체를 만들고 활용           *
 *********************************************************/
int main()
{
  // 첫 번째 circle 객체를 만들고 멤버 함수 호출
  cout << "Circle 1" << endl;
  Circle circle1;
  circle1.setRadius(10.0);
  cout << "반지름: " << circle1.getRadius() << endl;
  cout << "넓이: " << circle1.getArea() << endl;
  cout << "둘레: " << circle1.getPerimeter() << endl
       << endl;
  // 두 번째 circle 객체를 만들고 멤버 함수 호출
  cout << "Circle 2" << endl;
  Circle circle2;
  circle2.setRadius(20.0);
  cout << "반지름: " << circle2.getRadius() << endl;
  cout << "넓이: " << circle2.getArea() << endl;
  cout << "둘레: " << circle2.getPerimeter();
  return 0;
}