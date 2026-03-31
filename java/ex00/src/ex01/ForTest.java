package ex01;

public class ForTest {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
//		int z =0;
//		for(int i=1;i<=100; i++,System.out.println(i)) {
//			z +=i;
//		}
//		System.out.println(z);

//		int sum=0;
//		
//		for(int i=1; i<=10;i++) {
//			sum+=i;
//			System.out.print(i);
//			if(i<=9)
//				System.out.print("+");
//			else {
//				System.out.print("=");
//				System.out.println(sum);
//			}
//		}
		for(int i=1; i<10; i++) {
			for(int j=1; j<10; j++) {
				System.out.print(i+"X"+j+"="+i*j);
				System.out.print('\t');
			}
			System.out.println();
		}
	}
}
