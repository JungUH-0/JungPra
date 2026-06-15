#include "product.h"
#include <iomanip>

// 정적 데이터 멤버 초기화
int Product::totalCount = 0;

// 생성자
Product::Product(std::string n, double p)
{
     assert(p >= 0); // 가격이 0보다 작을 수 없다는 불변 속성 검증
     name = n;
     price = p;
     totalCount++; // 생성 시 totalCount 증가
     std::cout << "제품 등록 완료: " << name
               << " 제품명: " << name
               << ", 가격: " << std::fixed << std::setprecision(0) << price
               << " 현재 총 제품 수: " << totalCount << std::endl;
}

// 소멸자
Product::~Product()
{
     totalCount--; // 소멸 시 totalCount 감소
     std::cout << "제품 삭제 완료: " << name << std::endl;
}

// 정적 멤버 함수
int Product::getTotalCount()
{
     return totalCount;
}

// printInfo
void Product::printInfo() const
{
     std::cout << "제품명: " << name
               << ", 가격: " << std::fixed << std::setprecision(0) << price << std::endl;
}