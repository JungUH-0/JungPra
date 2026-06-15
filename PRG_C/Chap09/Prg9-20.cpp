/********************************************************************
 * 인터페이스 파일에 선언된                                         *
 * 모든 함수를 정의하는                                             *
 * 인터페이스 파일                                                  *
 * 이전에 언급한 연산들을 구현                                      *
 ********************************************************************/
#include "matrix.h"

// 생성자: 힙에 메모리 영역을 잡음
Matrix::Matrix(int r, int c)
: rowSize(r), colSize(c)
{
  ptr  = new int*[rowSize];
  for(int i = 0; i < rowSize; i++)
  {
    ptr[i] = new int[colSize];
  }
}
// 소멸자: 힙에 있는 메모리 영역을 해제
Matrix::~Matrix()
{
  for(int i = 0; i < rowSize ; i++)
  {
    delete[] ptr[i];
  }
delete[] ptr;
}
// 행렬의 요소를 랜덤하게 초기화하는 함수
void Matrix::setup()
{
  for(int i = 0; i < rowSize; i++)
  {
    for(int j = 0; j < colSize; j++)
    {
      ptr[i][j] = rand() % 5 + 1;
    }
  }
}
// 두 행렬을 더하는 함수
void Matrix::add(const Matrix& second, Matrix& result) const
{
  assert(second.rowSize == rowSize && second.colSize == colSize);
  assert(result.rowSize == rowSize && result.colSize == colSize);
    
  for(int i = 0; i < rowSize ; i++)
  {
    for(int j = 0; j < second.colSize; j++)
    {
      result.ptr[i][j] = ptr[i][j] + second.ptr[i][j];
    }
  }
}
// 두 행렬을 빼는 함수
void Matrix::subtract(const Matrix& second, Matrix& result) const
{
  assert(second.rowSize == rowSize && second.colSize == colSize);
  assert(result.rowSize == rowSize && result.colSize == colSize);
  for(int i = 0; i < rowSize; i++)
  {
    for(int j = 0; j < second.colSize; j++)
    {
      result.ptr[i][j] = ptr[i][j] - second.ptr[i][j];
    }
  }
}
// 두 행렬을 곱하는 함수
void Matrix::multiply(const Matrix& second, Matrix& result) const
{
  assert(colSize == second.rowSize);
  assert(result.rowSize = rowSize);
  assert(result.colSize = second.colSize);
  for(int i = 0; i < rowSize; i++)
  {
    for(int j = 0; j < second.colSize; j++)
    {
      result.ptr[i][j] = 0;
      for(int k = 0 ; k < colSize; k++)
      {
        result.ptr[i][j] += ptr[i][k] * second.ptr[k][j];
      }
    }
  }
}
// 행렬의 요소를 출력하는 함수
void Matrix::print() const
{
  for(int i = 0 ; i < rowSize; i++)
  {
    for(int j = 0; j < colSize; j++)
    {
      cout << setw(5) << ptr[i][j];
    }
    cout << endl;
  }
  cout << endl;
}