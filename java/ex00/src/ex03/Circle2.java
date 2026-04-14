package ex03;

public class Circle2 {
	int radius;
	String name;
	
	public Circle2() {
		radius=1;
		name="";
	}
	public Circle2(int r, String n) {
		radius=r;
		name=n;
	}
	public double getArea() {
		return 3.14*radius*radius;
	}

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Circle2 pizza = new Circle2(10,"자바피자");
		
		double area = pizza.getArea();
		System.out.println(pizza.name+area);
		
		Circle2 donut = new Circle2();
		donut.name = "도넛피자";
		area = donut.getArea();
		System.out.println(donut.name + area);

	}

}
