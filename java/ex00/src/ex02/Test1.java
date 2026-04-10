package ex02;

public class Test1 {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		
//		for (int i=0; i<5; i++) {
//			for(int j =0; j<i+1; j++) {
//				System.out.print("*");
//			}
//			System.out.println();
//		}
		
//		for(int i=0; i<5; i++) {
//			for (int j=i; j<5; j++)
//				System.out.print(" ");
//			System.out.println("*");
//		}
		
		for(int i=0; i<5; i++) {
			
			for (int j=4; j>=0; j--)
				if(i==4|| i==j)
				System.out.print("*");
				else
					System.out.print(" ");
			
			for (int j=0; j<5; j++)
				if(i==4|| i==j)
				System.out.print("*");
				else
					System.out.print(" ");
			System.out.println();
		}
		
//		for (int i = 0; i<5; i++) {
//			for(int j =b; j>i; j--) {
//					System.out.print(" ");
//			}
//			for(int j =0; j<=i; j++) {
//					System.out.print("*");
//
//			}
//			System.out.println();
//		}
	}

}
