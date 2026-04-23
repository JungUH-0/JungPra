/*************************************************************
 * 여러 방향 조건 분기를 사용해서 학점을 찾는 프로그램       *
 *************************************************************/
 #include <iostream>
using namespace std;

int main()  
{
  // 변수 선언
  int score;
  char grade;
  // 입력받기
  cout << "0~100점 사이의 점수 입력: ";
  cin >> score;
  // if-else 조건문을 사용한 여러 방향 조건 분기
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
  // 출력
  cout << "최종 학점 = " << grade;  
  return 0; 
} // main 함수 종료