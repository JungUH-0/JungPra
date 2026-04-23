/*************************************************************
 * 알파벳의 개수를 세고,                                     * 
 * 소문자를 모두 대문자로 변경하는 프로그램                  *
 *************************************************************/
#include <iostream>
#include <cctype>
using namespace std;

int main()
{
  // 선언
  char ch;
  int count = 0;
  // 글자 입력받고 처리
  while(cin >> noskipws >> ch)
  {
    if(isalpha(ch))
    {
     count++;
    }
    ch = toupper(ch);
    cout << ch;
  }
  // 글자 개수 출력
  cout << "알파벳 문자의 개수 = " << count; 
  return 0;      
}