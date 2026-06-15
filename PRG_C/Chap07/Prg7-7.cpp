/**************************************************************
 * Circle 클래스의                                            *
 * 데이터 멤버와 멤버 함수의 선언을                           *
 * 제공하는 인터페이스 파일                                   *
 * 구현 파일과 애플리케이션 파일에서 읽어 들여 사용           *
 **************************************************************/
#ifndef CIRCLE_H
#define CIRCLE_H
#include <iostream>
#include <cassert>
#include "circle.h"
using namespace std;
// 클래스 정의
class Circle
{
private:
  double radius;

public:
  Circle(double radius);         // 매개변수가 있는 생성자
  Circle();                      // 기본 생성자
  Circle(const Circle &circle);  // 복사 생성자
  ~Circle();                     // 소멸자
  void setRadius(double radius); // 설정자
  double getRadius() const;      // 접근자
  double getArea() const;        // 접근자
  double getPerimeter() const;   // 접근자
};
#endif