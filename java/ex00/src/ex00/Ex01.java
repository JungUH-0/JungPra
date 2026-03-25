package ex00;

import java.util.Scanner;

public class Ex01 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc= new Scanner(System.in);
		
		System.out.print("원화를 입력하세요(단위 원): " );
		int won= sc.nextInt();
		double a = won;
		double dol = a /1200;
		System.out.println(won+"원은 $"+dol+" 입니다.");
		sc.close();
	}

}
