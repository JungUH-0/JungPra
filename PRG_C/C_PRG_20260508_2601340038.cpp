#include <iostream>
using namespace std;

// 1. Call by Value — 값 복사
void byValue(int x)
{
    x = 100;
}
// 2. Call by Reference — 참조
void byReference(int &x)
{
    x = 100;
}
// 3. Call by Pointer — 포인터
void byPointer(int *x)
{
    *x = 100;
}
void gugudan()
{
    for (int j = 1; j < 10; j++)
    {
        for (int i = 2; i < 10; i++)
        {
            int a = i * j;
            cout << i << "*" << j << "=" << a << "\t";
        }
        cout << "\n";
    }
}

int main()
{
    int a = 10, b = 10, c = 10;

    byValue(a);     // a = 10  (변화 없음)
    byReference(b); // b = 100 (원본 변경)
    byPointer(&c);  // c = 100 (원본 변경)

    cout << "Call by Value     : " << a << endl;
    cout << "Call by Reference : " << b << endl;
    cout << "Call by Pointer   : " << c << endl;

    gugudan();
}
