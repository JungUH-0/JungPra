/**************************************************************
 * [프로그램 8-10]에서 본                                     *
 * 인터페이스 파일의 구현 파일                                *
 **************************************************************/
#include "student.h"

// 기본 생성자
Student::Student()
{
}
// 매개변수가 있는 생성자
Student::Student(string nm, int sc)
    : name(nm), score(sc)
{
  char temp[] = {'F', 'F', 'F', 'F', 'F', 'F', 'D', 'C', 'B', 'A', 'A'};
  grade = temp[score / 10];
}
// 소멸자
Student::~Student()
{
}
// 멤버 함수 출력
void Student::print()
{
  cout << setw(12) << left << name;
  cout << setw(8) << right << score;
  cout << setw(8) << right << grade << endl;
}