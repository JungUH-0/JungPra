package ex07;
import java.io.*;

public class FileInputStreamEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		byte b[] = new byte[6];
		try {
			FileInputStream fin = new FileInputStream("c:\\Temp\\test.out");
			int n =0 , c;
			while ((c= fin.read())!=-1) {
				b[n]=(byte)c;
				n++;
			}
			System.out.println("c:\\Temp\\test.out에서 읽은 배열을 출력합니다.");
			for(int i =0; i<b.length; i++)System.out.print(b[i]+" ");
			System.out.println();
			fin.close();
		} catch (Exception e) {
			// TODO: handle exception
			System.out.println("c:\\Temp\\test.out에서 읽지 못했습니다");
		}

	}

}
