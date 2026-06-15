package ex07;
import java.io.*;

public class FileOutputStreamEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		byte b [] = {7,51,3,4,-1,24};
		try {
			FileOutputStream fout = 
					new FileOutputStream("c:\\Temp\\test.out");
			for(int i = 0; i<b.length; i++) {
				fout.write(b[i]);
			}
			fout.close();
			
		} catch (Exception e) {
			// TODO: handle exception
			System.out.println("없습니다.");
			return;
		}
		System.out.println("저장");

	}

}
