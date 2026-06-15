package ex07;
import java.io.*;
import java.util.*;
public class FileWriteEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		Scanner sc = new Scanner(System.in);
		FileWriter fout = null;
		int c ;
		try {
			fout = new FileWriter("c:\\Temp\\test.txt");
			while(true) {
				String line = sc.nextLine();
				if(line.length()==0)
					break;
				fout.write(line,0,line.length());
				fout.write("\r\n",0,2);
			}
			fout.close();
		} catch (Exception e) {
			System.out.println("입출력 오류");
			// TODO: handle exception
		}
		sc.close();
	}

}
