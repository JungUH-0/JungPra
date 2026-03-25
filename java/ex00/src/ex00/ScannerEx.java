package ex00;

import java.util.Scanner;
public class ScannerEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		System.out.println("이름, 도시, 나이 ,체중, 독신 여부를 빈칸으로 분리하여 입력하세요");
		Scanner sc = new Scanner(System.in);
		
		System.out.print("이름은:");
		String name = sc.next();
//		System.out.println("이름은 "+ name+", ");
		System.out.print("도시는:");
		String city = sc.next();
//		System.out.println("도시는 "+city+", ");
		System.out.print("나이는:");
		int age= sc.nextInt();
//		System.out.println("나이는 "+age+", ");
		System.out.print("체중은:");
		double weight = sc.nextDouble();
//		System.out.println("체중은 "+weight +", ");
		System.out.print("독신 여부:");
		boolean single = sc.nextBoolean();
//		System.out.println("독신 여부는 "+single+"입니다.");
		System.out.printf("이름은 %s, 도시는 %s, 나이는 %d, "
				+ "체중은 %f, 독신 여부는 %b",name,city,age,weight,single);
		sc.close();

	}

}
