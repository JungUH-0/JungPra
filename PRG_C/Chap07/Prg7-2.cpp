/**************************************************************
 * 객체 지향 프로그래밍에서 클래스를 사용하는 예              *
 **************************************************************/
#include <iostream>
using namespace std;

/**************************************************************
 * 클래스 정의                                                *
 * 매개변수 생성자, 기본 생성자,                              * 
 * 복사 생성자, 소멸자, 멤버 함수를 선언                      *
***************************************************************/
class Circle
{
  private: 
   double radius;                                                               
  public:
   Circle(double radius);           // 매개변수가 있는 생성자
   Circle();                        // 기본 생성자
   ~Circle();                       // 소멸자
   Circle(const Circle& circle);    // 복사 생성자
   void setRadius(double radius);   // 설정자
   double getRadius() const;        // 접근자
   double getArea() const;          // 접근자             
  double getPerimeter() const;       // 접근자
};
/*************************************************************
 * 멤버 함수 정의                                            *
 * 매개변수가 있는 생성자, 기본 생성자,                      * 
 * 복사 생성자, 소멸자, 멤버 함수를 정의                     *
 *************************************************************/
// 매개변수 생성자의 정의
Circle::Circle(double rds)
: radius(rds)
{
  cout << "매개변수가 있는 생성자가 호출되었습니다." << endl;
}
// 기본 생성자의 정의
Circle::Circle()
: radius(0.0)
{
  cout << "기본 생성자가 호출되었습니다." << endl;
}
// 복사 생성자의 정의
Circle::Circle(const Circle& circle)
: radius(circle.radius)
{
  cout << "복사 생성자가 호출되었습니다." << endl;
}
// 소멸자의 정의
Circle::~Circle()
{
  cout << "소멸자가 호출되었습니다." << radius;
  cout << endl;
}
// setRadius 멤버 함수의 정의
void Circle::setRadius(double value)
{
  radius = value;
}
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
  const double PI  = 3.14; 
  return (2 * PI * radius);
}
/***************************************************************
 * 애플리케이션                                                *
 * Circle 클래스의 객체를 3개(circle, circle2, circle3) 만들고 * 
 * 멤버 함수 호출                                              *
 ***************************************************************/
int main()
{
  // circle1 인스턴스화 후에 멤버 함수 호출
  Circle circle1(5.2);
  cout << "반지름: " << circle1.getRadius() << endl;
  cout << "넓이: " << circle1.getArea() << endl;
  cout << "둘레: " << circle1.getPerimeter() << endl << endl;
  // circle2 인스턴스화 후에 멤버 함수 호출
  Circle circle2(circle1); 
  cout << "반지름: " << circle2.getRadius() << endl;
  cout << "넓이: " <<  circle2.getArea() << endl;
  cout << "둘레: " << circle2.getPerimeter() << endl << endl;
  // circle3 인스턴스화 후에 멤버 함수 호출
  Circle circle3; 
  cout << "반지름: " << circle3.getRadius() << endl;
  cout << "넓이: " <<  circle3.getArea() << endl;
  cout << "둘레: " << circle3.getPerimeter() << endl << endl;
  // 소멸자 호출 시점
  return 0;
}