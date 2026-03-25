package ex00;

import java.util.Scanner;

public class Ex05 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc =new Scanner(System.in);
		
		int a,b;
		double c;
		int x,y;
	
		System.out.print("원의 중심과 반지름을 입력하시오.>>");
		a=sc.nextInt();
		b=sc.nextInt();
		c=sc.nextDouble();
		System.out.print("점을 입력하시오.>>");
		x=sc.nextInt();
		y=sc.nextInt();
		//원의 방정식 ((x - a)*(x - a) + (y - b)*(y - b) <= c*c)
		int xx = x-a;
		int yy= y-b;
		if((xx*xx)+(yy*yy)<=c*c)
			System.out.printf("점(%.1f,%.1f)는 원 안에 있습니다.",(double)x,(double)y); // %.nf는 소수점 n번째 자리까지 출력
		else
			System.out.printf("점(%.1f,%.1f)는 원 안에 없습니다.",(double)x,(double)y);
		sc.close();

	}

}
