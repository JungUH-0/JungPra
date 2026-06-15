package ex07;

import java.io.*;
import java.util.Scanner;

public class BufferdIOEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		FileReader fin =null;
		int c ;
		try {
			fin = new FileReader("c:\\Temp\\test2.txt");
			BufferedOutputStream out =
					new BufferedOutputStream(System.out,5);
			while ((c=fin.read())!= -1) {
				out.write(c);
			}
			
			//파일 데이터가 모두 출력된 상태
			new Scanner(System.in).nextLine(); // 엔터키 기다림
			out.flush();//버퍼에 남아있던 문자 모두 출력
			fin.close();
			out.close();
		} catch (Exception e) {
			// TODO: handle exception
			e.printStackTrace();
		}

	}

}
