#include <iostream>
#include <typeinfo> // 값의 타입을 알기위한 함수 호출
#include <limits>   //numric_limits 위해 필요
#include <bitset>   // bitset 쓰기위해
using namespace std;

int main()
{
     int num1, num2, num3, num4;
     char op1, op2, op3;

     // do
     // {

     // } while (true);
     // {
     // }
     // 첫번째 숫자
     while (true)
     {
          cout << "첫번째 숫자를 입력하세요 : ";

          if (cin >> num1)
          {
               // cout << "입력받은 정수는 " << num1;
               break;
          }
          else
          {
               cout << "정수 아님";
               cin.clear();
               cin.ignore(numeric_limits<streamsize>::max(), '\n'); // 위 헤더에 <limits> 불러오고 이 형식 유지
          }
     }
     // 첫번째 연산자
     while (true)
     {
          cout << "첫번째 연산자를 입력하세여(+, -, /, *) : ";
          cin >> op1;
          if (op1 == '+' || op1 == '-' || op1 == '*' || op1 == '/')
          {
               break;
          }
          else
          {
               cout << "연산자가 아닙니다";
               cin.clear();
               cin.ignore(numeric_limits<streamsize>::max(), '\n');
          }
     }

     // 두번째 숫자
     while (true)
     {
          cout << "두번째 숫자를 입력하세요 : ";

          if (cin >> num2)
          {
               // cout << "입력받은 정수는 " << num2;
               break;
          }
          else
          {
               cout << "정수 아님";
               cin.clear();
               cin.ignore(numeric_limits<streamsize>::max(), '\n');
          }
     }
     // 두번째 연산자
     while (true)
     {
          cout << "두번째 연산자를 입력하세여(+, -, /, *) : ";
          cin >> op2;
          if (op2 == '+' || op2 == '-' || op2 == '*' || op2 == '/')
          {
               break;
          }
          else
          {
               cout << "연산자가 아닙니다";
               cin.clear();
               cin.ignore(numeric_limits<streamsize>::max(), '\n');
          }
     }
     // 세번째 숫자
     while (true)
     {
          cout << "세번째 숫자를 입력하세요 : ";

          if (cin >> num3)
          {
               // cout << "입력받은 정수는 " << num3;
               break;
          }
          else
          {
               cout << "정수 아님";
               cin.clear();
               cin.ignore(numeric_limits<streamsize>::max(), '\n');
          }
     }
     // 세번째 연산자
     while (true)
     {
          cout << "세번째 연산자를 입력하세여(+, -, /, *) : ";
          cin >> op3;
          if (op3 == '+' || op3 == '-' || op3 == '*' || op3 == '/')
          {
               break;
          }
          else
          {
               cout << "연산자가 아닙니다";
               cin.clear();
               cin.ignore(numeric_limits<streamsize>::max(), '\n');
          }
     }
     // 네번째 숫자
     while (true)
     {
          cout << "네번째 숫자를 입력하세요 : ";

          if (cin >> num4)
          {
               // cout << "입력받은 정수는 " << num4;
               break;
          }
          else
          {
               cout << "정수 아님";
               cin.clear();
               cin.ignore(numeric_limits<streamsize>::max(), '\n');
          }
     }

     // cout << "num1\t" << num1 << endl
     //      << "num2\t" << num2 << endl
     //      << "num3\t" << num3 << endl
     //      << "num4\t" << num4 << endl;
     // cout << "op1\t" << op1 << endl
     //      << "op2\t" << op2 << endl
     //      << "op3\t" << op3 << endl;

     int result = 0;
     int tempNum = num1;
     char tempOp = '+';

     //  첫번째 계산
     if (op1 == '*' || op1 == '/')
     {
          if (op1 == '*')
               tempNum *= num2;
          else
               tempNum /= num2;
     }
     else
     {
          if (tempOp == '+')
               result += tempNum;
          else
               result -= tempNum;
          tempNum = num2;
          tempOp = op1;
     }
     //  두번째 계산
     if (op2 == '*' || op2 == '/')
     {
          if (op2 == '*')
               tempNum *= num3;
          else
               tempNum /= num3;
     }
     else
     {
          if (tempOp == '+')
               result += tempNum;
          else
               result -= tempNum;
          tempNum = num3;
          tempOp = op2;
     }
     //  세번째 계산
     if (op3 == '*' || op3 == '/')
     {
          if (op3 == '*')
               tempNum *= num4;
          else
               tempNum /= num4;
     }
     else
     {
          if (tempOp == '+')
               result += tempNum;
          else
               result -= tempNum;
          tempNum = num4;
          tempOp = op3;
     }
     if (tempOp == '+')
          result += tempNum;
     else
          result -= tempNum;

     cout << "Bin 결과 : \t" << bitset<16>(result) << endl;
     cout << "Dec 결과 : \t" << result << endl;
     cout << "Hex 결과 : \t" << showbase << hex << uppercase << result << endl;
     // cout << typeid(op1).name() << endl;
     return 0;
}