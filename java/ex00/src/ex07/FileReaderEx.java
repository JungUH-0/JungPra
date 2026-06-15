package ex07;
import java.io.*;
public class FileReaderEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		FileReader fin = null;
		try {
			fin =new FileReader("c:\\windows\\system.ini");
			int c ;
			while((c=fin.read())!= -1) {
				System.out.print((char)c);
			}
			fin.close();
		} catch (Exception e) {
			// TODO: handle exception
			System.out.println("입출력 오류");
		} 
	}

}
