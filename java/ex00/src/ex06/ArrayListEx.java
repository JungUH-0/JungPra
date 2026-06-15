package ex06;

import java.util.ArrayList;
import java.util.Scanner;

public class ArrayListEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		//문자열만 삽입가능한 ArrayList 컬렉션 생성
		ArrayList<String> a = new ArrayList<String>();
		
		//키보드로부터 4개의 이름 입력받아 ArrayList에 삽입
		Scanner sc = new Scanner(System.in);
		for(int i=0; i<4; i++) {
			System.out.println("이름을 입력하세여 >>");
			String s = sc.next();
			a.add(s);
		}
		//ArrayList에 들어있는 모든 이름 출력
		
		for (int i=0; i<a.size(); i++) {
			//ArrayList의 i 번째 문자열 얻어오기
			String name = a.get(i);
			System.out.print(name + " ");
		}
		//가장 긴 이름 출력 
		int longestIndex = 0;
		for (int i =1 ; i<a.size(); i++) {
			if(a.get(longestIndex).length() <a.get(i).length())
				longestIndex = i;
		}
		System.out.println("\n 가장 긴 이름은 : " + a.get(longestIndex));
		sc.close();

	}

}
