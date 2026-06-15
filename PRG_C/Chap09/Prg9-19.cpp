/*********************************************************************************
* Matrix 클래스의 인터페이스 파일                                                *
* 행렬의 크기와 힙에 생성할 행렬을                                               *
* 가리킬 포인터만 private 멤버로 선언                                            *
* 이외의 모든 멤버 함수는 public 멤버로 선언                                     *
* 생성자는 힙에 배열을 생성하고, 소멸자는 힙에서 배열을 제거                     *
* setup 멤버 함수는 행렬을 랜덤한 값으로 초기화                                  *
* 이외에도 addition, subtraction,                                                *
* multiplication, print 멤버 함수를 선언                                         *
**********************************************************************************/
#include <iostream>
#ifndef MATRIX_H
#define MATRIX_H
#include <cmath>
#include <cstdlib>
#include <iomanip> 
#include <cassert> 
using namespace std;

// Matrix 클래스 정의
class Matrix  
{  
  private:  
    int rowSize;                    
    int colSize;  
    int** ptr;
  public:                                                                                                                                         
    Matrix(int rowSize, int colSize);               
    ~Matrix();
    void setup();
    void add(const Matrix& second, Matrix& result) const;
    void subtract(const Matrix& second, Matrix& result) const;
    void multiply(const Matrix& second, Matrix& result) const;
    void print() const;
};   
#endif