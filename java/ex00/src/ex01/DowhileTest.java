package ex01;

public class DowhileTest {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		char c='a';
		do {
			System.out.print(c);
			c=(char)(c+1);
		}while(c<='z');
		System.out.println(" ");
		System.out.println("--------------------------");
		
		c='a';
		while(c<='z') {
			System.out.print(c);
			c=(char)(c+1);
		}

	}

}
