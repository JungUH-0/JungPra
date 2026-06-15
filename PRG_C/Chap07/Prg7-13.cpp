/**************************************************************
 * Time 클래스의 인터페이스 파일                              *
 **************************************************************/
#include <iostream>
using namespace std;

#ifndef TIME_H
#define TIME_H

class Time  
{  
  private:  
    int hours;  
    int minutes;
    int seconds;
  public:                                                                                                                                       
    Time(int hours, int minutes, int seconds);               
    Time();                                                              
    ~Time();                                                         
    void print() const;               
    void tick();                            
  
  private:
    void normalize();  // 보조 함수             
};
#endif