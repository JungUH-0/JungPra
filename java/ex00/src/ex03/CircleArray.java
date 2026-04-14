package ex03;
class Circle3{
	int radius;
	
	public Circle3(int radius) {
		this.radius = radius;
	}
	public double  getArea(){
		return 3.14*radius*radius;
	}
}

public class CircleArray {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Circle3 [] c;
		c = new Circle3[5];
		
		for (int i =0; i<c.length; i++)
			c[i] = new Circle3(i);

		for (int i = 0; i<c.length; i++)
			System.out.println((int)(c[i].getArea())+ " ");
	}

}
