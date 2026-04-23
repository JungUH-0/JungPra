package ex05;

public class AutoBoxingUnBoxingEx {
	public static void main(String[] args) {
		int n = 10;
		Integer intObject = n; //auto Boxing
		System.out.println("intObject = "+intObject);
		
		int m = intObject + 10; //auto UnBoxing
		System.out.println("m = "+m);
	}
}
