package ex00;

import java.util.Scanner;

public class Ex02 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc= new Scanner(System.in);
		
		System.out.print("금액을 입력하시오: ");
		int money= sc.nextInt();
		int num= 50000;
		
		System.out.println("오만원권 "+(money/num)+"매");
		money = money - ((money/num)*num);
		num=10000;
		System.out.println("만원권 "+(money/num)+"매");
		money = money - ((money/num)*num);
		num=1000;
		System.out.println("천원권 "+(money/num)+"매");
		money = money - ((money/num)*num);
		num=100;
		System.out.println("백원 "+(money/num)+"매");
		money = money - ((money/num)*num);
		num=50;
		System.out.println("오십원 "+(money/num)+"매");
		money = money - ((money/num)*num);
		num=10;
		System.out.println("십원 "+(money/num)+"매");
		money = money - ((money/num)*num);
		num=1;
		System.out.println("일원 "+(money/num)+"매");
		sc.close();

	}

}
