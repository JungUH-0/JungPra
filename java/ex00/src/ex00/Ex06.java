package ex00;

import java.util.Scanner;

public class Ex06 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc=new Scanner(System.in);
		
		System.out.print("달을 입력하세요(1~12)>> ");
		int m= sc.nextInt();
		
		switch(m) {
			case 3:case 4:	case 5:
				System.out.println("봄");
				break;
			case 6:	case 7:	case 8:
				System.out.println("여름");
				break;
			case 9:	case 10: case 11:
				System.out.println("가을");
				break;
			case 12: case 1: case 2:
				System.out.println("겨울");
				break;
			default :
				System.out.print("1~12사이 숫자 입력: ");
				m=sc.nextInt();
		}
		//if 문 버전
		if(m>=3 && m<=5) {
			System.out.println("봄");
		}else if(m>=6&&m<=8)
			System.out.println("여름");
		else if(m>=9&&m<=11)
			System.out.println("가을");
		else if(m>=1&&m<=2||m==12)
			System.out.println("겨울");
		else
			System.out.println("잘못입력");
		sc.close();
	}

}
