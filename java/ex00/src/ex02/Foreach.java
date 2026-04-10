package ex02;

public class Foreach {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		int intArray[][] = new int [4][];
		intArray[0]= new int [3];
		intArray[1]=new int [2];
		intArray[2]=new int [3];
		intArray[3]=new int [2];
		
		int a=0;
		for(int[] i : intArray) {
//			System.out.println(i.length);
			int b=0;
			for(int j :i) {
				intArray[a][b]= (a+1)*10+b;	
				b++;
//				System.out.println(b);
			}
			a++;
		}
//		for (int i=0; i<intArray.length; i++) {
//			for(int j=0; j<intArray[i].length; j++) {
//				System.out.print(intArray[i][j]+ " ");
//			}System.out.println();
//		}
		for(int [] i :intArray) {
			for (int j : i) 
				System.out.print(j+" ");
			System.out.println();
		}
		
	}

}
