#include <iostream>
#include <vector>
#include <string>
#include <limits> // 오버플로우 체크용
#include <bitset> // 2진수 변환용
#include <iomanip> // 16진수 변환용
 
using namespace std;
 
// 오버플로우/언더플로우 체크 함수
bool is_safe(long long a, char op, long long b) {
    if (op == '+') return (b > 0 && a > LLONG_MAX - b) || (b < 0 && a < LLONG_MIN - b) ? false : true;
    if (op == '-') return (b > 0 && a < LLONG_MIN + b) || (b < 0 && a > LLONG_MAX + b) ? false : true;
    if (op == '*') {
        if (a > 0 && b > 0 && a > LLONG_MAX / b) return false;
        if (a > 0 && b < 0 && b < LLONG_MIN / a) return false;
        if (a < 0 && b > 0 && a < LLONG_MIN / b) return false;
        if (a < 0 && b < 0 && (a == -1 || b == -1 ? false : a < LLONG_MAX / b)) return false;
    }
    return true;
}
 
int main() {
    vector<long long> nums(4);
    vector<char> ops(3);
 
    // 1. 입력 단계
    string labels[] = {"첫번째", "두번째", "세번째", "네번째"};
    for (int i = 0; i < 4; ++i) {
        cout << labels[i] << " 숫자를 입력하세요 : ";
        cin >> nums[i];
        if (i < 3) {
            cout << labels[i] << " 연산자를 입력하세요 : ";
            cin >> ops[i];
        }
    }
 
    // 2. 우선순위 적용 계산 (곱셈, 나눗셈 먼저)
    for (int i = 0; i < ops.size(); ) {
        if (ops[i] == '*' || ops[i] == '/') {
            if (!is_safe(nums[i], ops[i], nums[i+1])) {
                cout << "오버플로우/언더플로우 발생!" << endl;
                return 0;
            }
            if (ops[i] == '*') nums[i] = nums[i] * nums[i + 1];
            else nums[i] = nums[i] / nums[i + 1];
 
            nums.erase(nums.begin() + i + 1);
            ops.erase(ops.begin() + i);
        } else {
            i++;
        }
    }
 
    // 3. 나머지 계산 (덧셈, 뺄셈)
    long long result = nums[0];
    for (int i = 0; i < ops.size(); ++i) {
        if (!is_safe(result, ops[i], nums[i+1])) {
            cout << "오버플로우/언더플로우 발생!" << endl;
            return 0;
        }
        if (ops[i] == '+') result += nums[i + 1];
        else result -= nums[i + 1];
    }
 
    // 4. 결과 출력 (2진수, 10진수, 16진수)
    cout << "\n[ 결과 ]" << endl;
    cout << "Bin : " << bitset<16>(result) << " (하위 16비트 기준)" << endl;
    cout << "Dec : " << result << endl;
    cout << "Hex : 0x" << uppercase << hex << result << endl;
 
    return 0;
}