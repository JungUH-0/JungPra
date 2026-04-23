/***********************************************************
 * EOF 제어 while 반복문을 사용해서 파일에 저장된          *
 * 숫자들의 합을 구하는 프로그램                           *
 ***********************************************************/
#include <iostream>
#include <fstream>
using namespace std;

int main()  
{
  // 선언
  int sum = 0;
  int num;
  ifstream infile;
  // 파일 열기
  infile.open("numbers.dat");
  // While 반복문
  if (infile.fail()) {
        std::cerr << "오류: 파일을 찾을 수 없거나 열 수 없습니다." << std::endl;
        return 1;
    }
  std::cout << "파일 열기 성공! 데이터를 읽기 시작합니다..." << std::endl;
  while(infile >> num)
  {
    sum = sum + num;
  } 
  // 결과 출력
  cout << "합 = " << sum;
  infile.close();
  return 0; 
}