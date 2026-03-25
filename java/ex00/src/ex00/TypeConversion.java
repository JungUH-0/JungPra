package ex00;

public class TypeConversion {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		byte b =127;
		int i = 100;
		System.out.println(b+i);
		System.out.println(10/4);
		System.out.println(10.0/4);
		System.out.println((char)0x12340041);//0x41
		System.out.println((byte)(b+i));
		System.out.printf("1번");
		System.out.println((int)2.9+1.8);
		System.out.printf("2번");
		System.out.println((int)(2.9+1.8));
		System.out.printf("3번");
		System.out.println((int)2.9+(int)1.8);
		int a = 80;
		System.out.println(a>90 ? "s" : "a");

		
	}

}
