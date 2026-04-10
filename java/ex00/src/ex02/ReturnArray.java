package ex02;

public class ReturnArray {

	static int [] makeArray(){
		int temp [] = new int [4];
		for(int i=0; i<temp.length; i++)
			temp[i]=i;
		return temp;
		
	}
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		int intArray[];
		intArray=makeArray();
		for(int i : intArray)
			System.out.print(i+" ");
		

	}

}
