/**************************************************************
 * 학생 점수를 3개 입력 받고                                  *
 * 최소값과 최대값을 기반으로 평균을 구해서                   *
 * 학생의 성적을 찾는 프로그램                                *
 **************************************************************/ 
#include <iostream>
using namespace std;

int main()
{
  // 변수 선언
  int score1, score2, score3, maxScore, minScore, score;
  // 입력받기
  cout << "첫 번째 점수 입력: ";
  cin >> score1;
  cout << "두 번째 점수 입력: ";
  cin >> score2;
  cout << "세 번째 점수 입력: ";
  cin >> score3;
  // 가장 큰 점수 찾기
  if(score1 > score2 && score1 > score3)
  {
    maxScore = score1;
  }
  else if(score2 > score1 && score2 > score3)
  {
    maxScore = score2;
  }
  else
  {
    maxScore = score3;
  }
  // 가장 작은 점수 찾기
  if(score1 < score2 && score1 < score3)
  {
    minScore = score1;
  }
  else if(score2 < score1 && score2 <= score3)
  {
    minScore = score2;
  }
  else
  {
    minScore = score3;
  }
  // 학생 성적을 구하고 올림하기(홀수일 때만 올림)  
  int temp = maxScore + minScore;
  if(temp % 2 == 1) 
  {
    temp += 1;
  }
  score = temp / 2;
  // 결과 출력
  cout << "입력한 점수 = " << score1 << " " << score2 << " " << score3 << endl;
  cout << "최소 점수와 최대 점수 = ";
  cout << minScore << " " << maxScore << endl;
  cout << "학생 성적 = " << score;
  return 0;      
} 