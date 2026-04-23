package ex05;
class Point3{
	private int x,y;
	public Point3(int x,int y) {
		this.x=x; this.y=y;
	}
	public boolean equals (Object obj) {
		Point3 p = (Point3)obj; //다운 캐스팅
		if(x==p.x && y==p.y)return true;
		else return false;
	}
}


public class EqualsEx {
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Point3 a = new Point3(2,3);
		Point3 b= new Point3(2,3);
		Point3 c= new Point3(3,4);
		
		if(a==b)
			System.out.println("a==b");
		if(a.equals(b))
			System.out.println("a is equal to b");
		if(a.equals(c))
			System.out.println("a is equal to c");

	}

}
