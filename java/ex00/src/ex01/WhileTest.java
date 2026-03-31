package ex01;

import java.util.Scanner;

public class WhileTest {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		int count =0; //입력된 정수의 개수
		int sum=0; //sum 은 합
		
		Scanner sc=new Scanner(System.in);
		System.out.println("정수를 입력하고 마지막에 -1을 입력하세요.");
		
		
		//do while 문
		int n=0;
		do{ //-1이 입력되면 while 문 벗어남
			sum+=n;
			count ++;
			n=sc.nextInt(); //정수 입력
		}while(n!=-1);
		 count --;
		
		// while 문 
//		int n = sc.nextInt();//정수입력
//		while(n!=-1) { //-1이 입력되면 while 문 벗어남
//			sum+=n;
//			count ++;
//			n=sc.nextInt(); //정수 입력
//		}
		if(count==0)System.out.println("입력된 수가 없습니다");
		else {
			System.out.print("정수의 개수는"+count+"개이며");
			System.out.println("평균은"+(double)sum/count+"입니다");
					
		}
		sc.close();

	}

}
