// Console.cpp : 이 파일에는 'main' 함수가 포함됩니다. 거기서 프로그램 실행이 시작되고 종료됩니다.
//

#include "pch.h"
#include "framework.h"
#include "Console.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif


// 유일한 애플리케이션 개체입니다.

CWinApp theApp;

using namespace std;

int main()
{
    int nRetCode = 0;

    HMODULE hModule = ::GetModuleHandle(nullptr);

    if (hModule != nullptr)
    {
        // MFC를 초기화합니다. 초기화하지 못한 경우 오류를 인쇄합니다.
        if (!AfxWinInit(hModule, nullptr, ::GetCommandLine(), 0))
        {
            // TODO: 여기에 애플리케이션 동작을 코딩합니다.
            wprintf(L"심각한 오류: MFC 초기화 실패\n");
            nRetCode = 1;
        }
        else
        {
            // TODO: 여기에 애플리케이션 동작을 코딩합니다.
            //_tsetlocale(LC_ALL, _T("")); // 유니코드 한국어 출력에 필요
            //CString str1;
            //str1 = _T("안녕하세요."); // 문자열을 직접 대입한다.
            //CString str2(_T("오늘은")); // 문자열을 생성자 인자로 전달한다.
            //CString str3(str2); // CString 객체를 생성자 인자로 전달한다.
            //// CString 객체와 문자열을 붙인다.
            //CString str4 = str1 + _T(" ") + str2 + _T(" 즐거운 날입니다.");
            //_tprintf(_T("%s\n"), (LPCTSTR)str1);
            //_tprintf(_T("%s\n"), (LPCTSTR)str2);
            //_tprintf(_T("%s\n"), (LPCTSTR)str3);
            //_tprintf(_T("%s\n"), (LPCTSTR)str4);
            //// + = 연산자를 이용하여 기존 문자열에 새로운 문자열을 덧붙인다.
            //str4 += _T(" 하하하");
            //_tprintf(_T("%s\n"), (LPCTSTR)str4);
            //CString str;
            //str.Format(_T("x=%d, y=%d"), 100, 200);
            //MessageBox(NULL, str, _T("CString::Format() 연습"), MB_OK);
            // CString 객체는 물론이고 일반 문자열도 리스트에 추가할 수 있다.
            _tsetlocale(LC_ALL, _T("")); // 유니코드 한국어 출력에 필요
           const TCHAR* szFruits[] = {
                   _T("사과"), _T("딸기"), _T("포도"), _T("오렌지"), _T("자두")
            };

           CStringList list;// 리스트 객체 생성

           for (int i = 0; i < 5; i++)
               list.AddTail(szFruits[i]);

           // 리스트 맨 앞에서부터 순회하면서 데이터를 출력한다.
           POSITION pos = list.GetHeadPosition();
           while (pos != NULL) {
               CString str = list.GetNext(pos);
               _tprintf(_T("%s "), (LPCTSTR)str);
           }
           _tprintf(_T("\n"));
           // 리스트 맨 뒤에서부터 순회하면서 데이터를 출력한다.
           pos = list.GetTailPosition();
           while (pos != NULL) {
               CString str = list.GetPrev(pos);
               _tprintf(_T("%s "), (LPCTSTR)str);
           }
           _tprintf(_T("\n"));

           pos = list.Find(_T("포도")); // 데이터의 위치를 얻는다.
           list.InsertBefore(pos, _T("살구")); // 앞쪽에 데이터를 삽입한다.
           list.InsertAfter(pos, _T("바나나")); // 뒤쪽에 데이터를 삽입한다.
           list.RemoveAt(pos); // 데이터를 삭제한다.
           // 리스트 맨 앞에서부터 순회하면서 데이터를 출력한다.
           pos = list.GetHeadPosition();
           while (pos != NULL) {
               CString str = list.GetNext(pos);
               _tprintf(_T("%s "), (LPCTSTR)str);
           }
           _tprintf(_T("\n"));

        }
    }
    else
    {
        // TODO: 오류 코드를 필요에 따라 수정합니다.
        wprintf(L"심각한 오류: GetModuleHandle 실패\n");
        nRetCode = 1;
    }

    return nRetCode;
}
