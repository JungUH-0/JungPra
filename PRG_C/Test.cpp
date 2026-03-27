#include <iostream>
using namespace std;

int main(){
     // Variable Declaration 
int x;
int y; 
// First assignment
cout << "Return value of assignment expression:" << (x = 15) << endl; // x= 15 저부분에서 x= 생략 되고 15만 나타나며 x는 15값을 가져간다 
cout << "Value of variable x:" << x << endl;
// Second assignment
cout << "Return value of assignment expression:" << (y = 7) << endl; 
cout << "Value of variable y:" << y;
return 0;

}