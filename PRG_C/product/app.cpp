#include "product.h"

int main()
{
     std::cout << "초기 제품 수: " << Product::getTotalCount() << std::endl;

     Product p1("노트북", 1500000);
     p1.printInfo();

     std::cout << "현재 총 제품 수: " << Product::getTotalCount() << std::endl
               << std::endl;

     std::cout << "--- 블록 진입 ---" << std::endl;
     {
          Product p2("마우스", 30000);
          p2.printInfo();

          std::cout << "블록 내부 제품 수: " << p2.getTotalCount() << std::endl;
          std::cout << "--- 블록 탈출 시도 ---" << std::endl;
     } // p2 소멸자 자동 호출

     std::cout << std::endl
               << "블록 탈출 후 총 제품 수: " << Product::getTotalCount() << std::endl;

     return 0;
}