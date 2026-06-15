/*************************************************************
 * Student 클래스의 인터페이스 파일                          *
 * 3개의 private 데이터 멤버와 4개의 public 멤버 함수를 가짐 *
 *************************************************************/
#ifndef STUDENT_H
#define STUDENT_H
#include <iostream>
#include <string>
#include <iomanip>
using namespace std;

class Student
{
  private: 
    string name;
    int score;
    char grade;
  public:
    Student();
    Student(string name, int score);
    ~Student();
    void print();  
};
#endif