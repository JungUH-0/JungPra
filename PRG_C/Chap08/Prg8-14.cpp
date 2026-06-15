/*********************************************************
 * 파일에서 0~9 범위의 정수를 읽어 들이고                * 
 * 빈도 배열과 히스토그램을                              *      
 * 만들어서 출력하는 프로그램                            *                                        
 *********************************************************/
#include <iostream>
#include <fstream>
#include <iomanip>
using namespace std;

int main()
{
  // 선언과 초기화
  const int CAPACITY = 10;
  int frequencies[CAPACITY] = {0};
  ifstream integerFile;
  // 정수 파일 열기
  integerFile.open("integerFile.dat");
  if(!integerFile)
  {
    cout << "숫자 파일을 열 수 없습니다." << endl;
    cout << "프로그램을 중단합니다.";
   return 0;
  }
  // 파일에서 정수 읽어 들이고, 빈도 배열 생성
  int data;
  int size = 0;
  while(integerFile >> data )
  {
    if(data >= 0 && data <= 9)
    {
      size++;
      frequencies[data]++;
    }
  }
  // 정수 파일 닫기
  integerFile.close();
  // 빈도 배열과 히스토그램 출력
  cout << "파일 안에 " << size << "개의 유효한 데이터가 있습니다." << endl;

  for(int i = 0; i < 10 ; i++)
 {
   cout << setw(3) << i << " ";

   for(int f = 1; f <= frequencies[i] ; f++)
   {
     cout << '*' ;
   }
   cout << " " << frequencies[i] << endl;
   }
  return 0;  
}