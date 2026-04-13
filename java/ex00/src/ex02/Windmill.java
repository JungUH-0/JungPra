package ex02;

public class Windmill {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		for (int i = 0; i<15; i++) {
			for(int j = 0; j<15; j++) {
				// j 
				if(i==j || i==7 || j==7)
					System.out.print("*");
				else if(j==0 && i<7)
					System.out.print("*");
				else if (j>7&& i==0)
					System.out.print("*");
				else if (i+j == 14)
					System.out.print("*");
				else if (j==14 && i>7)
					System.out.print("*");
				else if (i==14 && j<7)
					System.out.print("*");
				else 
					System.out.print(" ");
				
			}
			System.out.println();
			// i
		}
	}

}
