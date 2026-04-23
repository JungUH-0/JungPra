/***********************************************************
 * 입력, 처리, 출력 함수들을 사용해서                      *
 * 학생 점수를 기반으로 등급을 계산하는 프로그램           *
 ***********************************************************/
#include <iostream>
using namespace std;

// 함수 선언
int getScore();
char findGrade(int score);
void printResult(int score, char grade);

int main()  
{
  // 선언
  int score;
  char grade;
  // 함수 호출
  score = getScore();
  grade = findGrade(score);
  printResult(score, grade);
  return 0;
}
/**************************************************************
 * getScore 함수는 부가 작용을 갖는 입력 함수                 *
 * 사용자로부터 점수를 입력 받고, 이를 main 함수에 값으로 리턴*
 * 지역 변수 score를 리턴하는 형태                            *
 * 함수 내부에서는 점수가 0~100 사이의 정수인지               *
 * 확인하는 유효성 검사도 하고 있음                           *
 **************************************************************/
int getScore()
{
  int score;  // 지역 선언
  do 
  {
    cout << "점수를 입력하세요(0~100): ";
    cin >> score;
  } while(score < 0 || score > 100);
  return score;
}
/*************************************************************************
 * findGrade 함수는 값으로 전달 메커니즘으로                             *
 * 전달된 매개변수 score의 값을                                          *
 * 기반으로 등급(A, B, C, D, F)을 계산하고,                              *
 * 등급을 값으로 리턴하는 함수                                           *
 * if-else 조건문을 사용했는데, switch 조건문으로도 쉽게 구현할 수 있음  *
 *                                                                       *
 *************************************************************************/
char findGrade(int score)
{
  char grade;  // 지역 선언
  if(score >= 90)
  {
    grade = 'A';
  }
  else if(score >= 80)
  {
    grade = 'B';
  }
  else if(score >= 70)
  {
    grade = 'C';
  }
  else if(score >= 60)
  {
    grade = 'D';
  }
  else 
  {
   grade = 'F';
  }
  return grade;
}
/**************************************************************
 * 점수와 점수에 맞는 등급을 출력하는 함수                    *
 **************************************************************/
void printResult(int score, char grade)
{
  cout << endl << "시험 결과" << endl;
  cout << "점수 = " << score << "/100" << endl;
  cout << "등급 = " << grade << endl;
}