/**************************************************************
 * 객체를 인스턴스화하고                                      *
 * 객체의 멤버 함수를 호출해서 처리하는 애플리케이션 파일     *
 * 이 파일을 컴파일 하려면 인터페이스 파일을 읽어 들여야 함   *
 **************************************************************/
# include "circle.h"
int main()
{
  // 첫 번째 객체를 인스턴스화하고 멤버 함수를 호출
  Circle circle1(5.2);
  cout << "반지름: " << circle1.getRadius() << endl;
  cout << "넓이: " << circle1.getArea() << endl;
  cout << "둘레: " << circle1.getPerimeter() << endl;
  cout << endl;
  // 두 번째 객체를 인스턴스화하고 멤버 함수를 호출
  Circle circle2(circle1); 
  cout << "반지름: " << circle2.getRadius() << endl;
  cout << "넓이: " << circle2.getArea() << endl;
  cout << "둘레: " << circle2.getPerimeter() << endl;
  cout << endl;
  // 세 번째 객체를 인스턴스화하고 멤버 함수를 호출
  Circle circle3; 
  cout << "반지름: " << circle3.getRadius() << endl;
  cout << "넓이: " <<  circle3.getArea() << endl;
  cout << "둘레: " << circle3.getPerimeter() << endl;
  cout << endl;
  return 0;
}