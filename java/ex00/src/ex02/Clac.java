package ex02;

public class Clac {

	
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		double sum=0.0;
		
		for(int i=0; i<args.length; i++)
			sum+= Double.parseDouble(args[i]);
		System.out.println("합계"+sum);

	}

}
