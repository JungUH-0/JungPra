/*********************************************************************
 * Matrix 클래스의 객체를 몇 개 만들고                               *
 * 연산을 테스트하는 프로그램                                        *
 *********************************************************************/
#include "matrix.h"

int main()
{
  // matrix1 인스턴스화
  cout << "matrix1" << endl;
  Matrix matrix1(3, 4);
  matrix1.setup();
  matrix1.print();
  // matrix2 인스턴스화
  cout << "matrix2" << endl;
  Matrix matrix2(3, 4);
  matrix2.setup();
  matrix2.print();
  // matrix3 인스턴스화
  cout << "matrix3" << endl;
  Matrix matrix3(4, 2);
  matrix3.setup();
  matrix3.print();
  // matrix1 + matrix2를 구하고 결과 출력
  cout << "matrix1 + matrix2의 결과" << endl;
  Matrix addResult(3, 4);
  matrix1.add(matrix2, addResult);
  addResult.print();
 // matrix1 - matrix2를 구하고 결과 출력  
  cout << "matrix1 - matrix2의 결과" << endl;
  Matrix subResult(3, 4);
  matrix1.subtract(matrix2, subResult);
  subResult.print();
  // matrix1 - matrix2를 구하고 결과 출력
  cout << "matrix1 * matrix3의 결과" << endl;
  Matrix mulResult(3, 2);
  matrix1.multiply(matrix3, mulResult);
  mulResult.print();
  return 0;
}