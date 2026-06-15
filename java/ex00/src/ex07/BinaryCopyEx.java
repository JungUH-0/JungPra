package ex07;
import java.io.*;

public class BinaryCopyEx {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		File src = new File("c:\\Windows\\Web\\Wallpaper\\Windows\\img0.jpg"); 
		File dest = new File("c:\\Temp\\copyimg.jpg");
		int c ;
		try {
			FileInputStream fi = new FileInputStream(src);
			FileOutputStream fo = new FileOutputStream(dest);
			while((c=fi.read())!=-1) {
				fo.write((byte)c);
			}
			fi.close();
			fo.close();
			System.out.println("복사");
		} catch (Exception e) {
			// TODO: handle exception
			System.out.println("실패");
		}

	}

}
