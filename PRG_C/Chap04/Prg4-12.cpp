/*************************************************************
 * switch 조건을 사용해서 점수를 기반으로 학점 출력하기      *
 *************************************************************/
 #include <iostream>
using namespace std;

int main()  
{
  // 변수 선언
  int score;
  char grade;
  // 입력받기
  cout << "0~100점 사이의 점수를 입력하세요: ";
  cin >> score;
  // 의사 결정
  switch(score / 10)
  {
    case 10: grade = 'A';
             break;        
    case 9 : grade = 'A';
             break;          
    case 8 : grade = 'B';
             break;    
    case 7 : grade = 'C';
             break;      
    case 6 : grade = 'D';
             break;          
    default: grade = 'F';
  } // switch 구문 종료
  // 출력
  cout << "Score: " << score << endl;
  cout << "Grade: " << grade << endl;
  return 0;
}