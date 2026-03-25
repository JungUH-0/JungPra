package ex00;

import java.util.Scanner;

public class SuccessOrFail {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc= new Scanner(System.in);
		
//		System.out.print("점수를 입력하시오:");
//		int score= sc.nextInt();
//		if(score>=80)
//			System.out.println("축하합니다! 합격입니다.");
//		
		
		
		//MultipleOfThree
//		System.out.print("수를 입력하시오: ");
//		int num=sc.nextInt();
//		if(num%3==0)
//			System.out.println("3의 배수입니다.");
//		else
//			System.out.println("3의 배수가 아닙니다.");


		//Grading
//		char grade;
//		
//		System.out.print("점수를 입력하세요(0~100): ");
//		int score =sc.nextInt();//점수 읽기
//		
//		if(score>=90)//score가 90 이상
//			grade='A';
//		else if(score>=80)//score가 80 이상
//			grade='B';
//		else if(score>=70) //score가 70 이상
//			grade='C';
//		else if(score>=60) //score가 60 이상
//			grade='D';
//		else //score가 60 미만
//			grade='F';
//		System.out.println("학점은 "+grade+" 입니다.");
//		
		
		//Nestedlf
//		for(int i=0; i<10; i++) {
		System.out.print("점수를 입력하세요(0~100): ");
		int score=sc.nextInt();
		System.out.print("학년을 입력하세요(1~4): ");
		int year=sc.nextInt();
		
		if(score>=60) {//60점 이상
			if(year!=4)
				System.out.println("합격!"); //4학년 아니면 합격
			else if(score>=70)
				System.out.println("합격!"); //4학년이 70점이상이면 합격
			else
				System.out.println("불합격!"); //4학년이 70점미만이면 불합격
		}
		else //60점 미만 불합격
			System.out.println("불합격!");
		
		
////		}
//		
		sc.close();
		
	}

}
