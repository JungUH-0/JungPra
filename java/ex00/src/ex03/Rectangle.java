package ex03;

import java.util.Scanner;

public class Rectangle {
	int width;
	int height;
	
	public int getArea() {
		return width*height;
	}

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Rectangle rect = new Rectangle();
		Scanner sc = new Scanner(System.in);
		System.out.print(">>");
		
		rect.width = sc.nextInt();
		rect.height =sc.nextInt();
		
		System.out.println("사각형의 면적은"+rect.getArea());
		sc.close();

	}

}
