/*************************************************************
 * private 멤버 함수로 생성자를 도와주는                     * 
 * 헬퍼 함수(도우미 함수)를 정의                             *
 * 모든 처리는 생성자에서 하고                               *
 * 소멸자에서는 힙에 할당한 메모리 영역을 제거하고           *
 * 파일을 닫는 프로그램                                      * 
 *************************************************************/
#ifndef COURSE_H
#define COURSE_H
#include <iostream>
#include <fstream> 
using namespace std;

class Course
{
  private:
    int numOfStds;
    const char* inputFileName;
    ifstream inputFile;
    struct Student {int id; int score; char grade; 
                    double deviation;};
    Student* students;
    double averageScore;
    double standardDeviation;
    void getInput();
    void setGrades();
    void setAverage();
    void setDeviations();
    void printResult() const;

  public:
    Course(int numOfStds, const char* inputFileName);
    ~Course();
};
#endif