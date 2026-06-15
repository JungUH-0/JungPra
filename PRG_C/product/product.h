#ifndef PRODUCT_H
#define PRODUCT_H

#include <iostream>
#include <string>
#include <cassert>

class Product
{
private:
     std::string name;
     double price;
     static int totalCount;

public:
     Product(std::string n, double p);
     ~Product();

     Product(const Product &other) = delete;

     static int getTotalCount();
     void printInfo() const;
};

#endif