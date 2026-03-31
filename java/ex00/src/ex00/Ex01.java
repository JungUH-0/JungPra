package ex00;

import java.util.Scanner;

public class Ex01 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc= new Scanner(System.in);// scanner 객체 생성
		
		System.out.print("원화를 입력하세요(단위 원): " );
		int won= sc.nextInt();//Scanner로 값 입력 받는다.
		double a = won;
		double dol = a /1490;
		System.out.println(won+"원은 $"+dol+" 입니다.");//결과 화면 출력
		System.out.printf("%d원은 $ %.2f 입니다.",won,dol);
		
		sc.close();
	}

}
