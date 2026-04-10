package ex02;

import java.util.Scanner;

public class Array {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc = new Scanner(System.in);
		
		int intArray[] = new int [5];
		
		int max=0;
		System.out.println("양수 5개를 입력하세요.");
		for(int i =0; i<5; i++) {
			intArray[i] = sc.nextInt(); //입력받은 정수를 배열에 저장
			if(intArray[i]>max) //intArray[i]가 현재 가장 큰 수보다 크면
				max = intArray[i]; //intArray[i]를 max로 변경
		}
		System.out.println("가장 큰 수는 "+max+" 입니다.");
		sc.close();

	}

}
