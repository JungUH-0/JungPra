#include <iostream>
using namespace std;
int main()
{
     string name;
     int age;
     string vision;
     int goal;
     int now;
     double per;
     bool ing;

     cout << "이름을 입력하세요 : ";
     cin >> name;
     cout << "나이를 입력하세요 : ";
     cin >> age;
     cout << "나의 비전(한 단어)을 입력하세요 : ";
     cin >> vision;
     cout << "목표 수치를 입력하세요(0~100) : ";
     cin >> goal;
     cout << "현재 진행 수치를 입력하세요(0~100) : ";
     cin >> now;
     cout << "비전 활성화 여부 (1: 시작, 0: 대기)";
     cin >> ing;
     per = double(now) / double(goal) * 100;

     cout << "--- 나의 성자 비전 리포트 ---" << endl;
     cout << "성함 : " << name << "(" << age << "세)" << endl;
     cout << "목표 비전 : " << vision << endl;
     cout << "진행도 : " << now << "/" << vision << endl;
     cout << "현재 달성률 : " << per << "%" << endl;
     if (ing == 0)
     {
          cout << "운영 상태 : 준비 중" << endl;
     }
     else
     {
          cout << "운영 상태 : 진행 중" << endl;
     }
     cout << "-------------------------------------";
}