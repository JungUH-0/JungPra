package ex00;

import java.util.Scanner;

public class Ex04 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc= new Scanner(System.in);
		int x,y;
		int a = 100,b=100;
		int c=200,d=200;
		System.out.print("점 (x,y)의 좌표를 입력하시오. >>");
		x= sc.nextInt();
		y= sc.nextInt();
//		System.out.println(x);
//		System.out.println(y);
//		if(a<=x && c>=x) {
//			if(b<=y && d>=y ) {
//				System.out.printf("(%d,%d)는 사각형 안에 있습니다.",x,y);
//			}else
//				System.out.printf("(%d,%d)는 사각형 안에 없습니다.",x,y);
//		}else
//			System.out.printf("(%d,%d)는 사각형 안에 없습니다.",x,y);
		if(a<=x && c>=x && b<=y && d>=y) {
			System.out.printf("(%d,%d)는 사각형 안에 있습니다.",x,y);
		}else
			System.out.printf("(%d,%d)는 사각형 안에 없습니다.",x,y);
		sc.close();
	}

}
