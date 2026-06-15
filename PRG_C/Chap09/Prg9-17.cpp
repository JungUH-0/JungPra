/**************************************************************
 * 모든 private 멤버 함수와                                   *
 * public 멤버 함수를 정의하는 구현 파일                      *
 **************************************************************/
#include "course.h"
#include <iomanip>
#include <cmath> 
    
/**************************************************************
 * 생성자에서는 파일을 열고,                                  *
 * 힙 배열을 할당한 뒤                                        *
 * 여러 헬퍼 함수를 활용                                      *
 * 배열을 초기화한 뒤                                         *
 * 등급, 평균, 표준 편차를                                    *
 * 구하고 출력하는 프로그램                                   *
 **************************************************************/
Course::Course(int num, const char* ifn)
:numOfStds(num), inputFileName(ifn)
{
  inputFile.open(inputFileName);
  students = new Student[numOfStds];
  getInput();
  setGrades();
  setAverage();
  setDeviations();
  printResult();
}
/**************************************************************
 * 소멸자에서는 포인터를 사용해서                             *
 * 힙에 생성한 배열을 제거하고,                               *
 * 생성자에서 열었던 파일을 닫음                              *
 **************************************************************/
Course::~Course()
{
  delete[] students;
  inputFile.close();
}
/**************************************************************
 * getInput 함수는 입력 파일에서                              *
 * 학생들의 학번과 성적을 읽어 들임                           *
 **************************************************************/
void Course::getInput()
{
  for(int i = 0; i < numOfStds; i++)
  {
    inputFile >> students[i].id;
    inputFile >> students[i].score;
  }
}
/**************************************************************
 * setGrades 함수는 배열과 학생들의 성적을 기반으로           *
 * 학생들의 등급을 계산                                       *
 **************************************************************/
void Course::setGrades()
{
  char charGrades[] = 
                  {'F', 'F',  'F' ,  'F' , 'F' , 'F', 'D' , 'C' , 'B' , 'A' , 'A'};
  for(int i = 0; i < numOfStds; i++)
  {
    int index = students[i].score / 10;
    students[i].grade = charGrades[index];
  }
}
/**************************************************************
 * setAverage 함수는 배열 내부에 있는 학생들의 성적을         *
 * 기반으로 평균을 계산                                       *
 **************************************************************/
void Course::setAverage()
{
  int sum = 0;
  for(int i = 0; i < numOfStds; i++)
  {
    sum += students[i].score;
  }
  averageScore = static_cast<double>(sum) / numOfStds;
}
/**************************************************************
 * setDeviations 함수는 학생들의 점수와 평균을                *
 * 기반으로 표준 편차를 계산                                  *
 **************************************************************/
void Course::setDeviations()
{
  standardDeviation = 0.0;
  for(int i = 0; i < numOfStds; i++)
  {
    students[i].deviation = students[i].score - averageScore;
    standardDeviation += pow(students[i].deviation , 2); 
  }
  standardDeviation = sqrt(standardDeviation) / numOfStds;
}
/**************************************************************
 * printResult 함수에서는                                     *
 * 모든 정보를 출력                                           *
 **************************************************************/
void Course::printResult() const
{
  cout << endl;
  cout << " ID 점수 등급 편차" << endl;
  cout << "--------    -----      -----           ---------" << endl;
  for(int i = 0; i < numOfStds ; i++)
  {
    cout << setw(4) << noshowpoint << noshowpos;
    cout << right << students[i].id;
    cout << setw(14) << noshowpoint << noshowpos; 
    cout << right << students[i].score;
    cout << setw(10) << right << students[i].grade;
    cout << fixed << setw(20) << right << setprecision(2);
    cout << showpoint << showpos;
    cout << students[i].deviation << endl;
  }
  cout << "평균 점수: " << fixed << setw(4);
  cout << setprecision(2) << averageScore << endl;
  cout << "표준 편차: " << standardDeviation;
}