package ex00;

import java.util.Scanner;

public class Ex03 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc= new Scanner(System.in);
		
		int a,b,c;
		System.out.print("1번 정수를 입력하시오. : ");
		a= sc.nextInt();
		System.out.print("2번 정수를 입력하시오. : ");
		b= sc.nextInt();
		System.out.print("3번 정수를 입력하시오. : ");
		c= sc.nextInt();
		//if(a+b>c && a+c>b && c+b>a)
		if(a+b>c) {
			if(a+c>b) {
				if(c+b>a) {
					System.out.println("삼각형이 됩니다^^!");
				}else 
					System.out.println("삼각형 실패!!!");	
			}
			else 
				System.out.println("삼각형 실패!!!");	
		}
		else 
			System.out.println("삼각형 실패!!!!!!!!!!!!");	
		sc.close();

	}

}
