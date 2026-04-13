package ex02;

public class Fly {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		for (int i = 0; i<15; i++) {
			for(int j = 0; j<15; j++) {
				
				if(j == 7 || j ==0 || j==14)
				System.out.print("*");
				else if (i+j == 14)
					System.out.print("*");
				else if (i==j)
					System.out.print("*");
				else  
					System.out.print(" ");
			}
			System.out.println();
		}

	}

}
