package intro;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Scanner;

public class Jung {

	public static void main(String[] args) {
		// TODO Auto-generated method stub
		
		Scanner sc = new Scanner(System.in);

        System.out.println("간단 자기소개서 작성기");

        //데이터 입력 
        System.out.print("이름: ");
        String name = sc.nextLine();
        System.out.print("언어 목록: ");
        String lang = sc.nextLine();
        System.out.print("툴 목록: ");
        String tls = sc.nextLine();
        // 저장할 내용 구성하기
        String result = "--- 자기소개서 ---\n" +
                        "이름: " + name + "\n" +
                        "언어: " + lang + "\n" +
                        "툴 " + tls + "\n" +
                        "-----------------";

        // 파일 저장
        try {
            FileWriter writer = new FileWriter("정의형간단자기소개.txt");
            writer.write(result);
            writer.close(); 
            
            System.out.println("\n성공적으로 저장되었습니다! (파일명: 정의형간단자기소개.txt)");
            System.out.println("내용 확인:\n" + result);
            
        } catch (IOException e) {
            System.out.println("파일 저장 중 오류가 발생했습니다.");
            e.printStackTrace();
        } finally {
            sc.close();
        }
    }
		

	}


